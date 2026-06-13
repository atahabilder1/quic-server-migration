// Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
// http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
// <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
// option. This file may not be copied, modified, or distributed
// except according to those terms.

//! Connection state serialization for cross-machine server-side migration.
//!
//! This module enables exporting a QUIC connection's critical state from one
//! server (primary) and importing it on another (preferred), so that the
//! preferred server can handle PATH_CHALLENGE and continue serving traffic.

use std::net::SocketAddr;

use neqo_common::{Decoder, Encoder};
use nss::{hkdf, Cipher, TLS_VERSION_1_3};

use crate::{
    crypto::{CryptoDxAppData, CryptoDxDirection},
    packet, version::Version, Error, Res,
};

/// Serializable representation of crypto state for one direction (read or write).
#[derive(Debug)]
pub struct CryptoStateExport {
    /// Raw bytes of the TLS secret used to derive AEAD and HP keys.
    pub secret_bytes: Vec<u8>,
    /// Raw bytes of the next secret (for key updates).
    pub next_secret_bytes: Vec<u8>,
    /// The TLS cipher suite identifier.
    pub cipher: Cipher,
    /// QUIC version.
    pub version: Version,
    /// Read or Write direction.
    pub direction: CryptoDxDirection,
    /// Current epoch (key generation number).
    pub epoch: usize,
    /// Start of used packet number range.
    pub used_pn_start: packet::Number,
    /// End of used packet number range.
    pub used_pn_end: packet::Number,
    /// Minimum allowed packet number.
    pub min_pn: packet::Number,
}

/// A connection ID with its sequence number.
#[derive(Debug, Clone)]
pub struct CidExport {
    pub cid: Vec<u8>,
    pub seqno: u64,
}

/// The complete state needed to reconstruct a connection on the preferred server.
#[derive(Debug)]
pub struct MigrationState {
    /// Application-layer write key state (server -> client).
    pub write_crypto: CryptoStateExport,
    /// Application-layer read key state (client -> server).
    pub read_crypto: CryptoStateExport,
    /// Our connection IDs that the client knows about.
    pub local_cids: Vec<CidExport>,
    /// The peer's (client's) connection IDs.
    pub remote_cids: Vec<CidExport>,
    /// The client's socket address.
    pub client_addr: SocketAddr,
    /// QUIC version in use.
    pub version: Version,
}

impl MigrationState {
    /// Serialize the migration state into bytes for network transfer.
    pub fn encode(&self) -> Vec<u8> {
        let mut enc = Encoder::default();

        // Magic header
        enc.encode(&[0x4D, 0x49, 0x47, 0x52]); // "MIGR"

        // Version (4 bytes)
        enc.encode_uint(4, u64::from(self.version.wire_version()));

        // Write crypto
        Self::encode_crypto_state(&mut enc, &self.write_crypto);

        // Read crypto
        Self::encode_crypto_state(&mut enc, &self.read_crypto);

        // Local CIDs
        enc.encode_uint(2, self.local_cids.len() as u16);
        for cid in &self.local_cids {
            enc.encode_uint(8, cid.seqno);
            enc.encode_vvec(&cid.cid);
        }

        // Remote CIDs
        enc.encode_uint(2, self.remote_cids.len() as u16);
        for cid in &self.remote_cids {
            enc.encode_uint(8, cid.seqno);
            enc.encode_vvec(&cid.cid);
        }

        // Client address
        match self.client_addr {
            SocketAddr::V4(addr) => {
                enc.encode_uint(1, 4u8);
                enc.encode(&addr.ip().octets());
                enc.encode_uint(2, addr.port());
            }
            SocketAddr::V6(addr) => {
                enc.encode_uint(1, 6u8);
                enc.encode(&addr.ip().octets());
                enc.encode_uint(2, addr.port());
            }
        }

        enc.into()
    }

    /// Deserialize migration state from bytes.
    pub fn decode(data: &[u8]) -> Res<Self> {
        let mut dec = Decoder::from(data);

        // Check magic
        let magic = dec.decode(4).ok_or(Error::Internal)?;
        if magic != [0x4D, 0x49, 0x47, 0x52] {
            return Err(Error::Internal);
        }

        // Version
        let wire_version: u32 = dec.decode_uint().ok_or(Error::Internal)?;
        let version = Version::try_from(wire_version).map_err(|_| Error::Internal)?;

        // Write crypto
        let write_crypto = Self::decode_crypto_state(&mut dec, version)?;

        // Read crypto
        let read_crypto = Self::decode_crypto_state(&mut dec, version)?;

        // Local CIDs
        let num_local: u16 = dec.decode_uint().ok_or(Error::Internal)?;
        let mut local_cids = Vec::with_capacity(num_local as usize);
        for _ in 0..num_local {
            let seqno: u64 = dec.decode_uint().ok_or(Error::Internal)?;
            let cid = dec.decode_vvec().ok_or(Error::Internal)?.to_vec();
            local_cids.push(CidExport { cid, seqno });
        }

        // Remote CIDs
        let num_remote: u16 = dec.decode_uint().ok_or(Error::Internal)?;
        let mut remote_cids = Vec::with_capacity(num_remote as usize);
        for _ in 0..num_remote {
            let seqno: u64 = dec.decode_uint().ok_or(Error::Internal)?;
            let cid = dec.decode_vvec().ok_or(Error::Internal)?.to_vec();
            remote_cids.push(CidExport { cid, seqno });
        }

        // Client address
        let addr_type: u8 = dec.decode_uint().ok_or(Error::Internal)?;
        let client_addr = match addr_type {
            4 => {
                let octets: [u8; 4] = dec
                    .decode(4)
                    .ok_or(Error::Internal)?
                    .try_into()
                    .map_err(|_| Error::Internal)?;
                let port: u16 = dec.decode_uint().ok_or(Error::Internal)?;
                SocketAddr::new(std::net::Ipv4Addr::from(octets).into(), port)
            }
            6 => {
                let octets: [u8; 16] = dec
                    .decode(16)
                    .ok_or(Error::Internal)?
                    .try_into()
                    .map_err(|_| Error::Internal)?;
                let port: u16 = dec.decode_uint().ok_or(Error::Internal)?;
                SocketAddr::new(std::net::Ipv6Addr::from(octets).into(), port)
            }
            _ => return Err(Error::Internal),
        };

        Ok(Self {
            write_crypto,
            read_crypto,
            local_cids,
            remote_cids,
            client_addr,
            version,
        })
    }

    fn encode_crypto_state(enc: &mut Encoder, state: &CryptoStateExport) {
        // Secret bytes (variable length)
        enc.encode_vvec(&state.secret_bytes);
        // Next secret bytes (variable length)
        enc.encode_vvec(&state.next_secret_bytes);
        // Cipher (2 bytes)
        enc.encode_uint(2, state.cipher as u16);
        // Direction (1 byte: 0=Read, 1=Write)
        enc.encode_uint(
            1,
            match state.direction {
                CryptoDxDirection::Read => 0u8,
                CryptoDxDirection::Write => 1u8,
            },
        );
        // Epoch (4 bytes)
        enc.encode_uint(4, state.epoch as u32);
        // Packet number state (8 bytes each)
        enc.encode_uint(8, state.used_pn_start);
        enc.encode_uint(8, state.used_pn_end);
        enc.encode_uint(8, state.min_pn);
    }

    fn decode_crypto_state(dec: &mut Decoder, version: Version) -> Res<CryptoStateExport> {
        let secret_bytes = dec.decode_vvec().ok_or(Error::Internal)?.to_vec();
        let next_secret_bytes = dec.decode_vvec().ok_or(Error::Internal)?.to_vec();
        let cipher: u16 = dec.decode_uint().ok_or(Error::Internal)?;
        let dir_byte: u8 = dec.decode_uint().ok_or(Error::Internal)?;
        let direction = match dir_byte {
            0 => CryptoDxDirection::Read,
            1 => CryptoDxDirection::Write,
            _ => return Err(Error::Internal),
        };
        let epoch: u32 = dec.decode_uint().ok_or(Error::Internal)?;
        let used_pn_start: u64 = dec.decode_uint().ok_or(Error::Internal)?;
        let used_pn_end: u64 = dec.decode_uint().ok_or(Error::Internal)?;
        let min_pn: u64 = dec.decode_uint().ok_or(Error::Internal)?;

        Ok(CryptoStateExport {
            secret_bytes,
            next_secret_bytes,
            cipher: cipher as Cipher,
            version,
            direction,
            epoch: epoch as usize,
            used_pn_start,
            used_pn_end,
            min_pn,
        })
    }
}

/// Reconstruct a `CryptoDxAppData` from exported state.
/// This re-derives the AEAD and HP keys from the raw secret bytes.
pub fn import_crypto_app_data(state: &CryptoStateExport) -> Res<CryptoDxAppData> {
    let secret = hkdf::import_key(TLS_VERSION_1_3, &state.secret_bytes)?;
    CryptoDxAppData::new_from_migration(
        state.version,
        state.direction,
        &secret,
        state.cipher,
        state.epoch,
        state.used_pn_start,
        state.used_pn_end,
        state.min_pn,
        &state.next_secret_bytes,
    )
}

#[cfg(test)]
mod tests {
    use std::net::{Ipv4Addr, Ipv6Addr, SocketAddr};

    use nss::{TLS_AES_128_GCM_SHA256, TLS_CHACHA20_POLY1305_SHA256, TLS_VERSION_1_3, hkdf};

    use super::*;
    use crate::{
        crypto::{CryptoDxAppData, CryptoDxDirection},
        version::Version,
    };

    fn init_nss() {
        nss::init_db(concat!(env!("CARGO_MANIFEST_DIR"), "/../test-fixture/db")).unwrap();
    }

    fn make_test_secret(fill: u8) -> Vec<u8> {
        vec![fill; 32]
    }

    fn make_write_crypto(secret_bytes: &[u8]) -> CryptoDxAppData {
        let secret = hkdf::import_key(TLS_VERSION_1_3, secret_bytes).unwrap();
        CryptoDxAppData::new(
            Version::Version1,
            CryptoDxDirection::Write,
            &secret,
            TLS_AES_128_GCM_SHA256,
        )
        .unwrap()
    }

    fn make_read_crypto(secret_bytes: &[u8]) -> CryptoDxAppData {
        let secret = hkdf::import_key(TLS_VERSION_1_3, secret_bytes).unwrap();
        CryptoDxAppData::new(
            Version::Version1,
            CryptoDxDirection::Read,
            &secret,
            TLS_AES_128_GCM_SHA256,
        )
        .unwrap()
    }

    fn make_test_migration_state() -> MigrationState {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0xaa));
        let read = make_read_crypto(&make_test_secret(0xbb));
        MigrationState {
            write_crypto: write.export_for_migration().unwrap(),
            read_crypto: read.export_for_migration().unwrap(),
            local_cids: vec![
                CidExport { cid: vec![0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08], seqno: 0 },
                CidExport { cid: vec![0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18], seqno: 1 },
            ],
            remote_cids: vec![
                CidExport { cid: vec![0xa1, 0xa2, 0xa3, 0xa4], seqno: 0 },
            ],
            client_addr: SocketAddr::new(Ipv4Addr::new(192, 168, 1, 100).into(), 12345),
            version: Version::Version1,
        }
    }

    // ─── Encode/Decode Roundtrip Tests ───

    #[test]
    fn encode_decode_roundtrip_ipv4() {
        let state = make_test_migration_state();
        let encoded = state.encode();
        let decoded = MigrationState::decode(&encoded).unwrap();

        assert_eq!(decoded.version, state.version);
        assert_eq!(decoded.client_addr, state.client_addr);
        assert_eq!(decoded.local_cids.len(), state.local_cids.len());
        assert_eq!(decoded.remote_cids.len(), state.remote_cids.len());

        for (a, b) in decoded.local_cids.iter().zip(state.local_cids.iter()) {
            assert_eq!(a.cid, b.cid);
            assert_eq!(a.seqno, b.seqno);
        }
        for (a, b) in decoded.remote_cids.iter().zip(state.remote_cids.iter()) {
            assert_eq!(a.cid, b.cid);
            assert_eq!(a.seqno, b.seqno);
        }

        assert_eq!(decoded.write_crypto.secret_bytes, state.write_crypto.secret_bytes);
        assert_eq!(decoded.write_crypto.next_secret_bytes, state.write_crypto.next_secret_bytes);
        assert_eq!(decoded.write_crypto.cipher, state.write_crypto.cipher);
        assert_eq!(decoded.write_crypto.epoch, state.write_crypto.epoch);
        assert_eq!(decoded.write_crypto.used_pn_start, state.write_crypto.used_pn_start);
        assert_eq!(decoded.write_crypto.used_pn_end, state.write_crypto.used_pn_end);
        assert_eq!(decoded.write_crypto.min_pn, state.write_crypto.min_pn);

        assert_eq!(decoded.read_crypto.secret_bytes, state.read_crypto.secret_bytes);
        assert_eq!(decoded.read_crypto.direction, state.read_crypto.direction);
    }

    #[test]
    fn encode_decode_roundtrip_ipv6() {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0xcc));
        let read = make_read_crypto(&make_test_secret(0xdd));
        let state = MigrationState {
            write_crypto: write.export_for_migration().unwrap(),
            read_crypto: read.export_for_migration().unwrap(),
            local_cids: vec![CidExport { cid: vec![0x01; 8], seqno: 0 }],
            remote_cids: vec![CidExport { cid: vec![0x02; 4], seqno: 0 }],
            client_addr: SocketAddr::new(
                Ipv6Addr::new(0xfe80, 0, 0, 0, 0, 0, 0, 1).into(),
                54321,
            ),
            version: Version::Version1,
        };

        let encoded = state.encode();
        let decoded = MigrationState::decode(&encoded).unwrap();

        assert_eq!(decoded.client_addr, state.client_addr);
        assert_eq!(decoded.write_crypto.secret_bytes, state.write_crypto.secret_bytes);
    }

    #[test]
    fn encode_decode_empty_cids() {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0x11));
        let read = make_read_crypto(&make_test_secret(0x22));
        let state = MigrationState {
            write_crypto: write.export_for_migration().unwrap(),
            read_crypto: read.export_for_migration().unwrap(),
            local_cids: vec![],
            remote_cids: vec![],
            client_addr: SocketAddr::new(Ipv4Addr::LOCALHOST.into(), 1234),
            version: Version::Version1,
        };

        let encoded = state.encode();
        let decoded = MigrationState::decode(&encoded).unwrap();
        assert!(decoded.local_cids.is_empty());
        assert!(decoded.remote_cids.is_empty());
    }

    #[test]
    fn magic_header_present() {
        let state = make_test_migration_state();
        let encoded = state.encode();
        assert_eq!(&encoded[..4], b"MIGR");
    }

    // ─── Corrupt Data Tests ───

    #[test]
    fn decode_bad_magic() {
        let state = make_test_migration_state();
        let mut encoded = state.encode();
        encoded[0] = 0xFF;
        assert!(MigrationState::decode(&encoded).is_err());
    }

    #[test]
    fn decode_truncated_data() {
        let state = make_test_migration_state();
        let encoded = state.encode();
        // Truncate at various points
        for len in [0, 3, 4, 8, 20, encoded.len() / 2] {
            assert!(
                MigrationState::decode(&encoded[..len]).is_err(),
                "Should fail at truncation len={len}"
            );
        }
    }

    #[test]
    fn decode_invalid_addr_type() {
        let state = make_test_migration_state();
        let mut encoded = state.encode();
        // Find and corrupt the address type byte (near the end, before IP bytes)
        // The addr_type byte is 1 byte: 4 or 6. Set it to an invalid value.
        // Search backwards for the addr type byte by looking for 0x04 (IPv4)
        let len = encoded.len();
        // The address is at the end: 1 byte type + 4 bytes IP + 2 bytes port = 7 bytes from end
        encoded[len - 7] = 0xFF;
        assert!(MigrationState::decode(&encoded).is_err());
    }

    // ─── CryptoStateExport Tests ───

    #[test]
    fn crypto_state_export_preserves_direction() {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0xaa));
        let export = write.export_for_migration().unwrap();
        assert_eq!(export.direction, CryptoDxDirection::Write);

        let read = make_read_crypto(&make_test_secret(0xbb));
        let export = read.export_for_migration().unwrap();
        assert_eq!(export.direction, CryptoDxDirection::Read);
    }

    #[test]
    fn crypto_state_export_preserves_version() {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0xaa));
        let export = write.export_for_migration().unwrap();
        assert_eq!(export.version, Version::Version1);
    }

    #[test]
    fn crypto_state_export_has_nonzero_secrets() {
        init_nss();
        let write = make_write_crypto(&make_test_secret(0xaa));
        let export = write.export_for_migration().unwrap();
        assert!(!export.secret_bytes.is_empty());
        assert!(!export.next_secret_bytes.is_empty());
        // secret and next_secret should differ (next is derived via HKDF)
        assert_ne!(export.secret_bytes, export.next_secret_bytes);
    }

    // ─── Crypto Import/Export Roundtrip Tests ───

    #[test]
    fn crypto_export_import_roundtrip() {
        init_nss();
        let original = make_write_crypto(&make_test_secret(0xaa));
        let export = original.export_for_migration().unwrap();
        let imported = import_crypto_app_data(&export).unwrap();

        assert_eq!(imported.epoch(), original.epoch());
        assert_eq!(imported.dx().next_pn(), original.dx().next_pn());
    }

    #[test]
    fn imported_crypto_can_encrypt() {
        init_nss();
        let original = make_write_crypto(&make_test_secret(0xaa));
        let export = original.export_for_migration().unwrap();
        let mut imported = import_crypto_app_data(&export).unwrap();

        // Build a test packet: [header | plaintext | space for AEAD tag]
        let header = b"test_header";
        let plaintext = b"hello migration!";
        let expansion = imported.dx().expansion();
        let mut pkt = Vec::new();
        pkt.extend_from_slice(header);
        pkt.extend_from_slice(plaintext);
        pkt.resize(pkt.len() + expansion, 0);

        let pn = imported.dx().next_pn();
        let hdr_range = 0..header.len();
        let ct_len = imported.dx_mut().encrypt(pn, hdr_range, &mut pkt).unwrap();
        assert!(ct_len > 0);
    }

    #[test]
    fn cross_instance_encrypt_then_decrypt() {
        init_nss();
        let secret = make_test_secret(0xcc);

        // "Server A" creates write crypto and encrypts
        let mut writer = make_write_crypto(&secret);
        let header = b"short_hdr_";
        let plaintext = b"secret data for migration test";
        let expansion = writer.dx().expansion();

        let mut pkt = Vec::new();
        pkt.extend_from_slice(header);
        pkt.extend_from_slice(plaintext);
        pkt.resize(pkt.len() + expansion, 0);

        let pn = writer.dx().next_pn();
        let hdr_range = 0..header.len();
        let ct_len = writer.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt).unwrap();
        pkt.truncate(header.len() + ct_len);
        let encrypted_pkt = pkt.clone();

        // Export writer's state
        let export = writer.export_for_migration().unwrap();

        // "Server B" imports and creates a READ crypto from the same secret
        // (In real migration, the read side uses a different secret, but for
        // encrypt/decrypt test we need matching keys. So we test the raw import
        // path: import the write export as-is, then build a reader from the same secret.)
        let reader_secret = hkdf::import_key(TLS_VERSION_1_3, &export.secret_bytes).unwrap();
        let mut reader = CryptoDxAppData::new(
            Version::Version1,
            CryptoDxDirection::Read,
            &reader_secret,
            export.cipher,
        )
        .unwrap();

        // Decrypt
        let mut decrypt_pkt = encrypted_pkt;
        let pt_len = reader.dx_mut().decrypt(pn, hdr_range, &mut decrypt_pkt).unwrap();
        assert_eq!(&decrypt_pkt[header.len()..header.len() + pt_len], plaintext);
    }

    #[test]
    fn packet_number_continuity_after_import() {
        init_nss();
        let mut writer = make_write_crypto(&make_test_secret(0xdd));

        // Encrypt a few packets to advance the PN
        for _ in 0..5 {
            let mut pkt = vec![0u8; 32 + writer.dx().expansion()];
            pkt[0] = 0x40;
            let pn = writer.dx().next_pn();
            let _ = writer.dx_mut().encrypt(pn, 0..1, &mut pkt).unwrap();
        }
        let pn_before_export = writer.dx().next_pn();
        assert_eq!(pn_before_export, 5);

        // Export and reimport
        let export = writer.export_for_migration().unwrap();
        assert_eq!(export.used_pn_end, 5);

        let imported = import_crypto_app_data(&export).unwrap();
        // The imported state preserves the used PN range from the export
        assert_eq!(imported.dx().next_pn(), 5);
    }

    #[test]
    fn key_update_after_import() {
        init_nss();
        let original = make_write_crypto(&make_test_secret(0xee));
        let export = original.export_for_migration().unwrap();
        let imported = import_crypto_app_data(&export).unwrap();

        // Should be able to derive next key generation
        let next = imported.next().unwrap();
        assert_eq!(next.epoch(), imported.epoch() + 1);
    }

    #[test]
    fn chacha20_cipher_roundtrip() {
        init_nss();
        let secret_bytes = make_test_secret(0xff);
        let secret = hkdf::import_key(TLS_VERSION_1_3, &secret_bytes).unwrap();
        let original = CryptoDxAppData::new(
            Version::Version1,
            CryptoDxDirection::Write,
            &secret,
            TLS_CHACHA20_POLY1305_SHA256,
        )
        .unwrap();

        let export = original.export_for_migration().unwrap();
        assert_eq!(export.cipher, TLS_CHACHA20_POLY1305_SHA256);

        let state = MigrationState {
            write_crypto: export,
            read_crypto: make_read_crypto(&make_test_secret(0x11))
                .export_for_migration()
                .unwrap(),
            local_cids: vec![],
            remote_cids: vec![],
            client_addr: SocketAddr::new(Ipv4Addr::LOCALHOST.into(), 1234),
            version: Version::Version1,
        };

        let encoded = state.encode();
        let decoded = MigrationState::decode(&encoded).unwrap();
        assert_eq!(decoded.write_crypto.cipher, TLS_CHACHA20_POLY1305_SHA256);

        let reimported = import_crypto_app_data(&decoded.write_crypto).unwrap();
        assert_eq!(reimported.epoch(), original.epoch());
    }

    #[test]
    fn full_pipeline_encode_transfer_decode_decrypt() {
        init_nss();
        // Simulate the full pipeline: Server A encrypts, exports state,
        // serializes over "network", Server B deserializes, imports, decrypts.

        let write_secret = make_test_secret(0xaa);
        let read_secret = make_test_secret(0xbb);

        // Server A: encrypt a packet
        let mut server_a_writer = make_write_crypto(&write_secret);
        let header = b"hdr";
        let plaintext = b"exfiltrated data";
        let expansion = server_a_writer.dx().expansion();
        let mut pkt = Vec::new();
        pkt.extend_from_slice(header);
        pkt.extend_from_slice(plaintext);
        pkt.resize(pkt.len() + expansion, 0);

        let pn = server_a_writer.dx().next_pn();
        let hdr_range = 0..header.len();
        let ct_len = server_a_writer
            .dx_mut()
            .encrypt(pn, hdr_range.clone(), &mut pkt)
            .unwrap();
        pkt.truncate(header.len() + ct_len);
        let wire_packet = pkt;

        // Server A: export full migration state
        let migration = MigrationState {
            write_crypto: server_a_writer.export_for_migration().unwrap(),
            read_crypto: make_read_crypto(&read_secret)
                .export_for_migration()
                .unwrap(),
            local_cids: vec![CidExport {
                cid: vec![0x01; 8],
                seqno: 0,
            }],
            remote_cids: vec![CidExport {
                cid: vec![0x02; 4],
                seqno: 0,
            }],
            client_addr: SocketAddr::new(Ipv4Addr::new(141, 217, 168, 127).into(), 5000),
            version: Version::Version1,
        };

        // Serialize (simulates TCP transfer between servers)
        let wire_bytes = migration.encode();
        assert!(wire_bytes.len() > 100); // sanity check

        // Server B: deserialize
        let received = MigrationState::decode(&wire_bytes).unwrap();

        // Server B: import write crypto (to verify it can produce same ciphertext context)
        let imported_write = import_crypto_app_data(&received.write_crypto).unwrap();
        assert_eq!(imported_write.epoch(), server_a_writer.epoch());

        // Server B: build reader from same secret to decrypt the packet Server A wrote
        let reader_secret =
            hkdf::import_key(TLS_VERSION_1_3, &received.write_crypto.secret_bytes).unwrap();
        let mut reader = CryptoDxAppData::new(
            Version::Version1,
            CryptoDxDirection::Read,
            &reader_secret,
            received.write_crypto.cipher,
        )
        .unwrap();

        let mut decrypt_pkt = wire_packet;
        let pt_len = reader
            .dx_mut()
            .decrypt(pn, hdr_range, &mut decrypt_pkt)
            .unwrap();
        assert_eq!(
            &decrypt_pkt[header.len()..header.len() + pt_len],
            plaintext
        );
    }
}

//! Integration tests for cross-machine server-side migration.
//!
//! These tests verify the complete migration pipeline:
//! - Crypto state export/import across independent instances
//! - Encrypt on one instance, decrypt on another
//! - Header protection applied by writer, removed by reader after import
//! - Packet number management across migration boundary
//! - Full packet construction matching what preferred_server.rs does

use std::net::{Ipv4Addr, SocketAddr};
use std::ops::Range;

use neqo_transport::{
    crypto::{CryptoDxAppData, CryptoDxDirection},
    migration_state::{CidExport, MigrationState, import_crypto_app_data},
    version::Version,
};
use nss::{TLS_AES_128_GCM_SHA256, TLS_VERSION_1_3, hkdf};

fn init_nss() {
    nss::init_db(concat!(env!("CARGO_MANIFEST_DIR"), "/../test-fixture/db")).unwrap();
}

fn make_crypto(dir: CryptoDxDirection, secret_bytes: &[u8]) -> CryptoDxAppData {
    let secret = hkdf::import_key(TLS_VERSION_1_3, secret_bytes).unwrap();
    CryptoDxAppData::new(Version::Version1, dir, &secret, TLS_AES_128_GCM_SHA256).unwrap()
}

/// Simulate what primary_server.rs does: encrypt packets and export state.
/// Then simulate what preferred_server.rs does: import state and decrypt.
#[test]
fn full_migration_encrypt_export_import_decrypt() {
    init_nss();

    // These represent the two directions of a real connection:
    // - write_secret: server -> client (server encrypts, client decrypts)
    // - read_secret:  client -> server (client encrypts, server decrypts)
    let write_secret = vec![0xaa; 32];
    let read_secret = vec![0xbb; 32];

    // === PRIMARY SERVER: encrypt some packets, then export ===

    let mut primary_writer = make_crypto(CryptoDxDirection::Write, &write_secret);
    let mut primary_reader = make_crypto(CryptoDxDirection::Read, &read_secret);

    // Simulate the primary server sending 3 packets to client before migration
    let mut sent_packets: Vec<(u64, Vec<u8>)> = Vec::new();
    for i in 0..3 {
        let header = format!("hdr{i}").into_bytes();
        let plaintext = format!("primary server packet {i}").into_bytes();
        let expansion = primary_writer.dx().expansion();
        let mut pkt = Vec::new();
        pkt.extend_from_slice(&header);
        pkt.extend_from_slice(&plaintext);
        pkt.resize(pkt.len() + expansion, 0);

        let pn = primary_writer.dx().next_pn();
        let hdr_range = 0..header.len();
        let ct_len = primary_writer.dx_mut().encrypt(pn, hdr_range, &mut pkt).unwrap();
        pkt.truncate(header.len() + ct_len);
        sent_packets.push((pn, pkt));
    }

    // Simulate client sending 2 packets that primary reads
    let mut client_writer = make_crypto(CryptoDxDirection::Write, &read_secret);
    for i in 0..2 {
        let header = b"chdr".to_vec();
        let plaintext = format!("client packet {i}").into_bytes();
        let expansion = client_writer.dx().expansion();
        let mut pkt = Vec::new();
        pkt.extend_from_slice(&header);
        pkt.extend_from_slice(&plaintext);
        pkt.resize(pkt.len() + expansion, 0);

        let pn = client_writer.dx().next_pn();
        let hdr_range = 0..header.len();
        let ct_len = client_writer.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt).unwrap();
        pkt.truncate(header.len() + ct_len);

        // Primary server decrypts
        let pt_len = primary_reader.dx_mut().decrypt(pn, hdr_range, &mut pkt).unwrap();
        let decrypted = &pkt[header.len()..header.len() + pt_len];
        assert_eq!(decrypted, plaintext.as_slice());
    }

    // Export state after some packets have been processed
    let write_export = primary_writer.export_for_migration().unwrap();
    let read_export = primary_reader.export_for_migration().unwrap();

    assert_eq!(write_export.used_pn_end, 3); // wrote 3 packets
    assert_eq!(read_export.used_pn_end, 2);  // read 2 packets

    // === SERIALIZE (simulates TCP transfer) ===

    let migration = MigrationState {
        write_crypto: write_export,
        read_crypto: read_export,
        local_cids: vec![
            CidExport { cid: vec![0x01; 8], seqno: 0 },
            CidExport { cid: vec![0x02; 8], seqno: 1 },
        ],
        remote_cids: vec![CidExport { cid: vec![0xa1; 4], seqno: 0 }],
        client_addr: SocketAddr::new(Ipv4Addr::new(141, 217, 168, 127).into(), 5000),
        version: Version::Version1,
    };

    let wire = migration.encode();
    let received = MigrationState::decode(&wire).unwrap();

    // === PREFERRED SERVER: import and continue the connection ===

    let mut pref_writer = import_crypto_app_data(&received.write_crypto).unwrap();
    let mut pref_reader = import_crypto_app_data(&received.read_crypto).unwrap();

    // Preferred server encrypts new packets (continuing from where primary left off)
    let header = b"pref";
    let plaintext = b"PATH_RESPONSE_DATA!!";
    let expansion = pref_writer.dx().expansion();
    let mut pkt = Vec::new();
    pkt.extend_from_slice(header);
    pkt.extend_from_slice(plaintext);
    pkt.resize(pkt.len() + expansion, 0);

    let pn = pref_writer.dx().next_pn();
    let hdr_range = 0..header.len();
    let ct_len = pref_writer.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt).unwrap();
    pkt.truncate(header.len() + ct_len);

    // Client should be able to decrypt (using a reader with the same write_secret)
    let mut client_reader = make_crypto(CryptoDxDirection::Read, &write_secret);
    // Advance client reader past the 3 packets from primary
    // (In real life, client already processed those. Here we just decrypt PN=0 from pref.)
    let mut decrypt_pkt = pkt;
    let pt_len = client_reader.dx_mut().decrypt(pn, hdr_range, &mut decrypt_pkt).unwrap();
    assert_eq!(&decrypt_pkt[header.len()..header.len() + pt_len], plaintext);

    // Preferred server can also decrypt new packets from client
    let header = b"chdr";
    let plaintext = b"client says hello to preferred!";
    let expansion = client_writer.dx().expansion();
    let mut pkt = Vec::new();
    pkt.extend_from_slice(header);
    pkt.extend_from_slice(plaintext);
    pkt.resize(pkt.len() + expansion, 0);

    let pn = client_writer.dx().next_pn();
    let hdr_range = 0..header.len();
    let ct_len = client_writer.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt).unwrap();
    pkt.truncate(header.len() + ct_len);

    let pt_len = pref_reader.dx_mut().decrypt(pn, hdr_range, &mut pkt).unwrap();
    assert_eq!(&pkt[header.len()..header.len() + pt_len], plaintext);
}

/// Test header protection: writer applies HP, reader removes it.
/// This matches the real packet format used by preferred_server.rs.
#[test]
fn header_protection_roundtrip_after_migration() {
    init_nss();

    let secret = vec![0xcc; 32];
    let dcid = vec![0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08];

    // Create writer, export, import on "other server"
    let original_writer = make_crypto(CryptoDxDirection::Write, &secret);
    let export = original_writer.export_for_migration().unwrap();
    let mut writer = import_crypto_app_data(&export).unwrap();

    // Build a QUIC short header packet (matching preferred_server.rs format)
    let pn = writer.dx().next_pn();
    let pn_len = 2usize;

    let mut pkt = Vec::with_capacity(128);

    // First byte: 0FSSKPPP where F=fixed(1), K=key_phase(0), PPP=pn_len-1
    let first_byte: u8 = 0x40 | ((pn_len as u8 - 1) & 0x03);
    pkt.push(first_byte);
    pkt.extend_from_slice(&dcid);
    pkt.push(((pn >> 8) & 0xff) as u8);
    pkt.push((pn & 0xff) as u8);

    let header_len = pkt.len(); // 1 + 8 + 2 = 11

    // PATH_RESPONSE frame
    pkt.push(0x1b); // PATH_RESPONSE type
    pkt.extend_from_slice(&[0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]);

    // AEAD tag space
    let expansion = writer.dx().expansion();
    pkt.resize(pkt.len() + expansion, 0);

    // Encrypt payload
    let hdr_range: Range<usize> = 0..header_len;
    let ct_len = writer.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt).unwrap();
    let total_len = header_len + ct_len;
    pkt.truncate(total_len);

    // Apply header protection (same logic as preferred_server.rs)
    let sample_offset = header_len + (4 - pn_len);
    assert!(sample_offset + 16 <= pkt.len(), "packet too short for HP sample");
    let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();
    let mask = writer.dx().compute_mask(&sample).unwrap();
    pkt[0] ^= mask[0] & 0x1f;
    for i in 0..pn_len {
        pkt[1 + dcid.len() + i] ^= mask[1 + i];
    }

    // === Now read side: import same secret as reader and undo everything ===
    let reader_key = hkdf::import_key(TLS_VERSION_1_3, &export.secret_bytes).unwrap();
    let mut reader = CryptoDxAppData::new(
        Version::Version1,
        CryptoDxDirection::Read,
        &reader_key,
        export.cipher,
    )
    .unwrap();

    // Remove header protection (same logic as preferred_server.rs)
    let hp_sample_offset = 1 + dcid.len() + 4; // header_end + 4
    let hp_sample: [u8; 16] = pkt[hp_sample_offset..hp_sample_offset + 16].try_into().unwrap();
    let read_mask = reader.dx().compute_mask(&hp_sample).unwrap();

    pkt[0] ^= read_mask[0] & 0x1f;
    let recovered_pn_len = ((pkt[0] & 0x03) + 1) as usize;
    assert_eq!(recovered_pn_len, pn_len);

    for i in 0..recovered_pn_len {
        pkt[1 + dcid.len() + i] ^= read_mask[1 + i];
    }

    // Extract packet number
    let mut recovered_pn: u64 = 0;
    for i in 0..recovered_pn_len {
        recovered_pn = (recovered_pn << 8) | (pkt[1 + dcid.len() + i] as u64);
    }
    assert_eq!(recovered_pn, pn);

    // Decrypt
    let hdr_end = 1 + dcid.len() + recovered_pn_len;
    let pt_len = reader.dx_mut().decrypt(recovered_pn, 0..hdr_end, &mut pkt[..total_len]).unwrap();

    // Verify PATH_RESPONSE frame
    let payload = &pkt[hdr_end..hdr_end + pt_len];
    assert_eq!(payload[0], 0x1b); // PATH_RESPONSE frame type
    assert_eq!(&payload[1..9], &[0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]);
}

/// Test that state serialization size is reasonable and stable.
#[test]
fn migration_state_size_is_reasonable() {
    init_nss();

    let writer = make_crypto(CryptoDxDirection::Write, &vec![0xaa; 32]);
    let reader = make_crypto(CryptoDxDirection::Read, &vec![0xbb; 32]);

    let state = MigrationState {
        write_crypto: writer.export_for_migration().unwrap(),
        read_crypto: reader.export_for_migration().unwrap(),
        local_cids: vec![
            CidExport { cid: vec![0x01; 8], seqno: 0 },
            CidExport { cid: vec![0x02; 8], seqno: 1 },
        ],
        remote_cids: vec![CidExport { cid: vec![0xa1; 4], seqno: 0 }],
        client_addr: SocketAddr::new(Ipv4Addr::new(141, 217, 168, 127).into(), 5000),
        version: Version::Version1,
    };

    let encoded = state.encode();
    // The real migration produces ~358 bytes. Allow some margin.
    assert!(encoded.len() > 100, "too small: {}", encoded.len());
    assert!(encoded.len() < 1000, "too large: {}", encoded.len());
}

/// Verify that multiple encode/decode cycles produce identical output (idempotency).
#[test]
fn encode_is_deterministic() {
    init_nss();

    let writer = make_crypto(CryptoDxDirection::Write, &vec![0xaa; 32]);
    let reader = make_crypto(CryptoDxDirection::Read, &vec![0xbb; 32]);

    let state = MigrationState {
        write_crypto: writer.export_for_migration().unwrap(),
        read_crypto: reader.export_for_migration().unwrap(),
        local_cids: vec![CidExport { cid: vec![0x01; 8], seqno: 0 }],
        remote_cids: vec![CidExport { cid: vec![0xa1; 4], seqno: 0 }],
        client_addr: SocketAddr::new(Ipv4Addr::LOCALHOST.into(), 4433),
        version: Version::Version1,
    };

    let encoded1 = state.encode();
    // Decode and re-encode
    let decoded = MigrationState::decode(&encoded1).unwrap();
    let encoded2 = decoded.encode();
    assert_eq!(encoded1, encoded2, "encode should be deterministic/idempotent");
}

/// Test key update works after migration on both imported instances.
#[test]
fn key_update_works_after_migration() {
    init_nss();

    let writer = make_crypto(CryptoDxDirection::Write, &vec![0xaa; 32]);
    let reader = make_crypto(CryptoDxDirection::Read, &vec![0xbb; 32]);

    let write_export = writer.export_for_migration().unwrap();
    let read_export = reader.export_for_migration().unwrap();

    let imported_writer = import_crypto_app_data(&write_export).unwrap();
    let imported_reader = import_crypto_app_data(&read_export).unwrap();

    // Both should support key update
    let next_writer = imported_writer.next().unwrap();
    let next_reader = imported_reader.next().unwrap();

    assert_eq!(next_writer.epoch(), imported_writer.epoch() + 1);
    assert_eq!(next_reader.epoch(), imported_reader.epoch() + 1);

    // And another update
    let next_next_writer = next_writer.next().unwrap();
    assert_eq!(next_next_writer.epoch(), next_writer.epoch() + 1);
}

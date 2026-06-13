//! Preferred server for cross-machine QUIC server-side migration.
//!
//! Receives migration state, imports crypto keys, decrypts PATH_CHALLENGE,
//! sends PATH_RESPONSE to complete the migration.
//! After migration, continues to decrypt and ACK client data to prove
//! the connection remains fully functional.
//!
//! Supports two timing strategies via TRANSFER_TIMING env var:
//!   immediate (default) - Block and wait for state before listening for packets
//!   lazy                - Listen for packets first, fetch state on-demand when unknown CID arrives

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    env,
    net::SocketAddr,
    ops::Range,
    time::Instant,
};

use neqo_transport::migration_state::MigrationState;

/// Imported crypto state and connection metadata.
struct ConnectionState {
    read_crypto: neqo_transport::crypto::CryptoDxAppData,
    write_crypto: neqo_transport::crypto::CryptoDxAppData,
    local_cids: Vec<Vec<u8>>,
    client_cid: Vec<u8>,
    dcid_len: usize,
}

/// Import state from raw bytes.
fn import_state(data: &[u8]) -> ConnectionState {
    let state = MigrationState::decode(data).expect("Failed to decode");
    let data_len = data.len();
    println!("  State received ({data_len} bytes):");
    println!("    Client addr:  {}", state.client_addr);
    println!("    Version:      {:?}", state.version);
    println!("    Local CIDs:   {}", state.local_cids.len());
    println!();

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let read_crypto = neqo_transport::migration_state::import_crypto_app_data(&state.read_crypto)
        .expect("Failed to import read crypto");
    let write_crypto = neqo_transport::migration_state::import_crypto_app_data(&state.write_crypto)
        .expect("Failed to import write crypto");

    println!("  Crypto imported!");

    let local_cids: Vec<Vec<u8>> = state.local_cids.iter().map(|c| c.cid.clone()).collect();
    let dcid_len = local_cids.first().map_or(0, |c| c.len());
    let client_cid: Vec<u8> = state.remote_cids.first().map_or_else(Vec::new, |c| c.cid.clone());

    println!("  Client CID (for response DCID): {}", hex(&client_cid));
    println!("  Accepting {} local DCIDs (len={}):", local_cids.len(), dcid_len);
    for (i, cid) in local_cids.iter().enumerate() {
        println!("    CID[{}] seqno={}: {}", i, state.local_cids[i].seqno, hex(cid));
    }
    println!();

    ConnectionState { read_crypto, write_crypto, local_cids, client_cid, dcid_len }
}

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <quic_listen_addr> [state_listen_port]", args[0]);
        eprintln!("  quic_listen_addr:  Address to listen for QUIC packets (e.g. 141.217.168.143:4433)");
        eprintln!("  state_listen_port: (optional) For tcp backend, overrides STATE_TCP_PORT env var");
        eprintln!();
        eprintln!("  Backend selection via STATE_TRANSFER env var: tcp, http, redis_kv, redis_ps, file");
        eprintln!("  Timing strategy via TRANSFER_TIMING env var: immediate (default), lazy");
        std::process::exit(1);
    }

    let quic_addr: SocketAddr = args[1].parse().expect("Invalid QUIC listen address");
    let timing = env::var("TRANSFER_TIMING").unwrap_or_else(|_| "immediate".to_string());

    // Backward compatibility: if 2nd arg is given and STATE_TCP_PORT is not set, use it
    if args.len() >= 3 && std::env::var("STATE_TCP_PORT").is_err() {
        // SAFETY: single-threaded at this point, before any threads are spawned
        unsafe { std::env::set_var("STATE_TCP_PORT", &args[2]); }
    }

    let mut state_receiver = transfer::create_receiver();
    let inst_id = transfer::instance_id();

    println!("=== PREFERRED SERVER ===");
    println!("  QUIC listen:    {quic_addr}");
    println!("  Timing:         {timing}");
    println!();

    match timing.as_str() {
        "immediate" => run_immediate(quic_addr, &mut *state_receiver, &inst_id),
        "lazy" => run_lazy(quic_addr, state_receiver, &inst_id),
        _ => {
            eprintln!("Unknown TRANSFER_TIMING: {timing}. Use: immediate, lazy");
            std::process::exit(1);
        }
    }
}

/// Immediate timing: receive state first, then listen for packets.
fn run_immediate(
    quic_addr: SocketAddr,
    state_receiver: &mut dyn transfer::StateReceiver,
    inst_id: &str,
) {
    println!("[Timing: IMMEDIATE] Waiting for state before listening...");
    let (data, recv_metrics) = state_receiver.receive_state(inst_id).expect("Failed to receive state");
    recv_metrics.print_summary();

    let mut conn = import_state(&data);
    run_packet_loop(quic_addr, &mut conn);
}

/// Lazy timing: start receiving state in background, but only import crypto
/// when the first QUIC packet arrives. This ensures that TCP Push and Redis
/// Pub/Sub work (receiver is listening from startup), while the actual crypto
/// import is deferred until needed.
fn run_lazy(
    quic_addr: SocketAddr,
    state_receiver: Box<dyn transfer::StateReceiver>,
    inst_id: &str,
) {
    println!("[Timing: LAZY] Starting state receiver in background...");
    println!("[Timing: LAZY] Crypto import deferred until first packet arrives.");
    println!("Listening on {quic_addr}...");
    println!();

    // Start receiving state in a background thread.
    // The receiver begins listening/subscribing immediately (so TCP and Pub/Sub work),
    // but the result is sent through a channel for the main thread to use later.
    let inst_id_owned = inst_id.to_string();
    let (tx, rx) = std::sync::mpsc::channel::<(Vec<u8>, transfer::TransferMetrics)>();

    std::thread::spawn(move || {
        let mut receiver = state_receiver;
        match receiver.receive_state(&inst_id_owned) {
            Ok(result) => {
                let _ = tx.send(result);
            }
            Err(e) => {
                eprintln!("  [Background] Failed to receive state: {e}");
            }
        }
    });

    let socket = std::net::UdpSocket::bind(quic_addr).expect("UDP bind failed");
    let mut buf = vec![0u8; 65536];
    let mut conn: Option<ConnectionState> = None;
    let mut buffered_packets: Vec<(Vec<u8>, SocketAddr)> = Vec::new();
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;

    // Track whether state has arrived in background
    let mut state_data: Option<(Vec<u8>, transfer::TransferMetrics)> = None;

    loop {
        // Non-blocking check: has the background thread received state?
        if state_data.is_none() {
            if let Ok(result) = rx.try_recv() {
                println!("  [Timing: LAZY] State arrived in background ({} bytes)", result.0.len());
                state_data = Some(result);
            }
        }

        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                let packet = buf[..size].to_vec();
                println!("  << {size} bytes from {src}");

                if size < 10 || (packet[0] & 0x80) != 0 {
                    println!("     Long header or too small, skipping");
                    continue;
                }

                // If crypto not yet imported, try to import now
                if conn.is_none() {
                    let import_start = Instant::now();

                    // Check if state already arrived in background
                    let data = if let Some(sd) = state_data.take() {
                        Some(sd)
                    } else {
                        // State not yet available -- wait briefly for it
                        println!("     First packet received -- waiting for state...");
                        // Block-wait with timeout for state from background thread
                        match rx.recv_timeout(std::time::Duration::from_secs(5)) {
                            Ok(result) => Some(result),
                            Err(_) => {
                                eprintln!("     Timeout waiting for state, buffering packet");
                                buffered_packets.push((packet, src));
                                continue;
                            }
                        }
                    };

                    if let Some((raw_data, recv_metrics)) = data {
                        let import_time = import_start.elapsed();
                        recv_metrics.print_summary();
                        println!("  [Timing: LAZY] Crypto imported on-demand in {:?}", import_time);
                        conn = Some(import_state(&raw_data));
                        buffered_packets.push((packet, src));

                        // Process all buffered packets
                        if let Some(ref mut c) = conn {
                            for (pkt_data, pkt_src) in buffered_packets.drain(..) {
                                process_packet(&pkt_data, pkt_src, c, &socket, &mut received_pns, &mut path_validated);
                            }
                        }
                        continue;
                    }
                }

                // We have state, process normally
                if let Some(ref mut c) = conn {
                    process_packet(&packet, src, c, &socket, &mut received_pns, &mut path_validated);
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
            Err(e) => {
                eprintln!("  recv error: {e}");
            }
        }
    }
}

/// Process a single QUIC packet with imported crypto state.
fn process_packet(
    packet: &[u8],
    src: SocketAddr,
    conn: &mut ConnectionState,
    socket: &std::net::UdpSocket,
    received_pns: &mut Vec<u64>,
    path_validated: &mut bool,
) {
    let size = packet.len();
    if size < 1 + conn.dcid_len + 4 + 16 {
        println!("     Too small, skipping");
        return;
    }

    if (packet[0] & 0x80) != 0 {
        println!("     Long header, skipping");
        return;
    }

    let dcid = &packet[1..1 + conn.dcid_len];
    if !conn.local_cids.iter().any(|c| c.as_slice() == dcid) {
        println!("     DCID {} not ours", hex(dcid));
        return;
    }
    println!("     DCID {} MATCH", hex(dcid));

    let header_end = 1 + conn.dcid_len;
    let sample_offset = header_end + 4;
    if sample_offset + 16 > size {
        println!("     Not enough data for HP sample");
        return;
    }

    let mut pkt = packet.to_vec();
    let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();

    let mask = match conn.read_crypto.dx().compute_mask(&sample) {
        Ok(m) => m,
        Err(e) => {
            println!("     HP mask error: {e:?}");
            return;
        }
    };

    pkt[0] ^= mask[0] & 0x1f;
    let pn_len = ((pkt[0] & 0x03) + 1) as usize;
    for i in 0..pn_len {
        pkt[header_end + i] ^= mask[1 + i];
    }

    let mut pn: u64 = 0;
    for i in 0..pn_len {
        pn = (pn << 8) | (pkt[header_end + i] as u64);
    }
    println!("     PN={pn} (len={pn_len})");

    let hdr_range: Range<usize> = 0..(header_end + pn_len);

    match conn.read_crypto.dx_mut().decrypt(pn, hdr_range.clone(), &mut pkt[..size]) {
        Ok(pt_len) => {
            let payload = &pkt[hdr_range.end..hdr_range.end + pt_len];
            println!("     DECRYPTED! {} bytes plaintext", pt_len);

            received_pns.push(pn);

            let had_challenge = parse_and_respond(payload, pn, &conn.client_cid, &mut conn.write_crypto, socket, src);
            if had_challenge {
                *path_validated = true;
            }

            if *path_validated && !had_challenge && !received_pns.is_empty() {
                let largest_pn = *received_pns.iter().max().unwrap();
                send_ack(largest_pn, received_pns, &conn.client_cid, &mut conn.write_crypto, socket, src);
            }
        }
        Err(e) => {
            println!("     Decrypt FAILED: {e:?}");
        }
    }
}

/// Immediate timing packet loop (uses ConnectionState directly).
fn run_packet_loop(quic_addr: SocketAddr, conn: &mut ConnectionState) {
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;

    println!("Listening on {quic_addr}...");
    println!();
    let socket = std::net::UdpSocket::bind(quic_addr).expect("UDP bind failed");
    let mut buf = vec![0u8; 65536];

    loop {
        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                let packet = buf[..size].to_vec();
                println!("  << {size} bytes from {src}");
                process_packet(&packet, src, conn, &socket, &mut received_pns, &mut path_validated);
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
            Err(e) => {
                eprintln!("  recv error: {e}");
            }
        }
    }
}

/// Parse frames from a decrypted QUIC packet.
/// Returns true if a PATH_CHALLENGE was found (and responded to).
fn parse_and_respond(
    payload: &[u8],
    _recv_pn: u64,
    client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket,
    client_addr: SocketAddr,
) -> bool {
    let mut offset = 0;
    let mut found_challenge = false;

    let mut padding_count = 0u32;
    while offset < payload.len() {
        // QUIC frame type is varint
        let (frame_type, consumed) = read_varint(&payload[offset..]);
        offset += consumed;

        match frame_type {
            0x00 => {
                // PADDING - just count, don't print each one
                padding_count += 1;
            }
            0x01 => {
                // PING
                println!("       Frame: PING");
            }
            0x1a => {
                // PATH_CHALLENGE
                if offset + 8 > payload.len() {
                    println!("       Frame: PATH_CHALLENGE (truncated)");
                    break;
                }
                let challenge_data = &payload[offset..offset + 8];
                offset += 8;
                println!("       Frame: PATH_CHALLENGE data={}", hex(challenge_data));
                println!();
                println!("    >>> SENDING PATH_RESPONSE <<<");

                // Build and send PATH_RESPONSE
                send_path_response(challenge_data, client_cid, write_crypto, socket, client_addr);
                found_challenge = true;
            }
            0x1b => {
                // PATH_RESPONSE
                if offset + 8 > payload.len() { break; }
                println!("       Frame: PATH_RESPONSE");
                offset += 8;
            }
            0x02 | 0x03 => {
                // ACK frame
                // Parse: largest_ack(varint) + ack_delay(varint) + ack_range_count(varint) + first_ack_range(varint)
                let (largest_ack, c) = read_varint(&payload[offset..]); offset += c;
                let (_ack_delay, c) = read_varint(&payload[offset..]); offset += c;
                let (ack_range_count, c) = read_varint(&payload[offset..]); offset += c;
                let (first_range, c) = read_varint(&payload[offset..]); offset += c;
                println!("       Frame: ACK largest={largest_ack} ranges={ack_range_count} first_range={first_range}");
                // Skip additional ACK ranges
                for _ in 0..ack_range_count {
                    let (_gap, c) = read_varint(&payload[offset..]); offset += c;
                    let (_range, c) = read_varint(&payload[offset..]); offset += c;
                }
                if frame_type == 0x03 {
                    // ECN counts
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                }
            }
            // STREAM frames: 0x08-0x0f
            0x08..=0x0f => {
                let has_off = (frame_type & 0x04) != 0;
                let has_len = (frame_type & 0x02) != 0;
                let has_fin = (frame_type & 0x01) != 0;

                let (stream_id, c) = read_varint(&payload[offset..]); offset += c;
                let stream_offset = if has_off {
                    let (o, c) = read_varint(&payload[offset..]); offset += c;
                    o
                } else {
                    0
                };
                let data_len = if has_len {
                    let (l, c) = read_varint(&payload[offset..]); offset += c;
                    l as usize
                } else {
                    payload.len() - offset
                };

                if offset + data_len > payload.len() {
                    println!("       Frame: STREAM (truncated)");
                    break;
                }

                let stream_data = &payload[offset..offset + data_len];
                offset += data_len;

                println!("       Frame: STREAM id={stream_id} offset={stream_offset} len={data_len} fin={has_fin}");
                println!("       >>> POST-MIGRATION DATA RECEIVED <<<");
                println!("       Data (hex): {}", hex(stream_data));
                if let Ok(text) = std::str::from_utf8(stream_data) {
                    println!("       Data (text): {text}");
                }
            }
            // NEW_CONNECTION_ID
            0x18 => {
                let (_seq, c) = read_varint(&payload[offset..]); offset += c;
                let (_retire, c) = read_varint(&payload[offset..]); offset += c;
                if offset >= payload.len() { break; }
                let cid_len = payload[offset] as usize; offset += 1;
                offset += cid_len; // CID bytes
                offset += 16; // stateless reset token
                println!("       Frame: NEW_CONNECTION_ID");
            }
            // ACK_FREQUENCY
            0xaf => {
                let (_seq, c) = read_varint(&payload[offset..]); offset += c;
                let (_tol, c) = read_varint(&payload[offset..]); offset += c;
                let (_delay, c) = read_varint(&payload[offset..]); offset += c;
                if offset < payload.len() { offset += 1; } // ignore_order
                println!("       Frame: ACK_FREQUENCY");
            }
            _ => {
                println!("       Frame: type=0x{frame_type:02x} (unknown, stopping parse)");
                break;
            }
        }
    }
    if padding_count > 0 {
        println!("       ({padding_count} PADDING frames)");
    }
    found_challenge
}

fn send_path_response(
    challenge_data: &[u8],
    client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket,
    client_addr: SocketAddr,
) {
    let pn = write_crypto.dx().next_pn();
    let pn_len = 2usize;

    println!("    Response PN={pn}, client_cid_len={}, expansion={}", client_cid.len(), write_crypto.dx().expansion());

    // Short header: [first_byte] [DCID=client_cid] [PN] [payload] [AEAD tag]
    let mut pkt = Vec::with_capacity(1300);

    // First byte: 0FSSKPPP where F=fixed(1), K=key_phase(0), PPP=pn_len-1
    let first_byte: u8 = 0x40 | ((pn_len as u8 - 1) & 0x03);
    pkt.push(first_byte);

    // DCID = client's connection ID
    pkt.extend_from_slice(client_cid);

    // Packet number (2 bytes)
    pkt.push(((pn >> 8) & 0xff) as u8);
    pkt.push((pn & 0xff) as u8);

    let header_len = pkt.len(); // 1 + client_cid.len() + 2

    // PATH_RESPONSE frame: type 0x1b + 8 bytes data
    pkt.push(0x1b);
    pkt.extend_from_slice(challenge_data);

    // Pad to minimum size for path validation (1200 bytes per RFC 9000 Section 8.2.1)
    // PADDING frames (type 0x00)
    let expansion = write_crypto.dx().expansion();
    let min_size = 1200;
    let payload_so_far = pkt.len() - header_len;
    if header_len + payload_so_far + expansion < min_size {
        let pad_needed = min_size - header_len - payload_so_far - expansion;
        pkt.extend(std::iter::repeat(0u8).take(pad_needed));
    }

    // Add space for AEAD tag
    pkt.resize(pkt.len() + expansion, 0);

    // Encrypt
    let hdr_range: Range<usize> = 0..header_len;
    match write_crypto.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt) {
        Ok(ct_len) => {
            let total_len = header_len + ct_len;
            pkt.truncate(total_len);

            // Apply header protection
            // Sample is at 4 bytes after PN start (header_len is after PN)
            // So sample_offset = header_len + (4 - pn_len)
            let sample_offset = header_len + (4 - pn_len);
            if sample_offset + 16 <= pkt.len() {
                let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();
                if let Ok(mask) = write_crypto.dx().compute_mask(&sample) {
                    pkt[0] ^= mask[0] & 0x1f;
                    for i in 0..pn_len {
                        pkt[1 + client_cid.len() + i] ^= mask[1 + i];
                    }
                }
            }

            match socket.send_to(&pkt, client_addr) {
                Ok(n) => println!("    >> Sent PATH_RESPONSE ({n} bytes, DCID={}) to {client_addr}", hex(client_cid)),
                Err(e) => eprintln!("    >> Send failed: {e}"),
            }
        }
        Err(e) => {
            eprintln!("    >> Encrypt failed: {e:?}");
        }
    }
}

fn send_ack(
    largest_pn: u64,
    received_pns: &[u64],
    client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket,
    client_addr: SocketAddr,
) {
    let pn = write_crypto.dx().next_pn();
    let pn_len = 2usize;

    let mut pkt = Vec::with_capacity(128);

    // Short header
    let first_byte: u8 = 0x40 | ((pn_len as u8 - 1) & 0x03);
    pkt.push(first_byte);
    pkt.extend_from_slice(client_cid);
    pkt.push(((pn >> 8) & 0xff) as u8);
    pkt.push((pn & 0xff) as u8);

    let header_len = pkt.len();

    // ACK frame (type 0x02)
    // Format: type(varint) + largest_ack(varint) + ack_delay(varint) + range_count(varint) + first_range(varint)
    pkt.push(0x02); // ACK frame type
    encode_varint(&mut pkt, largest_pn); // largest acknowledged
    encode_varint(&mut pkt, 0); // ack delay
    encode_varint(&mut pkt, 0); // ack range count (just one contiguous range)

    // First ACK range: how many packets before largest_pn are also acknowledged
    let min_pn = received_pns.iter().min().copied().unwrap_or(largest_pn);
    let first_range = largest_pn - min_pn;
    encode_varint(&mut pkt, first_range);

    // Add space for AEAD tag
    let expansion = write_crypto.dx().expansion();
    pkt.resize(pkt.len() + expansion, 0);

    // Encrypt
    let hdr_range: Range<usize> = 0..header_len;
    match write_crypto.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt) {
        Ok(ct_len) => {
            let total_len = header_len + ct_len;
            pkt.truncate(total_len);

            // Apply header protection
            let sample_offset = header_len + (4 - pn_len);
            if sample_offset + 16 <= pkt.len() {
                let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();
                if let Ok(mask) = write_crypto.dx().compute_mask(&sample) {
                    pkt[0] ^= mask[0] & 0x1f;
                    for i in 0..pn_len {
                        pkt[1 + client_cid.len() + i] ^= mask[1 + i];
                    }
                }
            }

            match socket.send_to(&pkt, client_addr) {
                Ok(n) => println!("    >> Sent ACK ({n} bytes, largest_pn={largest_pn}) to {client_addr}"),
                Err(e) => eprintln!("    >> ACK send failed: {e}"),
            }
        }
        Err(e) => {
            eprintln!("    >> ACK encrypt failed: {e:?}");
        }
    }
}

fn encode_varint(buf: &mut Vec<u8>, val: u64) {
    if val < 0x3f {
        buf.push(val as u8);
    } else if val < 0x3fff {
        buf.push(((val >> 8) as u8) | 0x40);
        buf.push((val & 0xff) as u8);
    } else if val < 0x3fff_ffff {
        let bytes = (val as u32).to_be_bytes();
        buf.push(bytes[0] | 0x80);
        buf.extend_from_slice(&bytes[1..]);
    } else {
        let bytes = val.to_be_bytes();
        buf.push(bytes[0] | 0xc0);
        buf.extend_from_slice(&bytes[1..]);
    }
}

fn read_varint(data: &[u8]) -> (u64, usize) {
    if data.is_empty() {
        return (0, 0);
    }
    let first = data[0];
    let len = 1 << (first >> 6);
    if data.len() < len {
        return (0, 0);
    }
    let mut val = u64::from(first & 0x3f);
    for i in 1..len {
        val = (val << 8) | u64::from(data[i]);
    }
    (val, len)
}

fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}

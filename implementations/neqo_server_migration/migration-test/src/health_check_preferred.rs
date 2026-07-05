//! Health-Check Preferred Server — same as preferred-server but with heartbeat.
//!
//! Adds a background heartbeat thread that:
//!   - TCP mode: listens on a separate heartbeat port for health probes
//!   - Redis mode: publishes "alive" to Redis key "preferred:health" every 1s (TTL 3s)
//!
//! Health check mode via HEALTH_CHECK env var: tcp (default), redis
//!
//! Usage:
//!   health-check-preferred <quic_listen_addr> [state_listen_port]
//!
//! Example:
//!   health-check-preferred 141.217.168.143:4433 9999

// This binary wraps the existing preferred server functionality and adds heartbeat.
// Rather than duplicating the entire preferred_server.rs, we re-export its main
// functionality and add heartbeat on top.
//
// Since Rust doesn't support calling another binary's main(), we spawn the heartbeat
// thread and then exec the same logic as preferred_server.

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    collections::HashMap,
    env,
    io::Write,
    net::{IpAddr, SocketAddr, TcpListener, TcpStream},
    ops::Range,
    sync::{Arc, atomic::{AtomicBool, Ordering}},
    time::{Duration, Instant},
};

use neqo_transport::migration_state::MigrationState;

const IDLE_TIMEOUT: Duration = Duration::from_secs(30);
const MAX_PACKETS_PER_SEC: u64 = 1000;
const MAX_PER_IP_PER_SEC: u64 = 100;
const MAX_RECEIVED_PNS: usize = 10_000;
const MAX_BUFFERED_PACKETS: usize = 50;
const MAX_DECRYPT_FAILURES: u64 = 20;
const BLOCK_DURATION: Duration = Duration::from_secs(10);
const HEARTBEAT_INTERVAL: Duration = Duration::from_secs(1);
const REDIS_HEARTBEAT_TTL: u64 = 3;

/// Start heartbeat thread based on HEALTH_CHECK mode.
fn start_heartbeat(quic_addr: SocketAddr) {
    let mode = env::var("HEALTH_CHECK").unwrap_or_else(|_| "tcp".to_string());

    match mode.as_str() {
        "tcp" => {
            // Dedicated health check TCP listener (separate from state transfer port!)
            let health_port: u16 = env::var("HEALTH_PORT")
                .unwrap_or_else(|_| "9998".to_string())
                .parse()
                .unwrap_or(9998);
            println!("  [Heartbeat] TCP mode: health listener on port {health_port}");

            std::thread::spawn(move || {
                let listener = TcpListener::bind(format!("0.0.0.0:{health_port}"))
                    .unwrap_or_else(|e| panic!("Failed to bind health port {health_port}: {e}"));
                loop {
                    // Accept health probe connections and immediately close them.
                    // The primary just does a TCP connect to check if we're alive.
                    match listener.accept() {
                        Ok((stream, _)) => { drop(stream); }
                        Err(_) => { std::thread::sleep(Duration::from_millis(100)); }
                    }
                }
            });
        }
        "redis" => {
            let url = env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://141.217.168.200:6379".to_string());
            println!("  [Heartbeat] Redis mode: publishing to preferred:health every {HEARTBEAT_INTERVAL:?} (TTL {REDIS_HEARTBEAT_TTL}s)");
            println!("  [Heartbeat] Redis URL: {url}");

            std::thread::spawn(move || {
                loop {
                    if let Err(e) = publish_redis_heartbeat(&url) {
                        eprintln!("  [Heartbeat] Redis publish failed: {e}");
                    }
                    std::thread::sleep(HEARTBEAT_INTERVAL);
                }
            });
        }
        _ => {
            println!("  [Heartbeat] Mode '{mode}' not recognized, no heartbeat");
        }
    }
}

/// Publish heartbeat to Redis using raw RESP protocol (no dependency).
fn publish_redis_heartbeat(url: &str) -> Result<(), String> {
    let addr = url
        .strip_prefix("redis://")
        .unwrap_or("141.217.168.200:6379");
    let mut stream = TcpStream::connect_timeout(
        &addr.parse().map_err(|e| format!("parse: {e}"))?,
        Duration::from_millis(500),
    ).map_err(|e| format!("connect: {e}"))?;

    stream.set_write_timeout(Some(Duration::from_millis(500))).ok();
    stream.set_read_timeout(Some(Duration::from_millis(500))).ok();

    // SET preferred:health alive EX 3
    // RESP: *5\r\n$3\r\nSET\r\n$16\r\npreferred:health\r\n$5\r\nalive\r\n$2\r\nEX\r\n$1\r\n3\r\n
    let cmd = format!(
        "*5\r\n$3\r\nSET\r\n$16\r\npreferred:health\r\n$5\r\nalive\r\n$2\r\nEX\r\n$1\r\n{}\r\n",
        REDIS_HEARTBEAT_TTL
    );
    stream.write_all(cmd.as_bytes()).map_err(|e| format!("write: {e}"))?;
    stream.flush().map_err(|e| format!("flush: {e}"))?;

    let mut buf = [0u8; 32];
    std::io::Read::read(&mut stream, &mut buf).map_err(|e| format!("read: {e}"))?;
    Ok(())
}

// ─── The rest is identical to preferred_server.rs ───
// We include the same packet processing logic.

struct RateLimiter {
    per_ip: HashMap<IpAddr, IpState>,
    global_count: u64,
    global_window_start: Instant,
    dropped_total: u64,
    last_drop_log: Instant,
}

struct IpState {
    count: u64,
    window_start: Instant,
    decrypt_failures: u64,
    blocked_until: Option<Instant>,
}

impl RateLimiter {
    fn new() -> Self {
        Self {
            per_ip: HashMap::new(),
            global_count: 0,
            global_window_start: Instant::now(),
            dropped_total: 0,
            last_drop_log: Instant::now(),
        }
    }

    fn check(&mut self, src: IpAddr) -> bool {
        let now = Instant::now();
        if now.duration_since(self.global_window_start) >= Duration::from_secs(1) {
            self.global_count = 0;
            self.global_window_start = now;
        }
        self.global_count += 1;
        if self.global_count > MAX_PACKETS_PER_SEC {
            self.record_drop(now);
            return false;
        }
        let ip_state = self.per_ip.entry(src).or_insert(IpState {
            count: 0, window_start: now, decrypt_failures: 0, blocked_until: None,
        });
        if let Some(until) = ip_state.blocked_until {
            if now < until { self.record_drop(now); return false; }
            ip_state.blocked_until = None;
            ip_state.decrypt_failures = 0;
            ip_state.count = 0;
            ip_state.window_start = now;
        }
        if now.duration_since(ip_state.window_start) >= Duration::from_secs(1) {
            ip_state.count = 0;
            ip_state.window_start = now;
        }
        ip_state.count += 1;
        if ip_state.count > MAX_PER_IP_PER_SEC {
            ip_state.blocked_until = Some(now + BLOCK_DURATION);
            self.record_drop(now);
            return false;
        }
        true
    }

    fn record_decrypt_failure(&mut self, src: IpAddr) {
        let now = Instant::now();
        let ip_state = self.per_ip.entry(src).or_insert(IpState {
            count: 0, window_start: now, decrypt_failures: 0, blocked_until: None,
        });
        ip_state.decrypt_failures += 1;
        if ip_state.decrypt_failures >= MAX_DECRYPT_FAILURES {
            ip_state.blocked_until = Some(now + BLOCK_DURATION);
        }
    }

    fn record_drop(&mut self, now: Instant) {
        self.dropped_total += 1;
        if now.duration_since(self.last_drop_log) >= Duration::from_secs(5) && self.dropped_total > 0 {
            self.last_drop_log = now;
        }
    }

    fn cleanup_stale(&mut self) {
        let now = Instant::now();
        self.per_ip.retain(|_, state| {
            if let Some(until) = state.blocked_until { now < until }
            else { now.duration_since(state.window_start) < Duration::from_secs(60) }
        });
    }
}

enum FrameAction {
    Normal { had_challenge: bool },
    ConnectionClosed { error_code: u64, reason: String },
}

struct ConnectionState {
    read_crypto: neqo_transport::crypto::CryptoDxAppData,
    write_crypto: neqo_transport::crypto::CryptoDxAppData,
    local_cids: Vec<Vec<u8>>,
    client_cid: Vec<u8>,
    dcid_len: usize,
}

fn secure_wipe(buf: &mut [u8]) {
    for byte in buf.iter_mut() {
        unsafe { std::ptr::write_volatile(byte, 0) };
    }
}

fn import_state(data: &[u8]) -> ConnectionState {
    let state = MigrationState::decode(data).expect("Failed to decode");
    println!("  State received ({} bytes):", data.len());
    println!("    Client addr:  {}", state.client_addr);
    println!("    Version:      {:?}", state.version);
    println!("    Local CIDs:   {}", state.local_cids.len());

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let read_crypto = neqo_transport::migration_state::import_crypto_app_data(&state.read_crypto)
        .expect("Failed to import read crypto");
    let write_crypto = neqo_transport::migration_state::import_crypto_app_data(&state.write_crypto)
        .expect("Failed to import write crypto");

    println!("  Crypto imported!");

    let local_cids: Vec<Vec<u8>> = state.local_cids.iter().map(|c| c.cid.clone()).collect();
    let dcid_len = local_cids.first().map_or(0, |c| c.len());
    let client_cid = state.remote_cids.first().map_or_else(Vec::new, |c| c.cid.clone());

    println!("  Client CID: {}", hex(&client_cid));
    println!("  Accepting {} local DCIDs (len={}):", local_cids.len(), dcid_len);
    for (i, cid) in local_cids.iter().enumerate() {
        println!("    CID[{i}] seqno={}: {}", state.local_cids[i].seqno, hex(cid));
    }
    println!();

    ConnectionState { read_crypto, write_crypto, local_cids, client_cid, dcid_len }
}

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <quic_listen_addr> [state_listen_port]", args[0]);
        eprintln!();
        eprintln!("  HEALTH_CHECK env var: tcp (default), redis");
        std::process::exit(1);
    }

    let quic_addr: SocketAddr = args[1].parse().expect("Invalid QUIC listen address");
    let timing = env::var("TRANSFER_TIMING").unwrap_or_else(|_| "immediate".to_string());

    if args.len() >= 3 && std::env::var("STATE_TCP_PORT").is_err() {
        unsafe { std::env::set_var("STATE_TCP_PORT", &args[2]); }
    }

    println!("=== HEALTH-CHECK PREFERRED SERVER ===");
    println!("  QUIC listen:    {quic_addr}");
    println!("  Timing:         {timing}");

    // Start heartbeat thread
    start_heartbeat(quic_addr);
    println!();

    let mut state_receiver = transfer::create_receiver();
    let inst_id = transfer::instance_id();

    match timing.as_str() {
        "immediate" => run_immediate(quic_addr, &mut *state_receiver, &inst_id),
        "lazy" => run_lazy(quic_addr, state_receiver, &inst_id),
        _ => {
            eprintln!("Unknown TRANSFER_TIMING: {timing}");
            std::process::exit(1);
        }
    }
}

fn run_immediate(
    quic_addr: SocketAddr,
    state_receiver: &mut dyn transfer::StateReceiver,
    inst_id: &str,
) {
    println!("[Timing: IMMEDIATE] Waiting for state...");
    let (mut data, recv_metrics) = state_receiver.receive_state(inst_id).expect("Failed to receive state");
    recv_metrics.print_summary();

    let mut conn = import_state(&data);
    secure_wipe(&mut data);
    drop(data);
    println!("  [Security] Raw migration state wiped");

    run_packet_loop(quic_addr, &mut conn);
}

fn run_lazy(
    quic_addr: SocketAddr,
    state_receiver: Box<dyn transfer::StateReceiver>,
    inst_id: &str,
) {
    println!("[Timing: LAZY] Starting state receiver in background...");

    let inst_id_owned = inst_id.to_string();
    let (tx, rx) = std::sync::mpsc::channel::<(Vec<u8>, transfer::TransferMetrics)>();

    std::thread::spawn(move || {
        let mut receiver = state_receiver;
        match receiver.receive_state(&inst_id_owned) {
            Ok(result) => { let _ = tx.send(result); }
            Err(e) => { eprintln!("  [Background] Failed: {e}"); }
        }
    });

    let socket = std::net::UdpSocket::bind(quic_addr).expect("UDP bind failed");
    socket.set_read_timeout(Some(Duration::from_secs(1))).expect("set_read_timeout failed");
    let mut buf = vec![0u8; 65536];
    let mut conn: Option<ConnectionState> = None;
    let mut buffered_packets: Vec<(Vec<u8>, SocketAddr)> = Vec::new();
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;
    let mut last_packet_time = Instant::now();
    let mut rate_limiter = RateLimiter::new();
    let mut cleanup_counter: u64 = 0;
    let mut state_data: Option<(Vec<u8>, transfer::TransferMetrics)> = None;

    loop {
        if conn.is_some() && last_packet_time.elapsed() > IDLE_TIMEOUT {
            println!("  [Security] Idle timeout");
            if let Some(ref mut c) = conn { secure_cleanup(c); }
            return;
        }
        cleanup_counter += 1;
        if cleanup_counter % 1000 == 0 { rate_limiter.cleanup_stale(); }

        if state_data.is_none() {
            if let Ok(result) = rx.try_recv() {
                state_data = Some(result);
            }
        }

        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                if !rate_limiter.check(src.ip()) { continue; }
                last_packet_time = Instant::now();
                let packet = buf[..size].to_vec();

                if size < 10 || (packet[0] & 0x80) != 0 { continue; }

                if conn.is_none() {
                    let data = if let Some(sd) = state_data.take() {
                        Some(sd)
                    } else {
                        match rx.recv_timeout(Duration::from_secs(5)) {
                            Ok(result) => Some(result),
                            Err(_) => {
                                if buffered_packets.len() < MAX_BUFFERED_PACKETS {
                                    buffered_packets.push((packet, src));
                                }
                                continue;
                            }
                        }
                    };
                    if let Some((mut raw_data, recv_metrics)) = data {
                        recv_metrics.print_summary();
                        conn = Some(import_state(&raw_data));
                        secure_wipe(&mut raw_data);
                        drop(raw_data);
                        if buffered_packets.len() < MAX_BUFFERED_PACKETS {
                            buffered_packets.push((packet, src));
                        }
                        if let Some(ref mut c) = conn {
                            for (pkt_data, pkt_src) in buffered_packets.drain(..) {
                                if let PacketAction::ConnectionClosed = process_packet(&pkt_data, pkt_src, c, &socket, &mut received_pns, &mut path_validated, &mut rate_limiter) {
                                    secure_cleanup(c);
                                    return;
                                }
                            }
                        }
                        continue;
                    }
                }

                if let Some(ref mut c) = conn {
                    if let PacketAction::ConnectionClosed = process_packet(&packet, src, c, &socket, &mut received_pns, &mut path_validated, &mut rate_limiter) {
                        secure_cleanup(c);
                        return;
                    }
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut => {}
            Err(e) => { eprintln!("  recv error: {e}"); }
        }
    }
}

enum PacketAction { Continue, ConnectionClosed }

fn process_packet(
    packet: &[u8], src: SocketAddr, conn: &mut ConnectionState,
    socket: &std::net::UdpSocket, received_pns: &mut Vec<u64>,
    path_validated: &mut bool, rate_limiter: &mut RateLimiter,
) -> PacketAction {
    let size = packet.len();
    if size < 1 + conn.dcid_len + 4 + 16 { return PacketAction::Continue; }
    if (packet[0] & 0x80) != 0 { return PacketAction::Continue; }

    let dcid = &packet[1..1 + conn.dcid_len];
    if !conn.local_cids.iter().any(|c| c.as_slice() == dcid) { return PacketAction::Continue; }
    println!("     DCID {} MATCH", hex(dcid));

    let header_end = 1 + conn.dcid_len;
    let sample_offset = header_end + 4;
    if sample_offset + 16 > size { return PacketAction::Continue; }

    let mut pkt = packet.to_vec();
    let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();

    let mask = match conn.read_crypto.dx().compute_mask(&sample) {
        Ok(m) => m,
        Err(_) => return PacketAction::Continue,
    };

    pkt[0] ^= mask[0] & 0x1f;
    let pn_len = ((pkt[0] & 0x03) + 1) as usize;
    for i in 0..pn_len { pkt[header_end + i] ^= mask[1 + i]; }

    let mut pn: u64 = 0;
    for i in 0..pn_len { pn = (pn << 8) | (pkt[header_end + i] as u64); }
    println!("     PN={pn} (len={pn_len})");

    let hdr_range: Range<usize> = 0..(header_end + pn_len);

    match conn.read_crypto.dx_mut().decrypt(pn, hdr_range.clone(), &mut pkt[..size]) {
        Ok(pt_len) => {
            let payload = &pkt[hdr_range.end..hdr_range.end + pt_len];
            println!("     DECRYPTED! {pt_len} bytes");

            if received_pns.len() >= MAX_RECEIVED_PNS {
                let keep_from = received_pns.len() / 2;
                received_pns.drain(..keep_from);
            }
            received_pns.push(pn);

            match parse_and_respond(payload, pn, &conn.client_cid, &mut conn.write_crypto, socket, src) {
                FrameAction::ConnectionClosed { error_code, reason } => {
                    println!("    CONNECTION_CLOSE error=0x{error_code:x} reason={reason}");
                    return PacketAction::ConnectionClosed;
                }
                FrameAction::Normal { had_challenge } => {
                    if had_challenge { *path_validated = true; }
                    if *path_validated && !had_challenge && !received_pns.is_empty() {
                        let largest_pn = *received_pns.iter().max().unwrap();
                        send_ack(largest_pn, received_pns, &conn.client_cid, &mut conn.write_crypto, socket, src);
                    }
                }
            }
        }
        Err(_) => { rate_limiter.record_decrypt_failure(src.ip()); }
    }
    PacketAction::Continue
}

fn run_packet_loop(quic_addr: SocketAddr, conn: &mut ConnectionState) {
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;
    let mut rate_limiter = RateLimiter::new();
    let mut cleanup_counter: u64 = 0;

    println!("Listening on {quic_addr}...");
    let socket = std::net::UdpSocket::bind(quic_addr).expect("UDP bind failed");
    socket.set_read_timeout(Some(Duration::from_secs(1))).expect("set_read_timeout failed");
    let mut buf = vec![0u8; 65536];
    let mut last_packet_time = Instant::now();

    loop {
        if last_packet_time.elapsed() > IDLE_TIMEOUT {
            println!("  [Security] Idle timeout");
            secure_cleanup(conn);
            return;
        }
        cleanup_counter += 1;
        if cleanup_counter % 1000 == 0 { rate_limiter.cleanup_stale(); }

        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                if !rate_limiter.check(src.ip()) { continue; }
                last_packet_time = Instant::now();
                let packet = buf[..size].to_vec();
                println!("  << {size} bytes from {src}");
                match process_packet(&packet, src, conn, &socket, &mut received_pns, &mut path_validated, &mut rate_limiter) {
                    PacketAction::ConnectionClosed => { secure_cleanup(conn); return; }
                    PacketAction::Continue => {}
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut => {}
            Err(e) => { eprintln!("  recv error: {e}"); }
        }
    }
}

fn secure_cleanup(conn: &mut ConnectionState) {
    for cid in &mut conn.local_cids { secure_wipe(cid); }
    secure_wipe(&mut conn.client_cid);
    println!("  [Security] Cleanup complete.");
}

fn parse_and_respond(
    payload: &[u8], _recv_pn: u64, client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket, client_addr: SocketAddr,
) -> FrameAction {
    let mut offset = 0;
    let mut found_challenge = false;
    let mut padding_count = 0u32;

    while offset < payload.len() {
        let (frame_type, consumed) = read_varint(&payload[offset..]);
        offset += consumed;

        match frame_type {
            0x00 => { padding_count += 1; }
            0x01 => { println!("       Frame: PING"); }
            0x1c | 0x1d => {
                let (error_code, c) = read_varint(&payload[offset..]); offset += c;
                if frame_type == 0x1c {
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                }
                let (reason_len, c) = read_varint(&payload[offset..]); offset += c;
                let reason = if reason_len > 0 && offset + reason_len as usize <= payload.len() {
                    let rb = &payload[offset..offset + reason_len as usize];
                    offset += reason_len as usize;
                    std::str::from_utf8(rb).unwrap_or("<non-utf8>").to_string()
                } else { String::new() };
                return FrameAction::ConnectionClosed { error_code, reason };
            }
            0x1a => {
                if offset + 8 > payload.len() { break; }
                let challenge_data = &payload[offset..offset + 8];
                offset += 8;
                println!("       Frame: PATH_CHALLENGE data={}", hex(challenge_data));
                println!("    >>> SENDING PATH_RESPONSE <<<");
                send_path_response(challenge_data, client_cid, write_crypto, socket, client_addr);
                found_challenge = true;
            }
            0x1b => { if offset + 8 > payload.len() { break; } offset += 8; }
            0x02 | 0x03 => {
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                let (ack_range_count, c) = read_varint(&payload[offset..]); offset += c;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                for _ in 0..ack_range_count {
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                }
                if frame_type == 0x03 {
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                    let (_, c) = read_varint(&payload[offset..]); offset += c;
                }
            }
            0x08..=0x0f => {
                let has_off = (frame_type & 0x04) != 0;
                let has_len = (frame_type & 0x02) != 0;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                if has_off { let (_, c) = read_varint(&payload[offset..]); offset += c; }
                let data_len = if has_len {
                    let (l, c) = read_varint(&payload[offset..]); offset += c; l as usize
                } else { payload.len() - offset };
                if offset + data_len > payload.len() { break; }
                offset += data_len;
            }
            0x18 => {
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                if offset >= payload.len() { break; }
                let cid_len = payload[offset] as usize; offset += 1;
                offset += cid_len + 16;
            }
            0xaf => {
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                let (_, c) = read_varint(&payload[offset..]); offset += c;
                if offset < payload.len() { offset += 1; }
            }
            _ => { break; }
        }
    }
    FrameAction::Normal { had_challenge: found_challenge }
}

fn send_path_response(
    challenge_data: &[u8], client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket, client_addr: SocketAddr,
) {
    let pn = write_crypto.dx().next_pn();
    let pn_len = 2usize;
    let mut pkt = Vec::with_capacity(1300);
    let first_byte: u8 = 0x40 | ((pn_len as u8 - 1) & 0x03);
    pkt.push(first_byte);
    pkt.extend_from_slice(client_cid);
    pkt.push(((pn >> 8) & 0xff) as u8);
    pkt.push((pn & 0xff) as u8);
    let header_len = pkt.len();
    pkt.push(0x1b);
    pkt.extend_from_slice(challenge_data);
    let expansion = write_crypto.dx().expansion();
    let min_size = 1200;
    let payload_so_far = pkt.len() - header_len;
    if header_len + payload_so_far + expansion < min_size {
        let pad_needed = min_size - header_len - payload_so_far - expansion;
        pkt.extend(std::iter::repeat(0u8).take(pad_needed));
    }
    pkt.resize(pkt.len() + expansion, 0);
    let hdr_range: Range<usize> = 0..header_len;
    match write_crypto.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt) {
        Ok(ct_len) => {
            let total_len = header_len + ct_len;
            pkt.truncate(total_len);
            let sample_offset = header_len + (4 - pn_len);
            if sample_offset + 16 <= pkt.len() {
                let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();
                if let Ok(mask) = write_crypto.dx().compute_mask(&sample) {
                    pkt[0] ^= mask[0] & 0x1f;
                    for i in 0..pn_len { pkt[1 + client_cid.len() + i] ^= mask[1 + i]; }
                }
            }
            match socket.send_to(&pkt, client_addr) {
                Ok(n) => println!("    >> Sent PATH_RESPONSE ({n} bytes) to {client_addr}"),
                Err(e) => eprintln!("    >> Send failed: {e}"),
            }
        }
        Err(e) => { eprintln!("    >> Encrypt failed: {e:?}"); }
    }
}

fn send_ack(
    largest_pn: u64, received_pns: &[u64], client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket, client_addr: SocketAddr,
) {
    let pn = write_crypto.dx().next_pn();
    let pn_len = 2usize;
    let mut pkt = Vec::with_capacity(128);
    let first_byte: u8 = 0x40 | ((pn_len as u8 - 1) & 0x03);
    pkt.push(first_byte);
    pkt.extend_from_slice(client_cid);
    pkt.push(((pn >> 8) & 0xff) as u8);
    pkt.push((pn & 0xff) as u8);
    let header_len = pkt.len();
    pkt.push(0x02);
    encode_varint(&mut pkt, largest_pn);
    encode_varint(&mut pkt, 0);
    encode_varint(&mut pkt, 0);
    let min_pn = received_pns.iter().min().copied().unwrap_or(largest_pn);
    encode_varint(&mut pkt, largest_pn - min_pn);
    let expansion = write_crypto.dx().expansion();
    pkt.resize(pkt.len() + expansion, 0);
    let hdr_range: Range<usize> = 0..header_len;
    match write_crypto.dx_mut().encrypt(pn, hdr_range.clone(), &mut pkt) {
        Ok(ct_len) => {
            pkt.truncate(header_len + ct_len);
            let sample_offset = header_len + (4 - pn_len);
            if sample_offset + 16 <= pkt.len() {
                let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();
                if let Ok(mask) = write_crypto.dx().compute_mask(&sample) {
                    pkt[0] ^= mask[0] & 0x1f;
                    for i in 0..pn_len { pkt[1 + client_cid.len() + i] ^= mask[1 + i]; }
                }
            }
            let _ = socket.send_to(&pkt, client_addr);
        }
        Err(_) => {}
    }
}

fn encode_varint(buf: &mut Vec<u8>, val: u64) {
    if val < 0x3f { buf.push(val as u8); }
    else if val < 0x3fff { buf.push(((val >> 8) as u8) | 0x40); buf.push((val & 0xff) as u8); }
    else if val < 0x3fff_ffff {
        let bytes = (val as u32).to_be_bytes();
        buf.push(bytes[0] | 0x80); buf.extend_from_slice(&bytes[1..]);
    } else {
        let bytes = val.to_be_bytes();
        buf.push(bytes[0] | 0xc0); buf.extend_from_slice(&bytes[1..]);
    }
}

fn read_varint(data: &[u8]) -> (u64, usize) {
    if data.is_empty() { return (0, 0); }
    let first = data[0];
    let len = 1 << (first >> 6);
    if data.len() < len { return (0, 0); }
    let mut val = u64::from(first & 0x3f);
    for i in 1..len { val = (val << 8) | u64::from(data[i]); }
    (val, len)
}

fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}

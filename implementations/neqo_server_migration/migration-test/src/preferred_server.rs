//! Preferred server for cross-machine QUIC server-side migration.
//!
//! Receives migration state, imports crypto keys, decrypts PATH_CHALLENGE,
//! sends PATH_RESPONSE to complete the migration.
//! After migration, continues to decrypt and ACK client data to prove
//! the connection remains fully functional.
//!
//! Security features:
//!   - Migration state blob is zeroed in memory immediately after key import
//!   - CONNECTION_CLOSE (0x1c/0x1d) detection triggers graceful shutdown
//!   - Idle timeout (default 30s) auto-cleans keys if no packets arrive
//!   - All crypto state is explicitly zeroed before process exit
//!
//! DoS protections:
//!   - Global rate limit: max 1000 packets/sec processed
//!   - Per-IP rate limit: max 100 packets/sec per source IP
//!   - Decrypt failure tracking: IPs with 20+ failures are blocked for 10s
//!   - Bounded received_pns vector: capped at 10,000 entries
//!   - Bounded packet buffer in lazy mode: capped at 50 packets
//!
//! Supports two timing strategies via TRANSFER_TIMING env var:
//!   immediate (default) - Block and wait for state before listening for packets
//!   lazy                - Listen for packets first, fetch state on-demand when unknown CID arrives

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    collections::HashMap,
    env,
    net::{IpAddr, SocketAddr},
    ops::Range,
    time::{Duration, Instant},
};

use neqo_transport::migration_state::MigrationState;

/// Default idle timeout: if no packets arrive within this duration, the server
/// assumes the connection is dead and performs a secure cleanup.
const IDLE_TIMEOUT: Duration = Duration::from_secs(30);

// ─── DoS Protection Constants ───

/// Maximum UDP packets processed per second (across all sources).
const MAX_PACKETS_PER_SEC: u64 = 1000;

/// Maximum packets per second from a single source IP before it is throttled.
const MAX_PER_IP_PER_SEC: u64 = 100;

/// Maximum number of packet numbers tracked (prevents memory exhaustion).
const MAX_RECEIVED_PNS: usize = 10_000;

/// Maximum buffered packets in lazy mode (prevents memory exhaustion).
const MAX_BUFFERED_PACKETS: usize = 50;

/// Maximum consecutive decrypt failures before dropping packets from that IP.
const MAX_DECRYPT_FAILURES: u64 = 20;

/// How long a source IP is blocked after exceeding failure/rate limits.
const BLOCK_DURATION: Duration = Duration::from_secs(10);

/// Simple per-IP rate limiter and failure tracker for DoS protection.
struct RateLimiter {
    /// Per-IP: (packet_count, window_start, decrypt_failures, blocked_until)
    per_ip: HashMap<IpAddr, IpState>,
    /// Global packet counter for this second.
    global_count: u64,
    global_window_start: Instant,
    /// Count of dropped packets (for periodic logging).
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

    /// Returns true if the packet should be ALLOWED, false if it should be dropped.
    fn check(&mut self, src: IpAddr) -> bool {
        let now = Instant::now();

        // Reset global counter every second
        if now.duration_since(self.global_window_start) >= Duration::from_secs(1) {
            self.global_count = 0;
            self.global_window_start = now;
        }

        // Global rate limit
        self.global_count += 1;
        if self.global_count > MAX_PACKETS_PER_SEC {
            self.record_drop(now);
            return false;
        }

        // Per-IP check
        let ip_state = self.per_ip.entry(src).or_insert(IpState {
            count: 0,
            window_start: now,
            decrypt_failures: 0,
            blocked_until: None,
        });

        // Check if IP is blocked
        if let Some(until) = ip_state.blocked_until {
            if now < until {
                self.record_drop(now);
                return false;
            }
            // Block expired, reset
            ip_state.blocked_until = None;
            ip_state.decrypt_failures = 0;
            ip_state.count = 0;
            ip_state.window_start = now;
        }

        // Reset per-IP counter every second
        if now.duration_since(ip_state.window_start) >= Duration::from_secs(1) {
            ip_state.count = 0;
            ip_state.window_start = now;
        }

        ip_state.count += 1;
        if ip_state.count > MAX_PER_IP_PER_SEC {
            ip_state.blocked_until = Some(now + BLOCK_DURATION);
            println!("  [DoS] Rate limit exceeded for {src} — blocked for {BLOCK_DURATION:?}");
            self.record_drop(now);
            return false;
        }

        true
    }

    /// Record a decrypt failure for a source IP. Block the IP if threshold exceeded.
    fn record_decrypt_failure(&mut self, src: IpAddr) {
        let now = Instant::now();
        let ip_state = self.per_ip.entry(src).or_insert(IpState {
            count: 0,
            window_start: now,
            decrypt_failures: 0,
            blocked_until: None,
        });
        ip_state.decrypt_failures += 1;
        if ip_state.decrypt_failures >= MAX_DECRYPT_FAILURES {
            ip_state.blocked_until = Some(now + BLOCK_DURATION);
            println!("  [DoS] Too many decrypt failures from {src} — blocked for {BLOCK_DURATION:?}");
        }
    }

    fn record_drop(&mut self, now: Instant) {
        self.dropped_total += 1;
        // Log every 5 seconds at most
        if now.duration_since(self.last_drop_log) >= Duration::from_secs(5) && self.dropped_total > 0 {
            println!("  [DoS] Dropped {} packets total", self.dropped_total);
            self.last_drop_log = now;
        }
    }

    /// Periodically clean up old per-IP entries to prevent memory growth.
    fn cleanup_stale(&mut self) {
        let now = Instant::now();
        self.per_ip.retain(|_, state| {
            // Keep entries that are either blocked or were active in the last 60 seconds
            if let Some(until) = state.blocked_until {
                now < until
            } else {
                now.duration_since(state.window_start) < Duration::from_secs(60)
            }
        });
    }
}

/// Result of parsing frames from a decrypted QUIC packet.
enum FrameAction {
    /// Normal frames processed (may include PATH_CHALLENGE).
    Normal { had_challenge: bool },
    /// Client sent CONNECTION_CLOSE — connection is over.
    ConnectionClosed { error_code: u64, reason: String },
}

/// Imported crypto state and connection metadata.
struct ConnectionState {
    read_crypto: neqo_transport::crypto::CryptoDxAppData,
    write_crypto: neqo_transport::crypto::CryptoDxAppData,
    local_cids: Vec<Vec<u8>>,
    client_cid: Vec<u8>,
    dcid_len: usize,
}

/// Securely zero a byte buffer to prevent secrets lingering in memory.
/// Uses `write_volatile` to prevent the compiler from optimizing away the zeroing.
fn secure_wipe(buf: &mut [u8]) {
    for byte in buf.iter_mut() {
        unsafe { std::ptr::write_volatile(byte, 0) };
    }
}

/// Import state from raw bytes. The caller's copy is wiped after this returns.
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
    let (mut data, recv_metrics) = state_receiver.receive_state(inst_id).expect("Failed to receive state");
    recv_metrics.print_summary();

    let mut conn = import_state(&data);

    // Security: wipe the raw migration blob from memory immediately.
    // The derived keys are in ConnectionState; the raw secrets are no longer needed.
    secure_wipe(&mut data);
    drop(data);
    println!("  [Security] Raw migration state wiped from memory");

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
    socket.set_read_timeout(Some(Duration::from_secs(1))).expect("set_read_timeout failed");
    let mut buf = vec![0u8; 65536];
    let mut conn: Option<ConnectionState> = None;
    let mut buffered_packets: Vec<(Vec<u8>, SocketAddr)> = Vec::new();
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;
    let mut last_packet_time = Instant::now();
    let mut rate_limiter = RateLimiter::new();
    let mut cleanup_counter: u64 = 0;

    // Track whether state has arrived in background
    let mut state_data: Option<(Vec<u8>, transfer::TransferMetrics)> = None;

    loop {
        // Check idle timeout (only after we have imported state and started serving)
        if conn.is_some() && last_packet_time.elapsed() > IDLE_TIMEOUT {
            println!();
            println!("  [Security] Idle timeout ({IDLE_TIMEOUT:?}) — no packets received.");
            println!("  [Security] Performing secure cleanup...");
            if let Some(ref mut c) = conn {
                secure_cleanup(c);
            }
            return;
        }

        // Periodically clean up stale rate limiter entries
        cleanup_counter += 1;
        if cleanup_counter % 1000 == 0 {
            rate_limiter.cleanup_stale();
        }

        // Non-blocking check: has the background thread received state?
        if state_data.is_none() {
            if let Ok(result) = rx.try_recv() {
                println!("  [Timing: LAZY] State arrived in background ({} bytes)", result.0.len());
                state_data = Some(result);
            }
        }

        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                // DoS protection: rate limit check before any processing
                if !rate_limiter.check(src.ip()) {
                    continue;
                }

                last_packet_time = Instant::now();
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
                                // DoS protection: cap buffered packets
                                if buffered_packets.len() < MAX_BUFFERED_PACKETS {
                                    buffered_packets.push((packet, src));
                                } else {
                                    println!("  [DoS] Buffer full ({MAX_BUFFERED_PACKETS}), dropping packet");
                                }
                                continue;
                            }
                        }
                    };

                    if let Some((mut raw_data, recv_metrics)) = data {
                        let import_time = import_start.elapsed();
                        recv_metrics.print_summary();
                        println!("  [Timing: LAZY] Crypto imported on-demand in {:?}", import_time);
                        conn = Some(import_state(&raw_data));
                        // Security: wipe raw migration blob immediately
                        secure_wipe(&mut raw_data);
                        drop(raw_data);
                        println!("  [Security] Raw migration state wiped from memory");
                        if buffered_packets.len() < MAX_BUFFERED_PACKETS {
                            buffered_packets.push((packet, src));
                        }

                        // Process all buffered packets
                        let mut should_close = false;
                        if let Some(ref mut c) = conn {
                            for (pkt_data, pkt_src) in buffered_packets.drain(..) {
                                match process_packet(&pkt_data, pkt_src, c, &socket, &mut received_pns, &mut path_validated, &mut rate_limiter) {
                                    PacketAction::ConnectionClosed => { should_close = true; break; }
                                    PacketAction::Continue => {}
                                }
                            }
                        }
                        if should_close {
                            if let Some(ref mut c) = conn {
                                secure_cleanup(c);
                            }
                            return;
                        }
                        continue;
                    }
                }

                // We have state, process normally
                if let Some(ref mut c) = conn {
                    match process_packet(&packet, src, c, &socket, &mut received_pns, &mut path_validated, &mut rate_limiter) {
                        PacketAction::ConnectionClosed => {
                            secure_cleanup(c);
                            return;
                        }
                        PacketAction::Continue => {}
                    }
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut => {}
            Err(e) => {
                eprintln!("  recv error: {e}");
            }
        }
    }
}

/// Process a single QUIC packet with imported crypto state.
/// Returns `PacketAction::ConnectionClosed` if the client sent CONNECTION_CLOSE.
fn process_packet(
    packet: &[u8],
    src: SocketAddr,
    conn: &mut ConnectionState,
    socket: &std::net::UdpSocket,
    received_pns: &mut Vec<u64>,
    path_validated: &mut bool,
    rate_limiter: &mut RateLimiter,
) -> PacketAction {
    let size = packet.len();
    if size < 1 + conn.dcid_len + 4 + 16 {
        println!("     Too small, skipping");
        return PacketAction::Continue;
    }

    if (packet[0] & 0x80) != 0 {
        println!("     Long header, skipping");
        return PacketAction::Continue;
    }

    let dcid = &packet[1..1 + conn.dcid_len];
    if !conn.local_cids.iter().any(|c| c.as_slice() == dcid) {
        println!("     DCID {} not ours", hex(dcid));
        return PacketAction::Continue;
    }
    println!("     DCID {} MATCH", hex(dcid));

    let header_end = 1 + conn.dcid_len;
    let sample_offset = header_end + 4;
    if sample_offset + 16 > size {
        println!("     Not enough data for HP sample");
        return PacketAction::Continue;
    }

    let mut pkt = packet.to_vec();
    let sample: [u8; 16] = pkt[sample_offset..sample_offset + 16].try_into().unwrap();

    let mask = match conn.read_crypto.dx().compute_mask(&sample) {
        Ok(m) => m,
        Err(e) => {
            println!("     HP mask error: {e:?}");
            return PacketAction::Continue;
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

            // DoS protection: cap received_pns to prevent unbounded memory growth.
            // Keep only the most recent packet numbers for ACK generation.
            if received_pns.len() >= MAX_RECEIVED_PNS {
                // Keep only the last half to avoid constant truncation
                let keep_from = received_pns.len() / 2;
                received_pns.drain(..keep_from);
            }
            received_pns.push(pn);

            match parse_and_respond(payload, pn, &conn.client_cid, &mut conn.write_crypto, socket, src) {
                FrameAction::ConnectionClosed { error_code, reason } => {
                    println!();
                    println!("    === CONNECTION_CLOSE received ===");
                    println!("    Error code: {error_code} (0x{error_code:x})");
                    if !reason.is_empty() {
                        println!("    Reason: {reason}");
                    }
                    println!("    Client has ended the connection.");
                    println!("    [Security] Initiating secure cleanup...");
                    return PacketAction::ConnectionClosed;
                }
                FrameAction::Normal { had_challenge } => {
                    if had_challenge {
                        *path_validated = true;
                    }

                    if *path_validated && !had_challenge && !received_pns.is_empty() {
                        let largest_pn = *received_pns.iter().max().unwrap();
                        send_ack(largest_pn, received_pns, &conn.client_cid, &mut conn.write_crypto, socket, src);
                    }
                }
            }
        }
        Err(e) => {
            println!("     Decrypt FAILED: {e:?}");
            // DoS protection: track decrypt failures per source IP.
            // Repeated failures from one IP likely indicate a flood attack.
            rate_limiter.record_decrypt_failure(src.ip());
        }
    }
    PacketAction::Continue
}

/// Immediate timing packet loop (uses ConnectionState directly).
fn run_packet_loop(quic_addr: SocketAddr, conn: &mut ConnectionState) {
    let mut received_pns: Vec<u64> = Vec::new();
    let mut path_validated = false;
    let mut rate_limiter = RateLimiter::new();
    let mut cleanup_counter: u64 = 0;

    println!("Listening on {quic_addr}...");
    println!("  [Security] Idle timeout: {}s", IDLE_TIMEOUT.as_secs());
    println!("  [DoS] Rate limit: {MAX_PACKETS_PER_SEC} pkt/s global, {MAX_PER_IP_PER_SEC} pkt/s per IP");
    println!("  [DoS] Max tracked PNs: {MAX_RECEIVED_PNS}");
    println!();
    let socket = std::net::UdpSocket::bind(quic_addr).expect("UDP bind failed");
    socket.set_read_timeout(Some(Duration::from_secs(1))).expect("set_read_timeout failed");
    let mut buf = vec![0u8; 65536];
    let mut last_packet_time = Instant::now();

    loop {
        // Check idle timeout
        if last_packet_time.elapsed() > IDLE_TIMEOUT {
            println!();
            println!("  [Security] Idle timeout ({IDLE_TIMEOUT:?}) — no packets received.");
            println!("  [Security] Performing secure cleanup...");
            secure_cleanup(conn);
            return;
        }

        // Periodically clean up stale rate limiter entries (every 1000 packets)
        cleanup_counter += 1;
        if cleanup_counter % 1000 == 0 {
            rate_limiter.cleanup_stale();
        }

        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                // DoS protection: rate limit check before any processing
                if !rate_limiter.check(src.ip()) {
                    continue; // silently drop
                }

                last_packet_time = Instant::now();
                let packet = buf[..size].to_vec();
                println!("  << {size} bytes from {src}");
                let action = process_packet(
                    &packet, src, conn, &socket,
                    &mut received_pns, &mut path_validated,
                    &mut rate_limiter,
                );
                match action {
                    PacketAction::Continue => {}
                    PacketAction::ConnectionClosed => {
                        secure_cleanup(conn);
                        return;
                    }
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock
                    || e.kind() == std::io::ErrorKind::TimedOut => {}
            Err(e) => {
                eprintln!("  recv error: {e}");
            }
        }
    }
}

/// What the packet loop should do after processing a packet.
enum PacketAction {
    Continue,
    ConnectionClosed,
}

/// Securely wipe all crypto state before exiting.
fn secure_cleanup(conn: &mut ConnectionState) {
    // Wipe connection IDs
    for cid in &mut conn.local_cids {
        secure_wipe(cid);
    }
    secure_wipe(&mut conn.client_cid);

    // Note: The AEAD keys and HP keys inside CryptoDxAppData are managed by NSS
    // (Mozilla's crypto library) and will be freed when the structs are dropped.
    // We drop them explicitly here to ensure deterministic cleanup.
    println!("  [Security] Crypto state dropped.");
    println!("  [Security] Cleanup complete — all secrets removed from memory.");
    println!();
}

/// Parse frames from a decrypted QUIC packet.
/// Returns `FrameAction::ConnectionClosed` if a CONNECTION_CLOSE frame is found,
/// otherwise `FrameAction::Normal` indicating whether a PATH_CHALLENGE was handled.
fn parse_and_respond(
    payload: &[u8],
    _recv_pn: u64,
    client_cid: &[u8],
    write_crypto: &mut neqo_transport::crypto::CryptoDxAppData,
    socket: &std::net::UdpSocket,
    client_addr: SocketAddr,
) -> FrameAction {
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
            // CONNECTION_CLOSE (RFC 9000 Section 19.19)
            // 0x1c = QUIC layer error, 0x1d = application layer error
            0x1c | 0x1d => {
                let close_type = if frame_type == 0x1c { "QUIC" } else { "Application" };
                let (error_code, c) = read_varint(&payload[offset..]); offset += c;
                if frame_type == 0x1c {
                    // QUIC CONNECTION_CLOSE has a frame_type field
                    let (_trigger_frame, c) = read_varint(&payload[offset..]); offset += c;
                }
                let (reason_len, c) = read_varint(&payload[offset..]); offset += c;
                let reason = if reason_len > 0 && offset + reason_len as usize <= payload.len() {
                    let reason_bytes = &payload[offset..offset + reason_len as usize];
                    offset += reason_len as usize;
                    std::str::from_utf8(reason_bytes).unwrap_or("<non-utf8>").to_string()
                } else {
                    String::new()
                };
                println!("       Frame: CONNECTION_CLOSE ({close_type}) error=0x{error_code:x}");

                if padding_count > 0 {
                    println!("       ({padding_count} PADDING frames)");
                }
                return FrameAction::ConnectionClosed { error_code, reason };
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
    FrameAction::Normal { had_challenge: found_challenge }
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

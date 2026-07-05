//! WebSeed Primary Server - serves large files via HTTP/3 with QUIC migration.
//!
//! Proof of concept for BitTorrent WebSeed migration: two HTTP/3 servers host
//! the same large file, and the primary migrates the connection to the preferred
//! server mid-transfer via QUIC preferred_address.
//!
//! Usage:
//!   webseed-primary <listen_addr> <preferred_addr> <file_path> [state_transfer_addr]
//!
//! Example:
//!   webseed-primary 0.0.0.0:4433 141.217.168.143:4433 /tmp/test_100mb.bin 141.217.168.143:9999

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    cell::RefCell,
    env,
    io::Write,
    net::SocketAddr,
    path::Path,
    rc::Rc,
    slice,
    time::{Duration, Instant},
};

use neqo_common::{Datagram, Header, event::Provider as _};
use neqo_http3::{Http3Parameters, Http3Server, Http3ServerEvent};
use neqo_transport::{
    ConnectionParameters, Output, RandomConnectionIdGenerator,
    tparams::PreferredAddress,
};
use nss::{AllowZeroRtt, AntiReplay};

const ANTI_REPLAY_WINDOW: Duration = Duration::from_secs(10);

/// Simple SHA-256 implementation (pure Rust, no external dependency).
/// Based on FIPS 180-4.
mod sha256 {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ];

    fn ch(x: u32, y: u32, z: u32) -> u32 { (x & y) ^ (!x & z) }
    fn maj(x: u32, y: u32, z: u32) -> u32 { (x & y) ^ (x & z) ^ (y & z) }
    fn ep0(x: u32) -> u32 { x.rotate_right(2) ^ x.rotate_right(13) ^ x.rotate_right(22) }
    fn ep1(x: u32) -> u32 { x.rotate_right(6) ^ x.rotate_right(11) ^ x.rotate_right(25) }
    fn sig0(x: u32) -> u32 { x.rotate_right(7) ^ x.rotate_right(18) ^ (x >> 3) }
    fn sig1(x: u32) -> u32 { x.rotate_right(17) ^ x.rotate_right(19) ^ (x >> 10) }

    pub fn hash(data: &[u8]) -> [u8; 32] {
        let mut h: [u32; 8] = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
        ];

        let bit_len = (data.len() as u64) * 8;
        let mut padded = data.to_vec();
        padded.push(0x80);
        while (padded.len() % 64) != 56 {
            padded.push(0);
        }
        padded.extend_from_slice(&bit_len.to_be_bytes());

        for chunk in padded.chunks(64) {
            let mut w = [0u32; 64];
            for i in 0..16 {
                w[i] = u32::from_be_bytes([
                    chunk[i * 4], chunk[i * 4 + 1],
                    chunk[i * 4 + 2], chunk[i * 4 + 3],
                ]);
            }
            for i in 16..64 {
                w[i] = sig1(w[i - 2]).wrapping_add(w[i - 7])
                    .wrapping_add(sig0(w[i - 15]))
                    .wrapping_add(w[i - 16]);
            }

            let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = h;

            for i in 0..64 {
                let t1 = hh.wrapping_add(ep1(e))
                    .wrapping_add(ch(e, f, g))
                    .wrapping_add(K[i])
                    .wrapping_add(w[i]);
                let t2 = ep0(a).wrapping_add(maj(a, b, c));
                hh = g; g = f; f = e;
                e = d.wrapping_add(t1);
                d = c; c = b; b = a;
                a = t1.wrapping_add(t2);
            }

            h[0] = h[0].wrapping_add(a); h[1] = h[1].wrapping_add(b);
            h[2] = h[2].wrapping_add(c); h[3] = h[3].wrapping_add(d);
            h[4] = h[4].wrapping_add(e); h[5] = h[5].wrapping_add(f);
            h[6] = h[6].wrapping_add(g); h[7] = h[7].wrapping_add(hh);
        }

        let mut result = [0u8; 32];
        for (i, val) in h.iter().enumerate() {
            result[i * 4..i * 4 + 4].copy_from_slice(&val.to_be_bytes());
        }
        result
    }

    pub fn hex(hash: &[u8; 32]) -> String {
        hash.iter().map(|b| format!("{b:02x}")).collect()
    }
}

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "Usage: {} <listen_addr> <preferred_addr> <file_path> [state_transfer_addr]",
            args[0]
        );
        eprintln!("  listen_addr:         Address to listen (e.g. 0.0.0.0:4433)");
        eprintln!("  preferred_addr:      Preferred server address (e.g. 141.217.168.143:4433)");
        eprintln!("  file_path:           Path to file to serve (e.g. /tmp/test_100mb.bin)");
        eprintln!("  state_transfer_addr: (optional) For tcp backend");
        std::process::exit(1);
    }

    let listen_addr: SocketAddr = args[1].parse().expect("Invalid listen address");
    let preferred_addr: SocketAddr = args[2].parse().expect("Invalid preferred address");
    let file_path = &args[3];

    // Backward compatibility: if 4th arg is given and STATE_TCP_ADDR is not set
    if args.len() >= 5 && std::env::var("STATE_TCP_ADDR").is_err() {
        unsafe { std::env::set_var("STATE_TCP_ADDR", &args[4]); }
    }

    // Load file and compute SHA-256
    let file_data = std::fs::read(file_path).unwrap_or_else(|e| {
        eprintln!("Failed to read file {file_path}: {e}");
        std::process::exit(1);
    });
    let file_name = Path::new(file_path)
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string();
    let file_hash = sha256::hash(&file_data);
    let file_hash_hex = sha256::hex(&file_hash);

    println!("=== WEBSEED PRIMARY SERVER (HTTP/3) ===");
    println!("  Listen:         {listen_addr}");
    println!("  Preferred:      {preferred_addr}");
    println!("  File:           {file_path}");
    println!("  File size:      {} bytes ({:.2} MB)", file_data.len(), file_data.len() as f64 / 1_048_576.0);
    println!("  SHA-256:        {file_hash_hex}");
    println!();

    let mut state_sender = transfer::create_sender();

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let anti_replay = AntiReplay::new(Instant::now(), ANTI_REPLAY_WINDOW, 7, 14)
        .expect("AntiReplay init failed");

    let cid_manager = Rc::new(RefCell::new(RandomConnectionIdGenerator::new(8)));

    let preferred = match preferred_addr {
        SocketAddr::V4(v4) => PreferredAddress::new(Some(v4), None),
        SocketAddr::V6(v6) => PreferredAddress::new(None, Some(v6)),
    };

    let conn_params = ConnectionParameters::default()
        .preferred_address(preferred);

    let http3_params = Http3Parameters::default()
        .connection_parameters(conn_params);

    let mut server = Http3Server::new(
        Instant::now(),
        slice::from_ref(&"key"),
        &["h3"],
        anti_replay,
        cid_manager,
        http3_params,
        None,
    )
    .expect("Http3Server creation failed");

    println!("HTTP/3 server created, binding UDP socket...");

    let socket = std::net::UdpSocket::bind(listen_addr).expect("UDP bind failed");
    socket.set_nonblocking(false).expect("set_nonblocking failed");
    socket.set_read_timeout(Some(Duration::from_millis(50))).expect("set_read_timeout failed");

    println!("Listening on {listen_addr}, waiting for client...");

    let mut buf = vec![0u8; 65536];
    let mut state_sent = false;

    loop {
        match socket.recv_from(&mut buf) {
            Ok((size, src)) => {
                let now = Instant::now();
                let dgram = Datagram::new(src, listen_addr, neqo_common::Tos::default(), &buf[..size]);
                let out = server.process(Some(dgram), now);
                send_output(&socket, &out);
                loop {
                    let now = Instant::now();
                    let out = server.process(None::<Datagram<&mut [u8]>>, now);
                    if !send_output(&socket, &out) {
                        break;
                    }
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                let now = Instant::now();
                let out = server.process(None::<Datagram<&mut [u8]>>, now);
                send_output(&socket, &out);
            }
            Err(e) => {
                eprintln!("recv error: {e}");
            }
        }

        while let Some(event) = server.next_event() {
            match event {
                Http3ServerEvent::Headers {
                    stream,
                    headers,
                    fin: _,
                } => {
                    println!("  >> HTTP/3 request received:");
                    for h in &headers {
                        println!("     {}: {}", h.name(), String::from_utf8_lossy(h.value()));
                    }

                    // Serve the file as binary download
                    if stream.send_headers(&[
                        Header::new(":status", "200"),
                        Header::new("content-type", "application/octet-stream"),
                        Header::new("content-disposition", format!("attachment; filename=\"{file_name}\"")),
                        Header::new("content-length", file_data.len().to_string()),
                        Header::new("x-sha256", file_hash_hex.clone()),
                        Header::new("alt-svc", "h3=\":4433\"; ma=3600"),
                    ]).is_ok() {
                        let now = Instant::now();
                        let _ = stream.send_data(&file_data, now);
                        let _ = stream.stream_close_send(now);
                        println!("  << Sent file response ({} bytes, SHA-256: {})", file_data.len(), &file_hash_hex[..16]);
                    }
                }
                Http3ServerEvent::Data { .. } => {}
                Http3ServerEvent::DataWritable { .. } => {}
                Http3ServerEvent::StateChange { conn, state, .. } => {
                    println!("  Connection state: {state:?}");

                    if matches!(state, neqo_http3::Http3State::Connected | neqo_http3::Http3State::GoingAway(..))
                        && !state_sent
                    {
                        match conn.borrow().export_migration_state() {
                            Ok(migration_state) => {
                                let mut encoded = migration_state.encode();
                                println!();
                                println!(">>> EXPORTING MIGRATION STATE <<<");
                                println!("    State size:   {} bytes", encoded.len());
                                println!("    Client addr:  {}", migration_state.client_addr);
                                println!("    Version:      {:?}", migration_state.version);
                                println!("    Local CIDs:   {}", migration_state.local_cids.len());
                                println!("    Remote CIDs:  {}", migration_state.remote_cids.len());

                                let inst_id = transfer::instance_id();
                                println!("    Sending state via {} backend (instance={inst_id})...", state_sender.name());
                                match state_sender.send_state(&encoded, &inst_id) {
                                    Ok(metrics) => {
                                        println!("    State sent successfully!");
                                        metrics.print_summary();
                                        state_sent = true;
                                    }
                                    Err(e) => {
                                        eprintln!("    Failed to send state: {e}");
                                    }
                                }
                                for byte in encoded.iter_mut() {
                                    unsafe { std::ptr::write_volatile(byte, 0) };
                                }
                                drop(encoded);
                                drop(migration_state);
                                println!("    [Security] Migration state wiped from primary memory");
                            }
                            Err(e) => {
                                eprintln!("    Failed to export migration state: {e:?}");
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        loop {
            let now = Instant::now();
            let out = server.process(None::<Datagram<&mut [u8]>>, now);
            if !send_output(&socket, &out) {
                break;
            }
        }
    }
}

fn send_output(socket: &std::net::UdpSocket, out: &Output) -> bool {
    if let Output::Datagram(dgram) = out {
        socket.send_to(dgram.as_ref(), dgram.destination()).expect("send failed");
        true
    } else {
        false
    }
}

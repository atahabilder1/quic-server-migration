//! QUIC-Native Load Balancer Frontend.
//!
//! Acts as a "fire-and-forget" load balancer: accepts QUIC handshakes, selects
//! a backend via configurable policy, advertises the backend as preferred_address,
//! exports migration state, and sends it to the selected backend. Post-handshake,
//! all traffic flows directly client-to-backend (frontend is out of the data path).
//!
//! Load balancing policies (via LB_POLICY env var):
//!   round_robin (default) - Cycle through backends sequentially
//!   random                - Random backend selection
//!
//! Usage:
//!   lb-frontend <listen_addr> <backend1_quic_addr> <backend2_quic_addr> [...]
//!
//! Example:
//!   lb-frontend 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433
//!
//! Each backend should run preferred-server on the given QUIC address with
//! state listener on port 9999.

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    cell::RefCell,
    env,
    io::Write,
    net::SocketAddr,
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

const HTML_PAGE: &str = r#"<!DOCTYPE html>
<html>
<head>
    <title>QUIC Load Balancer Demo</title>
    <style>
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            max-width: 800px; margin: 60px auto; padding: 20px;
            background: #0a0a0a; color: #e0e0e0;
        }
        h1 { color: #4fc3f7; border-bottom: 2px solid #4fc3f7; padding-bottom: 10px; }
        .box {
            background: #1a1a2e; border-radius: 8px; padding: 20px;
            margin: 20px 0; border-left: 4px solid #4fc3f7;
        }
        .success { border-left-color: #66bb6a; }
        code { background: #2d2d44; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        .server-tag { display: inline-block; padding: 4px 12px; border-radius: 20px;
            background: #4fc3f7; color: #000; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        td:first-child { color: #90caf9; width: 180px; }
    </style>
</head>
<body>
    <h1>QUIC-Native Load Balancer Demo</h1>

    <div class="box success">
        <span class="server-tag">LB FRONTEND</span>
        <p>This page was served by the <strong>load balancer frontend</strong>.
           Your connection is being migrated to backend: <code>BACKEND_ADDR</code></p>
    </div>

    <div class="box">
        <h3>How It Works</h3>
        <p>Unlike traditional load balancers (HAProxy, NGINX), this LB is <strong>not in the data path</strong>
           after the handshake. It uses QUIC's <code>preferred_address</code> to migrate your connection
           directly to the backend server.</p>
        <ol>
            <li>Frontend handles the TLS handshake (1 RTT)</li>
            <li>Frontend selects backend via <code>LB_POLICY</code> policy</li>
            <li>Frontend advertises backend as <code>preferred_address</code></li>
            <li>Your browser migrates directly to the backend</li>
            <li>Frontend is now completely out of the data path</li>
        </ol>
    </div>

    <div class="box">
        <h3>Connection Details</h3>
        <table>
            <tr><td>LB Frontend</td><td>PRIMARY_ADDR</td></tr>
            <tr><td>Selected Backend</td><td>BACKEND_ADDR</td></tr>
            <tr><td>LB Policy</td><td>LB_POLICY</td></tr>
            <tr><td>Connection #</td><td>CONN_NUM</td></tr>
            <tr><td>Total Backends</td><td>NUM_BACKENDS</td></tr>
        </table>
    </div>
</body>
</html>"#;

/// Backend server info
#[derive(Clone)]
struct Backend {
    quic_addr: SocketAddr,
    state_addr: SocketAddr,
    connections: u64,
}

/// Load balancing policy
enum LbPolicy {
    RoundRobin,
    Random,
}

impl LbPolicy {
    fn from_env() -> Self {
        match env::var("LB_POLICY").unwrap_or_else(|_| "round_robin".to_string()).as_str() {
            "random" => Self::Random,
            _ => Self::RoundRobin,
        }
    }

    fn name(&self) -> &str {
        match self {
            Self::RoundRobin => "round_robin",
            Self::Random => "random",
        }
    }

    fn select(&self, backends: &[Backend], counter: u64) -> usize {
        match self {
            Self::RoundRobin => (counter as usize) % backends.len(),
            Self::Random => {
                // Simple pseudo-random based on time
                let nanos = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .subsec_nanos() as usize;
                nanos % backends.len()
            }
        }
    }
}

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!(
            "Usage: {} <listen_addr> <backend1_addr> <backend2_addr> [...]",
            args[0]
        );
        eprintln!();
        eprintln!("  LB_POLICY env var: round_robin (default), random");
        eprintln!("  STATE_PORT env var: backend state port (default: 9999)");
        eprintln!();
        eprintln!("Example:");
        eprintln!("  {} 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433", args[0]);
        std::process::exit(1);
    }

    let listen_addr: SocketAddr = args[1].parse().expect("Invalid listen address");
    let state_port: u16 = env::var("STATE_PORT")
        .unwrap_or_else(|_| "9999".to_string())
        .parse()
        .unwrap_or(9999);

    let backends: Vec<Backend> = args[2..].iter().map(|addr_str| {
        let quic_addr: SocketAddr = addr_str.parse().expect(&format!("Invalid backend address: {addr_str}"));
        let state_addr = SocketAddr::new(quic_addr.ip(), state_port);
        Backend { quic_addr, state_addr, connections: 0 }
    }).collect();

    let policy = LbPolicy::from_env();

    println!("=== QUIC-NATIVE LOAD BALANCER ===");
    println!("  Listen:     {listen_addr}");
    println!("  Policy:     {}", policy.name());
    println!("  Backends:   {}", backends.len());
    for (i, b) in backends.iter().enumerate() {
        println!("    [{i}] QUIC={} State={}", b.quic_addr, b.state_addr);
    }
    println!();

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let primary_display = if listen_addr.ip().is_unspecified() {
        format!("141.217.168.152:{}", listen_addr.port())
    } else {
        listen_addr.to_string()
    };

    let socket = std::net::UdpSocket::bind(listen_addr).expect("UDP bind failed");
    socket.set_nonblocking(false).expect("set_nonblocking failed");
    socket.set_read_timeout(Some(Duration::from_millis(50))).expect("set_read_timeout failed");

    println!("Listening on {listen_addr}, waiting for connections...");
    println!();

    let mut buf = vec![0u8; 65536];
    let mut conn_counter: u64 = 0;
    let mut backends = backends;

    // Main loop: handle one connection at a time, then reset for next
    loop {
        // Select backend for this connection
        let backend_idx = policy.select(&backends, conn_counter);
        let selected_backend = backends[backend_idx].clone();
        backends[backend_idx].connections += 1;
        conn_counter += 1;

        println!("═══════════════════════════════════════════");
        println!("  Connection #{conn_counter}");
        println!("  Selected backend [{backend_idx}]: {}", selected_backend.quic_addr);
        println!("  Policy: {}", policy.name());
        println!("═══════════════════════════════════════════");

        // Create a fresh Http3Server with this backend as preferred_address
        let anti_replay = AntiReplay::new(Instant::now(), ANTI_REPLAY_WINDOW, 7, 14)
            .expect("AntiReplay init failed");
        let cid_manager = Rc::new(RefCell::new(RandomConnectionIdGenerator::new(8)));

        let preferred = match selected_backend.quic_addr {
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

        // Create TCP sender for this specific backend
        let mut state_sender: Box<dyn transfer::StateSender> =
            Box::new(transfer::tcp_push::TcpPushSender::new(selected_backend.state_addr));

        let html = HTML_PAGE
            .replace("PRIMARY_ADDR", &primary_display)
            .replace("BACKEND_ADDR", &selected_backend.quic_addr.to_string())
            .replace("LB_POLICY", policy.name())
            .replace("CONN_NUM", &conn_counter.to_string())
            .replace("NUM_BACKENDS", &backends.len().to_string());

        let mut state_sent = false;
        let mut request_served = false;
        let connection_start = Instant::now();

        // Process this connection until state is exported
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
                        println!("  >> HTTP/3 request received");

                        let body = html.as_bytes();
                        if stream.send_headers(&[
                            Header::new(":status", "200"),
                            Header::new("content-type", "text/html; charset=utf-8"),
                            Header::new("content-length", body.len().to_string()),
                            Header::new("alt-svc", "h3=\":4433\"; ma=3600"),
                        ]).is_ok() {
                            let now = Instant::now();
                            let _ = stream.send_data(body, now);
                            let _ = stream.stream_close_send(now);
                            request_served = true;
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
                                    println!(">>> MIGRATING TO BACKEND [{backend_idx}] {} <<<", selected_backend.quic_addr);
                                    println!("    State size: {} bytes", encoded.len());

                                    let inst_id = transfer::instance_id();
                                    match state_sender.send_state(&encoded, &inst_id) {
                                        Ok(metrics) => {
                                            println!("    State sent to {} successfully!", selected_backend.state_addr);
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
                                }
                                Err(e) => {
                                    eprintln!("    Failed to export: {e:?}");
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }

            // Drain outputs
            loop {
                let now = Instant::now();
                let out = server.process(None::<Datagram<&mut [u8]>>, now);
                if !send_output(&socket, &out) {
                    break;
                }
            }

            // After state is sent and request served, we can move on to the next connection
            if state_sent && request_served {
                let elapsed = connection_start.elapsed();
                println!();
                println!("  Connection #{conn_counter} dispatched to backend [{backend_idx}] in {elapsed:?}");
                print_stats(&backends);
                println!();
                break;
            }

            // Timeout: if no state sent within 30s, skip this connection
            if connection_start.elapsed() > Duration::from_secs(30) {
                eprintln!("  Connection #{conn_counter} timed out");
                break;
            }
        }
    }
}

fn print_stats(backends: &[Backend]) {
    println!("  ┌─────────────────────────────────────┐");
    println!("  │ Backend Statistics                   │");
    println!("  ├─────────────────────────────────────┤");
    for (i, b) in backends.iter().enumerate() {
        println!("  │ [{i}] {} — {} conns │", b.quic_addr, b.connections);
    }
    println!("  └─────────────────────────────────────┘");
}

fn send_output(socket: &std::net::UdpSocket, out: &Output) -> bool {
    if let Output::Datagram(dgram) = out {
        socket.send_to(dgram.as_ref(), dgram.destination()).expect("send failed");
        true
    } else {
        false
    }
}

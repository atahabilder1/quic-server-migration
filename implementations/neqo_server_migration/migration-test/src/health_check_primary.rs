//! Health-Checked Primary Server for cross-machine QUIC server-side migration.
//!
//! Like primary-server, but checks preferred server health before advertising
//! preferred_address. If the preferred is unreachable, serves directly without migration.
//!
//! Health check modes (via HEALTH_CHECK env var):
//!   tcp   (default) - TCP probe to preferred's state port (200ms timeout)
//!   redis           - Check Redis key "preferred:health" (TTL 3s)
//!   none            - Disable health checks (same as primary-server)
//!
//! Usage:
//!   health-check-primary <listen_addr> <preferred_addr> [state_transfer_addr]
//!
//! Example:
//!   health-check-primary 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    cell::RefCell,
    env,
    io::Write,
    net::{SocketAddr, TcpStream},
    rc::Rc,
    slice,
    sync::{Arc, atomic::{AtomicBool, Ordering}},
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
const TCP_PROBE_TIMEOUT: Duration = Duration::from_millis(200);
const HEALTH_CHECK_INTERVAL: Duration = Duration::from_secs(5);

const HTML_PAGE: &str = r#"<!DOCTYPE html>
<html>
<head>
    <title>QUIC Server Migration Demo (Health-Checked)</title>
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
        .warn { border-left-color: #ffa726; }
        code { background: #2d2d44; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        .server-tag { display: inline-block; padding: 4px 12px; border-radius: 20px;
            background: #4fc3f7; color: #000; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        td:first-child { color: #90caf9; width: 180px; }
    </style>
</head>
<body>
    <h1>QUIC Server-Side Migration Demo (Health-Checked)</h1>

    <div class="box MIGRATION_STATUS_CLASS">
        <span class="server-tag">MIGRATION_STATUS_TAG</span>
        <p>MIGRATION_STATUS_MSG</p>
    </div>

    <div class="box">
        <h3>Health Check Details</h3>
        <table>
            <tr><td>Health check mode</td><td>HEALTH_MODE</td></tr>
            <tr><td>Preferred server</td><td>PREFERRED_ADDR</td></tr>
            <tr><td>Preferred status</td><td>HEALTH_STATUS</td></tr>
            <tr><td>Migration</td><td>MIGRATION_DECISION</td></tr>
        </table>
    </div>

    <div class="box">
        <h3>Connection Details</h3>
        <table>
            <tr><td>Protocol</td><td>HTTP/3 over QUIC</td></tr>
            <tr><td>Primary Server</td><td>PRIMARY_ADDR</td></tr>
            <tr><td>Preferred Server</td><td>PREFERRED_ADDR</td></tr>
        </table>
    </div>
</body>
</html>"#;

/// Health check mode
enum HealthCheckMode {
    Tcp { health_port: u16 },
    Redis { url: String },
    None,
}

impl HealthCheckMode {
    fn from_env(preferred_addr: SocketAddr) -> Self {
        match env::var("HEALTH_CHECK").unwrap_or_else(|_| "tcp".to_string()).as_str() {
            "tcp" => {
                // Use a SEPARATE port for health checks (not the state transfer port!)
                let health_port: u16 = env::var("HEALTH_PORT")
                    .unwrap_or_else(|_| "9998".to_string())
                    .parse()
                    .unwrap_or(9998);
                Self::Tcp { health_port }
            }
            "redis" => {
                let url = env::var("REDIS_URL")
                    .unwrap_or_else(|_| "redis://141.217.168.200:6379".to_string());
                Self::Redis { url }
            }
            "none" => Self::None,
            other => {
                eprintln!("Unknown HEALTH_CHECK mode: {other}. Using tcp.");
                let health_port: u16 = env::var("HEALTH_PORT")
                    .unwrap_or_else(|_| "9998".to_string())
                    .parse()
                    .unwrap_or(9998);
                Self::Tcp { health_port }
            }
        }
    }

    fn name(&self) -> &str {
        match self {
            Self::Tcp { .. } => "tcp",
            Self::Redis { .. } => "redis",
            Self::None => "none",
        }
    }

    fn check(&self, preferred_ip: std::net::IpAddr) -> bool {
        match self {
            Self::Tcp { health_port } => {
                let addr = SocketAddr::new(preferred_ip, *health_port);
                TcpStream::connect_timeout(&addr, TCP_PROBE_TIMEOUT).is_ok()
            }
            Self::Redis { url } => {
                // Simple Redis PING via TCP (no dependency needed)
                // Connect to Redis, send GET preferred:health, check response
                check_redis_health(url)
            }
            Self::None => true,
        }
    }
}

/// Simple Redis health check without external dependency.
/// Connects to Redis, sends GET preferred:health, returns true if key exists.
fn check_redis_health(url: &str) -> bool {
    // Parse redis://host:port
    let addr = url
        .strip_prefix("redis://")
        .unwrap_or("141.217.168.200:6379");
    let stream = match TcpStream::connect_timeout(
        &addr.parse().unwrap_or_else(|_| "141.217.168.200:6379".parse().unwrap()),
        TCP_PROBE_TIMEOUT,
    ) {
        Ok(s) => s,
        Err(_) => return false,
    };
    stream.set_read_timeout(Some(TCP_PROBE_TIMEOUT)).ok();
    stream.set_write_timeout(Some(TCP_PROBE_TIMEOUT)).ok();

    let mut stream = std::io::BufWriter::new(stream);
    // RESP protocol: *2\r\n$3\r\nGET\r\n$16\r\npreferred:health\r\n
    let cmd = "*2\r\n$3\r\nGET\r\n$16\r\npreferred:health\r\n";
    if stream.write_all(cmd.as_bytes()).is_err() {
        return false;
    }
    if stream.flush().is_err() {
        return false;
    }

    let inner = stream.into_inner().unwrap();
    let mut buf = [0u8; 64];
    match std::io::Read::read(&mut &inner, &mut buf) {
        Ok(n) if n > 0 => {
            let resp = std::str::from_utf8(&buf[..n]).unwrap_or("");
            // $-1 means nil (key doesn't exist), $N means key exists
            !resp.starts_with("$-1")
        }
        _ => false,
    }
}

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!(
            "Usage: {} <listen_addr> <preferred_addr> [state_transfer_addr]",
            args[0]
        );
        eprintln!();
        eprintln!("  HEALTH_CHECK env var: tcp (default), redis, none");
        std::process::exit(1);
    }

    let listen_addr: SocketAddr = args[1].parse().expect("Invalid listen address");
    let preferred_addr: SocketAddr = args[2].parse().expect("Invalid preferred address");

    if args.len() >= 4 && std::env::var("STATE_TCP_ADDR").is_err() {
        unsafe { std::env::set_var("STATE_TCP_ADDR", &args[3]); }
    }

    let health_mode = HealthCheckMode::from_env(preferred_addr);

    println!("=== HEALTH-CHECKED PRIMARY SERVER (HTTP/3) ===");
    println!("  Listen:         {listen_addr}");
    println!("  Preferred:      {preferred_addr}");
    println!("  Health check:   {}", health_mode.name());
    println!();

    // Initial health check
    let preferred_healthy = health_mode.check(preferred_addr.ip());
    println!("  [Health] Initial check: {}", if preferred_healthy { "HEALTHY" } else { "UNHEALTHY" });

    if !preferred_healthy {
        println!("  [Health] Preferred server is DOWN — serving directly without migration");
    }
    println!();

    // Background health checker thread
    let healthy_flag = Arc::new(AtomicBool::new(preferred_healthy));
    {
        let flag = healthy_flag.clone();
        let preferred_ip = preferred_addr.ip();
        let mode_name = health_mode.name().to_string();
        let health_port: u16 = env::var("HEALTH_PORT")
            .unwrap_or_else(|_| "9998".to_string())
            .parse()
            .unwrap_or(9998);
        let redis_url = env::var("REDIS_URL")
            .unwrap_or_else(|_| "redis://141.217.168.200:6379".to_string());

        std::thread::spawn(move || {
            let mut last_status = flag.load(Ordering::Relaxed);
            loop {
                std::thread::sleep(HEALTH_CHECK_INTERVAL);
                let healthy = match mode_name.as_str() {
                    "tcp" => {
                        let addr = SocketAddr::new(preferred_ip, health_port);
                        TcpStream::connect_timeout(&addr, TCP_PROBE_TIMEOUT).is_ok()
                    }
                    "redis" => check_redis_health(&redis_url),
                    _ => true,
                };
                flag.store(healthy, Ordering::Relaxed);
                if healthy != last_status {
                    println!("  [Health] Status CHANGED: {} → {}",
                        if last_status { "HEALTHY" } else { "UNHEALTHY" },
                        if healthy { "HEALTHY" } else { "UNHEALTHY" });
                    last_status = healthy;
                }
            }
        });
    }

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let anti_replay = AntiReplay::new(Instant::now(), ANTI_REPLAY_WINDOW, 7, 14)
        .expect("AntiReplay init failed");

    let cid_manager = Rc::new(RefCell::new(RandomConnectionIdGenerator::new(8)));

    // Conditionally set preferred address based on health
    let use_migration = healthy_flag.load(Ordering::Relaxed);

    let conn_params = if use_migration {
        let preferred = match preferred_addr {
            SocketAddr::V4(v4) => PreferredAddress::new(Some(v4), None),
            SocketAddr::V6(v6) => PreferredAddress::new(None, Some(v6)),
        };
        println!("  [Decision] Preferred is HEALTHY — advertising preferred_address");
        ConnectionParameters::default().preferred_address(preferred)
    } else {
        println!("  [Decision] Preferred is UNHEALTHY — serving directly (no migration)");
        ConnectionParameters::default()
    };

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

    let mut state_sender = if use_migration {
        Some(transfer::create_sender())
    } else {
        None
    };

    println!("HTTP/3 server created, binding UDP socket...");

    let socket = std::net::UdpSocket::bind(listen_addr).expect("UDP bind failed");
    socket.set_nonblocking(false).expect("set_nonblocking failed");
    socket.set_read_timeout(Some(Duration::from_millis(50))).expect("set_read_timeout failed");

    println!("Listening on {listen_addr}, waiting for client...");

    let mut buf = vec![0u8; 65536];
    let mut state_sent = false;

    let primary_display = if listen_addr.ip().is_unspecified() {
        format!("141.217.168.152:{}", listen_addr.port())
    } else {
        listen_addr.to_string()
    };

    let health_status = if use_migration { "HEALTHY" } else { "UNHEALTHY" };
    let migration_decision = if use_migration { "Enabled (migrating to preferred)" } else { "Disabled (serving directly)" };
    let status_class = if use_migration { "success" } else { "warn" };
    let status_tag = if use_migration { "PRIMARY SERVER (MIGRATING)" } else { "PRIMARY SERVER (DIRECT)" };
    let status_msg = if use_migration {
        "Connected via HTTP/3. Migration to preferred server is <strong>active</strong>."
    } else {
        "Connected via HTTP/3. Preferred server is <strong>down</strong> — serving directly."
    };

    let html = HTML_PAGE
        .replace("PRIMARY_ADDR", &primary_display)
        .replace("PREFERRED_ADDR", &preferred_addr.to_string())
        .replace("HEALTH_MODE", health_mode.name())
        .replace("HEALTH_STATUS", health_status)
        .replace("MIGRATION_DECISION", migration_decision)
        .replace("MIGRATION_STATUS_CLASS", status_class)
        .replace("MIGRATION_STATUS_TAG", status_tag)
        .replace("MIGRATION_STATUS_MSG", status_msg);

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
                        println!("  << Sent HTML response ({} bytes)", body.len());
                    }
                }
                Http3ServerEvent::Data { .. } => {}
                Http3ServerEvent::DataWritable { .. } => {}
                Http3ServerEvent::StateChange { conn, state, .. } => {
                    println!("  Connection state: {state:?}");

                    if matches!(state, neqo_http3::Http3State::Connected | neqo_http3::Http3State::GoingAway(..))
                        && !state_sent
                        && use_migration
                    {
                        match conn.borrow().export_migration_state() {
                            Ok(migration_state) => {
                                let mut encoded = migration_state.encode();
                                println!();
                                println!(">>> EXPORTING MIGRATION STATE <<<");
                                println!("    State size:   {} bytes", encoded.len());
                                println!("    Client addr:  {}", migration_state.client_addr);

                                if let Some(ref mut sender) = state_sender {
                                    let inst_id = transfer::instance_id();
                                    println!("    Sending state via {} backend...", sender.name());
                                    match sender.send_state(&encoded, &inst_id) {
                                        Ok(metrics) => {
                                            println!("    State sent successfully!");
                                            metrics.print_summary();
                                            state_sent = true;
                                        }
                                        Err(e) => {
                                            eprintln!("    Failed to send state: {e}");
                                        }
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

//! Primary server for cross-machine QUIC server-side migration.
//!
//! This server:
//! 1. Accepts a QUIC connection from a client (Firefox, neqo-client, etc.)
//! 2. Serves an HTML page via HTTP/3
//! 3. Completes the handshake (advertising preferred_address)
//! 4. Exports the connection's crypto state
//! 5. Sends it over TCP to the preferred server
//!
//! Usage:
//!   primary-server <listen_addr> <preferred_addr> <state_transfer_addr>
//!
//! Example:
//!   primary-server 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999

#[path = "transfer/mod.rs"]
mod transfer;

use std::{
    cell::RefCell,
    env,
    io::Write,
    net::{SocketAddr, TcpStream},
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

// ─── Firefox Configuration Notes ───
// To make Firefox connect via HTTP/3 to this server, set these in about:config:
//   1. network.http.http3.enabled = true  (create as Boolean if missing)
//   2. network.http.http3.alt-svc-mapping-for-testing = "141.217.168.152:4433;h3=\":4433\""
//   3. network.http.http3.disable_when_third_party_roots_found = false
// Also import the server's certificate into Firefox:
//   Settings → Privacy & Security → Certificates → View Certificates →
//   Authorities → Import → /tmp/quic_cert.pem → Trust for websites
// Then restart Firefox completely.

const HTML_PAGE: &str = r#"<!DOCTYPE html>
<html>
<head>
    <title>QUIC Server Migration Demo</title>
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
        .info { color: #90caf9; }
        code { background: #2d2d44; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        .server-tag { display: inline-block; padding: 4px 12px; border-radius: 20px;
            background: #4fc3f7; color: #000; font-weight: bold; }
        .step { color: #ffa726; font-weight: bold; }
        #status { font-size: 1.2em; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td { padding: 8px; border-bottom: 1px solid #333; }
        td:first-child { color: #90caf9; width: 180px; }
    </style>
</head>
<body>
    <h1>QUIC Server-Side Migration Demo</h1>

    <div class="box success">
        <span class="server-tag">PRIMARY SERVER</span>
        <p id="status">You are connected via HTTP/3 (QUIC) to the <strong>primary server</strong>.</p>
    </div>

    <div class="box">
        <h3>What's happening right now:</h3>
        <p><span class="step">Step 1:</span> Your browser completed a QUIC handshake with this server.</p>
        <p><span class="step">Step 2:</span> During the handshake, we sent a <code>preferred_address</code> transport parameter
           telling your browser to migrate to a <strong>different server</strong>.</p>
        <p><span class="step">Step 3:</span> Your browser is now validating the path to the preferred server
           by sending a <code>PATH_CHALLENGE</code>.</p>
        <p><span class="step">Step 4:</span> The preferred server responds with <code>PATH_RESPONSE</code> &mdash;
           your connection has <strong>silently migrated</strong> to a completely different machine!</p>
    </div>

    <div class="box warn">
        <h3>The Security Implication (QUIC-Exfil Attack)</h3>
        <p>A firewall watching this connection saw you connect to the primary server.
           But your traffic is now going to a <em>completely different machine</em>.
           The firewall <strong>cannot detect this migration</strong> because:</p>
        <ul>
            <li>The <code>preferred_address</code> was inside the encrypted handshake</li>
            <li>The <code>PATH_CHALLENGE/RESPONSE</code> are encrypted</li>
            <li>Post-migration packets look identical to normal QUIC traffic</li>
        </ul>
    </div>

    <div class="box">
        <h3>Connection Details</h3>
        <table>
            <tr><td>Protocol</td><td>HTTP/3 over QUIC</td></tr>
            <tr><td>Primary Server</td><td>PRIMARY_ADDR</td></tr>
            <tr><td>Preferred Server</td><td>PREFERRED_ADDR</td></tr>
            <tr><td>Migration Method</td><td>Server-side via preferred_address (RFC 9000 &sect;9.6)</td></tr>
        </table>
    </div>

    <div class="box">
        <h3>Verify with Wireshark</h3>
        <p>Run on the client machine:</p>
        <p><code>sudo tshark -i any -f 'udp port 4433' -T fields -e ip.dst -e udp.length</code></p>
        <p>You'll see packets initially going to <code>PRIMARY_ADDR</code>,
           then switching to <code>PREFERRED_ADDR</code>.</p>
    </div>
</body>
</html>"#;

fn main() {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        eprintln!(
            "Usage: {} <listen_addr> <preferred_addr> [state_transfer_addr]",
            args[0]
        );
        eprintln!("  listen_addr:         Address to listen for client connections (e.g. 0.0.0.0:4433)");
        eprintln!("  preferred_addr:      Address of the preferred server (e.g. 141.217.168.143:4433)");
        eprintln!("  state_transfer_addr: (optional) For tcp backend, overrides STATE_TCP_ADDR env var");
        eprintln!();
        eprintln!("  Backend selection via STATE_TRANSFER env var: tcp, http, redis_kv, redis_ps, file");
        std::process::exit(1);
    }

    let listen_addr: SocketAddr = args[1].parse().expect("Invalid listen address");
    let preferred_addr: SocketAddr = args[2].parse().expect("Invalid preferred address");

    // Backward compatibility: if 3rd arg is given and STATE_TCP_ADDR is not set, use it
    if args.len() >= 4 && std::env::var("STATE_TCP_ADDR").is_err() {
        // SAFETY: single-threaded at this point, before any threads are spawned
        unsafe { std::env::set_var("STATE_TCP_ADDR", &args[3]); }
    }

    // Create the state transfer sender
    let mut state_sender = transfer::create_sender();

    println!("=== PRIMARY SERVER (HTTP/3) ===");
    println!("  Listen:         {listen_addr}");
    println!("  Preferred:      {preferred_addr}");
    println!();

    nss::init_db("./test-fixture/db").expect("NSS init failed");

    let anti_replay = AntiReplay::new(Instant::now(), ANTI_REPLAY_WINDOW, 7, 14)
        .expect("AntiReplay init failed");

    let cid_manager = Rc::new(RefCell::new(RandomConnectionIdGenerator::new(8)));

    // Build preferred address config
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
    socket
        .set_nonblocking(false)
        .expect("set_nonblocking failed");
    socket
        .set_read_timeout(Some(Duration::from_millis(50)))
        .expect("set_read_timeout failed");

    println!("Listening on {listen_addr}, waiting for client...");

    let mut buf = vec![0u8; 65536];
    let mut state_sent = false;

    // Prepare HTML with actual addresses filled in
    // Use the actual server IP (from the first client connection) instead of 0.0.0.0
    let primary_display = if listen_addr.ip().is_unspecified() {
        format!("141.217.168.152:{}", listen_addr.port())
    } else {
        listen_addr.to_string()
    };
    let html = HTML_PAGE
        .replace("PRIMARY_ADDR", &primary_display)
        .replace("PREFERRED_ADDR", &preferred_addr.to_string());

    loop {
        // Receive UDP datagrams
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

        // Process HTTP/3 events
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

                    // Send HTML response
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

                    // Export migration state as soon as connection is confirmed
                    if matches!(state, neqo_http3::Http3State::Connected | neqo_http3::Http3State::GoingAway(..))
                        && !state_sent
                    {
                        match conn.borrow().export_migration_state() {
                            Ok(migration_state) => {
                                let encoded = migration_state.encode();
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

        // Drain outputs after event processing
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
        socket
            .send_to(dgram.as_ref(), dgram.destination())
            .expect("send failed");
        true
    } else {
        false
    }
}

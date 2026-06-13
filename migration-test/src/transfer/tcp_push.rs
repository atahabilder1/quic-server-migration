//! Backend 1: Direct TCP Push
//!
//! The original state transfer method. Primary server pushes state
//! directly to the preferred server over a plain TCP connection.
//!
//! Config:
//!   STATE_TRANSFER=tcp
//!   STATE_TCP_ADDR=141.217.168.143:9999  (sender: where to connect)
//!   STATE_TCP_PORT=9999                  (receiver: port to listen on)

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::time::Instant;

use super::{StateSender, StateReceiver, TransferMetrics, TransferResult};

/// Sender: connects to preferred server and pushes state.
pub struct TcpPushSender {
    addr: SocketAddr,
}

impl TcpPushSender {
    pub fn new(addr: SocketAddr) -> Self {
        println!("  [TCP Push] Will send state to {addr}");
        Self { addr }
    }
}

impl StateSender for TcpPushSender {
    fn send_state(&mut self, data: &[u8], _instance_id: &str) -> TransferResult<TransferMetrics> {
        let mut metrics = TransferMetrics::new(self.name());
        metrics.state_size = data.len();

        metrics.send_start = Some(Instant::now());

        let mut tcp = TcpStream::connect(self.addr)?;
        let len = (data.len() as u32).to_be_bytes();
        tcp.write_all(&len)?;
        tcp.write_all(data)?;
        tcp.flush()?;

        metrics.send_end = Some(Instant::now());
        Ok(metrics)
    }

    fn name(&self) -> &str { "tcp" }
}

/// Receiver: listens on TCP port and waits for state push.
pub struct TcpPushReceiver {
    port: u16,
}

impl TcpPushReceiver {
    pub fn new(port: u16) -> Self {
        println!("  [TCP Push] Will listen for state on port {port}");
        Self { port }
    }
}

impl StateReceiver for TcpPushReceiver {
    fn receive_state(&mut self, _instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)> {
        let mut metrics = TransferMetrics::new(self.name());

        let listen_addr: SocketAddr = format!("0.0.0.0:{}", self.port).parse().unwrap();
        let tcp_listener = TcpListener::bind(listen_addr)?;

        println!("Waiting for migration state on TCP port {}...", self.port);
        metrics.receive_start = Some(Instant::now());

        let (mut stream, src) = tcp_listener.accept()?;
        println!("  Received connection from {src}");

        let mut len_buf = [0u8; 4];
        stream.read_exact(&mut len_buf)?;
        let data_len = u32::from_be_bytes(len_buf) as usize;
        let mut data = vec![0u8; data_len];
        stream.read_exact(&mut data)?;
        drop(stream);

        metrics.receive_end = Some(Instant::now());
        metrics.state_size = data.len();

        Ok((data, metrics))
    }

    fn name(&self) -> &str { "tcp" }
}

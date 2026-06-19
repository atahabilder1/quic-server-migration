//! Backend 4: Redis Pub/Sub (Event-Driven Push)
//!
//! Primary server publishes state to a Redis channel.
//! Preferred server subscribes to the channel and receives state instantly.
//! This is an event-driven push pattern.
//!
//! Config:
//!   STATE_TRANSFER=redis_ps
//!   REDIS_URL=redis://127.0.0.1:6379

use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};

use super::{StateSender, StateReceiver, TransferMetrics, TransferResult, TransferError};

const CHANNEL_PREFIX: &str = "quic_migration:ch:";

/// Sender: publishes state to a Redis channel.
pub struct RedisPubSubSender {
    addr: String,
}

impl RedisPubSubSender {
    pub fn new(url: &str) -> Self {
        let addr = parse_redis_addr(url);
        println!("  [Redis Pub/Sub] Will PUBLISH state to {addr}");
        Self { addr }
    }
}

impl StateSender for RedisPubSubSender {
    fn send_state(&mut self, data: &[u8], instance_id: &str) -> TransferResult<TransferMetrics> {
        let mut metrics = TransferMetrics::new(self.name());
        metrics.state_size = data.len();
        metrics.send_start = Some(Instant::now());

        let channel = format!("{CHANNEL_PREFIX}{instance_id}");

        let mut conn = TcpStream::connect(&self.addr)
            .map_err(|e| TransferError::Backend(format!("Redis connect: {e}")))?;

        // PUBLISH channel hex_data
        let hex_data = hex_encode(data);
        let cmd = format!(
            "*3\r\n$7\r\nPUBLISH\r\n${}\r\n{}\r\n${}\r\n{}\r\n",
            channel.len(), channel,
            hex_data.len(), hex_data
        );
        conn.write_all(cmd.as_bytes())?;
        conn.flush()?;

        // Read response (integer: number of subscribers that received the message)
        let mut resp = [0u8; 64];
        let n = conn.read(&mut resp)?;
        let resp_str = String::from_utf8_lossy(&resp[..n]);
        println!("    [Redis Pub/Sub] Published ({} bytes), response: {}",
            data.len(), resp_str.trim());

        metrics.send_end = Some(Instant::now());
        Ok(metrics)
    }

    fn name(&self) -> &str { "redis_ps" }
}

/// Receiver: subscribes to Redis channel and waits for state.
pub struct RedisPubSubReceiver {
    addr: String,
}

impl RedisPubSubReceiver {
    pub fn new(url: &str) -> Self {
        let addr = parse_redis_addr(url);
        println!("  [Redis Pub/Sub] Will SUBSCRIBE to {addr}");
        Self { addr }
    }
}

impl StateReceiver for RedisPubSubReceiver {
    fn receive_state(&mut self, instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)> {
        let mut metrics = TransferMetrics::new(self.name());
        let channel = format!("{CHANNEL_PREFIX}{instance_id}");

        let mut conn = TcpStream::connect(&self.addr)
            .map_err(|e| TransferError::Backend(format!("Redis connect: {e}")))?;

        // SUBSCRIBE to the channel
        let cmd = format!(
            "*2\r\n$9\r\nSUBSCRIBE\r\n${}\r\n{}\r\n",
            channel.len(), channel
        );
        conn.write_all(cmd.as_bytes())?;
        conn.flush()?;

        // Read subscription confirmation
        let mut buf = [0u8; 256];
        let _ = conn.read(&mut buf);

        println!("Waiting for migration state on Redis Pub/Sub (channel={channel})...");
        metrics.receive_start = Some(Instant::now());

        // Wait for published message
        // Redis sends: *3\r\n$7\r\nmessage\r\n$<chan_len>\r\n<channel>\r\n$<msg_len>\r\n<message>\r\n
        let mut all_data = Vec::new();
        const MAX_PUBSUB_MSG: usize = 65_536;
        loop {
            let mut read_buf = [0u8; 8192];
            match conn.read(&mut read_buf) {
                Ok(0) => return Err(TransferError::Backend("Redis connection closed".to_string())),
                Ok(n) => {
                    all_data.extend_from_slice(&read_buf[..n]);
                    if all_data.len() > MAX_PUBSUB_MSG {
                        return Err(TransferError::Backend(
                            format!("Pub/Sub message too large (>{MAX_PUBSUB_MSG} bytes)")
                        ));
                    }

                    // Try to parse the message
                    let resp = String::from_utf8_lossy(&all_data);
                    if let Some(hex_data) = parse_pubsub_message(&resp) {
                        let data = hex_decode(&hex_data)
                            .map_err(|e| TransferError::Backend(format!("Hex decode: {e}")))?;

                        metrics.receive_end = Some(Instant::now());
                        metrics.state_size = data.len();
                        println!("  State received via Pub/Sub ({} bytes)", data.len());

                        return Ok((data, metrics));
                    }
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    std::thread::sleep(Duration::from_millis(10));
                }
                Err(e) => return Err(e.into()),
            }
        }
    }

    fn name(&self) -> &str { "redis_ps" }
}

/// Parse a Redis Pub/Sub message to extract the data.
/// Format: *3\r\n$7\r\nmessage\r\n$<chan_len>\r\n<channel>\r\n$<data_len>\r\n<data>\r\n
fn parse_pubsub_message(resp: &str) -> Option<String> {
    let parts: Vec<&str> = resp.split("\r\n").collect();

    // We need at least: *3, $7, message, $chan_len, channel, $data_len, data
    if parts.len() < 7 { return None; }

    // Find "message" in the parts
    for i in 0..parts.len() {
        if parts[i] == "message" {
            // parts[i+1] = $chan_len, parts[i+2] = channel, parts[i+3] = $data_len, parts[i+4] = data
            if i + 4 < parts.len() {
                let data = parts[i + 4];
                if !data.is_empty() && !data.starts_with('$') {
                    return Some(data.to_string());
                }
            }
        }
    }
    None
}

fn parse_redis_addr(url: &str) -> String {
    url.strip_prefix("redis://").unwrap_or(url).to_string()
}

fn hex_encode(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}

fn hex_decode(s: &str) -> Result<Vec<u8>, String> {
    if s.len() % 2 != 0 {
        return Err("Odd hex string length".to_string());
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|e| e.to_string()))
        .collect()
}

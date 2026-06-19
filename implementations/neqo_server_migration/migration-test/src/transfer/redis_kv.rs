//! Backend 3: Redis Key-Value (SET/GET)
//!
//! Primary server writes state to Redis with SET + TTL.
//! Preferred server reads state from Redis with GET (polling).
//! This is a shared storage pattern: push (write) + pull (read).
//!
//! Config:
//!   STATE_TRANSFER=redis_kv
//!   REDIS_URL=redis://127.0.0.1:6379
//!   REDIS_TTL=60  (seconds, default)

use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};

use super::{StateSender, StateReceiver, TransferMetrics, TransferResult, TransferError};

const KEY_PREFIX: &str = "quic_migration:";

/// Sender: writes state to Redis using SET with TTL.
pub struct RedisKvSender {
    addr: String,
    ttl: u64,
}

impl RedisKvSender {
    pub fn new(url: &str, ttl: u64) -> Self {
        let addr = parse_redis_addr(url);
        println!("  [Redis KV] Will SET state to {addr} (TTL={ttl}s)");
        Self { addr, ttl }
    }
}

impl StateSender for RedisKvSender {
    fn send_state(&mut self, data: &[u8], instance_id: &str) -> TransferResult<TransferMetrics> {
        let mut metrics = TransferMetrics::new(self.name());
        metrics.state_size = data.len();
        metrics.send_start = Some(Instant::now());

        let redis_key = format!("{KEY_PREFIX}{instance_id}");

        let mut conn = TcpStream::connect(&self.addr)
            .map_err(|e| TransferError::Backend(format!("Redis connect failed: {e}")))?;

        // RESP protocol: SET key value EX ttl
        let hex_data = hex_encode(data);
        let cmd = format!(
            "*5\r\n$3\r\nSET\r\n${}\r\n{}\r\n${}\r\n{}\r\n$2\r\nEX\r\n${}\r\n{}\r\n",
            redis_key.len(), redis_key,
            hex_data.len(), hex_data,
            self.ttl.to_string().len(), self.ttl
        );
        conn.write_all(cmd.as_bytes())?;
        conn.flush()?;

        // Read response (+OK\r\n)
        let mut resp = [0u8; 64];
        let n = conn.read(&mut resp)?;
        let resp_str = String::from_utf8_lossy(&resp[..n]);
        if !resp_str.starts_with("+OK") {
            return Err(TransferError::Backend(format!("Redis SET failed: {resp_str}")));
        }

        metrics.send_end = Some(Instant::now());
        println!("    [Redis KV] State written ({} bytes, TTL={}s)", data.len(), self.ttl);

        Ok(metrics)
    }

    fn name(&self) -> &str { "redis_kv" }
}

/// Receiver: polls Redis with GET until state is available.
pub struct RedisKvReceiver {
    addr: String,
}

impl RedisKvReceiver {
    pub fn new(url: &str) -> Self {
        let addr = parse_redis_addr(url);
        println!("  [Redis KV] Will GET state from {addr}");
        Self { addr }
    }
}

impl StateReceiver for RedisKvReceiver {
    fn receive_state(&mut self, instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)> {
        let mut metrics = TransferMetrics::new(self.name());
        let redis_key = format!("{KEY_PREFIX}{instance_id}");

        println!("Waiting for migration state in Redis (key={redis_key})...");
        metrics.receive_start = Some(Instant::now());

        // Poll Redis until key exists
        loop {
            match try_redis_get(&self.addr, &redis_key) {
                Ok(Some(data)) => {
                    metrics.receive_end = Some(Instant::now());
                    metrics.state_size = data.len();
                    println!("  State read from Redis ({} bytes)", data.len());

                    // Delete the key after reading
                    let _ = redis_del(&self.addr, &redis_key);

                    return Ok((data, metrics));
                }
                Ok(None) => {
                    // Key doesn't exist yet, poll
                    std::thread::sleep(Duration::from_millis(50));
                }
                Err(e) => {
                    eprintln!("  Redis GET error: {e}, retrying...");
                    std::thread::sleep(Duration::from_millis(200));
                }
            }
        }
    }

    fn name(&self) -> &str { "redis_kv" }
}

/// Try to GET the migration state from Redis.
fn try_redis_get(addr: &str, redis_key: &str) -> TransferResult<Option<Vec<u8>>> {
    let mut conn = TcpStream::connect(addr)
        .map_err(|e| TransferError::Backend(format!("Redis connect: {e}")))?;
    conn.set_read_timeout(Some(Duration::from_secs(2)))?;

    let cmd = format!("*2\r\n$3\r\nGET\r\n${}\r\n{}\r\n", redis_key.len(), redis_key);
    conn.write_all(cmd.as_bytes())?;
    conn.flush()?;

    let mut resp = Vec::new();
    let mut buf = [0u8; 8192];
    const MAX_REDIS_RESP: usize = 65_536;
    loop {
        match conn.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => {
                resp.extend_from_slice(&buf[..n]);
                if resp.len() > MAX_REDIS_RESP {
                    return Err(TransferError::Backend(
                        format!("Redis response too large (>{MAX_REDIS_RESP} bytes)")
                    ));
                }
            }
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
            Err(e) if e.kind() == std::io::ErrorKind::TimedOut => break,
            Err(e) => return Err(e.into()),
        }
        // Check if we have a complete response
        if resp.ends_with(b"\r\n") { break; }
    }

    let resp_str = String::from_utf8_lossy(&resp);

    // $-1\r\n means key doesn't exist
    if resp_str.starts_with("$-1") {
        return Ok(None);
    }

    // Parse bulk string: $<len>\r\n<data>\r\n
    if resp_str.starts_with('$') {
        if let Some(first_crlf) = resp_str.find("\r\n") {
            let data_str = &resp_str[first_crlf + 2..];
            // Remove trailing \r\n
            let hex_data = data_str.trim_end_matches("\r\n");
            let data = hex_decode(hex_data)
                .map_err(|e| TransferError::Backend(format!("Hex decode: {e}")))?;
            return Ok(Some(data));
        }
    }

    Err(TransferError::Backend(format!("Unexpected Redis response: {resp_str}")))
}

/// Delete the key from Redis.
fn redis_del(addr: &str, redis_key: &str) -> TransferResult<()> {
    let mut conn = TcpStream::connect(addr)?;
    let cmd = format!("*2\r\n$3\r\nDEL\r\n${}\r\n{}\r\n", redis_key.len(), redis_key);
    conn.write_all(cmd.as_bytes())?;
    conn.flush()?;
    Ok(())
}

/// Parse redis://host:port URL to host:port string.
fn parse_redis_addr(url: &str) -> String {
    let stripped = url
        .strip_prefix("redis://")
        .unwrap_or(url);
    stripped.to_string()
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

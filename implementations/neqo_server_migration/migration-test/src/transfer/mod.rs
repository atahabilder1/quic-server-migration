//! State transfer backends for QUIC cross-machine migration.
//!
//! Select backend via STATE_TRANSFER environment variable:
//!   tcp       - Direct TCP push (default)
//!   http      - HTTP pull (preferred requests from primary)
//!   redis_kv  - Redis SET/GET (shared key-value storage)
//!   redis_ps  - Redis Pub/Sub (event-driven push)
//!   file      - Shared filesystem (write/read)

pub mod tcp_push;
pub mod http_pull;
pub mod redis_kv;
pub mod redis_pubsub;
pub mod file_backend;

use std::time::Instant;

/// Result type for state transfer operations.
pub type TransferResult<T> = Result<T, TransferError>;

/// Errors that can occur during state transfer.
#[derive(Debug)]
pub enum TransferError {
    /// Connection or I/O error
    Io(std::io::Error),
    /// Backend-specific error
    Backend(String),
    /// Timeout waiting for state
    Timeout,
}

impl std::fmt::Display for TransferError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(e) => write!(f, "I/O error: {e}"),
            Self::Backend(msg) => write!(f, "Backend error: {msg}"),
            Self::Timeout => write!(f, "Timeout waiting for state"),
        }
    }
}

impl From<std::io::Error> for TransferError {
    fn from(e: std::io::Error) -> Self {
        Self::Io(e)
    }
}

/// Timing metrics for a state transfer operation.
#[derive(Debug, Clone)]
pub struct TransferMetrics {
    pub backend: String,
    pub send_start: Option<Instant>,
    pub send_end: Option<Instant>,
    pub receive_start: Option<Instant>,
    pub receive_end: Option<Instant>,
    pub state_size: usize,
}

impl TransferMetrics {
    pub fn new(backend: &str) -> Self {
        Self {
            backend: backend.to_string(),
            send_start: None,
            send_end: None,
            receive_start: None,
            receive_end: None,
            state_size: 0,
        }
    }

    /// Print timing summary.
    pub fn print_summary(&self) {
        println!("  [Metrics] backend={}", self.backend);
        println!("  [Metrics] state_size={} bytes", self.state_size);
        if let (Some(start), Some(end)) = (self.send_start, self.send_end) {
            println!("  [Metrics] send_time={:?}", end.duration_since(start));
        }
        if let (Some(start), Some(end)) = (self.receive_start, self.receive_end) {
            println!("  [Metrics] receive_time={:?}", end.duration_since(start));
        }
    }
}

/// Sender side: used by the primary server to send migration state.
pub trait StateSender: Send {
    /// Send the encoded migration state. `instance_id` uniquely identifies this
    /// connection (used for multi-server routing, e.g. Redis key prefix).
    fn send_state(&mut self, data: &[u8], instance_id: &str) -> TransferResult<TransferMetrics>;

    /// Backend name for logging.
    fn name(&self) -> &str;
}

/// Receiver side: used by the preferred server to receive migration state.
pub trait StateReceiver: Send {
    /// Wait for and receive migration state. `instance_id` uniquely identifies
    /// this connection (must match what sender used).
    fn receive_state(&mut self, instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)>;

    /// Backend name for logging.
    fn name(&self) -> &str;
}

/// Generate an instance ID from environment or use default.
/// For multi-server, set INSTANCE_ID env var (e.g., "4433" or "server1").
pub fn instance_id() -> String {
    std::env::var("INSTANCE_ID").unwrap_or_else(|_| "default".to_string())
}

/// Read backend name from STATE_TRANSFER env var (default: "tcp").
pub fn backend_name() -> String {
    std::env::var("STATE_TRANSFER").unwrap_or_else(|_| "tcp".to_string())
}

/// Create a sender for the configured backend.
pub fn create_sender() -> Box<dyn StateSender> {
    let backend = backend_name();
    println!("  [Transfer] Backend: {backend}");

    match backend.as_str() {
        "tcp" => {
            let addr = std::env::var("STATE_TCP_ADDR")
                .expect("STATE_TCP_ADDR required for tcp backend (e.g. 141.217.168.143:9999)");
            Box::new(tcp_push::TcpPushSender::new(addr.parse().expect("Invalid STATE_TCP_ADDR")))
        }
        "http" => {
            let port: u16 = std::env::var("STATE_HTTP_PORT")
                .unwrap_or_else(|_| "9998".to_string())
                .parse()
                .expect("Invalid STATE_HTTP_PORT");
            Box::new(http_pull::HttpPullSender::new(port))
        }
        "redis_kv" => {
            let url = std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
            let ttl: u64 = std::env::var("REDIS_TTL")
                .unwrap_or_else(|_| "60".to_string())
                .parse()
                .unwrap_or(60);
            Box::new(redis_kv::RedisKvSender::new(&url, ttl))
        }
        "redis_ps" => {
            let url = std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
            Box::new(redis_pubsub::RedisPubSubSender::new(&url))
        }
        "file" => {
            let path = std::env::var("STATE_FILE_PATH")
                .unwrap_or_else(|_| "/tmp/quic_migration_state".to_string());
            Box::new(file_backend::FileSender::new(&path))
        }
        _ => {
            eprintln!("Unknown STATE_TRANSFER backend: {backend}");
            eprintln!("Valid options: tcp, http, redis_kv, redis_ps, file");
            std::process::exit(1);
        }
    }
}

/// Create a receiver for the configured backend.
pub fn create_receiver() -> Box<dyn StateReceiver> {
    let backend = backend_name();
    println!("  [Transfer] Backend: {backend}");

    match backend.as_str() {
        "tcp" => {
            let port: u16 = std::env::var("STATE_TCP_PORT")
                .unwrap_or_else(|_| "9999".to_string())
                .parse()
                .expect("Invalid STATE_TCP_PORT");
            Box::new(tcp_push::TcpPushReceiver::new(port))
        }
        "http" => {
            let primary_addr = std::env::var("STATE_HTTP_PRIMARY")
                .expect("STATE_HTTP_PRIMARY required for http backend (e.g. 141.217.168.152:9998)");
            Box::new(http_pull::HttpPullReceiver::new(&primary_addr))
        }
        "redis_kv" => {
            let url = std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
            Box::new(redis_kv::RedisKvReceiver::new(&url))
        }
        "redis_ps" => {
            let url = std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
            Box::new(redis_pubsub::RedisPubSubReceiver::new(&url))
        }
        "file" => {
            let path = std::env::var("STATE_FILE_PATH")
                .unwrap_or_else(|_| "/tmp/quic_migration_state".to_string());
            let poll_ms: u64 = std::env::var("STATE_FILE_POLL_MS")
                .unwrap_or_else(|_| "10".to_string())
                .parse()
                .unwrap_or(10);
            Box::new(file_backend::FileReceiver::new(&path, poll_ms))
        }
        _ => {
            eprintln!("Unknown STATE_TRANSFER backend: {backend}");
            std::process::exit(1);
        }
    }
}

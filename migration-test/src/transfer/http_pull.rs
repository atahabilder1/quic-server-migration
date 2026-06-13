//! Backend 2: HTTP Pull
//!
//! Primary server exposes an HTTP endpoint serving migration state.
//! Preferred server polls/requests the state when it needs it.
//!
//! Config:
//!   STATE_TRANSFER=http
//!   STATE_HTTP_PORT=9998                    (sender: HTTP server port)
//!   STATE_HTTP_PRIMARY=141.217.168.152:9998 (receiver: where to pull from)

use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::time::Instant;

use super::{StateSender, StateReceiver, TransferMetrics, TransferResult, TransferError};

/// Sender: starts an HTTP server that serves the state on GET /state.
pub struct HttpPullSender {
    port: u16,
}

impl HttpPullSender {
    pub fn new(port: u16) -> Self {
        println!("  [HTTP Pull] Will serve state on HTTP port {port}");
        Self { port }
    }
}

impl StateSender for HttpPullSender {
    fn send_state(&mut self, data: &[u8], _instance_id: &str) -> TransferResult<TransferMetrics> {
        let mut metrics = TransferMetrics::new(self.name());
        metrics.state_size = data.len();
        metrics.send_start = Some(Instant::now());

        // Start a simple HTTP server that serves the state exactly once
        let listener = TcpListener::bind(format!("0.0.0.0:{}", self.port))?;
        println!("    [HTTP] Serving state on port {} (waiting for pull)...", self.port);

        // Store data for the handler
        let data_owned = data.to_vec();

        // Accept one connection and serve the state
        let (mut stream, src) = listener.accept()?;
        println!("    [HTTP] Pull request from {src}");

        // Read the HTTP request (we don't care about the content)
        let mut req_buf = [0u8; 4096];
        let _ = stream.read(&mut req_buf);

        // Send HTTP response with the state as binary body
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
            data_owned.len()
        );
        stream.write_all(response.as_bytes())?;
        stream.write_all(&data_owned)?;
        stream.flush()?;

        metrics.send_end = Some(Instant::now());
        println!("    [HTTP] State served ({} bytes)", data_owned.len());

        Ok(metrics)
    }

    fn name(&self) -> &str { "http" }
}

/// Receiver: pulls state from primary's HTTP endpoint.
pub struct HttpPullReceiver {
    primary_addr: String,
}

impl HttpPullReceiver {
    pub fn new(primary_addr: &str) -> Self {
        println!("  [HTTP Pull] Will pull state from http://{primary_addr}/state");
        Self { primary_addr: primary_addr.to_string() }
    }
}

impl StateReceiver for HttpPullReceiver {
    fn receive_state(&mut self, _instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)> {
        let mut metrics = TransferMetrics::new(self.name());

        println!("Waiting to pull migration state from {}...", self.primary_addr);
        metrics.receive_start = Some(Instant::now());

        // Retry connecting until primary's HTTP server is ready
        let mut stream;
        loop {
            match TcpStream::connect(&self.primary_addr) {
                Ok(s) => { stream = s; break; }
                Err(_) => {
                    std::thread::sleep(std::time::Duration::from_millis(100));
                    continue;
                }
            }
        }

        // Send HTTP GET request
        let request = format!(
            "GET /state HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n",
            self.primary_addr
        );
        stream.write_all(request.as_bytes())?;
        stream.flush()?;

        // Read the full response
        let mut response = Vec::new();
        stream.read_to_end(&mut response)?;

        // Parse HTTP response: find the body after \r\n\r\n
        let header_end = find_header_end(&response)
            .ok_or_else(|| TransferError::Backend("Invalid HTTP response".to_string()))?;
        let body = response[header_end..].to_vec();

        metrics.receive_end = Some(Instant::now());
        metrics.state_size = body.len();

        println!("  State pulled ({} bytes)", body.len());

        Ok((body, metrics))
    }

    fn name(&self) -> &str { "http" }
}

/// Find the end of HTTP headers (position after \r\n\r\n).
fn find_header_end(data: &[u8]) -> Option<usize> {
    for i in 0..data.len().saturating_sub(3) {
        if &data[i..i + 4] == b"\r\n\r\n" {
            return Some(i + 4);
        }
    }
    None
}

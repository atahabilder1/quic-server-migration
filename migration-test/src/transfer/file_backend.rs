//! Backend 5: Shared File
//!
//! Primary server writes state to a file on a shared filesystem.
//! Preferred server polls the file until it appears, then reads it.
//!
//! For testing on the same machine, use /tmp/.
//! For cross-machine, use NFS or any shared mount.
//!
//! Config:
//!   STATE_TRANSFER=file
//!   STATE_FILE_PATH=/tmp/quic_migration_state  (path to state file)
//!   STATE_FILE_POLL_MS=10                       (poll interval, receiver only)

use std::fs;
use std::path::PathBuf;
use std::time::{Duration, Instant};

use super::{StateSender, StateReceiver, TransferMetrics, TransferResult, TransferError};

/// Sender: writes state to a file.
pub struct FileSender {
    path: PathBuf,
}

impl FileSender {
    pub fn new(path: &str) -> Self {
        println!("  [File] Will write state to {path}");
        // Clean up any leftover file from previous run
        let _ = fs::remove_file(path);
        Self { path: PathBuf::from(path) }
    }
}

impl StateSender for FileSender {
    fn send_state(&mut self, data: &[u8], _instance_id: &str) -> TransferResult<TransferMetrics> {
        let mut metrics = TransferMetrics::new(self.name());
        metrics.state_size = data.len();
        metrics.send_start = Some(Instant::now());

        // Write to a temp file first, then rename (atomic on same filesystem)
        let tmp_path = self.path.with_extension("tmp");
        fs::write(&tmp_path, data)?;
        fs::rename(&tmp_path, &self.path)?;

        metrics.send_end = Some(Instant::now());
        println!("    [File] State written to {:?} ({} bytes)", self.path, data.len());

        Ok(metrics)
    }

    fn name(&self) -> &str { "file" }
}

/// Receiver: polls for the state file until it appears.
pub struct FileReceiver {
    path: PathBuf,
    poll_ms: u64,
}

impl FileReceiver {
    pub fn new(path: &str, poll_ms: u64) -> Self {
        println!("  [File] Will watch for state at {path} (poll every {poll_ms}ms)");
        // Clean up any leftover file from previous run
        let _ = fs::remove_file(path);
        Self { path: PathBuf::from(path), poll_ms }
    }
}

impl StateReceiver for FileReceiver {
    fn receive_state(&mut self, _instance_id: &str) -> TransferResult<(Vec<u8>, TransferMetrics)> {
        let mut metrics = TransferMetrics::new(self.name());

        println!("Waiting for migration state file at {:?}...", self.path);
        metrics.receive_start = Some(Instant::now());

        // Poll until file exists
        loop {
            if self.path.exists() {
                match fs::read(&self.path) {
                    Ok(data) if !data.is_empty() => {
                        metrics.receive_end = Some(Instant::now());
                        metrics.state_size = data.len();

                        // Delete file after reading
                        let _ = fs::remove_file(&self.path);

                        println!("  State read from file ({} bytes)", data.len());
                        return Ok((data, metrics));
                    }
                    _ => {
                        // File exists but is empty (still being written), wait
                    }
                }
            }
            std::thread::sleep(Duration::from_millis(self.poll_ms));
        }
    }

    fn name(&self) -> &str { "file" }
}

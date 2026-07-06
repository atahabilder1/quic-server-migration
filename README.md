# Cross-Machine QUIC Server-Side Migration

> **A complete research platform for QUIC server-side connection migration across physically separate machines, with 5 real-world application proof-of-concepts.**

A research implementation using Mozilla's Neqo (Rust) that demonstrates how TLS cryptographic state can be transferred between separate servers to silently migrate a client's QUIC connection. Proves the feasibility of the QUIC-Exfil attack (RFC 9000 Section 9.6) and explores legitimate applications including load balancing, health-checked failover, anycast routing, BitTorrent WebSeed migration, and IPFS gateway migration.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Key Results](#key-results)
- [Application PoCs](#application-proof-of-concepts)
- [State Transfer Backends](#state-transfer-backends)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Test Results](#test-results)
- [Documentation](#documentation)
- [Research Context](#research-context)

---

## How It Works

A client (Firefox or neqo-client) connects to a **primary server** via HTTP/3. During the TLS handshake, the primary advertises a **preferred address** on a different physical machine. After the handshake, the primary exports ~445 bytes of TLS secrets and connection state and transfers it to the **preferred server**. The preferred server imports the keys, decrypts the client's `PATH_CHALLENGE`, and sends a `PATH_RESPONSE`. The client's connection silently migrates -- the browser gives **zero indication** that two servers are involved.

```
                QUIC Server-Side Migration Flow

   Client (Firefox)         Primary Server          Preferred Server
   141.217.168.127          141.217.168.152          141.217.168.143
        |                        |                        |
   [1]  |--- QUIC ClientHello -->|                        |
        |                        |                        |
   [2]  |<-- ServerHello --------|                        |
        |    + preferred_address |                        |
        |    = 141.217.168.143   |                        |
        |                        |                        |
   [3]  |                        |--- State Transfer ---->|
        |                        |    (TCP/HTTP/Redis)    |
        |                        |    445 bytes:          |
        |                        |    TLS secrets + CIDs  |
        |                        |    + packet numbers    |
        |                        |                        |
   [4]  |--- PATH_CHALLENGE ---------------------------->|
        |                        |                        |
   [5]  |<-- PATH_RESPONSE ------------------------------|
        |                        |                        |
   [6]  |====== Direct traffic (migration complete) ====>|
        |                        |                        |
        |  Browser shows .152    |   Traffic goes to .143 |
        |  (no visual indicator) |   (firewall can't tell)|
```

---

## Architecture

### Four-Machine Testbed

All experiments run across four separate physical machines on the same LAN (141.217.168.x):

| Machine | Role | IP Address | Ports | Software |
|---------|------|------------|-------|----------|
| optiplex7010 | **Client** | 141.217.168.127 | -- | Firefox 151+, neqo-client |
| opti7040 | **Primary Server** | 141.217.168.152 | 4433 (QUIC) | primary-server, lb-frontend, health-check-primary |
| homeserver2 | **Preferred Server** | 141.217.168.143 | 4433 (QUIC), 9998 (health), 9999 (state) | preferred-server, health-check-preferred |
| Proxmox VM | **Redis / Backend 2** | 141.217.168.200 | 6379 (Redis), 4433 (QUIC) | Redis, preferred-server (for LB PoC) |

### Migration State (445 bytes)

The state transferred between servers contains:

| Field | Size | Purpose |
|-------|------|---------|
| TLS Read Secret | ~48 bytes | Decrypt client's packets |
| TLS Write Secret | ~48 bytes | Encrypt responses to client |
| Read AEAD + HP keys | Derived | Actual decryption keys |
| Write AEAD + HP keys | Derived | Actual encryption keys |
| Local Connection IDs | 8 × ~10 bytes | Server's CIDs the client may use |
| Remote Connection IDs | ~10 bytes | Client's CID for response DCID |
| Client Address | ~6 bytes | Client's IP:port for sending |
| QUIC Version | 4 bytes | Version negotiation state |
| Packet Numbers | ~8 bytes | Next PN for encryption |

---

## Key Results

### Core Migration

- Cross-machine migration working across **3 physical machines**
- **5 state transfer backends** implemented and benchmarked
- **2 timing strategies** (Immediate and Lazy)
- **All 8 combinations tested** end-to-end with **100% success rate**
- Tested with **real Firefox browser** (HTTP/3, version 151.0.3)
- Migration state: **445 bytes** (TLS secrets, CIDs, client address)
- State transfer latency: **700μs** (TCP Push) to **25ms** (HTTP Pull)

### Evaluation Matrix (8 Metrics × 8 Combinations)

```
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Combination     | Lat | Sec | Scl | Rel | Cpl | Sim | Dep | Per | TOTAL |
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Imm + TCP Push  |  5  |  1  |  1  |  2  |  1  |  5  |  5  |  1  |  21   |
| Imm + HTTP Pull |  2  |  3  |  3  |  3  |  3  |  3  |  5  |  2  |  24   |
| Imm + Redis KV  |  4  |  3  |  5  |  5  |  5  |  3  |  2  |  5  |  32   | <-- Best Overall
| Imm + Redis PS  |  4  |  1  |  4  |  2  |  5  |  3  |  2  |  1  |  22   |
| Lazy + TCP Push |  5  |  2  |  1  |  3  |  1  |  3  |  5  |  1  |  21   |
| Lazy + HTTP Pull|  2  |  5  |  3  |  3  |  3  |  3  |  5  |  3  |  27   | <-- Best Security
| Lazy + Redis KV |  4  |  3  |  5  |  5  |  5  |  3  |  2  |  5  |  32   | <-- Best Overall
| Lazy + Redis PS |  4  |  1  |  4  |  3  |  5  |  3  |  2  |  1  |  23   |
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+

Lat=Latency  Sec=Security  Scl=Scalability  Rel=Reliability
Cpl=Coupling(loose=5)  Sim=Simplicity  Dep=No Dependencies  Per=Persistence
```

| Pick | Score | Use Case |
|------|-------|----------|
| **Redis KV** | 32/40 | Best overall -- scalability, reliability, persistence |
| **Lazy + HTTP Pull** | 27/40 | Best security -- secrets never leave primary memory |
| **Immediate + TCP Push** | 21/40 | Best for demos -- fastest, simplest, zero dependencies |

---

## Application Proof-of-Concepts

Five real-world applications built on top of the core migration mechanism, each with working code, test scripts, and comprehensive PDF documentation with diagrams.

### 1. Health-Checked Migration

> **Problem:** Primary unconditionally advertises `preferred_address`. If preferred is down, client times out.
> **Solution:** Check preferred health before migration. If unhealthy, serve directly.

| Feature | Detail |
|---------|--------|
| Binary | `health-check-primary`, `health-check-preferred` |
| Health modes | TCP Probe (port 9998, 200ms timeout), Redis Heartbeat (TTL 3s) |
| Env vars | `HEALTH_CHECK=tcp\|redis\|none`, `HEALTH_PORT=9998` |
| Background | Re-checks every 5s, logs status changes |
| Fallback | Serves directly without migration (zero client errors) |

```bash
# Preferred server (with health listener on port 9998):
health-check-preferred 141.217.168.143:4433 9999

# Primary server (probes port 9998 before advertising preferred_address):
HEALTH_CHECK=tcp health-check-primary 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999
```

### 2. QUIC-Native Load Balancer

> **Concept:** "Fire-and-forget" load balancing. Frontend handles handshake only (1 RTT), selects a backend, migrates the connection, then steps completely out of the data path.

| Feature | Detail |
|---------|--------|
| Binary | `lb-frontend` |
| Policies | `round_robin` (default), `random` |
| Env vars | `LB_POLICY=round_robin\|random`, `STATE_PORT=9999` |
| Backends | Any number of `preferred-server` instances |
| Key advantage | Zero bandwidth bottleneck -- frontend processes zero post-migration packets |

```
Traditional LB:        Client ↔ LB ↔ Backend   (every packet through LB)
QUIC Migration LB:     Client → LB (1 RTT)  →  Client ↔ Backend (direct)
```

```bash
# Start 2 backends:
preferred-server 141.217.168.143:4433 9999   # Backend 1
preferred-server 141.217.168.200:4433 9999   # Backend 2

# Start LB frontend:
lb-frontend 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433
```

### 3. BitTorrent WebSeed Migration

> **Concept:** Two HTTP/3 servers host the same large file (WebSeed). Primary migrates connection to preferred, enabling seamless failover with SHA-256 integrity verification.

| Feature | Detail |
|---------|--------|
| Binary | `webseed-primary` |
| SHA-256 | Pure Rust implementation (FIPS 180-4, no external deps) |
| Headers | `x-sha256`, `content-disposition`, `content-type: application/octet-stream` |
| Verification | Client compares `sha256sum` of downloaded file with `x-sha256` header |

```bash
# Create test file and serve:
dd if=/dev/urandom of=/tmp/test_100mb.bin bs=1M count=100
webseed-primary 0.0.0.0:4433 141.217.168.143:4433 /tmp/test_100mb.bin 141.217.168.143:9999
```

### 4. DNS + Anycast Hybrid Routing

> **Concept:** Use QUIC migration to make anycast-routed connections immune to BGP route changes. Phase 1: anycast for fast discovery. Phase 2: unicast for stable connection lifetime.

| Script | Purpose |
|--------|---------|
| `setup_anycast_sim.sh` | Create VIP (10.99.99.1), iptables DNAT to primary |
| `setup_dnsmasq.sh` | Local DNS resolving test domain to primary |
| `test_route_flap.sh` | Prove migrated connections survive BGP route changes |
| `teardown.sh` | Clean up all rules |

```
Before route flap: VIP → .152 (primary) → migration → .143 (direct unicast)
After route flap:  VIP → .200 (new PoP)  |  existing conn still on .143 ✓
```

### 5. IPFS Gateway Migration

> **Concept:** Two IPFS gateways (Kubo) pin the same content (CID). Migration between gateways preserves content integrity by design -- IPFS content is content-addressed.

| Script | Purpose |
|--------|---------|
| `setup_ipfs.sh` | Install Kubo on both servers, pin test CID |
| `test_ipfs_migration.sh` | Serve IPFS content via HTTP/3, verify integrity |
| `teardown_ipfs.sh` | Stop IPFS daemons |

```
CID = hash(content)  →  Same CID = same content (cryptographically guaranteed)
Migration cannot corrupt data  →  IPFS integrity is maintained across any server
```

---

## State Transfer Backends

Selected via `STATE_TRANSFER` environment variable:

| Backend | Env Var | Pattern | Latency | Dependencies |
|---------|---------|---------|---------|-------------|
| TCP Push | `STATE_TRANSFER=tcp` | Direct push to preferred | ~700μs | None |
| HTTP Pull | `STATE_TRANSFER=http` | Preferred pulls from primary | ~25ms | None |
| Redis KV | `STATE_TRANSFER=redis_kv` | Shared key-value store | ~1.3ms | Redis |
| Redis Pub/Sub | `STATE_TRANSFER=redis_ps` | Event-driven push | ~1.5ms | Redis |
| File | `STATE_TRANSFER=file` | Shared filesystem | ~10ms | NFS/shared mount |

### Timing Strategies

| Timing | Env Var | Description |
|--------|---------|-------------|
| Immediate | `TRANSFER_TIMING=immediate` | Transfer state right after handshake (default) |
| Lazy | `TRANSFER_TIMING=lazy` | Start receiver in background, import crypto on first packet |

---

## Quick Start

### Prerequisites

- Rust toolchain (1.90+) on all machines
- 3+ machines on the same network (or adjust IPs)
- Redis server (optional, for redis_kv/redis_ps backends)

### 1. Clone and Build

```bash
git clone git@github.com:atahabilder1/quic-server-migration.git
cd quic-server-migration/implementations/neqo_server_migration

# Build (same on all machines)
PKG_CONFIG_PATH=/nonexistent PKG_CONFIG_LIBDIR=/nonexistent cargo build --release

# Set library path
export LD_LIBRARY_PATH=$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)
```

### 2. Run the Basic Demo

```bash
# Terminal 1 — Preferred Server (homeserver2):
./target/release/preferred-server 141.217.168.143:4433 9999

# Terminal 2 — Primary Server (opti7040):
./target/release/primary-server 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999

# Terminal 3 — Client:
./target/release/neqo-client https://141.217.168.152:4433/
```

### 3. Run with Firefox

```bash
# Terminal 1 — Preferred Server:
preferred-up

# Terminal 2 — TCP HTTPS Bootstrap (opti7040):
bootstrap-up

# Terminal 3 — Primary Server (opti7040):
primary-up

# Firefox: navigate to https://141.217.168.152:4433/
# First load: TCP bootstrap (shows "Upgrading to HTTP/3")
# Refresh: HTTP/3 over QUIC with silent migration
```

Firefox `about:config` settings:
- `network.http.http3.enabled` = `true`
- `network.http.http3.alt-svc-mapping-for-testing` = `141.217.168.152:4433;h3=":4433"`
- `network.http.http3.disable_when_third_party_roots_found` = `false`

### 4. Switch Backends

```bash
# Primary server aliases:
primary-up              # TCP Push (default)
primary-up-redis        # Redis KV
primary-up-redis-ps     # Redis Pub/Sub
primary-up-http         # HTTP Pull

# Preferred server aliases:
preferred-up            # TCP Push, Immediate
preferred-up-redis      # Redis KV, Immediate
preferred-up-redis-lazy # Redis KV, Lazy
preferred-up-http       # HTTP Pull, Immediate
preferred-up-http-lazy  # HTTP Pull, Lazy
```

### 5. Run Application PoCs

```bash
# Health-Checked Migration:
HEALTH_CHECK=tcp health-check-primary 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999

# Load Balancer (2 backends):
lb-frontend 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433

# WebSeed (large file):
webseed-primary 0.0.0.0:4433 141.217.168.143:4433 /path/to/large/file

# DNS+Anycast Simulation:
cd application/poc/dns_anycast && sudo ./setup_anycast_sim.sh

# IPFS Gateway:
cd application/poc/ipfs_gateway && ./setup_ipfs.sh
```

---

## Project Structure

```
quic-server-migration/
│
├── implementations/
│   ├── neqo_server_migration/              # Modified Mozilla Neqo (Rust)
│   │   ├── migration-test/src/
│   │   │   ├── primary_server.rs           # HTTP/3 primary server
│   │   │   ├── preferred_server.rs         # Preferred server (immediate + lazy)
│   │   │   ├── health_check_primary.rs     # PoC 1: Health-checked primary
│   │   │   ├── health_check_preferred.rs   # PoC 1: Preferred with heartbeat
│   │   │   ├── lb_frontend.rs              # PoC 2: Load balancer frontend
│   │   │   ├── webseed_primary.rs          # PoC 3: WebSeed file server
│   │   │   └── transfer/                   # Pluggable state transfer backends
│   │   │       ├── mod.rs                  #   Trait definitions + factory
│   │   │       ├── tcp_push.rs             #   Backend 1: Direct TCP
│   │   │       ├── http_pull.rs            #   Backend 2: HTTP REST API
│   │   │       ├── redis_kv.rs             #   Backend 3: Redis SET/GET
│   │   │       ├── redis_pubsub.rs         #   Backend 4: Redis Pub/Sub
│   │   │       └── file_backend.rs         #   Backend 5: Shared filesystem
│   │   ├── neqo-transport/src/
│   │   │   ├── migration_state.rs          # State serialization (new)
│   │   │   ├── crypto.rs                   # TLS secret export/import (modified)
│   │   │   ├── connection/mod.rs           # export_migration_state() (modified)
│   │   │   ├── cid.rs                      # CID enumeration (modified)
│   │   │   └── lib.rs                      # Public crypto module (modified)
│   │   └── MIGRATION_DOCUMENTATION.md      # Comprehensive guide
│   │
│   └── paper_attack_impl/                  # QUIC-Exfil attack (Rust)
│
├── application/
│   ├── APPLICATION_ANALYSIS.pdf            # 5 application analyses (54KB)
│   ├── IPFS_QUIC_MIGRATION_ANALYSIS.pdf    # IPFS deep-dive
│   ├── RELATED_WORK_SURVEY.pdf             # Related work survey
│   ├── bibliography.bib                    # BibTeX references
│   └── poc/                                # Proof-of-Concept implementations
│       ├── HEALTH_CHECK_POC.pdf            # PoC 1 documentation (30KB, diagrams)
│       ├── LOAD_BALANCER_POC.pdf           # PoC 2 documentation (32KB, diagrams)
│       ├── WEBSEED_POC.pdf                 # PoC 3 documentation (33KB, diagrams)
│       ├── DNS_ANYCAST_POC.pdf             # PoC 4 documentation (29KB, diagrams)
│       ├── IPFS_GATEWAY_POC.pdf            # PoC 5 documentation (37KB, diagrams)
│       ├── dns_anycast/                    # PoC 4: iptables + dnsmasq scripts
│       ├── ipfs_gateway/                   # PoC 5: Kubo IPFS setup scripts
│       └── webseed/                        # PoC 3: File + torrent test scripts
│
├── ideas/                                  # Research task documents
├── benchmarks/                             # Benchmark scripts + results
├── scripts/                                # Machine setup scripts
├── alt_svc_server.py                       # TCP HTTPS bootstrap for Firefox
├── *.svg                                   # Architecture diagrams
└── *.ipynb                                 # Research notebooks
```

---

## Test Results

### All 8 Backend Combinations

```
                TCP Push       HTTP Pull      Redis KV       Redis Pub/Sub
             +-------------+-------------+-------------+---------------+
 Immediate   |    PASS      |    PASS      |    PASS      |    PASS       |
             |  send: 734μs |  send: 35ms  |  send: 1.2ms |  send: 1.5ms  |
             +-------------+-------------+-------------+---------------+
 Lazy        |    PASS      |    PASS      |    PASS      |    PASS       |
             |  send: 479μs |  send: 25ms  |  send: 1.5ms |  send: 1.5ms  |
             |  import: 7μs |  import: 24ms|  import: 4ms |  import: 425μs|
             +-------------+-------------+-------------+---------------+
```

### PoC Verification (67 tests)

| Category | Tests | Result |
|----------|-------|--------|
| Binary compilation | 7 | All PASS |
| CLI usage messages | 6 | All PASS |
| Health check modes (TCP, Redis, none) | 8 | All PASS |
| Load balancer policies | 4 | All PASS |
| WebSeed SHA-256 integrity | 5 | All PASS |
| End-to-end migration | 17 | All PASS |
| Scripts and documentation | 14 | All PASS |
| Cargo.toml registration | 6 | All PASS |
| **Total** | **67** | **67 PASS** |

---

## Documentation

| Document | Description | Size |
|----------|-------------|------|
| [`MIGRATION_DOCUMENTATION.md`](implementations/neqo_server_migration/MIGRATION_DOCUMENTATION.md) | Complete migration guide (architecture, code changes, demo) | -- |
| [`APPLICATION_ANALYSIS.pdf`](application/APPLICATION_ANALYSIS.pdf) | Analysis of 5 migration applications | 54KB |
| [`HEALTH_CHECK_POC.pdf`](application/poc/HEALTH_CHECK_POC.pdf) | Health check PoC with sequence diagrams | 30KB |
| [`LOAD_BALANCER_POC.pdf`](application/poc/LOAD_BALANCER_POC.pdf) | Load balancer PoC with data flow diagrams | 32KB |
| [`WEBSEED_POC.pdf`](application/poc/WEBSEED_POC.pdf) | WebSeed PoC with SHA-256 verification flow | 33KB |
| [`DNS_ANYCAST_POC.pdf`](application/poc/DNS_ANYCAST_POC.pdf) | DNS+Anycast PoC with route flap analysis | 29KB |
| [`IPFS_GATEWAY_POC.pdf`](application/poc/IPFS_GATEWAY_POC.pdf) | IPFS Gateway PoC with content-addressing diagrams | 37KB |
| [`PAPER_SUMMARY.md`](PAPER_SUMMARY.md) | Analysis of the QUIC-Exfil attack paper | -- |
| [`RELATED_WORK_SURVEY.pdf`](application/RELATED_WORK_SURVEY.pdf) | Related work survey with bibliography | -- |

---

## Code Changes to Neqo

We modified 4 files and added 1 new file in Mozilla's `neqo-transport` crate:

| File | Change | Purpose |
|------|--------|---------|
| `crypto.rs` | Added `secret` field to `CryptoDxAppData` | Retain TLS traffic secret for export |
| `migration_state.rs` | **New file** | Serialization/deserialization of migration state |
| `connection/mod.rs` | Added `export_migration_state()` | Export 445 bytes of connection state |
| `cid.rs` | Added accessor methods | Enumerate Connection IDs |
| `lib.rs` | Made `crypto` module public | Allow external access to crypto types |

Plus the `migration-test` crate with **6 binaries** and **5 transfer backends**.

---

## Binaries

| Binary | Purpose | Source |
|--------|---------|--------|
| `primary-server` | HTTP/3 server with migration | `primary_server.rs` |
| `preferred-server` | Imports state, handles PATH_CHALLENGE | `preferred_server.rs` |
| `health-check-primary` | Primary with TCP/Redis health check | `health_check_primary.rs` |
| `health-check-preferred` | Preferred with heartbeat | `health_check_preferred.rs` |
| `lb-frontend` | Load balancer with round-robin/random | `lb_frontend.rs` |
| `webseed-primary` | Large file server with SHA-256 | `webseed_primary.rs` |

---

## Research Context

- **RFC 9000, Section 9.6** -- Server's Preferred Address mechanism
- **QUIC-Exfil attack** -- Server-side migration exploited for data exfiltration
- **Key finding:** Firewalls cannot detect the migration (encrypted inside QUIC)
- **ML classifiers** achieve only 0-47% F1-score against this attack
- **Our contribution:** First working cross-machine implementation with 5 application PoCs

---

## License

Research project. Neqo modifications are based on Mozilla's Neqo (Apache 2.0 / MIT).

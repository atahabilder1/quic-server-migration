# Cross-Machine QUIC Server-Side Migration

A research implementation of cross-machine QUIC server-side migration using Mozilla's Neqo. Demonstrates and benchmarks how TLS cryptographic state can be transferred between physically separate servers to silently migrate a client's QUIC connection -- proving the feasibility of the QUIC-Exfil attack.

## What This Project Does

A client (Firefox or neqo-client) connects to a **primary server** via HTTP/3. During the TLS handshake, the primary server advertises a **preferred address** on a different physical machine. After the handshake, the primary server exports the TLS secrets and connection state (~445 bytes) and transfers it to the **preferred server**. The preferred server imports the keys, decrypts the client's PATH_CHALLENGE, and sends a PATH_RESPONSE. The client's connection silently migrates to the preferred server without any browser indication.

This is the QUIC-Exfil attack described in RFC 9000 Section 9.6 -- a firewall cannot detect this migration because everything is encrypted inside QUIC.

## Key Results

- Cross-machine migration working across 3 physical machines
- 4 state transfer mechanisms implemented and benchmarked (TCP Push, HTTP Pull, Redis KV, Redis Pub/Sub)
- 2 timing strategies (Immediate and Lazy)
- All 8 combinations tested end-to-end with 100% success rate
- Best overall: Redis KV (32/40 across 8 evaluation metrics)
- Tested with real Firefox browser (HTTP/3)

## Architecture

```
Client (Firefox)         Primary Server          Preferred Server
141.217.168.127          141.217.168.152          141.217.168.143
                         (opti7040)               (homeserver2)
     |                        |                        |
     |--- QUIC Handshake ---->|                        |
     |    (preferred_address   |                        |
     |     = 141.217.168.143) |                        |
     |                        |--- State Transfer ---->|
     |                        |    (TCP/HTTP/Redis)    |
     |                        |    445 bytes:          |
     |                        |    TLS secrets + CIDs  |
     |                        |                        |
     |--- PATH_CHALLENGE ---------------------------->|
     |<-- PATH_RESPONSE ------------------------------|
     |                                                |
     |    Connection silently migrated                |
```

## State Transfer Backends

Selected via `STATE_TRANSFER` environment variable:

| Backend | Command | Pattern | Latency |
|---------|---------|---------|---------|
| TCP Push | `STATE_TRANSFER=tcp` | Direct push | ~700us |
| HTTP Pull | `STATE_TRANSFER=http` | On-demand pull | ~25ms |
| Redis KV | `STATE_TRANSFER=redis_kv` | Shared storage | ~1.3ms |
| Redis Pub/Sub | `STATE_TRANSFER=redis_ps` | Event-driven | ~1.5ms |

## Timing Strategies

Selected via `TRANSFER_TIMING` environment variable:

| Timing | Command | Description |
|--------|---------|-------------|
| Immediate | `TRANSFER_TIMING=immediate` | Transfer state right after handshake (default) |
| Lazy | `TRANSFER_TIMING=lazy` | Start receiver in background, import crypto on first packet |

## Test Setup: Four Physical Machines

All experiments run across four separate physical machines on the same LAN:

```
Machine          Role               IP                Software
----------------------------------------------------------------------
optiplex7010     Client             141.217.168.127   neqo-client, Firefox
opti7040         Primary Server     141.217.168.152   primary-server, bootstrap-server
homeserver2      Preferred Server   141.217.168.143   preferred-server
redis-server     Redis (Proxmox VM) 141.217.168.200   Redis 6379
```

The client is unmodified -- standard Firefox or neqo-client. It has no idea two servers are involved. The primary server handles the TLS handshake and exports crypto state. The preferred server imports the state and takes over the connection.

## What We Test

Two independent research dimensions, tested in every combination:

**WHEN to transfer (timing):**
- **Immediate** -- transfer state right after handshake, before client migrates
- **Lazy** -- start receiver in background, import crypto only when first packet arrives

**HOW to transfer (mechanism):**
- **TCP Push** -- primary pushes directly to preferred over TCP socket
- **HTTP Pull** -- primary exposes HTTP endpoint, preferred pulls when needed
- **Redis KV** -- primary writes to Redis (SET), preferred reads (GET), CID-based keys
- **Redis Pub/Sub** -- primary publishes to channel, preferred subscribes

## Results: All 8 Combinations Pass

```
                TCP Push       HTTP Pull      Redis KV       Redis Pub/Sub
             +-------------+-------------+-------------+---------------+
 Immediate   |  PASS        |  PASS        |  PASS        |  PASS         |
             |  send: 734us |  send: 35ms  |  send: 1.2ms |  send: 1.5ms  |
             +-------------+-------------+-------------+---------------+
 Lazy        |  PASS        |  PASS        |  PASS        |  PASS         |
             |  send: 479us |  send: 25ms  |  send: 1.5ms |  send: 1.5ms  |
             |  import: 7us |  import: 24ms|  import: 4ms |  import: 425us|
             +-------------+-------------+-------------+---------------+
```

## Evaluation: 8 Metrics x 8 Combinations

```
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Combination     | Lat | Sec | Scl | Rel | Cpl | Sim | Dep | Per | TOTAL |
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+
| Imm + TCP Push  |  5  |  1  |  1  |  2  |  1  |  5  |  5  |  1  |  21   |
| Imm + HTTP Pull |  2  |  3  |  3  |  3  |  3  |  3  |  5  |  2  |  24   |
| Imm + Redis KV  |  4  |  3  |  5  |  5  |  5  |  3  |  2  |  5  |  32   |
| Imm + Redis PS  |  4  |  1  |  4  |  2  |  5  |  3  |  2  |  1  |  22   |
| Lazy + TCP Push |  5  |  2  |  1  |  3  |  1  |  3  |  5  |  1  |  21   |
| Lazy + HTTP Pull|  2  |  5  |  3  |  3  |  3  |  3  |  5  |  3  |  27   |
| Lazy + Redis KV |  4  |  3  |  5  |  5  |  5  |  3  |  2  |  5  |  32   |
| Lazy + Redis PS |  4  |  1  |  4  |  3  |  5  |  3  |  2  |  1  |  23   |
+-----------------+-----+-----+-----+-----+-----+-----+-----+-----+-------+

Lat=Latency  Sec=Security  Scl=Scalability  Rel=Reliability
Cpl=Coupling(loose=5)  Sim=Simplicity  Dep=No Dependencies  Per=Persistence
```

**Best overall (32/40):** Redis KV -- works with both timings, highest in scalability, reliability, persistence

**Best for security (27/40):** Lazy + HTTP Pull -- secrets stay in primary memory until pulled

**Best for demos (21/40):** Immediate + TCP Push -- fastest, simplest, no dependencies

## Reproducing the Setup

### Prerequisites

- Rust toolchain (on all 3 machines)
- 3 machines on the same network (or adjust IPs)
- Redis server (for redis_kv/redis_ps backends, can be a VM)

### 1. Clone the repo on all 3 machines

```bash
git clone git@github.com:atahabilder1/quic-server-migration.git
cd quic-server-migration
```

### 2. Run the setup script for each machine's role

```bash
# On client machine (this PC):
./scripts/setup-client.sh

# On primary server (opti7040):
./scripts/setup-primary.sh

# On preferred server (homeserver2):
./scripts/setup-preferred.sh
```

Each script builds the correct binary, sets env vars, and installs bash aliases.
To use custom IPs: `./scripts/setup-primary.sh <PREFERRED_IP> <REDIS_IP>` (see script headers for args).

### 3. Run the demo

```bash
# On preferred server:
preferred-up

# On primary server (two terminals):
bootstrap-up   # Terminal 1: TCP HTTPS for Firefox
primary-up     # Terminal 2: QUIC server

# On client:
quic-client                                    # neqo-client
# Or Firefox: navigate to https://<PRIMARY_IP>:4433/
```

### Switch backends

```bash
# Primary
primary-up-redis      # Redis KV
primary-up-redis-ps   # Redis Pub/Sub
primary-up-http       # HTTP Pull

# Preferred
preferred-up-redis         # Redis KV, Immediate
preferred-up-redis-lazy    # Redis KV, Lazy
preferred-up-http          # HTTP Pull, Immediate
preferred-up-http-lazy     # HTTP Pull, Lazy
```

### Run benchmarks

```bash
# Single-pair latency (20 runs per backend)
./benchmarks/run_benchmark.sh 20

# Multi-server (3 primary, 3 preferred)
./benchmarks/run_multiserver.sh

# Concurrent clients
./benchmarks/run_concurrent.sh 5
```

## Project Structure

```
quic-server-migration/
  implementations/
    neqo_server_migration/          # Modified Mozilla Neqo
      migration-test/src/
        primary_server.rs           # HTTP/3 primary server
        preferred_server.rs         # Preferred server (immediate + lazy)
        transfer/                   # Pluggable state transfer backends
          mod.rs                    # Trait definitions + selector
          tcp_push.rs               # Backend 1: Direct TCP
          http_pull.rs              # Backend 2: HTTP REST API
          redis_kv.rs               # Backend 3: Redis SET/GET
          redis_pubsub.rs           # Backend 4: Redis Pub/Sub
      neqo-transport/src/
        migration_state.rs          # State serialization (new)
        crypto.rs                   # TLS secret export/import (modified)
        connection/mod.rs           # Migration state export (modified)
      COMPREHENSIVE_GUIDE.pdf       # Full documentation (21 pages)
      COMPARISON_RESULTS.pdf        # Short comparison (3 pages)
    paper_attack_impl/              # QUIC-Exfil attack implementation
  benchmarks/
    run_benchmark.sh                # Experiment 1: Single-pair latency
    run_multiserver.sh              # Experiment 2: N:M routing
    run_concurrent.sh               # Experiment 3: Stress test
    results/                        # CSV benchmark data
  scripts/
    setup-client.sh                 # Client machine setup
    setup-primary.sh                # Primary server setup
    setup-preferred.sh              # Preferred server setup
  alt_svc_server.py                 # TCP HTTPS bootstrap for Firefox
  quic_server.py                    # Python QUIC server (aioquic)
  quic_client.py                    # Python QUIC client (aioquic)
  *.svg                             # Architecture diagrams
```

## Documentation

- **COMPREHENSIVE_GUIDE.pdf** -- Full 21-page guide covering architecture, code changes, timing strategies, transfer mechanisms, benchmark results, security analysis, and scoring
- **COMPARISON_RESULTS.pdf** -- 3-page focused comparison of all 8 When x How combinations
- **PAPER_SUMMARY.md** -- Analysis of the QUIC-Exfil attack paper

## Code Changes to Neqo

We modified 4 files and added 1 new file in Mozilla's neqo-transport crate:

1. **crypto.rs** -- Added `secret` field to retain TLS traffic secret for export
2. **migration_state.rs** (new) -- Serialization format for migration state
3. **connection/mod.rs** -- Added export_migration_state() method
4. **cid.rs** -- Added CID enumeration accessors
5. **lib.rs** -- Made crypto module public

Plus the migration-test crate with 2 binaries and 5 transfer backends.

## Research Context

- QUIC RFC 9000, Section 9.6 (Server's Preferred Address)
- QUIC-Exfil attack: server-side migration exploited for data exfiltration
- Firewalls cannot detect migration (encrypted inside QUIC)
- ML classifiers achieve only 0-47% F1-score against this attack

## License

Research project. Neqo modifications are based on Mozilla's Neqo (Apache 2.0 / MIT).

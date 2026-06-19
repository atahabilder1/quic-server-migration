#!/bin/bash
# Benchmark harness for QUIC migration state transfer backends.
#
# Runs each backend N times and collects metrics into CSV files.
#
# Usage:
#   ./benchmarks/run_benchmark.sh [runs_per_backend]
#   Default: 20 runs per backend
#
# Prerequisites:
#   - Servers built on opti7040 and homeserver2
#   - Redis running on homeserver2 (141.217.168.143:6379)
#   - SSH keys set up for opti7040Mini and homeserver2

set -e

RUNS=${1:-20}
NEQO_DIR="~/code/quic/implementations/neqo_server_migration"
LOCAL_DIR="$HOME/code/quic/implementations/neqo_server_migration"
CLIENT_BIN="$LOCAL_DIR/target/release/neqo-client"
CLIENT_LD="LD_LIBRARY_PATH=$(find $LOCAL_DIR/target/release/build -path '*/dist/Release/lib' -type d | head -1)"
RESULTS_DIR="$LOCAL_DIR/benchmarks/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

CSV="$RESULTS_DIR/benchmark_${TIMESTAMP}.csv"
echo "run,backend,send_latency_us,migration_success,client_connected,client_migrated" > "$CSV"

PRIMARY_HOST="opti7040Mini"
PREFERRED_HOST="homeserver2"
PRIMARY_IP="141.217.168.152"
PREFERRED_IP="141.217.168.143"

cleanup() {
    ssh $PRIMARY_HOST "kill \$(lsof -t -i:4433 -i:9998) 2>/dev/null" || true
    ssh $PREFERRED_HOST "kill \$(lsof -t -i:4433 -i:9999) 2>/dev/null" || true
    sleep 1
}

run_single_test() {
    local BACKEND=$1
    local RUN_NUM=$2
    local PREF_ENV=""
    local PREF_ARGS=""
    local PRIM_ENV=""
    local PRIM_ARGS=""

    case $BACKEND in
        tcp)
            PREF_ARGS="$PREFERRED_IP:4433 9999"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433 $PREFERRED_IP:9999"
            ;;
        http)
            PREF_ENV="STATE_TRANSFER=http STATE_HTTP_PRIMARY=$PRIMARY_IP:9998"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=http STATE_HTTP_PORT=9998"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
        redis_kv)
            PREF_ENV="STATE_TRANSFER=redis_kv REDIS_URL=141.217.168.200:6379"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_kv REDIS_URL=141.217.168.200:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
        redis_ps)
            PREF_ENV="STATE_TRANSFER=redis_ps REDIS_URL=141.217.168.200:6379"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_ps REDIS_URL=141.217.168.200:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
    esac

    # Start preferred server
    ssh $PREFERRED_HOST "cd $NEQO_DIR && $PREF_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 15 ./target/release/preferred-server $PREF_ARGS 2>&1" > /tmp/bench_preferred.log &
    local PREF_PID=$!
    sleep 1

    # Start primary server
    ssh $PRIMARY_HOST "cd $NEQO_DIR && $PRIM_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 15 ./target/release/primary-server $PRIM_ARGS 2>&1" > /tmp/bench_primary.log &
    local PRIM_PID=$!
    sleep 2

    # Run client
    eval $CLIENT_LD RUST_LOG=info timeout 8 $CLIENT_BIN https://$PRIMARY_IP:4433/ > /tmp/bench_client.log 2>&1 || true
    sleep 1

    # Extract metrics
    local SEND_LATENCY=$(grep "send_time=" /tmp/bench_primary.log 2>/dev/null | head -1 | sed 's/.*send_time=//; s/[^0-9.]//g')
    local MIGRATION_OK=$(grep -c "DECRYPTED" /tmp/bench_preferred.log 2>/dev/null || echo "0")
    local CLIENT_CONN=$(grep -c "Connection established" /tmp/bench_client.log 2>/dev/null || echo "0")
    local CLIENT_MIG=$(grep -c "Migrate to" /tmp/bench_client.log 2>/dev/null || echo "0")

    # Convert send latency to microseconds
    if [ -z "$SEND_LATENCY" ]; then
        SEND_LATENCY="0"
    fi

    echo "$RUN_NUM,$BACKEND,$SEND_LATENCY,$MIGRATION_OK,$CLIENT_CONN,$CLIENT_MIG" >> "$CSV"

    # Cleanup
    kill $PREF_PID $PRIM_PID 2>/dev/null || true
    wait $PREF_PID $PRIM_PID 2>/dev/null || true
    cleanup
}

echo "=== QUIC Migration Benchmark ==="
echo "  Runs per backend: $RUNS"
echo "  Output: $CSV"
echo "  Backends: tcp, http, redis_kv, redis_ps"
echo ""

for BACKEND in tcp http redis_kv redis_ps; do
    echo "--- Testing: $BACKEND ---"
    for i in $(seq 1 $RUNS); do
        printf "  Run %d/%d..." $i $RUNS
        cleanup
        run_single_test $BACKEND $i
        printf " done\n"
    done
    echo ""
done

echo "=== Benchmark Complete ==="
echo "Results: $CSV"
echo ""

# Print summary
echo "=== Summary ==="
for BACKEND in tcp http redis_kv redis_ps; do
    COUNT=$(grep ",$BACKEND," "$CSV" | wc -l)
    PASS=$(grep ",$BACKEND," "$CSV" | awk -F, '$4 > 0' | wc -l)
    echo "  $BACKEND: $PASS/$COUNT passed"
done

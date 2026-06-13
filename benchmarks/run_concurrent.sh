#!/bin/bash
# Experiment 3: Concurrent migrations (stress test)
#
# 1 primary server, 1 preferred server, N clients connecting simultaneously.
# Tests how each backend handles concurrent state transfers.
#
# Usage:
#   ./benchmarks/run_concurrent.sh [num_clients] [backend]
#   Default: 5 clients, all backends

set -e

NUM_CLIENTS=${1:-5}
BACKEND=${2:-"all"}
NEQO_DIR="~/code/quic/implementations/neqo_server_migration"
LOCAL_DIR="$HOME/code/quic/implementations/neqo_server_migration"
CLIENT_BIN="$LOCAL_DIR/target/release/neqo-client"
CLIENT_LD="LD_LIBRARY_PATH=$(find $LOCAL_DIR/target/release/build -path '*/dist/Release/lib' -type d | head -1)"
RESULTS_DIR="$LOCAL_DIR/benchmarks/results"

mkdir -p "$RESULTS_DIR"

PRIMARY_HOST="opti7040Mini"
PREFERRED_HOST="homeserver2"
PRIMARY_IP="141.217.168.152"
PREFERRED_IP="141.217.168.143"

cleanup() {
    ssh $PRIMARY_HOST "kill \$(lsof -t -i:4433 -i:9998) 2>/dev/null" || true
    ssh $PREFERRED_HOST "kill \$(lsof -t -i:4433 -i:9999) 2>/dev/null" || true
    sleep 1
}

run_concurrent_test() {
    local BACKEND=$1
    local LOG_PREFIX="/tmp/conc_${BACKEND}"

    echo ""
    echo "============================================"
    echo "  CONCURRENT TEST: $BACKEND ($NUM_CLIENTS clients)"
    echo "============================================"

    cleanup

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
            PREF_ENV="STATE_TRANSFER=redis_kv REDIS_URL=127.0.0.1:6379"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_kv REDIS_URL=$PREFERRED_IP:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
        redis_ps)
            PREF_ENV="STATE_TRANSFER=redis_ps REDIS_URL=127.0.0.1:6379"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_ps REDIS_URL=$PREFERRED_IP:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
    esac

    # Start preferred server
    ssh $PREFERRED_HOST "cd $NEQO_DIR && $PREF_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 30 ./target/release/preferred-server $PREF_ARGS 2>&1" > "${LOG_PREFIX}_pref.log" &
    sleep 1

    # Start primary server
    ssh $PRIMARY_HOST "cd $NEQO_DIR && $PRIM_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 30 ./target/release/primary-server $PRIM_ARGS 2>&1" > "${LOG_PREFIX}_prim.log" &
    sleep 2

    # Launch N clients simultaneously
    echo "  Launching $NUM_CLIENTS clients simultaneously..."
    local START_TIME=$(date +%s%N)
    for i in $(seq 1 $NUM_CLIENTS); do
        eval $CLIENT_LD RUST_LOG=info timeout 10 $CLIENT_BIN "https://$PRIMARY_IP:4433/" > "${LOG_PREFIX}_client${i}.log" 2>&1 &
    done
    wait
    local END_TIME=$(date +%s%N)
    local ELAPSED_MS=$(( ($END_TIME - $START_TIME) / 1000000 ))
    sleep 2

    # Collect results
    echo "  Results ($ELAPSED_MS ms total):"
    local CONNECTED=0
    local MIGRATED=0
    for i in $(seq 1 $NUM_CLIENTS); do
        local C=$(grep -c "Connection established" "${LOG_PREFIX}_client${i}.log" 2>/dev/null || echo "0")
        local M=$(grep -c "Migrate to" "${LOG_PREFIX}_client${i}.log" 2>/dev/null || echo "0")
        CONNECTED=$((CONNECTED + C))
        MIGRATED=$((MIGRATED + M))
    done

    local STATE_SENT=$(grep -c "sent successfully" "${LOG_PREFIX}_prim.log" 2>/dev/null || echo "0")
    local DECRYPTED=$(grep -c "DECRYPTED" "${LOG_PREFIX}_pref.log" 2>/dev/null || echo "0")

    echo "    Clients connected: $CONNECTED/$NUM_CLIENTS"
    echo "    Clients migrated:  $MIGRATED/$NUM_CLIENTS"
    echo "    States sent:       $STATE_SENT"
    echo "    Packets decrypted: $DECRYPTED"
    echo "    Total time:        ${ELAPSED_MS}ms"

    cleanup
}

echo "=== QUIC Concurrent Migration Test ==="
echo "  Clients: $NUM_CLIENTS"
echo ""

if [ "$BACKEND" = "all" ]; then
    for B in tcp http redis_kv redis_ps; do
        run_concurrent_test $B
    done
else
    run_concurrent_test $BACKEND
fi

echo ""
echo "=== Concurrent Tests Complete ==="

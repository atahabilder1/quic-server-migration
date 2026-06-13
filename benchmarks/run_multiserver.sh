#!/bin/bash
# Experiment 2: Multi-server migration (3 primaries, 3 preferred)
#
# Tests N:M routing capability of each backend.
# 3 primary servers on opti7040 (ports 4433, 4434, 4435)
# 3 preferred servers on homeserver2 (ports 4433, 4434, 4435)
# Each primary advertises a corresponding preferred server.
# 3 clients connect simultaneously, one to each primary.
#
# Usage:
#   ./benchmarks/run_multiserver.sh [backend]
#   Default: runs all backends

set -e

BACKEND=${1:-"all"}
NEQO_DIR="~/code/quic/implementations/neqo_server_migration"
LOCAL_DIR="$HOME/code/quic/implementations/neqo_server_migration"
CLIENT_BIN="$LOCAL_DIR/target/release/neqo-client"
CLIENT_LD="LD_LIBRARY_PATH=$(find $LOCAL_DIR/target/release/build -path '*/dist/Release/lib' -type d | head -1)"
RESULTS_DIR="$LOCAL_DIR/benchmarks/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

PRIMARY_HOST="opti7040Mini"
PREFERRED_HOST="homeserver2"
PRIMARY_IP="141.217.168.152"
PREFERRED_IP="141.217.168.143"

PORTS=(4433 4434 4435)
TCP_PORTS=(9999 9998 9997)

cleanup_all() {
    for PORT in "${PORTS[@]}"; do
        ssh $PRIMARY_HOST "kill \$(lsof -t -i:$PORT) 2>/dev/null" || true
        ssh $PREFERRED_HOST "kill \$(lsof -t -i:$PORT) 2>/dev/null" || true
    done
    for PORT in "${TCP_PORTS[@]}"; do
        ssh $PRIMARY_HOST "kill \$(lsof -t -i:$PORT) 2>/dev/null" || true
        ssh $PREFERRED_HOST "kill \$(lsof -t -i:$PORT) 2>/dev/null" || true
    done
    sleep 1
}

run_multiserver_test() {
    local BACKEND=$1
    local LOG_PREFIX="/tmp/multi_${BACKEND}"

    echo ""
    echo "============================================"
    echo "  MULTI-SERVER TEST: $BACKEND (3 primary, 3 preferred)"
    echo "============================================"

    cleanup_all

    # Start 3 preferred servers
    for i in 0 1 2; do
        local QPORT=${PORTS[$i]}
        local TPORT=${TCP_PORTS[$i]}
        local INST="server${i}"
        local PREF_ENV=""
        local PREF_ARGS=""

        case $BACKEND in
            tcp)
                PREF_ARGS="$PREFERRED_IP:$QPORT $TPORT"
                ;;
            http)
                local HTTP_PORT=$((9990 + $i))
                PREF_ENV="STATE_TRANSFER=http STATE_HTTP_PRIMARY=$PRIMARY_IP:$HTTP_PORT INSTANCE_ID=$INST"
                PREF_ARGS="$PREFERRED_IP:$QPORT"
                ;;
            redis_kv)
                PREF_ENV="STATE_TRANSFER=redis_kv REDIS_URL=127.0.0.1:6379 INSTANCE_ID=$INST"
                PREF_ARGS="$PREFERRED_IP:$QPORT"
                ;;
            redis_ps)
                PREF_ENV="STATE_TRANSFER=redis_ps REDIS_URL=127.0.0.1:6379 INSTANCE_ID=$INST"
                PREF_ARGS="$PREFERRED_IP:$QPORT"
                ;;
        esac

        ssh $PREFERRED_HOST "cd $NEQO_DIR && $PREF_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 20 ./target/release/preferred-server $PREF_ARGS 2>&1" > "${LOG_PREFIX}_pref${i}.log" &
        echo "  Started preferred-server[$i] on port $QPORT"
    done
    sleep 2

    # Start 3 primary servers
    for i in 0 1 2; do
        local QPORT=${PORTS[$i]}
        local TPORT=${TCP_PORTS[$i]}
        local INST="server${i}"
        local PRIM_ENV=""
        local PRIM_ARGS=""

        case $BACKEND in
            tcp)
                PRIM_ARGS="0.0.0.0:$QPORT $PREFERRED_IP:$QPORT $PREFERRED_IP:$TPORT"
                ;;
            http)
                local HTTP_PORT=$((9990 + $i))
                PRIM_ENV="STATE_TRANSFER=http STATE_HTTP_PORT=$HTTP_PORT INSTANCE_ID=$INST"
                PRIM_ARGS="0.0.0.0:$QPORT $PREFERRED_IP:$QPORT"
                ;;
            redis_kv)
                PRIM_ENV="STATE_TRANSFER=redis_kv REDIS_URL=$PREFERRED_IP:6379 INSTANCE_ID=$INST"
                PRIM_ARGS="0.0.0.0:$QPORT $PREFERRED_IP:$QPORT"
                ;;
            redis_ps)
                PRIM_ENV="STATE_TRANSFER=redis_ps REDIS_URL=$PREFERRED_IP:6379 INSTANCE_ID=$INST"
                PRIM_ARGS="0.0.0.0:$QPORT $PREFERRED_IP:$QPORT"
                ;;
        esac

        ssh $PRIMARY_HOST "cd $NEQO_DIR && $PRIM_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 20 ./target/release/primary-server $PRIM_ARGS 2>&1" > "${LOG_PREFIX}_prim${i}.log" &
        echo "  Started primary-server[$i] on port $QPORT"
    done
    sleep 3

    # Run 3 clients simultaneously
    echo "  Launching 3 clients..."
    for i in 0 1 2; do
        local QPORT=${PORTS[$i]}
        eval $CLIENT_LD RUST_LOG=info timeout 8 $CLIENT_BIN "https://$PRIMARY_IP:$QPORT/" > "${LOG_PREFIX}_client${i}.log" 2>&1 &
    done
    wait
    sleep 2

    # Check results
    echo ""
    echo "  Results:"
    local TOTAL_PASS=0
    for i in 0 1 2; do
        local PORT=${PORTS[$i]}
        local CONNECTED=$(grep -c "Connection established" "${LOG_PREFIX}_client${i}.log" 2>/dev/null || echo "0")
        local MIGRATED=$(grep -c "Migrate to" "${LOG_PREFIX}_client${i}.log" 2>/dev/null || echo "0")
        local STATE_SENT=$(grep -c "sent successfully" "${LOG_PREFIX}_prim${i}.log" 2>/dev/null || echo "0")
        local DECRYPTED=$(grep -c "DECRYPTED" "${LOG_PREFIX}_pref${i}.log" 2>/dev/null || echo "0")
        local SEND_TIME=$(grep "send_time=" "${LOG_PREFIX}_prim${i}.log" 2>/dev/null | head -1 | sed 's/.*send_time=//' | tr -d ' ')

        local STATUS="FAIL"
        if [ "$CONNECTED" -gt 0 ] && [ "$STATE_SENT" -gt 0 ]; then
            STATUS="PASS"
            TOTAL_PASS=$((TOTAL_PASS + 1))
        fi

        echo "    Server[$i] port=$PORT: connected=$CONNECTED migrated=$MIGRATED state_sent=$STATE_SENT decrypted=$DECRYPTED send_time=$SEND_TIME => $STATUS"
    done

    echo "  Overall: $TOTAL_PASS/3 passed"
    cleanup_all
}

echo "=== QUIC Multi-Server Migration Benchmark ==="
echo "  Setup: 3 primaries (opti7040), 3 preferred (homeserver2)"
echo ""

if [ "$BACKEND" = "all" ]; then
    for B in tcp http redis_kv redis_ps; do
        run_multiserver_test $B
    done
else
    run_multiserver_test $BACKEND
fi

echo ""
echo "=== Multi-Server Tests Complete ==="

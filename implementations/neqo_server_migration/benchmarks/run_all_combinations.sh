#!/bin/bash
# Run all 8 combinations (4 mechanisms x 2 timings) and generate a report.
#
# Usage: ./benchmarks/run_all_combinations.sh [runs_per_combo]
#        Default: 3 runs per combination

set -e

RUNS=${1:-3}
LOCAL_DIR="$HOME/code/quic/implementations/neqo_server_migration"
CLIENT_BIN="$LOCAL_DIR/target/release/neqo-client"
CLIENT_LD=$(find $LOCAL_DIR/target/release/build -path '*/dist/Release/lib' -type d | head -1)
RESULTS_DIR="$LOCAL_DIR/benchmarks/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NEQO_DIR="~/code/quic/implementations/neqo_server_migration"

PRIMARY_HOST="opti7040Mini"
PREFERRED_HOST="homeserver2"
PRIMARY_IP="141.217.168.152"
PREFERRED_IP="141.217.168.143"
REDIS_IP="141.217.168.200"

mkdir -p "$RESULTS_DIR"

CSV="$RESULTS_DIR/all_combinations_${TIMESTAMP}.csv"
REPORT="$RESULTS_DIR/report_${TIMESTAMP}.txt"

echo "mechanism,timing,run,send_latency_us,receive_latency_us,state_size,migration_success,path_challenges,path_responses,result" > "$CSV"

cleanup() {
    ssh $PRIMARY_HOST "kill -9 \$(lsof -t -i:4433 -i:9998) 2>/dev/null" 2>/dev/null || true
    ssh $PREFERRED_HOST "kill -9 \$(lsof -t -i:4433 -i:9999) 2>/dev/null" 2>/dev/null || true
    sleep 3
}

run_test() {
    local MECHANISM=$1
    local TIMING=$2
    local RUN_NUM=$3

    local PREF_ENV=""
    local PREF_ARGS=""
    local PRIM_ENV=""
    local PRIM_ARGS=""

    # Set timing env
    local TIMING_ENV=""
    if [ "$TIMING" = "lazy" ]; then
        TIMING_ENV="TRANSFER_TIMING=lazy"
    fi

    case $MECHANISM in
        tcp)
            PREF_ENV="$TIMING_ENV"
            PREF_ARGS="$PREFERRED_IP:4433 9999"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433 $PREFERRED_IP:9999"
            ;;
        http)
            PREF_ENV="STATE_TRANSFER=http STATE_HTTP_PRIMARY=$PRIMARY_IP:9998 $TIMING_ENV"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=http STATE_HTTP_PORT=9998"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
        redis_kv)
            PREF_ENV="STATE_TRANSFER=redis_kv REDIS_URL=$REDIS_IP:6379 $TIMING_ENV"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_kv REDIS_URL=$REDIS_IP:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
        redis_ps)
            PREF_ENV="STATE_TRANSFER=redis_ps REDIS_URL=$REDIS_IP:6379 $TIMING_ENV"
            PREF_ARGS="$PREFERRED_IP:4433"
            PRIM_ENV="STATE_TRANSFER=redis_ps REDIS_URL=$REDIS_IP:6379"
            PRIM_ARGS="0.0.0.0:4433 $PREFERRED_IP:4433"
            ;;
    esac

    # Start preferred server
    ssh $PREFERRED_HOST "cd $NEQO_DIR && $PREF_ENV LIBCLANG_PATH=/usr/lib/llvm-14/lib LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 30 ./target/release/preferred-server $PREF_ARGS 2>&1" > /tmp/bench_preferred.log 2>&1 &
    local PREF_PID=$!
    sleep 2

    # Start primary server
    ssh $PRIMARY_HOST "cd $NEQO_DIR && $PRIM_ENV LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1) timeout 20 ./target/release/primary-server $PRIM_ARGS 2>&1" > /tmp/bench_primary.log 2>&1 &
    local PRIM_PID=$!
    sleep 3

    # Run client
    LD_LIBRARY_PATH="$CLIENT_LD" RUST_LOG=info timeout 12 $CLIENT_BIN https://$PRIMARY_IP:4433/ > /tmp/bench_client.log 2>&1 || true
    sleep 2

    # Wait for servers to finish processing
    sleep 2

    # Extract metrics from primary log
    local SEND_TIME=$(grep "send_time=" /tmp/bench_primary.log 2>/dev/null | head -1 | grep -oP 'send_time=\K[0-9.]+[a-zµ]+' || echo "N/A")
    local STATE_SIZE=$(grep "state_size=" /tmp/bench_primary.log 2>/dev/null | head -1 | grep -oP 'state_size=\K[0-9]+' || echo "0")

    # Extract metrics from preferred log
    local RECV_TIME=$(grep "receive_time=" /tmp/bench_preferred.log 2>/dev/null | head -1 | grep -oP 'receive_time=\K[0-9.]+[a-zµ]+' || echo "N/A")
    local CHALLENGES=$(grep -c "PATH_CHALLENGE" /tmp/bench_preferred.log 2>/dev/null)
    CHALLENGES=${CHALLENGES:-0}
    local RESPONSES=$(grep -c "SENDING PATH_RESPONSE" /tmp/bench_preferred.log 2>/dev/null)
    RESPONSES=${RESPONSES:-0}
    local DECRYPTED=$(grep -c "DECRYPTED" /tmp/bench_preferred.log 2>/dev/null)
    DECRYPTED=${DECRYPTED:-0}

    # Determine result
    local RESULT="FAIL"
    if [ "${DECRYPTED:-0}" -gt 0 ] && [ "${RESPONSES:-0}" -gt 0 ]; then
        RESULT="PASS"
    elif [ "${DECRYPTED:-0}" -gt 0 ]; then
        RESULT="PARTIAL"
    fi

    # Client metrics
    local CLIENT_CONN=$(grep -c "Connection established" /tmp/bench_client.log 2>/dev/null || echo "0")
    local CLIENT_MIG=$(grep -c "Migrate to" /tmp/bench_client.log 2>/dev/null || echo "0")

    echo "$MECHANISM,$TIMING,$RUN_NUM,$SEND_TIME,$RECV_TIME,$STATE_SIZE,$DECRYPTED,$CHALLENGES,$RESPONSES,$RESULT" >> "$CSV"

    # Save individual logs
    cp /tmp/bench_primary.log "$RESULTS_DIR/log_${MECHANISM}_${TIMING}_run${RUN_NUM}_primary.log" 2>/dev/null || true
    cp /tmp/bench_preferred.log "$RESULTS_DIR/log_${MECHANISM}_${TIMING}_run${RUN_NUM}_preferred.log" 2>/dev/null || true
    cp /tmp/bench_client.log "$RESULTS_DIR/log_${MECHANISM}_${TIMING}_run${RUN_NUM}_client.log" 2>/dev/null || true

    # Cleanup
    kill $PREF_PID $PRIM_PID 2>/dev/null || true
    wait $PREF_PID $PRIM_PID 2>/dev/null || true
    cleanup

    printf "  %-12s %-10s Run %d/%d  send=%-12s  recv=%-12s  challenges=%d  responses=%d  %s\n" \
        "$MECHANISM" "$TIMING" "$RUN_NUM" "$RUNS" "$SEND_TIME" "$RECV_TIME" "$CHALLENGES" "$RESPONSES" "$RESULT"
}

echo "================================================================="
echo "  QUIC Server-Side Migration: Full Combination Test"
echo "================================================================="
echo ""
echo "  4 Machines:"
echo "    Client:     141.217.168.127 (optiplex7010)"
echo "    Primary:    141.217.168.152 (opti7040)"
echo "    Preferred:  141.217.168.143 (homeserver2)"
echo "    Redis:      141.217.168.200 (Proxmox VM)"
echo ""
echo "  Mechanisms: tcp, http, redis_kv, redis_ps"
echo "  Timings:    immediate, lazy"
echo "  Runs per combination: $RUNS"
echo "  Total tests: $((4 * 2 * RUNS))"
echo ""
echo "  CSV: $CSV"
echo "================================================================="
echo ""

# Run all 8 combinations
for MECHANISM in tcp http redis_kv redis_ps; do
    echo "--- $MECHANISM ---"
    for TIMING in immediate lazy; do
        for i in $(seq 1 $RUNS); do
            cleanup
            run_test "$MECHANISM" "$TIMING" "$i"
        done
    done
    echo ""
done

# Generate report
echo ""
echo "================================================================="
echo "  RESULTS SUMMARY"
echo "================================================================="
echo ""

{
echo "================================================================="
echo "  QUIC Server-Side Migration: Combination Test Report"
echo "  Generated: $(date)"
echo "================================================================="
echo ""
echo "Test Setup:"
echo "  Client:     141.217.168.127 (optiplex7010)"
echo "  Primary:    141.217.168.152 (opti7040)"
echo "  Preferred:  141.217.168.143 (homeserver2)"
echo "  Redis:      141.217.168.200 (Proxmox VM)"
echo "  Runs per combination: $RUNS"
echo ""
echo "Results:"
echo ""
printf "  %-14s %-12s %-8s %-14s %-10s %-12s\n" "Mechanism" "Timing" "Result" "Send Latency" "Responses" "Challenges"
printf "  %-14s %-12s %-8s %-14s %-10s %-12s\n" "---------" "------" "------" "------------" "---------" "----------"
} > "$REPORT"

for MECHANISM in tcp http redis_kv redis_ps; do
    for TIMING in immediate lazy; do
        PASS_COUNT=0
        TOTAL=0
        LAST_SEND=""
        LAST_RESP=""
        LAST_CHAL=""
        while IFS=, read -r m t r s rv sz d c rsp res; do
            if [ "$m" = "$MECHANISM" ] && [ "$t" = "$TIMING" ]; then
                TOTAL=$((TOTAL + 1))
                [ "$res" = "PASS" ] && PASS_COUNT=$((PASS_COUNT + 1))
                LAST_SEND="$s"
                LAST_RESP="$rsp"
                LAST_CHAL="$c"
            fi
        done < <(tail -n +2 "$CSV")

        if [ "$PASS_COUNT" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
            STATUS="PASS"
        elif [ "$PASS_COUNT" -gt 0 ]; then
            STATUS="PARTIAL"
        else
            STATUS="FAIL"
        fi

        LINE=$(printf "  %-14s %-12s %-8s %-14s %-10s %-12s" "$MECHANISM" "$TIMING" "$STATUS ($PASS_COUNT/$TOTAL)" "$LAST_SEND" "$LAST_RESP" "$LAST_CHAL")
        echo "$LINE"
        echo "$LINE" >> "$REPORT"
    done
done

echo "" | tee -a "$REPORT"
echo "CSV: $CSV" | tee -a "$REPORT"
echo "Report: $REPORT" | tee -a "$REPORT"
echo "Logs: $RESULTS_DIR/log_*" | tee -a "$REPORT"

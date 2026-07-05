#!/bin/bash
# =============================================================================
# WebSeed Migration PoC - Test Script
# =============================================================================
# Tests BitTorrent WebSeed migration: two HTTP/3 servers host the same large
# file, and the primary migrates the connection to the preferred server.
#
# Testbed:
#   Client:    141.217.168.127 (this machine)
#   Primary:   141.217.168.152 (opti7040)
#   Preferred: 141.217.168.143 (homeserver2)
# =============================================================================

set -e

FILE_SIZE_MB=${1:-100}
TEST_FILE="/tmp/test_${FILE_SIZE_MB}mb.bin"
DOWNLOADED_FILE="/tmp/downloaded_webseed.bin"
PRIMARY="141.217.168.152"
PREFERRED="141.217.168.143"
PORT="4433"

echo "=== WebSeed Migration PoC Test ==="
echo

# Step 1: Create test file
echo "[Step 1] Creating ${FILE_SIZE_MB}MB test file..."
if [ -f "$TEST_FILE" ]; then
    echo "  File already exists: $TEST_FILE"
else
    dd if=/dev/urandom of="$TEST_FILE" bs=1M count="$FILE_SIZE_MB" status=progress 2>&1
    echo "  Created: $TEST_FILE"
fi

# Step 2: Compute SHA-256
echo
echo "[Step 2] Computing SHA-256..."
EXPECTED_HASH=$(sha256sum "$TEST_FILE" | awk '{print $1}')
echo "  SHA-256: $EXPECTED_HASH"
echo "  Size:    $(stat --printf='%s' "$TEST_FILE") bytes"

# Step 3: Copy file to both servers
echo
echo "[Step 3] Copying test file to servers..."
echo "  Copying to primary ($PRIMARY)..."
scp "$TEST_FILE" "opti7040Mini:$TEST_FILE" 2>/dev/null && echo "    Done." || echo "    FAILED (copy manually)"
echo "  Copying to preferred ($PREFERRED)..."
scp "$TEST_FILE" "homeserver2:$TEST_FILE" 2>/dev/null && echo "    Done." || echo "    FAILED (copy manually)"

# Step 4: Instructions for starting servers
echo
echo "[Step 4] Start servers (in separate terminals):"
echo
echo "  On homeserver2 ($PREFERRED):"
echo "    cd ~/code/quic/implementations/neqo_server_migration"
echo "    export LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)"
echo "    ./target/release/preferred-server $PREFERRED:$PORT 9999"
echo
echo "  On opti7040 ($PRIMARY):"
echo "    cd ~/code/quic/implementations/neqo_server_migration"
echo "    export LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)"
echo "    ./target/release/webseed-primary 0.0.0.0:$PORT $PREFERRED:$PORT $TEST_FILE $PREFERRED:9999"
echo
read -p "Press Enter when both servers are running..."

# Step 5: Download the file
echo
echo "[Step 5] Downloading file via QUIC..."
rm -f "$DOWNLOADED_FILE"

# Try neqo-client first
NEQO_CLIENT="./implementations/neqo_server_migration/target/release/neqo-client"
if [ -x "$NEQO_CLIENT" ]; then
    echo "  Using neqo-client..."
    cd /home/anik/code/quic/implementations/neqo_server_migration
    export LD_LIBRARY_PATH=$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)
    ./target/release/neqo-client "https://$PRIMARY:$PORT/" --output "$DOWNLOADED_FILE" 2>&1 || true
    cd /home/anik/code/quic
else
    echo "  neqo-client not found. Try curl with HTTP/3:"
    echo "    curl --http3-only -k -o $DOWNLOADED_FILE https://$PRIMARY:$PORT/"
    read -p "Press Enter after download completes..."
fi

# Step 6: Verify integrity
echo
echo "[Step 6] Verifying file integrity..."
if [ -f "$DOWNLOADED_FILE" ]; then
    ACTUAL_HASH=$(sha256sum "$DOWNLOADED_FILE" | awk '{print $1}')
    ACTUAL_SIZE=$(stat --printf='%s' "$DOWNLOADED_FILE")
    echo "  Expected SHA-256: $EXPECTED_HASH"
    echo "  Actual SHA-256:   $ACTUAL_HASH"
    echo "  Expected size:    $(stat --printf='%s' "$TEST_FILE") bytes"
    echo "  Actual size:      $ACTUAL_SIZE bytes"
    echo
    if [ "$EXPECTED_HASH" = "$ACTUAL_HASH" ]; then
        echo "  RESULT: PASS - File integrity verified after migration!"
    else
        echo "  RESULT: FAIL - SHA-256 mismatch! Migration may have corrupted data."
    fi
else
    echo "  RESULT: SKIP - Downloaded file not found at $DOWNLOADED_FILE"
fi

# Step 7: Verify migration happened (check traffic)
echo
echo "[Step 7] To verify migration occurred, run:"
echo "  sudo tshark -i any -f 'udp port $PORT' -T fields -e ip.dst -e udp.length -c 30"
echo "  You should see packets going to $PREFERRED instead of $PRIMARY"
echo
echo "=== Test Complete ==="

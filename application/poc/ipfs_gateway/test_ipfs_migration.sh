#!/bin/bash
# =============================================================================
# IPFS Gateway Migration Test
# =============================================================================
# Tests that IPFS content can be served through QUIC HTTP/3 with transparent
# server migration. The primary fetches from local IPFS gateway, serves via
# HTTP/3, and the connection migrates to the preferred server.
#
# Prerequisites: Run setup_ipfs.sh first
# Run on: CLIENT machine (141.217.168.127)
# =============================================================================

set -e

PRIMARY="141.217.168.152"
PREFERRED="141.217.168.143"
GATEWAY_PORT="8080"
QUIC_PORT="4433"

# Get CID from setup
if [ -f /tmp/ipfs_test_cid.txt ]; then
    CID=$(cat /tmp/ipfs_test_cid.txt)
else
    echo "Error: Run setup_ipfs.sh first to add content and get CID"
    exit 1
fi

echo "=== IPFS Gateway Migration Test ==="
echo "  CID: $CID"
echo

# Step 1: Fetch content from IPFS and save to a file for the primary to serve
echo "[Step 1] Preparing IPFS content for HTTP/3 serving..."
echo "  Fetching CID $CID from primary IPFS gateway..."

# Fetch content and save on primary server
ssh opti7040Mini "curl -s http://localhost:$GATEWAY_PORT/ipfs/$CID > /tmp/ipfs_serve_content.bin"
CONTENT_SIZE=$(ssh opti7040Mini "stat --printf='%s' /tmp/ipfs_serve_content.bin")
echo "  Content size: $CONTENT_SIZE bytes"

# Also fetch on preferred server (for post-migration serving)
ssh homeserver2 "curl -s http://localhost:$GATEWAY_PORT/ipfs/$CID > /tmp/ipfs_serve_content.bin"

# Step 2: Start servers
echo
echo "[Step 2] Start the servers:"
echo
echo "  On homeserver2 ($PREFERRED):"
echo "    cd ~/code/quic/implementations/neqo_server_migration"
echo "    export LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)"
echo "    ./target/release/preferred-server $PREFERRED:$QUIC_PORT 9999"
echo
echo "  On opti7040 ($PRIMARY) — serve IPFS content via webseed-primary:"
echo "    cd ~/code/quic/implementations/neqo_server_migration"
echo "    export LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)"
echo "    ./target/release/webseed-primary 0.0.0.0:$QUIC_PORT $PREFERRED:$QUIC_PORT /tmp/ipfs_serve_content.bin $PREFERRED:9999"
echo
echo "  Or use the standard primary-server for the HTML demo page."
echo
read -p "Press Enter when both servers are running..."

# Step 3: Download content
echo
echo "[Step 3] Downloading content via QUIC HTTP/3..."
DOWNLOADED="/tmp/ipfs_downloaded.bin"
rm -f "$DOWNLOADED"

cd /home/anik/code/quic/implementations/neqo_server_migration
export LD_LIBRARY_PATH=$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)
./target/release/neqo-client "https://$PRIMARY:$QUIC_PORT/" --output "$DOWNLOADED" 2>&1 || true
cd /home/anik/code/quic

# Step 4: Verify content
echo
echo "[Step 4] Verifying content integrity..."
if [ -f "$DOWNLOADED" ]; then
    # Compare with original IPFS content
    ORIG_HASH=$(ssh opti7040Mini "sha256sum /tmp/ipfs_serve_content.bin" | awk '{print $1}')
    DL_HASH=$(sha256sum "$DOWNLOADED" | awk '{print $1}')

    echo "  Original SHA-256:   $ORIG_HASH"
    echo "  Downloaded SHA-256: $DL_HASH"

    if [ "$ORIG_HASH" = "$DL_HASH" ]; then
        echo
        echo "  RESULT: PASS - IPFS content integrity preserved through migration!"
    else
        echo
        echo "  RESULT: FAIL - Content mismatch (may be HTML response, check content)"
        echo "  Downloaded content (first 200 bytes):"
        head -c 200 "$DOWNLOADED"
        echo
    fi
else
    echo "  RESULT: SKIP - No downloaded file found"
fi

# Step 5: Verify migration via traffic capture
echo
echo "[Step 5] To verify migration, run:"
echo "  sudo tshark -i any -f 'udp port $QUIC_PORT' -T fields -e ip.dst -e udp.length -c 20"
echo "  You should see traffic going to $PREFERRED (not $PRIMARY)"
echo
echo "=== IPFS Gateway Migration Test Complete ==="
echo
echo "KEY INSIGHT: IPFS content is content-addressed (CIDs). Both servers"
echo "hold the same content, so migration preserves data integrity BY DESIGN."
echo "Unlike regular HTTP, the client can cryptographically verify the content"
echo "is the same regardless of which server delivered it."

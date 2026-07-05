#!/bin/bash
# =============================================================================
# IPFS Gateway Setup for Migration PoC
# =============================================================================
# Sets up IPFS (Kubo) on two server machines so both can serve the same content.
# The primary server serves IPFS content via HTTP/3 (through our Neqo server),
# and the preferred server takes over after migration.
#
# Machines:
#   Primary:   opti7040 (141.217.168.152) — SSH alias: opti7040Mini
#   Preferred: homeserver2 (141.217.168.143) — SSH alias: homeserver2
#
# Run on: CLIENT machine (141.217.168.127) — orchestrates remote setup
# =============================================================================

set -e

KUBO_VERSION="v0.28.0"
KUBO_URL="https://dist.ipfs.tech/kubo/${KUBO_VERSION}/kubo_${KUBO_VERSION}_linux-amd64.tar.gz"
PRIMARY_SSH="opti7040Mini"
PREFERRED_SSH="homeserver2"
TEST_FILE="/tmp/ipfs_test_content.txt"
GATEWAY_PORT="8080"

echo "=== IPFS Gateway Migration PoC Setup ==="
echo "  Kubo version: $KUBO_VERSION"
echo "  Primary:      $PRIMARY_SSH (141.217.168.152)"
echo "  Preferred:    $PREFERRED_SSH (141.217.168.143)"
echo

# Create test content
echo "[Step 1] Creating test content..."
cat > "$TEST_FILE" << 'EOF'
QUIC Server Migration - IPFS Gateway PoC

This file is served via IPFS through a QUIC HTTP/3 gateway.
The connection was transparently migrated from the primary server
to the preferred server using QUIC's preferred_address mechanism.

The fact that you can read this proves:
1. IPFS content is available on both gateway nodes
2. QUIC migration preserved the HTTP/3 session
3. Content integrity is guaranteed by IPFS's content addressing (CID)

Timestamp: GENERATED_AT
EOF
sed -i "s/GENERATED_AT/$(date -u)/" "$TEST_FILE"
echo "  Created: $TEST_FILE"

# Function to setup IPFS on a remote machine
setup_remote_ipfs() {
    local SSH_HOST=$1
    local HOST_NAME=$2

    echo
    echo "[Setup] Installing IPFS on $HOST_NAME ($SSH_HOST)..."

    ssh "$SSH_HOST" bash << REMOTE_EOF
set -e

# Check if ipfs is already installed
if command -v ipfs &>/dev/null; then
    echo "  IPFS already installed: \$(ipfs --version)"
else
    echo "  Downloading Kubo $KUBO_VERSION..."
    cd /tmp
    wget -q "$KUBO_URL" -O kubo.tar.gz
    tar xzf kubo.tar.gz
    cd kubo
    sudo ./install.sh
    rm -rf /tmp/kubo /tmp/kubo.tar.gz
    echo "  Installed: \$(ipfs --version)"
fi

# Initialize IPFS repo if needed
if [ ! -d ~/.ipfs ]; then
    echo "  Initializing IPFS repo..."
    ipfs init --profile server
else
    echo "  IPFS repo already exists"
fi

# Configure gateway port
ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/$GATEWAY_PORT 2>/dev/null || true

# Start IPFS daemon if not running
if ! pgrep -x ipfs > /dev/null; then
    echo "  Starting IPFS daemon..."
    nohup ipfs daemon --enable-gc > /tmp/ipfs.log 2>&1 &
    sleep 3
    echo "  IPFS daemon started (PID: \$(pgrep -x ipfs))"
else
    echo "  IPFS daemon already running (PID: \$(pgrep -x ipfs))"
fi

echo "  Gateway: http://\$(hostname -I | awk '{print \$1}'):$GATEWAY_PORT"
echo "  Peer ID: \$(ipfs id -f '<id>')"
REMOTE_EOF
}

# Step 2: Setup IPFS on both servers
echo "[Step 2] Setting up IPFS on primary and preferred servers..."
setup_remote_ipfs "$PRIMARY_SSH" "Primary"
setup_remote_ipfs "$PREFERRED_SSH" "Preferred"

# Step 3: Add test content to primary
echo
echo "[Step 3] Adding test content to primary IPFS node..."
scp "$TEST_FILE" "$PRIMARY_SSH:/tmp/ipfs_test_content.txt"
CID=$(ssh "$PRIMARY_SSH" "ipfs add -q /tmp/ipfs_test_content.txt")
echo "  Content CID: $CID"

# Step 4: Pin content on preferred (fetch from primary via IPFS network)
echo
echo "[Step 4] Pinning content on preferred server..."
# Connect preferred to primary first
PRIMARY_PEER_ID=$(ssh "$PRIMARY_SSH" "ipfs id -f '<id>'")
ssh "$PREFERRED_SSH" "ipfs swarm connect /ip4/141.217.168.152/tcp/4001/p2p/$PRIMARY_PEER_ID" 2>/dev/null || true
ssh "$PREFERRED_SSH" "ipfs pin add $CID" 2>/dev/null || {
    # If IPFS networking doesn't work, just copy the file directly
    echo "  Direct IPFS pin failed, copying file and adding locally..."
    scp "$TEST_FILE" "$PREFERRED_SSH:/tmp/ipfs_test_content.txt"
    CID2=$(ssh "$PREFERRED_SSH" "ipfs add -q /tmp/ipfs_test_content.txt")
    echo "  Preferred CID: $CID2 (should match $CID)"
}

# Step 5: Verify gateways
echo
echo "[Step 5] Verifying gateways serve the same content..."
echo "  Primary gateway:"
curl -s "http://141.217.168.152:$GATEWAY_PORT/ipfs/$CID" | head -3
echo
echo "  Preferred gateway:"
curl -s "http://141.217.168.143:$GATEWAY_PORT/ipfs/$CID" | head -3
echo

# Step 6: Save CID for test script
echo "$CID" > /tmp/ipfs_test_cid.txt
echo
echo "=== Setup Complete ==="
echo "  CID: $CID"
echo "  Saved to: /tmp/ipfs_test_cid.txt"
echo
echo "  Primary gateway:   http://141.217.168.152:$GATEWAY_PORT/ipfs/$CID"
echo "  Preferred gateway:  http://141.217.168.143:$GATEWAY_PORT/ipfs/$CID"
echo
echo "Next: Run ./test_ipfs_migration.sh to test migration with IPFS content"

#!/bin/bash
# =============================================================================
# Teardown IPFS Gateway Setup
# =============================================================================

set -e

echo "=== Teardown IPFS Gateway ==="

for HOST in opti7040Mini homeserver2; do
    echo "[Stopping IPFS on $HOST]"
    ssh "$HOST" "pkill ipfs 2>/dev/null || true; echo '  Stopped.'" 2>/dev/null || echo "  Could not reach $HOST"
done

rm -f /tmp/ipfs_test_cid.txt /tmp/ipfs_test_content.txt /tmp/ipfs_downloaded.bin

echo
echo "=== Teardown Complete ==="
echo "Note: IPFS repos (~/.ipfs) are preserved. Remove manually if needed:"
echo "  ssh opti7040Mini 'rm -rf ~/.ipfs'"
echo "  ssh homeserver2 'rm -rf ~/.ipfs'"

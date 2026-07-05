#!/bin/bash
# =============================================================================
# DNS Simulation Setup (dnsmasq)
# =============================================================================
# Sets up a local DNS server that resolves a test domain to our primary server.
# This simulates GeoDNS returning the "nearest" server.
#
# Run on: CLIENT machine (141.217.168.127)
# Requires: root/sudo
# =============================================================================

set -e

PRIMARY="141.217.168.152"
DOMAIN="quic-migration.test"

echo "=== DNS Simulation Setup (dnsmasq) ==="
echo "  Domain:  $DOMAIN -> $PRIMARY"
echo

# Step 1: Install dnsmasq if not present
if ! command -v dnsmasq &>/dev/null; then
    echo "[Step 1] Installing dnsmasq..."
    sudo apt-get update -qq && sudo apt-get install -y -qq dnsmasq
else
    echo "[Step 1] dnsmasq already installed"
fi

# Step 2: Configure dnsmasq
CONF="/etc/dnsmasq.d/quic-migration.conf"
echo "[Step 2] Creating dnsmasq config at $CONF..."
sudo tee "$CONF" > /dev/null << EOF
# QUIC migration test - resolve test domain to primary server
address=/$DOMAIN/$PRIMARY
# Don't forward queries for .test domains
server=/$DOMAIN/

# Listen only on localhost
listen-address=127.0.0.1
bind-interfaces
EOF

# Step 3: Restart dnsmasq
echo "[Step 3] Restarting dnsmasq..."
sudo systemctl restart dnsmasq 2>/dev/null || sudo service dnsmasq restart 2>/dev/null || {
    echo "  Starting dnsmasq manually..."
    sudo dnsmasq --conf-file="$CONF" --no-daemon &
}

# Step 4: Verify
echo "[Step 4] Verifying DNS resolution..."
RESULT=$(dig +short @127.0.0.1 $DOMAIN 2>/dev/null || nslookup $DOMAIN 127.0.0.1 2>/dev/null | grep Address | tail -1 | awk '{print $2}')
if [ "$RESULT" = "$PRIMARY" ]; then
    echo "  SUCCESS: $DOMAIN -> $RESULT"
else
    echo "  WARNING: Expected $PRIMARY, got '$RESULT'"
    echo "  You may need to add 'nameserver 127.0.0.1' to /etc/resolv.conf"
fi

echo
echo "=== DNS Setup Complete ==="
echo "  $DOMAIN resolves to $PRIMARY (simulated GeoDNS)"
echo
echo "To use with Firefox, you'd need to set the server cert CN to match"
echo "the domain, or use the IP directly with setup_anycast_sim.sh"

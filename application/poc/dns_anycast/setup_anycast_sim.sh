#!/bin/bash
# =============================================================================
# DNS + Anycast Simulation Setup
# =============================================================================
# Simulates anycast routing using iptables DNAT on the client machine.
# Creates a Virtual IP (VIP) that routes traffic to the primary server,
# which then migrates the connection to the preferred server via QUIC.
#
# After migration, the connection is on a direct unicast path to the
# preferred server — immune to anycast route changes.
#
# Run on: CLIENT machine (141.217.168.127)
# Requires: root/sudo
# =============================================================================

set -e

VIP="10.99.99.1"
VIP_IFACE="lo"
PRIMARY="141.217.168.152"
PREFERRED="141.217.168.143"
QUIC_PORT="4433"

echo "=== Anycast Simulation Setup ==="
echo "  VIP:        $VIP (simulated anycast address)"
echo "  Primary:    $PRIMARY (simulated nearest PoP)"
echo "  Preferred:  $PREFERRED (backend after migration)"
echo

# Step 1: Add VIP to loopback interface
echo "[Step 1] Adding VIP $VIP to $VIP_IFACE..."
sudo ip addr add ${VIP}/32 dev $VIP_IFACE 2>/dev/null || echo "  VIP already exists"

# Step 2: Add iptables DNAT rule — redirect VIP traffic to primary
echo "[Step 2] Adding iptables DNAT: $VIP:$QUIC_PORT -> $PRIMARY:$QUIC_PORT (UDP)..."
sudo iptables -t nat -A OUTPUT -d $VIP -p udp --dport $QUIC_PORT \
    -j DNAT --to-destination $PRIMARY:$QUIC_PORT 2>/dev/null || true

# Step 3: Also add for TCP (for Alt-Svc bootstrap)
echo "[Step 3] Adding iptables DNAT: $VIP:$QUIC_PORT -> $PRIMARY:$QUIC_PORT (TCP)..."
sudo iptables -t nat -A OUTPUT -d $VIP -p tcp --dport $QUIC_PORT \
    -j DNAT --to-destination $PRIMARY:$QUIC_PORT 2>/dev/null || true

echo
echo "=== Setup Complete ==="
echo
echo "Now you can connect to the VIP:"
echo "  Firefox:      https://$VIP:$QUIC_PORT/"
echo "  neqo-client:  neqo-client https://$VIP:$QUIC_PORT/"
echo
echo "Traffic flow:"
echo "  1. Client -> $VIP:$QUIC_PORT (iptables rewrites to $PRIMARY:$QUIC_PORT)"
echo "  2. Primary handles handshake, advertises preferred_address=$PREFERRED:$QUIC_PORT"
echo "  3. Client migrates directly to $PREFERRED:$QUIC_PORT (unicast, no VIP)"
echo "  4. Connection is now immune to anycast route changes!"
echo
echo "To simulate a route flap, run: ./test_route_flap.sh"
echo "To clean up, run: ./teardown.sh"

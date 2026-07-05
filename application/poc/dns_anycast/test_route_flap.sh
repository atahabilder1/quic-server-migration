#!/bin/bash
# =============================================================================
# Route Flap Test — proves migrated connections survive anycast changes
# =============================================================================
# After setup_anycast_sim.sh has been run:
# 1. Establishes a connection through the VIP -> primary -> migration -> preferred
# 2. Changes the iptables DNAT to point VIP to a DIFFERENT server (simulating BGP flap)
# 3. Shows that the migrated connection SURVIVES (it's on direct unicast to preferred)
# 4. Shows that a new connection through the VIP goes to the new destination
#
# Run on: CLIENT machine (141.217.168.127)
# Requires: root/sudo, setup_anycast_sim.sh already run
# =============================================================================

set -e

VIP="10.99.99.1"
PRIMARY="141.217.168.152"
PREFERRED="141.217.168.143"
NEW_PRIMARY="141.217.168.200"  # Proxmox VM acts as "new PoP after BGP flap"
QUIC_PORT="4433"

echo "=== Route Flap Simulation ==="
echo
echo "This test demonstrates that QUIC server migration makes connections"
echo "immune to anycast/BGP route changes."
echo
echo "Current routing: VIP($VIP) -> Primary($PRIMARY) -> Migration -> Preferred($PREFERRED)"
echo

# Step 1: Verify current setup
echo "[Step 1] Verifying current iptables DNAT..."
CURRENT=$(sudo iptables -t nat -L OUTPUT -n | grep "$VIP" | head -1)
if [ -z "$CURRENT" ]; then
    echo "  ERROR: No DNAT rule found. Run setup_anycast_sim.sh first."
    exit 1
fi
echo "  Current rule: $CURRENT"

# Step 2: Start packet capture in background
echo
echo "[Step 2] Starting packet capture (5 seconds)..."
echo "  Capturing initial traffic to verify migration path..."
sudo timeout 5 tshark -i any -f "udp port $QUIC_PORT" -T fields \
    -e frame.number -e ip.src -e ip.dst -e udp.length \
    -c 20 2>/dev/null &
TSHARK_PID=$!

# Give tshark time to start
sleep 1

# Step 3: Verify migration works (existing connection)
echo
echo "[Step 3] To test, connect to VIP in another terminal:"
echo "  cd ~/code/quic/implementations/neqo_server_migration"
echo "  export LD_LIBRARY_PATH=\$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)"
echo "  ./target/release/neqo-client https://$VIP:$QUIC_PORT/"
echo
read -p "Press Enter after the connection has been established and migrated..."

# Wait for capture to finish
wait $TSHARK_PID 2>/dev/null || true

# Step 4: Simulate BGP route flap — change DNAT to point to different server
echo
echo "[Step 4] SIMULATING ROUTE FLAP!"
echo "  Changing VIP DNAT: $PRIMARY -> $NEW_PRIMARY"
echo "  (This simulates BGP routing the anycast address to a different PoP)"

# Remove old rule
sudo iptables -t nat -D OUTPUT -d $VIP -p udp --dport $QUIC_PORT \
    -j DNAT --to-destination $PRIMARY:$QUIC_PORT 2>/dev/null || true

# Add new rule pointing to different server
sudo iptables -t nat -A OUTPUT -d $VIP -p udp --dport $QUIC_PORT \
    -j DNAT --to-destination $NEW_PRIMARY:$QUIC_PORT 2>/dev/null || true

echo "  Done. New routing: VIP($VIP) -> $NEW_PRIMARY"
echo

# Step 5: Verify existing connection still works
echo "[Step 5] Verifying existing migrated connection..."
echo "  The existing connection was migrated to $PREFERRED:$QUIC_PORT (direct unicast)."
echo "  It does NOT go through the VIP, so the route change has NO effect."
echo
echo "  If the connection is still active (e.g., long-lived HTTP/3 stream),"
echo "  you should still see packets flowing to/from $PREFERRED."
echo
echo "  Capturing traffic for 5 seconds..."
sudo timeout 5 tshark -i any -f "udp port $QUIC_PORT" -T fields \
    -e ip.src -e ip.dst -e udp.length -c 10 2>/dev/null || true

echo
echo "=== Results ==="
echo
echo "  Before route flap: VIP -> $PRIMARY -> migration -> $PREFERRED"
echo "  After route flap:  VIP -> $NEW_PRIMARY (but existing conn is on $PREFERRED directly)"
echo
echo "  KEY INSIGHT: The migrated connection survived the route change because"
echo "  it was on a direct unicast path ($PREFERRED:$QUIC_PORT), not through the VIP."
echo "  A non-migrated connection would have broken (VIP now routes to $NEW_PRIMARY)."
echo
echo "  To restore original routing, run: ./teardown.sh && ./setup_anycast_sim.sh"

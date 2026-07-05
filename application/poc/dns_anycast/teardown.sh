#!/bin/bash
# =============================================================================
# Teardown DNS + Anycast Simulation
# =============================================================================

set -e

VIP="10.99.99.1"
PRIMARY="141.217.168.152"
NEW_PRIMARY="141.217.168.200"
QUIC_PORT="4433"

echo "=== Teardown DNS + Anycast Simulation ==="

# Remove iptables DNAT rules
echo "[1] Removing iptables DNAT rules..."
sudo iptables -t nat -D OUTPUT -d $VIP -p udp --dport $QUIC_PORT \
    -j DNAT --to-destination $PRIMARY:$QUIC_PORT 2>/dev/null || true
sudo iptables -t nat -D OUTPUT -d $VIP -p tcp --dport $QUIC_PORT \
    -j DNAT --to-destination $PRIMARY:$QUIC_PORT 2>/dev/null || true
sudo iptables -t nat -D OUTPUT -d $VIP -p udp --dport $QUIC_PORT \
    -j DNAT --to-destination $NEW_PRIMARY:$QUIC_PORT 2>/dev/null || true
echo "  Done."

# Remove VIP
echo "[2] Removing VIP $VIP..."
sudo ip addr del ${VIP}/32 dev lo 2>/dev/null || echo "  VIP already removed"

# Remove dnsmasq config
echo "[3] Removing dnsmasq config..."
sudo rm -f /etc/dnsmasq.d/quic-migration.conf
sudo systemctl restart dnsmasq 2>/dev/null || true

echo
echo "=== Teardown Complete ==="

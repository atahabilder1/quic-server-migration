#!/usr/bin/env bash
# Setup script for the CLIENT machine (this PC / 141.217.168.127)
# Builds neqo-client and optionally exports certs for Firefox.
#
# Usage: ./scripts/setup-client.sh [PRIMARY_IP]
#   PRIMARY_IP - IP of the primary server (default: 141.217.168.152)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NEQO_DIR="$REPO_DIR/implementations/neqo_server_migration"

PRIMARY_IP="${1:-141.217.168.152}"

echo "=== QUIC Migration: Client Setup ==="
echo "Repo:        $REPO_DIR"
echo "Primary IP:  $PRIMARY_IP"
echo ""

# --- Build neqo-client ---
echo "[1/3] Building neqo-client..."
cd "$NEQO_DIR"
PKG_CONFIG_PATH=/nonexistent PKG_CONFIG_LIBDIR=/nonexistent cargo build --release -p neqo-bin --bin neqo-client
echo "Build complete."

# --- Export cert for Firefox ---
echo "[2/3] Exporting certificate for Firefox..."
NSS_BIN_DIR=$(find target/release/build -path '*/dist/Release/bin' -type d | head -1)
NSS_LIB_DIR=$(find target/release/build -path '*/dist/Release/lib' -type d | head -1)

if [ -n "$NSS_BIN_DIR" ] && [ -n "$NSS_LIB_DIR" ]; then
    export LD_LIBRARY_PATH="$NSS_LIB_DIR"
    DB_DIR="$NEQO_DIR/neqo-bin/tests/db"

    if [ -d "$DB_DIR" ]; then
        "$NSS_BIN_DIR/certutil" -L -d "sql:$DB_DIR" -n "MyCert" -a > /tmp/quic_cert.pem 2>/dev/null && \
            echo "Certificate exported to /tmp/quic_cert.pem" || \
            echo "Warning: Could not export cert. You may need to do this manually."
    else
        echo "Warning: NSS DB not found at $DB_DIR"
    fi
else
    echo "Warning: NSS tools not found in build output."
fi

# --- Install alias ---
echo "[3/3] Installing bash aliases..."

ALIAS_BLOCK="
# === QUIC Migration - Client (auto-generated) ===
alias quic-client='cd $NEQO_DIR && LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/neqo-client https://${PRIMARY_IP}:4433/'
# === End QUIC Migration ==="

ALIAS_FILE="$HOME/.bash_aliases"
if [ -f "$ALIAS_FILE" ]; then
    sed -i '/^# === QUIC Migration - Client/,/^# === End QUIC Migration/d' "$ALIAS_FILE"
fi
echo "$ALIAS_BLOCK" >> "$ALIAS_FILE"

echo ""
echo "Done!"
echo ""
echo "Quick start:"
echo "  quic-client                    # test with neqo-client"
echo ""
echo "Firefox setup (about:config):"
echo "  network.http.http3.enabled = true"
echo "  network.http.http3.alt-svc-mapping-for-testing = ${PRIMARY_IP}:4433;h3=\":4433\""
echo "  network.http.http3.disable_when_third_party_roots_found = false"
echo ""
echo "Then import /tmp/quic_cert.pem into Firefox:"
echo "  Settings > Privacy & Security > Certificates > View Certificates > Authorities > Import"

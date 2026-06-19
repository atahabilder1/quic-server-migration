#!/usr/bin/env bash
# Setup script for the PRIMARY server (opti7040 / 141.217.168.152)
# Builds the primary_server binary and installs bash aliases.
#
# Usage: ./scripts/setup-primary.sh [PREFERRED_IP] [REDIS_IP]
#   PREFERRED_IP  - IP of the preferred server (default: 141.217.168.143)
#   REDIS_IP      - IP of the Redis server (default: 141.217.168.200)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NEQO_DIR="$REPO_DIR/implementations/neqo_server_migration"

PREFERRED_IP="${1:-141.217.168.143}"
REDIS_IP="${2:-141.217.168.200}"

echo "=== QUIC Migration: Primary Server Setup ==="
echo "Repo:          $REPO_DIR"
echo "Preferred IP:  $PREFERRED_IP"
echo "Redis IP:      $REDIS_IP"
echo ""

# --- Build ---
echo "[1/2] Building primary_server..."
cd "$NEQO_DIR"
PKG_CONFIG_PATH=/nonexistent PKG_CONFIG_LIBDIR=/nonexistent cargo build --release -p migration-test --bin primary-server
echo "Build complete."

# --- Install aliases ---
echo "[2/2] Installing bash aliases..."

ALIAS_BLOCK="
# === QUIC Migration - Primary Server (auto-generated) ===
alias primary-up='cd $NEQO_DIR && LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/primary-server 0.0.0.0:4433 ${PREFERRED_IP}:4433 ${PREFERRED_IP}:9999'
alias primary-down='kill \$(lsof -t -i:4433) 2>/dev/null && echo \"Primary server stopped\" || echo \"No process on port 4433\"'
alias bootstrap-up='cd $REPO_DIR && python3 alt_svc_server.py'
alias bootstrap-down='kill \$(lsof -t -i tcp:4433) 2>/dev/null && echo \"Bootstrap server stopped\" || echo \"No TCP process on port 4433\"'
alias primary-up-redis='cd $NEQO_DIR && STATE_TRANSFER=redis_kv REDIS_URL=redis://${REDIS_IP}:6379 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/primary-server 0.0.0.0:4433 ${PREFERRED_IP}:4433'
alias primary-up-redis-ps='cd $NEQO_DIR && STATE_TRANSFER=redis_ps REDIS_URL=redis://${REDIS_IP}:6379 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/primary-server 0.0.0.0:4433 ${PREFERRED_IP}:4433'
alias primary-up-http='cd $NEQO_DIR && STATE_TRANSFER=http STATE_HTTP_PORT=9998 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/primary-server 0.0.0.0:4433 ${PREFERRED_IP}:4433'
# === End QUIC Migration ==="

# Remove old block if present, then append
ALIAS_FILE="$HOME/.bash_aliases"
if [ -f "$ALIAS_FILE" ]; then
    sed -i '/^# === QUIC Migration - Primary Server/,/^# === End QUIC Migration/d' "$ALIAS_FILE"
fi
echo "$ALIAS_BLOCK" >> "$ALIAS_FILE"

echo ""
echo "Done! Aliases installed in ~/.bash_aliases"
echo "Run 'source ~/.bash_aliases' or open a new terminal."
echo ""
echo "Quick start:"
echo "  1. bootstrap-up     (terminal 1 - TCP HTTPS for Firefox)"
echo "  2. primary-up       (terminal 2 - QUIC primary server)"

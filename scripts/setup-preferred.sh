#!/usr/bin/env bash
# Setup script for the PREFERRED server (homeserver2 / 141.217.168.143)
# Builds the preferred_server binary and installs bash aliases.
#
# Usage: ./scripts/setup-preferred.sh [PREFERRED_IP] [PRIMARY_IP] [REDIS_IP]
#   PREFERRED_IP  - This machine's IP (default: 141.217.168.143)
#   PRIMARY_IP    - IP of the primary server (default: 141.217.168.152)
#   REDIS_IP      - IP of the Redis server (default: 141.217.168.200)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NEQO_DIR="$REPO_DIR/implementations/neqo_server_migration"

PREFERRED_IP="${1:-141.217.168.143}"
PRIMARY_IP="${2:-141.217.168.152}"
REDIS_IP="${3:-141.217.168.200}"

echo "=== QUIC Migration: Preferred Server Setup ==="
echo "Repo:          $REPO_DIR"
echo "Preferred IP:  $PREFERRED_IP"
echo "Primary IP:    $PRIMARY_IP"
echo "Redis IP:      $REDIS_IP"
echo ""

# --- Build ---
echo "[1/2] Building preferred_server..."
cd "$NEQO_DIR"
LIBCLANG_PATH=/usr/lib/llvm-14/lib PKG_CONFIG_PATH=/nonexistent PKG_CONFIG_LIBDIR=/nonexistent cargo build --release -p migration-test --bin preferred-server
echo "Build complete."

# --- Install aliases ---
echo "[2/2] Installing bash aliases..."

ALIAS_BLOCK="
# === QUIC Migration - Preferred Server (auto-generated) ===
alias preferred-up='cd $NEQO_DIR && LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433 9999'
alias preferred-down='kill \$(lsof -t -i:9999 -i:4433) 2>/dev/null && echo \"Preferred server stopped\" || echo \"No process on ports 9999/4433\"'
alias preferred-up-redis='cd $NEQO_DIR && STATE_TRANSFER=redis_kv REDIS_URL=redis://${REDIS_IP}:6379 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
alias preferred-up-redis-lazy='cd $NEQO_DIR && STATE_TRANSFER=redis_kv REDIS_URL=redis://${REDIS_IP}:6379 TRANSFER_TIMING=lazy LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
alias preferred-up-redis-ps='cd $NEQO_DIR && STATE_TRANSFER=redis_ps REDIS_URL=redis://${REDIS_IP}:6379 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
alias preferred-up-redis-ps-lazy='cd $NEQO_DIR && STATE_TRANSFER=redis_ps REDIS_URL=redis://${REDIS_IP}:6379 TRANSFER_TIMING=lazy LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
alias preferred-up-http='cd $NEQO_DIR && STATE_TRANSFER=http STATE_HTTP_PRIMARY=${PRIMARY_IP}:9998 LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
alias preferred-up-http-lazy='cd $NEQO_DIR && STATE_TRANSFER=http STATE_HTTP_PRIMARY=${PRIMARY_IP}:9998 TRANSFER_TIMING=lazy LD_LIBRARY_PATH=\$(find target/release/build -path \"*/dist/Release/lib\" -type d | head -1) ./target/release/preferred-server ${PREFERRED_IP}:4433'
# === End QUIC Migration ==="

# Remove old block if present, then append
ALIAS_FILE="$HOME/.bash_aliases"
if [ -f "$ALIAS_FILE" ]; then
    sed -i '/^# === QUIC Migration - Preferred Server/,/^# === End QUIC Migration/d' "$ALIAS_FILE"
fi
echo "$ALIAS_BLOCK" >> "$ALIAS_FILE"

echo ""
echo "Done! Aliases installed in ~/.bash_aliases"
echo "Run 'source ~/.bash_aliases' or open a new terminal."
echo ""
echo "Quick start:"
echo "  preferred-up    (starts preferred server, waits for migration state)"

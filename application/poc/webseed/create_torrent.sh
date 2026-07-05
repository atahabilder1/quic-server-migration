#!/bin/bash
# =============================================================================
# Create a .torrent file with WebSeed entries pointing to both servers
# =============================================================================
# This creates a BitTorrent metainfo file that lists both our QUIC servers
# as WebSeeds (BEP 19). A BitTorrent client would try these HTTP URLs for
# piece downloads, and our QUIC migration makes failover transparent.
#
# Requirements: pip install torrentool
# =============================================================================

set -e

FILE_PATH="${1:-/tmp/test_100mb.bin}"
TORRENT_PATH="${2:-/tmp/test_webseed.torrent}"
PRIMARY="141.217.168.152"
PREFERRED="141.217.168.143"
PORT="4433"

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH"
    echo "Run test_webseed.sh first to create the test file."
    exit 1
fi

FILE_NAME=$(basename "$FILE_PATH")

# Check if torrentool is installed
if ! python3 -c "import torrentool" 2>/dev/null; then
    echo "Installing torrentool..."
    pip install torrentool
fi

echo "Creating .torrent with WebSeed entries..."
python3 << PYEOF
from torrentool.api import Torrent

t = Torrent.create_from('$FILE_PATH')
t.webseeds = [
    'https://$PRIMARY:$PORT/$FILE_NAME',
    'https://$PREFERRED:$PORT/$FILE_NAME',
]
t.to_file('$TORRENT_PATH')

print(f"  Torrent file: $TORRENT_PATH")
print(f"  Info hash:    {t.info_hash}")
print(f"  File:         $FILE_NAME")
print(f"  Size:         {t.total_size} bytes")
print(f"  Piece size:   {t.piece_length} bytes")
print(f"  Pieces:       {len(t.pieces)}")
print(f"  WebSeeds:")
for ws in t.webseeds:
    print(f"    - {ws}")
PYEOF

echo
echo "Done! The torrent file can be opened with:"
echo "  aria2c --check-certificate=false $TORRENT_PATH"
echo "  qbittorrent $TORRENT_PATH"

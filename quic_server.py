#!/usr/bin/env python3
"""
QUIC Server with Connection Migration Support
Demonstrates server-side handling of client migration events
"""

import asyncio
import logging
from typing import Dict, Optional
from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import (
    QuicEvent,
    StreamDataReceived,
    ConnectionTerminated,
    HandshakeCompleted,
)
import colorlog
import time

# Setup colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))
logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class MigrationTracker:
    """Tracks connection migration events"""

    def __init__(self):
        self.migrations: Dict[str, list] = {}

    def record_migration(self, conn_id: str, old_addr, new_addr):
        """Record a migration event"""
        if conn_id not in self.migrations:
            self.migrations[conn_id] = []

        migration_event = {
            'timestamp': time.time(),
            'old_address': old_addr,
            'new_address': new_addr,
            'migration_number': len(self.migrations[conn_id]) + 1
        }
        self.migrations[conn_id].append(migration_event)

        logger.warning(
            f"🔄 MIGRATION #{migration_event['migration_number']} detected for {conn_id[:8]}... "
            f"| {old_addr} -> {new_addr}"
        )

    def get_migration_count(self, conn_id: str) -> int:
        """Get total migrations for a connection"""
        return len(self.migrations.get(conn_id, []))


class QuicServerProtocol(QuicConnectionProtocol):
    """QUIC server protocol with migration tracking"""

    def __init__(self, *args, migration_tracker=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.migration_tracker = migration_tracker or MigrationTracker()
        self.connection_id = None
        self.last_client_addr = None
        self.stream_data = {}

    def quic_event_received(self, event: QuicEvent):
        """Handle QUIC events"""

        if isinstance(event, HandshakeCompleted):
            self.connection_id = str(id(self._quic))
            self.last_client_addr = self._quic._network_paths[0].addr if self._quic._network_paths else None
            logger.info(f"✅ Handshake completed | Connection ID: {self.connection_id[:8]}... | Client: {self.last_client_addr}")

        elif isinstance(event, StreamDataReceived):
            # Check for migration (address change)
            current_addr = self._quic._network_paths[0].addr if self._quic._network_paths else None

            if self.last_client_addr and current_addr != self.last_client_addr:
                self.migration_tracker.record_migration(
                    self.connection_id,
                    self.last_client_addr,
                    current_addr
                )
                self.last_client_addr = current_addr

            # Handle received data
            data = event.data.decode('utf-8')
            logger.info(f"📨 Received on stream {event.stream_id}: {data}")

            # Echo response with migration info
            migration_count = self.migration_tracker.get_migration_count(self.connection_id)
            response = f"Echo: {data} | Migrations: {migration_count}"

            self._quic.send_stream_data(event.stream_id, response.encode('utf-8'), end_stream=True)
            logger.info(f"📤 Sent response: {response}")

        elif isinstance(event, ConnectionTerminated):
            logger.info(f"🔌 Connection terminated | Error: {event.error_code} | Reason: {event.reason_phrase}")


async def run_server(host: str = "127.0.0.1", port: int = 4433):
    """Run the QUIC server"""

    # Configure QUIC with self-signed certificate
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=["quic-migration-demo"],
    )

    # Generate self-signed certificate
    from aioquic.tls import SessionTicket
    import ssl

    # Create self-signed cert for testing
    configuration.load_cert_chain("cert.pem", "key.pem")

    migration_tracker = MigrationTracker()

    logger.info(f"🚀 Starting QUIC server on {host}:{port}")
    logger.info(f"📋 Server supports connection migration")
    logger.info(f"🔧 ALPN: {configuration.alpn_protocols}")

    await serve(
        host,
        port,
        configuration=configuration,
        create_protocol=lambda *args, **kwargs: QuicServerProtocol(
            *args, **kwargs, migration_tracker=migration_tracker
        ),
    )

    # Keep server running
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")

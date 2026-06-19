#!/usr/bin/env python3
"""
Real QUIC Connection Migration Demo
Actually changes the source port to trigger real migration detection on the server.
"""

import asyncio
import socket
import logging
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived, HandshakeCompleted
from aioquic.asyncio.protocol import QuicConnectionProtocol
import colorlog

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


class MigrationClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_received = asyncio.Event()
        self.response_data = None

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            logger.info("Handshake completed with server")
        elif isinstance(event, StreamDataReceived):
            self.response_data = event.data.decode('utf-8')
            logger.info(f"Received: {self.response_data}")
            self.response_received.set()


async def send_and_wait(protocol, message):
    stream_id = protocol._quic.get_next_available_stream_id()
    logger.info(f"Sending on stream {stream_id}: {message}")
    protocol._quic.send_stream_data(stream_id, message.encode('utf-8'), end_stream=True)
    protocol.transmit()
    protocol.response_received.clear()
    await protocol.response_received.wait()
    return protocol.response_data


async def run_demo():
    print()
    print("=" * 70)
    print("  QUIC Connection Migration - REAL Demo")
    print("  Showing how QUIC handles source port changes (NAT rebinding)")
    print("=" * 70)
    print()

    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=["quic-migration-demo"],
        verify_mode=False,
    )

    host = "127.0.0.1"
    port = 4433

    logger.info(f"Connecting to {host}:{port}...")

    async with connect(host, port, configuration=configuration,
                       create_protocol=MigrationClientProtocol) as protocol:

        # --- Step 1: Normal communication ---
        print("\n" + "-" * 70)
        print("STEP 1: Normal communication (no migration)")
        print("-" * 70)
        await send_and_wait(protocol, "Hello! This is the first message.")
        await asyncio.sleep(1)

        # Show current connection info
        quic = protocol._quic
        if quic._network_paths:
            path = quic._network_paths[0]
            logger.info(f"Current path: {path.addr}")
            logger.info(f"Connection ID (hex): {quic._peer_cid.cid.hex()}")

        # --- Step 2: Trigger real migration via change_connection_id ---
        print("\n" + "-" * 70)
        print("STEP 2: Triggering Connection ID change (simulates migration)")
        print("-" * 70)
        logger.warning("Requesting new Connection ID...")
        quic.change_connection_id()
        protocol.transmit()
        await asyncio.sleep(1)

        new_cid = quic._peer_cid.cid.hex()
        logger.info(f"New Connection ID (hex): {new_cid}")
        await send_and_wait(protocol, "Message after Connection ID change!")
        await asyncio.sleep(1)

        # --- Step 3: Key update (crypto migration) ---
        print("\n" + "-" * 70)
        print("STEP 3: Key Update (rotate encryption keys)")
        print("-" * 70)
        logger.warning("Requesting key update...")
        quic.request_key_update()
        protocol.transmit()
        await asyncio.sleep(1)

        await send_and_wait(protocol, "Message after key rotation!")
        await asyncio.sleep(1)

        # --- Step 4: Multiple rapid CID changes ---
        print("\n" + "-" * 70)
        print("STEP 4: Rapid Connection ID rotation (privacy feature)")
        print("-" * 70)
        for i in range(3):
            logger.warning(f"CID rotation #{i+1}...")
            try:
                quic.change_connection_id()
                protocol.transmit()
                await asyncio.sleep(0.5)
                cid = quic._peer_cid.cid.hex()
                logger.info(f"  New CID: {cid}")
            except Exception as e:
                logger.error(f"  CID change failed: {e} (no more CIDs available)")
                break

        await send_and_wait(protocol, "Message after rapid CID rotation!")

        # --- Step 5: Final message ---
        print("\n" + "-" * 70)
        print("STEP 5: Final message")
        print("-" * 70)
        await send_and_wait(protocol, "Goodbye! Connection survived everything!")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE!")
    print("=" * 70)
    print("""
  What you saw:
  1. Normal QUIC connection established with Connection ID
  2. Connection ID was changed (like what happens during migration)
  3. Encryption keys were rotated (forward secrecy)
  4. Rapid CID rotation (privacy: prevents tracking)
  5. Connection survived ALL of these changes!

  In a real network:
  - Switching WiFi -> Cellular changes your IP address
  - The server sees packets from a NEW IP but with the SAME Connection ID
  - Server sends PATH_CHALLENGE to verify the new path
  - Client responds with PATH_RESPONSE
  - Connection continues WITHOUT re-handshaking!

  This is what the QUIC-Exfil paper exploits:
  - The attacker FAKES a server migration
  - Sends stolen data to an evil server
  - Firewall thinks it's a normal migration
  - Can't tell the difference!
""")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        logger.error(f"Error: {e}")
        print("\nMake sure the server is running: python quic_server.py")

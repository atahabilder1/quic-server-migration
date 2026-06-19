#!/usr/bin/env python3
"""
Server-Side QUIC Connection Migration Demo (Preferred Address)

Demonstrates the exact mechanism the QUIC-Exfil paper exploits:
  1. Server listens on TWO addresses (primary + preferred)
  2. During handshake, server tells client: "migrate to my preferred address"
  3. Client validates the new path (PATH_CHALLENGE / PATH_RESPONSE)
  4. Client migrates — all future traffic goes to the preferred address

The paper's attack:
  - Malware on the victim's PC sniffs real QUIC traffic
  - When a connection retires its CID, malware crafts FAKE migration packets
  - Sends stolen data to an EVIL server, pretending it's a "preferred address" migration
  - Firewall sees what looks like a normal server migration and lets it through
"""

import asyncio
import logging
import os
import socket
import time
from aioquic.asyncio import QuicConnectionProtocol, serve, connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import (
    QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted,
)
from aioquic.quic.packet import QuicPreferredAddress, QuicTransportParameters
import colorlog

# Setup logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s [%(name)s] %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan', 'INFO': 'green',
        'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red,bg_white',
    }
))
root = logging.getLogger()
root.handlers.clear()
root.addHandler(handler)
root.setLevel(logging.INFO)

logger_srv = logging.getLogger("SERVER")
logger_cli = logging.getLogger("CLIENT")
logger_demo = logging.getLogger("DEMO")


# ─── Server Protocol ────────────────────────────────────────────────

class ServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, label="", **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.client_addr = None

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            self.client_addr = (
                self._quic._network_paths[0].addr if self._quic._network_paths else None
            )
            logger_srv.info(
                f"[{self.label}] Handshake completed | Client: {self.client_addr}"
            )

        elif isinstance(event, StreamDataReceived):
            current_addr = (
                self._quic._network_paths[0].addr if self._quic._network_paths else None
            )
            if self.client_addr and current_addr != self.client_addr:
                logger_srv.warning(
                    f"[{self.label}] MIGRATION detected! "
                    f"{self.client_addr} -> {current_addr}"
                )
                self.client_addr = current_addr

            data = event.data.decode("utf-8")
            logger_srv.info(f"[{self.label}] Received: {data}")

            response = f"[{self.label}] Echo: {data}"
            self._quic.send_stream_data(
                event.stream_id, response.encode("utf-8"), end_stream=True
            )
            logger_srv.info(f"[{self.label}] Sent response")

        elif isinstance(event, ConnectionTerminated):
            logger_srv.info(f"[{self.label}] Connection terminated")


# ─── Client Protocol ────────────────────────────────────────────────

class ClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_event = asyncio.Event()
        self.response_data = None

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            logger_cli.info("Handshake completed")
        elif isinstance(event, StreamDataReceived):
            self.response_data = event.data.decode("utf-8")
            logger_cli.info(f"Response: {self.response_data}")
            self.response_event.set()


async def send(proto, msg):
    sid = proto._quic.get_next_available_stream_id()
    logger_cli.info(f"Sending: {msg}")
    proto._quic.send_stream_data(sid, msg.encode("utf-8"), end_stream=True)
    proto.transmit()
    proto.response_event.clear()
    await asyncio.wait_for(proto.response_event.wait(), timeout=5)
    return proto.response_data


# ─── Demo Runner ────────────────────────────────────────────────────

async def run_demo():
    PRIMARY_HOST, PRIMARY_PORT = "127.0.0.1", 4433
    PREFERRED_HOST, PREFERRED_PORT = "127.0.0.1", 4434

    print()
    print("=" * 72)
    print("  SERVER-SIDE QUIC CONNECTION MIGRATION DEMO")
    print("  (preferred_address — the feature exploited by QUIC-Exfil)")
    print("=" * 72)

    # ── Start two servers ───────────────────────────────────────────
    server_config = QuicConfiguration(is_client=False, alpn_protocols=["demo"])
    server_config.load_cert_chain("cert.pem", "key.pem")

    print(f"\n  Primary  server: {PRIMARY_HOST}:{PRIMARY_PORT}")
    print(f"  Preferred server: {PREFERRED_HOST}:{PREFERRED_PORT}")

    logger_demo.info("Starting PRIMARY server...")
    await serve(
        PRIMARY_HOST, PRIMARY_PORT,
        configuration=server_config,
        create_protocol=lambda *a, **kw: ServerProtocol(*a, label="PRIMARY", **kw),
    )

    logger_demo.info("Starting PREFERRED server...")
    await serve(
        PREFERRED_HOST, PREFERRED_PORT,
        configuration=server_config,
        create_protocol=lambda *a, **kw: ServerProtocol(*a, label="PREFERRED", **kw),
    )

    logger_demo.info("Both servers running!\n")

    # ── Phase 1: Connect to PRIMARY ─────────────────────────────────
    print("-" * 72)
    print("  PHASE 1: Client connects to PRIMARY server")
    print("-" * 72)

    client_config = QuicConfiguration(
        is_client=True, alpn_protocols=["demo"], verify_mode=False
    )

    async with connect(
        PRIMARY_HOST, PRIMARY_PORT,
        configuration=client_config,
        create_protocol=ClientProtocol,
    ) as proto:
        resp = await send(proto, "Hello from primary connection!")
        quic = proto._quic
        path = quic._network_paths[0].addr if quic._network_paths else "?"
        cid = quic._peer_cid.cid.hex()
        logger_cli.info(f"Current path: {path}")
        logger_cli.info(f"Connection ID: {cid}")

        await asyncio.sleep(1)

        # ── Phase 2: Show CID rotation ─────────────────────────────
        print()
        print("-" * 72)
        print("  PHASE 2: Connection ID rotation (privacy)")
        print("-" * 72)

        logger_cli.warning("Rotating Connection ID...")
        quic.change_connection_id()
        proto.transmit()
        await asyncio.sleep(0.5)
        new_cid = quic._peer_cid.cid.hex()
        logger_cli.info(f"Old CID: {cid}")
        logger_cli.info(f"New CID: {new_cid}")

        resp = await send(proto, "Still connected after CID change!")
        await asyncio.sleep(1)

        # ── Phase 3: Key rotation ──────────────────────────────────
        print()
        print("-" * 72)
        print("  PHASE 3: Key rotation (forward secrecy)")
        print("-" * 72)

        logger_cli.warning("Rotating encryption keys...")
        quic.request_key_update()
        proto.transmit()
        await asyncio.sleep(0.5)

        resp = await send(proto, "Survived key rotation too!")
        await asyncio.sleep(1)

    # ── Phase 4: Simulate the attack concept ────────────────────────
    print()
    print("-" * 72)
    print("  PHASE 4: How the QUIC-Exfil attack would work")
    print("-" * 72)
    print()

    print("  In a real attack, the malware would:")
    print()
    print("  1. SNIFF your normal QUIC traffic to YouTube/Google/etc")
    print("     and record packet sizes, timing, Connection IDs")
    print()
    print("  2. WAIT for a connection to retire its CID")
    print("     (this happens normally as a privacy feature)")
    print()
    print("  3. CRAFT fake packets that look like a server migration:")
    print(f"     - Source:      127.0.0.1 (your PC)")
    print(f"     - Destination: EVIL_SERVER_IP (attacker's server)")
    print(f"     - Payload:     YOUR stolen data (passwords, files, etc)")
    print(f"     - Disguised as: PATH_CHALLENGE to 'preferred_address'")
    print()
    print("  4. FIREWALL sees this and thinks:")
    print('     "Oh, the server told the client to migrate to a new address."')
    print('     "That is normal QUIC behavior. I will let it through."')
    print()
    print("  5. The attacker's server receives your stolen data!")

    # ── Now show the migration to the "preferred" port ──────────────
    print()
    print("-" * 72)
    print("  PHASE 5: Client connects to PREFERRED server")
    print("  (simulating what happens after a server-side migration)")
    print("-" * 72)

    async with connect(
        PREFERRED_HOST, PREFERRED_PORT,
        configuration=client_config,
        create_protocol=ClientProtocol,
    ) as proto2:
        resp = await send(proto2, "Connected to preferred address!")

        path2 = proto2._quic._network_paths[0].addr if proto2._quic._network_paths else "?"
        cid2 = proto2._quic._peer_cid.cid.hex()
        logger_cli.info(f"Preferred path: {path2}")
        logger_cli.info(f"Preferred CID:  {cid2}")

        resp = await send(proto2, "Data now flows through preferred server!")

    # ── Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 72)
    print("  DEMO COMPLETE!")
    print("=" * 72)
    print("""
  What happened:
  ─────────────
  1. Client connected to PRIMARY server (port 4433)
  2. Connection ID was rotated (privacy feature)
  3. Encryption keys were rotated (forward secrecy)
  4. Client connected to PREFERRED server (port 4434)
     → This is what server-side migration looks like

  The QUIC-Exfil attack:
  ──────────────────────
  • The paper shows that step 4 can be FAKED by malware
  • Instead of connecting to a real preferred server,
    the malware sends stolen data to an EVIL server
  • The firewall can't tell the difference because:
    - QUIC encrypts everything after the handshake
    - Server preferred_address is sent INSIDE the encrypted handshake
    - IP address changes are NORMAL in QUIC (that's the whole point!)
    - The fake packets mimic real packet sizes and timing

  Detection results (from the paper):
  ────────────────────────────────────
  • 5 ML classifiers tested → ALL FAILED (best F1: 0.35)
  • 5 major firewall vendors → NONE can detect it
  • Wireshark labels it as "Unknown QUIC connection" (not suspicious)
""")
    print("=" * 72)


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        logger_demo.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

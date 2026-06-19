#!/usr/bin/env python3
"""
QUIC Traffic Inspector
Captures and displays QUIC packets in real-time while running the demo.
Shows exactly what a firewall/middlebox would see on the wire.
"""

import asyncio
import subprocess
import os
import signal
import time
import struct
import socket
from aioquic.asyncio import QuicConnectionProtocol, serve, connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import (
    QuicEvent, StreamDataReceived, ConnectionTerminated, HandshakeCompleted,
)

# ANSI colors
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_RED  = "\033[41m"
    BG_GREEN= "\033[42m"
    BG_BLUE = "\033[44m"
    BG_YELLOW="\033[43m"


def banner(text, color=C.CYAN):
    width = 72
    print(f"\n{color}{C.BOLD}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{C.RESET}\n")


def step_banner(num, text):
    print(f"\n{C.YELLOW}{C.BOLD}{'─' * 72}")
    print(f"  STEP {num}: {text}")
    print(f"{'─' * 72}{C.RESET}\n")


def info(msg):
    print(f"  {C.GREEN}✓{C.RESET} {msg}")


def warn(msg):
    print(f"  {C.YELLOW}⚠{C.RESET} {msg}")


def highlight(msg):
    print(f"  {C.CYAN}→{C.RESET} {C.BOLD}{msg}{C.RESET}")


def firewall_view(msg):
    print(f"  {C.MAGENTA}🧱 Firewall sees:{C.RESET} {msg}")


def packet_display(direction, src, dst, size, ptype, extra=""):
    arrow = f"{C.GREEN}──▶{C.RESET}" if direction == "send" else f"{C.BLUE}◀──{C.RESET}"
    print(f"  {arrow}  {C.DIM}{src}{C.RESET} → {C.DIM}{dst}{C.RESET}  "
          f"│ {size:>5} bytes │ {C.BOLD}{ptype}{C.RESET} {extra}")


def explain(text):
    for line in text.strip().split("\n"):
        print(f"  {C.DIM}│{C.RESET} {line.strip()}")
    print()


# ─── Protocols ──────────────────────────────────────────────────────

class InspectServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, label="SERVER", **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.client_addr = None
        self.msg_count = 0

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            self.client_addr = (
                self._quic._network_paths[0].addr if self._quic._network_paths else None
            )
        elif isinstance(event, StreamDataReceived):
            self.msg_count += 1
            current_addr = (
                self._quic._network_paths[0].addr if self._quic._network_paths else None
            )

            if self.client_addr and current_addr != self.client_addr:
                print(f"\n  {C.RED}{C.BOLD}🔄 SERVER DETECTED MIGRATION!{C.RESET}")
                print(f"     Old: {self.client_addr}")
                print(f"     New: {current_addr}")
                self.client_addr = current_addr

            data = event.data.decode("utf-8")
            response = f"Echo#{self.msg_count}: {data}"
            self._quic.send_stream_data(
                event.stream_id, response.encode("utf-8"), end_stream=True
            )


class InspectClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_event = asyncio.Event()
        self.response_data = None
        self.handshake_done = asyncio.Event()

    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, HandshakeCompleted):
            self.handshake_done.set()
        elif isinstance(event, StreamDataReceived):
            self.response_data = event.data.decode("utf-8")
            self.response_event.set()


async def send(proto, msg):
    sid = proto._quic.get_next_available_stream_id()
    proto._quic.send_stream_data(sid, msg.encode("utf-8"), end_stream=True)
    proto.transmit()
    proto.response_event.clear()
    await asyncio.wait_for(proto.response_event.wait(), timeout=5)
    return proto.response_data


def show_quic_header(label, cid_hex, path):
    """Show what the QUIC header looks like to an observer"""
    print(f"\n  {C.BLUE}┌─────────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.BLUE}│{C.RESET}  {C.BOLD}{label}{C.RESET}")
    print(f"  {C.BLUE}├─────────────────────────────────────────────────┤{C.RESET}")
    print(f"  {C.BLUE}│{C.RESET}  UDP src: {path[0]}:{path[1] if len(path)>1 else '?'}")
    print(f"  {C.BLUE}│{C.RESET}  UDP dst: 127.0.0.1:4433")
    print(f"  {C.BLUE}│{C.RESET}  Connection ID: {C.CYAN}{cid_hex}{C.RESET}")
    print(f"  {C.BLUE}│{C.RESET}  Payload: {C.DIM}[ENCRYPTED — cannot read!]{C.RESET}")
    print(f"  {C.BLUE}└─────────────────────────────────────────────────┘{C.RESET}")


# ─── Main Demo ──────────────────────────────────────────────────────

async def run():
    banner("QUIC TRAFFIC INSPECTOR", C.CYAN)
    print(f"  This shows you {C.BOLD}exactly{C.RESET} what happens on the network")
    print(f"  when QUIC connections are made and migrated.")
    print(f"  You'll see what a {C.MAGENTA}firewall{C.RESET} sees vs what's {C.RED}hidden{C.RESET}.\n")

    input(f"  {C.YELLOW}Press ENTER to start...{C.RESET}")

    # ── Start servers ───────────────────────────────────────────────
    server_config = QuicConfiguration(is_client=False, alpn_protocols=["demo"])
    server_config.load_cert_chain("cert.pem", "key.pem")

    await serve("127.0.0.1", 4433, configuration=server_config,
                create_protocol=lambda *a, **kw: InspectServerProtocol(*a, label="PRIMARY", **kw))
    await serve("127.0.0.1", 4434, configuration=server_config,
                create_protocol=lambda *a, **kw: InspectServerProtocol(*a, label="PREFERRED", **kw))

    client_config = QuicConfiguration(is_client=True, alpn_protocols=["demo"], verify_mode=False)

    # ================================================================
    # STEP 1: TLS HANDSHAKE
    # ================================================================
    step_banner(1, "QUIC Handshake (Connection Setup)")

    explain("""
        The client sends an Initial packet to the server.
        This is the ONLY part that's partially visible to firewalls.
        It contains the TLS ClientHello (SNI, ALPN, etc.)
        After this, EVERYTHING is encrypted.
    """)

    print(f"  {C.DIM}Connecting to 127.0.0.1:4433...{C.RESET}")

    async with connect("127.0.0.1", 4433, configuration=client_config,
                       create_protocol=InspectClientProtocol) as proto:

        await proto.handshake_done.wait()
        quic = proto._quic
        path = quic._network_paths[0].addr if quic._network_paths else ("?",)
        cid = quic._peer_cid.cid.hex()
        local_cids = [c.cid.hex() for c in quic._host_cids.values()] if hasattr(quic, '_host_cids') else []

        info("Handshake complete!")
        print()

        packet_display("send", f"127.0.0.1:{path[1] if len(path)>1 else '?'}",
                      "127.0.0.1:4433", 1200, "Initial (ClientHello)")
        packet_display("recv", "127.0.0.1:4433",
                      f"127.0.0.1:{path[1] if len(path)>1 else '?'}", 1200, "Initial (ServerHello)")
        packet_display("send", f"127.0.0.1:{path[1] if len(path)>1 else '?'}",
                      "127.0.0.1:4433", 300, "Handshake (Finished)")

        print()
        firewall_view(f"New QUIC connection established")
        firewall_view(f"ALPN: demo, SNI: (none)")
        firewall_view(f"Client port: {path[1] if len(path)>1 else '?'}")

        show_quic_header("Current QUIC Packet Header", cid, path)

        print()
        highlight(f"Connection ID (what identifies this connection): {cid}")
        highlight(f"Client address: {path}")
        warn("From here on, the firewall can ONLY see: src IP, dst IP, ports, packet size")
        warn("Everything else (data, stream IDs, frames) is ENCRYPTED")

        input(f"\n  {C.YELLOW}Press ENTER for next step...{C.RESET}")

        # ================================================================
        # STEP 2: NORMAL DATA EXCHANGE
        # ================================================================
        step_banner(2, "Normal Data Exchange")

        explain("""
            Client and server exchange messages on QUIC streams.
            Each message is a Short Header packet (minimal overhead).
            The firewall sees UDP packets but CANNOT read the content.
        """)

        resp = await send(proto, "Hello server! Watching a video...")
        packet_display("send", f"client:{path[1] if len(path)>1 else '?'}",
                      "server:4433", 62, "Short Header", f"{C.DIM}[encrypted stream data]{C.RESET}")
        packet_display("recv", "server:4433",
                      f"client:{path[1] if len(path)>1 else '?'}", 80, "Short Header", f"{C.DIM}[encrypted response]{C.RESET}")
        info(f"Server replied: {resp}")

        await asyncio.sleep(0.5)
        resp = await send(proto, "Still watching... sending ACKs...")
        packet_display("send", f"client:{path[1] if len(path)>1 else '?'}",
                      "server:4433", 58, "Short Header", f"{C.DIM}[encrypted]{C.RESET}")
        packet_display("recv", "server:4433",
                      f"client:{path[1] if len(path)>1 else '?'}", 75, "Short Header", f"{C.DIM}[encrypted]{C.RESET}")
        info(f"Server replied: {resp}")

        print()
        firewall_view("UDP packets flowing, sizes ~60-80 bytes, regular timing")
        firewall_view("Looks like normal QUIC traffic ✓")

        input(f"\n  {C.YELLOW}Press ENTER for next step...{C.RESET}")

        # ================================================================
        # STEP 3: CONNECTION ID ROTATION
        # ================================================================
        step_banner(3, "Connection ID Rotation")

        explain("""
            QUIC rotates Connection IDs for PRIVACY.
            This prevents network observers from tracking users
            across different networks. The old CID is "retired."

            This is NORMAL and happens regularly!
            But it's also when the attacker strikes...
        """)

        old_cid = cid
        quic.change_connection_id()
        proto.transmit()
        await asyncio.sleep(0.5)
        new_cid = quic._peer_cid.cid.hex()

        print(f"  {C.RED}OLD CID: {old_cid}{C.RESET}  ← retired (no longer used)")
        print(f"  {C.GREEN}NEW CID: {new_cid}{C.RESET}  ← active now")
        print()

        firewall_view(f"Packets now have different Connection ID")
        firewall_view(f"Cannot link old CID to new CID (encrypted negotiation)")
        warn("The CID change happened INSIDE the encrypted channel")
        warn("Firewall has NO WAY to know these are the same connection!")

        print()
        show_quic_header("Before CID Rotation", old_cid, path)
        show_quic_header("After CID Rotation", new_cid, path)

        resp = await send(proto, "Message with new CID")
        info(f"Connection still works: {resp}")

        input(f"\n  {C.YELLOW}Press ENTER for next step...{C.RESET}")

        # ================================================================
        # STEP 4: KEY ROTATION
        # ================================================================
        step_banner(4, "Encryption Key Rotation")

        explain("""
            QUIC can rotate encryption keys mid-connection.
            This provides forward secrecy — even if old keys are
            compromised, new data is protected.

            Completely invisible to the firewall!
        """)

        quic.request_key_update()
        proto.transmit()
        await asyncio.sleep(0.5)

        info("Encryption keys rotated!")
        resp = await send(proto, "Encrypted with NEW keys now")
        info(f"Connection survived: {resp}")

        print()
        firewall_view("Packets look identical from outside")
        firewall_view("Cannot detect key rotation at all")

        input(f"\n  {C.YELLOW}Press ENTER for the ATTACK scenario...{C.RESET}")

    # ================================================================
    # STEP 5: THE ATTACK SCENARIO
    # ================================================================
    step_banner(5, "THE QUIC-EXFIL ATTACK")

    print(f"  {C.RED}{C.BOLD}Now imagine malware is running on this PC...{C.RESET}\n")

    explain("""
        The malware has been WATCHING all the QUIC traffic above.
        It recorded:
          • Packet sizes (62, 80, 58, 75 bytes...)
          • Timing between packets (0.5s, 1s...)
          • Connection IDs that were retired
          • Which servers you talk to
    """)

    input(f"  {C.YELLOW}Press ENTER to see the attack...{C.RESET}")

    print(f"\n  {C.RED}{'━' * 60}{C.RESET}")
    print(f"  {C.RED}{C.BOLD}  ATTACK PHASE 1: Fake Server Migration{C.RESET}")
    print(f"  {C.RED}{'━' * 60}{C.RESET}\n")

    explain("""
        The malware crafts a packet that looks like a PATH_CHALLENGE
        to a "preferred server address." This is what happens when a
        server tells a client to migrate to a better address.
    """)

    # Show the fake packet
    print(f"  {C.RED}┌─────────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.RED}│{C.RESET}  {C.BOLD}FAKE Migration Packet (crafted by malware){C.RESET}")
    print(f"  {C.RED}├─────────────────────────────────────────────────┤{C.RESET}")
    print(f"  {C.RED}│{C.RESET}  UDP src: 127.0.0.1:{path[1] if len(path)>1 else '?'}  (your PC)")
    print(f"  {C.RED}│{C.RESET}  UDP dst: {C.RED}10.10.10.10:443{C.RESET}  (EVIL SERVER!)")
    print(f"  {C.RED}│{C.RESET}  DCID: {C.CYAN}{old_cid}{C.RESET}  (reuses retired CID)")
    print(f"  {C.RED}│{C.RESET}  Size: 1200 bytes (mimics real path validation)")
    print(f"  {C.RED}│{C.RESET}  Contains: {C.RED}PATH_CHALLENGE + STOLEN DATA{C.RESET}")
    print(f"  {C.RED}│{C.RESET}  {C.DIM}(but all encrypted — looks like random bytes){C.RESET}")
    print(f"  {C.RED}└─────────────────────────────────────────────────┘{C.RESET}")

    print()
    firewall_view(f"UDP packet from internal host to 10.10.10.10:443")
    firewall_view(f"Looks like QUIC (has QUIC header structure)")
    firewall_view(f"Size = 1200 bytes (normal for path validation)")
    firewall_view(f"No preceding handshake... but that's normal for migration!")
    print(f"  {C.MAGENTA}🧱 Firewall decision: {C.GREEN}{C.BOLD}ALLOW ✓{C.RESET}")
    print(f"  {C.MAGENTA}   Reason: Outgoing UDP, looks like QUIC migration{C.RESET}")

    input(f"\n  {C.YELLOW}Press ENTER to continue...{C.RESET}")

    print(f"\n  {C.RED}{'━' * 60}{C.RESET}")
    print(f"  {C.RED}{C.BOLD}  ATTACK PHASE 2: Continuous Data Theft{C.RESET}")
    print(f"  {C.RED}{'━' * 60}{C.RESET}\n")

    explain("""
        After the fake migration, the malware keeps sending packets
        with your stolen data. It mimics the EXACT packet sizes and
        timing it learned from watching your real traffic.
    """)

    stolen_items = [
        ("passwords.txt", 62),
        ("credit_cards.csv", 78),
        ("ssh_keys/id_rsa", 65),
        ("browser_cookies.db", 71),
        (".env (API keys)", 58),
    ]

    print(f"  {C.RED}Stolen data flowing out:{C.RESET}\n")
    for item, size in stolen_items:
        time.sleep(0.4)
        packet_display("send", f"your_PC:{path[1] if len(path)>1 else '?'}",
                      f"{C.RED}evil:443{C.RESET}", size,
                      "Short Header",
                      f"{C.RED}← {item}{C.RESET}")
        firewall_view(f"UDP {size}b outgoing — looks normal ✓")

    print(f"\n  {C.RED}{C.BOLD}  All your data is now on the attacker's server! 😈{C.RESET}")

    input(f"\n  {C.YELLOW}Press ENTER for comparison...{C.RESET}")

    # ================================================================
    # STEP 6: SIDE BY SIDE
    # ================================================================
    step_banner(6, "Can YOU Tell the Difference?")

    print(f"  {C.BOLD}Real server migration packet:{C.RESET}\n")
    print(f"  {C.GREEN}┌─────────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.GREEN}│{C.RESET}  src: 192.168.1.50:43210")
    print(f"  {C.GREEN}│{C.RESET}  dst: 142.250.80.46:443  (Google)")
    print(f"  {C.GREEN}│{C.RESET}  DCID: a1b2c3d4e5f6")
    print(f"  {C.GREEN}│{C.RESET}  Size: 1200 bytes")
    print(f"  {C.GREEN}│{C.RESET}  Payload: {C.DIM}0x8a3f7b2e91c4d608...{C.RESET} (encrypted)")
    print(f"  {C.GREEN}└─────────────────────────────────────────────────┘{C.RESET}")

    print(f"\n  {C.BOLD}Fake exfiltration packet:{C.RESET}\n")
    print(f"  {C.RED}┌─────────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.RED}│{C.RESET}  src: 192.168.1.50:43210")
    print(f"  {C.RED}│{C.RESET}  dst: 34.102.136.208:443  (Evil on GCloud)")
    print(f"  {C.RED}│{C.RESET}  DCID: a1b2c3d4e5f6")
    print(f"  {C.RED}│{C.RESET}  Size: 1200 bytes")
    print(f"  {C.RED}│{C.RESET}  Payload: {C.DIM}0x7f2a9e1b4c8d3a05...{C.RESET} (encrypted)")
    print(f"  {C.RED}└─────────────────────────────────────────────────┘{C.RESET}")

    print(f"\n  {C.YELLOW}{C.BOLD}  → They look IDENTICAL from outside!{C.RESET}")
    print(f"  {C.YELLOW}  → Same structure, same size, same port{C.RESET}")
    print(f"  {C.YELLOW}  → Payload is encrypted either way{C.RESET}")
    print(f"  {C.YELLOW}  → Evil server is on Google Cloud (same WHOIS as Google!){C.RESET}")
    print(f"  {C.YELLOW}  → Firewall CANNOT tell them apart!{C.RESET}")

    # ================================================================
    # SUMMARY
    # ================================================================
    banner("SUMMARY", C.CYAN)

    print(f"""  {C.BOLD}What you saw on the wire:{C.RESET}

  1. {C.GREEN}Handshake{C.RESET}    → Only part partially visible (ClientHello/SNI)
  2. {C.GREEN}Data{C.RESET}         → Fully encrypted, firewall sees only sizes
  3. {C.GREEN}CID Rotation{C.RESET} → Invisible to firewall (inside encrypted channel)
  4. {C.GREEN}Key Rotation{C.RESET} → Completely invisible
  5. {C.RED}Fake Migration{C.RESET} → Looks exactly like real migration
  6. {C.RED}Data Theft{C.RESET}    → Indistinguishable from normal traffic

  {C.BOLD}The core problem:{C.RESET}
  QUIC's encryption + connection migration = {C.RED}perfect cover for data theft{C.RESET}

  {C.BOLD}Detection results from the paper:{C.RESET}
  • Random Forest:  F1 = 0.35 {C.RED}(FAIL){C.RESET}
  • Neural Network: F1 = 0.10 {C.RED}(FAIL){C.RESET}
  • SVM:            F1 = 0.05 {C.RED}(FAIL){C.RESET}
  • Autoencoder:    F1 = 0.01 {C.RED}(FAIL){C.RESET}
  • Isolation Forest:F1 = 0.05 {C.RED}(FAIL){C.RESET}
""")

    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Stopped.{C.RESET}")
    except Exception as e:
        print(f"\n{C.RED}Error: {e}{C.RESET}")
        import traceback
        traceback.print_exc()
        print(f"\nMake sure certs exist: python generate_certs.py")

#!/usr/bin/env python3
"""Generate DETAILED task document (PDF, comprehensive) for printing."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import date

OUTPUT = "ideas/RESEARCH_TASKS_DETAILED.pdf"

DARK_BLUE = HexColor("#1a365d")
MED_BLUE = HexColor("#2b6cb0")
LIGHT_BLUE = HexColor("#ebf4ff")
DARK_GRAY = HexColor("#2d3748")
GRAY_BG = HexColor("#f7fafc")
BORDER = HexColor("#cbd5e0")
GREEN = HexColor("#276749")
GREEN_BG = HexColor("#f0fff4")
ORANGE = HexColor("#c05621")
ORANGE_BG = HexColor("#fffaf0")
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")
RED = HexColor("#e53e3e")
RED_BG = HexColor("#fff5f5")


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Title"],
        fontSize=22, leading=26, textColor=DARK_BLUE, spaceAfter=4,
        alignment=TA_CENTER, fontName="Helvetica-Bold")
    subtitle = ParagraphStyle("Sub", parent=styles["Normal"],
        fontSize=11, leading=14, textColor=MED_BLUE, spaceAfter=4,
        alignment=TA_CENTER, fontName="Helvetica")
    date_style = ParagraphStyle("Date", parent=subtitle,
        fontSize=10, textColor=DARK_GRAY, spaceAfter=8)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"],
        fontSize=16, leading=20, textColor=DARK_BLUE,
        spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
        fontSize=13, leading=16, textColor=MED_BLUE,
        spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
    h3 = ParagraphStyle("H3", parent=styles["Heading3"],
        fontSize=11, leading=14, textColor=DARK_GRAY,
        spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=10, leading=14, textColor=DARK_GRAY,
        spaceAfter=6, alignment=TA_JUSTIFY, fontName="Helvetica")
    body_italic = ParagraphStyle("BI", parent=body,
        fontName="Helvetica-Oblique", textColor=MED_BLUE)
    bullet = ParagraphStyle("Bullet", parent=body,
        leftIndent=20, bulletIndent=8, spaceBefore=2, spaceAfter=2)
    sub_bullet = ParagraphStyle("SubBullet", parent=body,
        leftIndent=40, bulletIndent=26, spaceBefore=1, spaceAfter=1, fontSize=9)
    mono = ParagraphStyle("Mono", parent=body,
        fontName="Courier", fontSize=9, leading=12, leftIndent=20,
        spaceBefore=4, spaceAfter=4, textColor=DARK_GRAY)

    story = []

    def add_box(text, bg=LIGHT_BLUE, border_color=MED_BLUE):
        d = [[Paragraph(text, ParagraphStyle("Box", parent=body, textColor=DARK_BLUE))]]
        t = Table(d, colWidths=[6.2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    def add_table(data, col_widths=None):
        if not col_widths:
            n = len(data[0])
            col_widths = [6.5*inch / n] * n
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRAY_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════
    # TITLE
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 30))
    story.append(Paragraph("Research Tasks &amp; Exploration Plan", title_style))
    story.append(Paragraph("QUIC Server-Side Migration Project", subtitle))
    story.append(Paragraph(date.today().strftime('%B %d, %Y'), date_style))
    story.append(HRFlowable(width="100%", thickness=2, color=MED_BLUE, spaceAfter=12))
    story.append(Paragraph(
        "<b>Detailed Version</b> \u2014 Comprehensive descriptions, research questions, "
        "comparison tables, and sub-task breakdowns. Print and read.",
        body_italic))

    # ── STATUS ──
    story.append(Paragraph("Current Status", h1))
    story.append(Paragraph(
        "We have a <b>fully working cross-machine QUIC server migration</b> implementation "
        "using modified Mozilla Neqo (Rust). Verified with Firefox over HTTP/3 on 4 physical "
        "machines (same LAN). <b>Anik:</b> 5 state transfer backends. "
        "<b>Fatima:</b> Docker/namespace setup with /tmp migration.", body))


    # ── FOCUS ──
    story.append(Paragraph("Research Focus (Per Professor)", h1))
    story.append(Paragraph(
        "\u2022 <b>QUIC Proxy (Pass-Through Handshake)</b> \u2014 Explore primary as proxy "
        "during handshake. Compare against baselines.", bullet))
    story.append(Paragraph(
        "\u2022 <b>Precise Definition of Applications</b> \u2014 What are the real applications "
        "of QUIC migration? Server architecture, engineering perspective.", bullet))

    # ── OVERVIEW ──
    story.append(Spacer(1, 6))
    story.append(Paragraph("All Tasks at a Glance", h1))
    add_table([
        ["#", "Task", "Type"],
        ["1", "Docker Migration + 4 Backend Comparison\n(/tmp, TCP, Redis, QUIC)", "Engineering +\nBenchmarking"],
        ["2", "QUIC Proxy (Pass-Through Handshake)\nExploration + Decryption Problem", "Protocol\nExploration"],
        ["3", "Applications of QUIC Migration\n(Use Cases, Server Types, Stream LB,\nServer Chaining)", "Research +\nExploration"],
        ["4", "Neqo Server & Server Architecture\n(Neqo Capabilities, nginx Comparison,\nArchitecture Requirements)", "Investigation +\nAnalysis"],
        ["5", "Attack Surface vs. Benefits\nTradeoff Analysis", "Security\nAnalysis"],
    ], [0.4*inch, 3.6*inch, 1.3*inch])

    # ══════════════════════════════════════════════════════════════════
    # TASK 1: Docker + Backends
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Task 1: Docker-Based Migration with 4 Backend Comparison", h1))
    add_box("<b>Goal:</b> Convert Fatima's namespace-based implementation to Docker containers. "
        "Implement and benchmark 4 state transfer backends: /tmp (shared volume), TCP Push, "
        "Redis KV, and QUIC-based transfer. Measure latency, reliability, and migration success rate.")

    story.append(Paragraph("Background", h2))
    story.append(Paragraph(
        "Fatima has completed a working migration using network namespaces with /tmp (shared "
        "filesystem) as the state transfer mechanism. The migration state is ~445 bytes "
        "containing TLS secrets, connection IDs, packet numbers, and client address. The next "
        "step is to convert this to Docker containers and implement additional backends.", body))

    story.append(Paragraph("Sub-Tasks", h2))
    for s in [
        "<b>1a. Convert Namespace to Docker:</b> Each server (primary, preferred) in its own "
        "container. Shared Docker network for QUIC traffic. Redis in a third container.",
        "<b>1b. /tmp Backend (Shared Volume):</b> Primary writes state to shared Docker volume. "
        "Preferred reads from same volume. Baseline \u2014 zero network overhead. "
        "Leaves disk forensic artifacts.",
        "<b>1c. TCP Push Backend:</b> Primary opens TCP to preferred, pushes 445 bytes. "
        "Already implemented on physical machines \u2014 port to Docker. "
        "Observable side-channel (TCP connection visible to observer). Lowest latency (~1ms).",
        "<b>1d. Redis KV Backend:</b> State in Redis (separate container). Primary SETs, "
        "preferred GETs. Decoupled \u2014 supports lazy retrieval. Best multi-server scalability.",
        "<b>1e. QUIC-Based State Transfer (NEW):</b> QUIC connection between primary and "
        "preferred for state transfer. Encrypted, indistinguishable from regular QUIC traffic. "
        "Hardest for IDS to detect. New implementation required.",
    ]:
        story.append(Paragraph(f"\u2022 {s}", bullet))

    story.append(Paragraph("Comparison Metrics", h2))
    for m in [
        "Transfer latency (state export to preferred ready)",
        "Migration success rate (over 100 consecutive migrations)",
        "Time-to-first-byte after migration (client perspective)",
        "Network fingerprint visibility (tcpdump + Wireshark analysis)",
        "Disk/memory forensic artifacts",
        "Scalability (N preferred servers)",
        "Failure resilience (preferred not ready scenario)",
    ]:
        story.append(Paragraph(f"\u2022 {m}", bullet))

    story.append(Paragraph("Expected Comparison Matrix", h2))
    add_table([
        ["Backend", "Latency", "Network\nVisible?", "Forensic\nArtifacts", "Scalability", "Dependencies"],
        ["/tmp\n(shared vol)", "Lowest\n(disk I/O)", "No", "Yes\n(file on disk)", "Single host\nonly", "Shared\nstorage"],
        ["TCP Push", "~1ms\n(LAN)", "Yes\n(TCP conn)", "No\n(in-memory)", "Point-to-\npoint", "None"],
        ["Redis KV", "~2-3ms\n(LAN)", "Yes\n(Redis proto)", "Yes\n(Redis log)", "Multi-\nserver", "Redis\ninstance"],
        ["QUIC\nTransfer", "~2-5ms\n(LAN)", "Encrypted\n(looks normal)", "No\n(in-memory)", "Point-to-\npoint", "QUIC stack\non both"],
    ], [0.9*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])

    story.append(Paragraph("Research Questions", h2))
    for i, q in enumerate([
        "Which backend achieves the lowest migration latency?",
        "Does the choice of backend affect migration success rate?",
        "Can a network observer distinguish QUIC-based state transfer from regular QUIC traffic?",
        "Which backend is most resilient when the preferred server is not immediately ready?",
        "What is the operational overhead of each backend in a real deployment?",
    ], 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # TASK 2: QUIC Proxy
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Task 2: QUIC Proxy \u2014 Pass-Through Handshake Exploration", h1))
    add_box("<b>Goal:</b> Explore whether the primary server can act as a proxy during the "
        "QUIC/TLS 1.3 handshake, forwarding handshake messages to the preferred server in "
        "real-time so it derives its own crypto keys. Identify the decryption problem. "
        "If a practical solution exists, compare latency against Task 1 baselines.")

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "In our current implementation, the primary completes the full TLS 1.3 handshake, "
        "then exports ~445 bytes of crypto state to the preferred server. This creates a window "
        "where the preferred has no crypto context. A pass-through model would let the preferred "
        "participate from the beginning, potentially eliminating the state transfer delay.", body))

    story.append(Paragraph("How It Would Work (Ideal Case)", h2))
    for i, s in enumerate([
        "Client sends Initial packet to the primary server.",
        "Primary handles handshake normally BUT also forwards handshake packets to preferred in real-time.",
        "Preferred silently processes the same handshake messages and derives identical TLS keys.",
        "Handshake completes. Primary advertises <font face='Courier'>preferred_address</font>.",
        "Client sends PATH_CHALLENGE to preferred.",
        "Preferred already has the keys \u2014 responds immediately. Zero delay.",
    ], 1):
        story.append(Paragraph(f"\u2022 <b>Step {i}:</b> {s}", bullet))

    story.append(Paragraph("The Decryption Problem (Critical Challenge)", h2))
    add_box(
        "<b>Key Issue:</b> Pure pass-through does NOT work due to TLS 1.3 ECDHE. "
        "The preferred server cannot derive traffic keys just by observing forwarded "
        "handshake packets. It lacks the primary's ephemeral private key needed for "
        "the Diffie-Hellman computation.",
        bg=RED_BG, border_color=RED)

    story.append(Paragraph("In TLS 1.3, the handshake uses ECDHE:", body))
    story.append(Paragraph(
        "\u2022 Client sends ephemeral <b>PUBLIC</b> key in ClientHello.", bullet))
    story.append(Paragraph(
        "\u2022 Primary generates ephemeral key pair, sends <b>PUBLIC</b> key in ServerHello.", bullet))
    story.append(Paragraph(
        "\u2022 Both compute: <font face='Courier'>shared_secret = their_private "
        "\u00d7 other_public</font>.", bullet))
    story.append(Paragraph(
        "If primary forwards these packets, preferred sees both PUBLIC keys but does NOT have "
        "the primary's ephemeral PRIVATE key. Without it, it CANNOT compute the shared secret.", body))
    story.append(Paragraph(
        "The primary would still need to send either the ephemeral private key OR the derived "
        "shared secret. This brings us back to crypto state export \u2014 just during the "
        "handshake instead of after. The latency benefit needs experimental verification.", body))

    story.append(Paragraph("Current vs. Pass-Through Comparison", h2))
    add_table([
        ["Aspect", "Current\n(Post-Handshake Export)", "QUIC Proxy\n(Pass-Through)"],
        ["When preferred gets keys", "After handshake", "During handshake\n(if feasible)"],
        ["What is transferred", "~445 bytes\n(secrets, CIDs, pkt#)", "Ephemeral key or\nshared secret"],
        ["Transfer delay", "After handshake\n+ transfer time", "Overlaps with\nhandshake"],
        ["Decrypt issue?", "No \u2014 full state\nexported", "Yes \u2014 needs\ninvestigation"],
        ["Complexity", "Moderate", "Higher\n(real-time fwd)"],
    ], [1.3*inch, 2.2*inch, 2.2*inch])

    story.append(Paragraph("Research Questions", h2))
    for i, q in enumerate([
        "Can we forward enough TLS state during the handshake for preferred to derive keys?",
        "Does forwarding the ephemeral key during handshake reduce latency vs. post-handshake export?",
        "What are the security implications? Does sharing ephemeral key weaken forward secrecy?",
        "Is there a way to involve preferred in key generation from the start (coordinated ECDHE)?",
        "Compatible with TLS 1.3 session resumption and 0-RTT?",
        "What is the minimum state that must be forwarded during handshake vs. after?",
    ], 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    story.append(Paragraph("Deliverable", h2))
    story.append(Paragraph(
        "A feasibility report: (1) whether pass-through is possible given TLS 1.3, "
        "(2) decryption limitations, (3) if partial solution exists, "
        "(4) if feasible, latency benchmarks against Task 1 baselines.", body))

    # ══════════════════════════════════════════════════════════════════
    # TASK 3: Applications of QUIC Migration (THE BIG ONE)
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Task 3: Applications of QUIC Migration", h1))
    add_box(
        "<b>Goal:</b> Explore and research the real-world applications of QUIC server-side "
        "migration. Investigate use cases and content models, server type applicability, "
        "stream-level load balancing, and server-to-server chaining. "
        "Do basic research on each area and list what should be investigated further.",
        bg=GREEN_BG, border_color=GREEN)

    story.append(Paragraph(
        "What is QUIC server migration actually useful for, and where does it fall short?", body))

    # ── 3a: What Are the Applications? ──
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=10, spaceAfter=6))
    story.append(Paragraph("3a. Use Cases and Content Model", h2))
    story.append(Paragraph(
        "What are the concrete applications of QUIC server-side migration? For each, specify: "
        "server architecture, content model (same vs. different), migration workflow, and what "
        "additional state (beyond TLS) needs to migrate.", body))

    story.append(Paragraph("Same Content vs. Different Content", h3))
    add_table([
        ["Scenario", "Content Model", "How It Works", "Example"],
        ["Horizontal LB\n(Replicas)", "Same content\non all servers", "Client gets identical\nresponse from any", "CDN edges,\nstateless APIs"],
        ["Vertical\nSeparation", "Different roles,\ndifferent content", "Primary = gateway\nPreferred = backend", "TLS terminator\n+ app server"],
        ["Stateful\nServices", "Same content,\nshared state", "App state in\nexternal store", "Shopping cart,\nsessions"],
        ["Malicious", "Different\n(attacker ctrl)", "Preferred serves\nattacker content", "QUIC-Exfil"],
    ], [1.1*inch, 1.2*inch, 1.6*inch, 1.2*inch])

    story.append(Paragraph("Application: Seamless Load Balancing (Horizontal)", h3))
    story.append(Paragraph(
        "Both servers are identical replicas. Primary handles TLS handshake, migrates to "
        "a less-loaded replica. After migration, replica communicates directly with client "
        "\u2014 no proxy in the data path. Key advantage over nginx: no proxy bottleneck.", body))

    story.append(Paragraph("Application: Vertical Separation", h3))
    story.append(Paragraph(
        "Primary is a lightweight TLS gateway. It handles handshake/auth, then migrates to "
        "a heavyweight application backend. Different roles, potentially different software. "
        "This is the 'vertical' split the professor mentioned.", body))

    story.append(Paragraph("Application: Zero-Downtime Maintenance", h3))
    story.append(Paragraph(
        "Active connections migrated to standby before primary goes offline. "
        "No client errors. Supports rolling updates.", body))

    story.append(Paragraph("Application: Geographic Optimization / Failover", h3))
    story.append(Paragraph(
        "Mid-session migration to better server. Sub-second failover without TCP reconnect. "
        "Not possible with DNS after connection established.", body))

    story.append(Paragraph("What State Needs to Migrate?", h3))
    add_table([
        ["State Type", "Currently\nMigrated?", "Size", "Needed For"],
        ["TLS secrets", "Yes", "~128 bytes", "All scenarios"],
        ["Connection IDs", "Yes", "~40 bytes", "All scenarios"],
        ["Packet numbers", "Yes", "~16 bytes", "All scenarios"],
        ["HTTP/3 stream state", "No", "Variable", "Mid-request migration"],
        ["Application session", "No", "Variable", "Stateful services"],
        ["Request context\n(URL, headers)", "No", "Variable", "Vertical separation"],
        ["Flow control state", "No", "~32 bytes", "High-throughput"],
    ], [1.6*inch, 0.8*inch, 0.8*inch, 1.6*inch])

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "For each application, what is the minimum state that must migrate?",
        "Can we define a generic 'application state export' API for different server types?",
        "Which application has the strongest case for a paper contribution?",
        "Are there real-world deployments we can reference or compare against?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ── 3b: Server Type Applicability ──
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=6, spaceAfter=6))
    story.append(Paragraph("3b. Server Type Applicability", h2))
    story.append(Paragraph(
        "Is QUIC migration equally applicable to all server types, or does each need "
        "separate implementation? Our 445-byte migration = TLS state only. "
        "What about stateful servers?", body))

    add_table([
        ["Server Type", "Stateless?", "App State\nto Migrate", "Migration\nComplexity", "Example"],
        ["Static web", "Yes", "None", "Easy \u2014 current\nimpl sufficient", "nginx HTML"],
        ["REST API", "Mostly", "Session (maybe)", "Easy if\nstateless", "Microservices"],
        ["Streaming\n(Netflix)", "No", "Stream position,\nbuffer, bitrate", "Hard \u2014 need\nplayback state", "Video, live"],
        ["Database-\nbacked", "No", "DB conn,\ntransaction", "Hard \u2014 DB\ndon't migrate", "E-commerce"],
        ["WebSocket /\nreal-time", "No", "Session,\nsubscriptions", "Hard \u2014\ncomplex state", "Chat, gaming"],
        ["CDN edge", "Yes (cache)", "Cache (optional)", "Easy if cached\non both", "Cloudflare"],
    ], [0.9*inch, 0.7*inch, 1.1*inch, 1.0*inch, 1.0*inch, 0.9*inch])

    story.append(Paragraph("Key Insight", h3))
    story.append(Paragraph(
        "For <b>stateless servers</b> (static web, REST APIs, CDN), our current TLS-only "
        "migration is sufficient. For <b>stateful servers</b> (streaming, database, real-time), "
        "additional application state must transfer \u2014 our implementation doesn't handle this.", body))

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "Can we define a generic 'application state export' interface for different server types?",
        "Is there a clean separation: transport migration (QUIC) vs. app migration (HTTP/3)?",
        "One framework or separate implementations per type?",
        "For Netflix-style streaming: what exactly needs to transfer? (bitrate, position, buffer)",
        "For database: can we migrate the QUIC connection but keep the DB connection separate?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ── 3c: Stream-Level LB ──
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=10, spaceAfter=6))
    story.append(Paragraph("3c. Stream-Level Load Balancing \u2014 Why It Doesn't Work", h2))
    story.append(Paragraph(
        "QUIC has independent multiplexed streams, which raises a natural question: could "
        "individual streams be routed to different servers? We analyze why this is not feasible "
        "with the current protocol.", body))

    story.append(Paragraph("Why Per-Stream Routing Breaks Down", h3))
    story.append(Paragraph(
        "Despite QUIC streams being logically independent, they share critical "
        "connection-level state that cannot be split:", body))
    for c in [
        "<b>Shared encryption:</b> All streams use the same TLS keys. A single QUIC packet "
        "can carry frames from multiple streams \u2014 you cannot decrypt one stream without "
        "decrypting the entire packet.",
        "<b>Shared packet numbers:</b> Packet numbers are per-connection, not per-stream. "
        "Multiple servers would need to coordinate packet number allocation to avoid collisions.",
        "<b>Shared congestion control:</b> QUIC runs one congestion controller per connection. "
        "Splitting streams across servers breaks congestion feedback.",
        "<b>Shared ACK state:</b> ACKs are per-connection. Server A cannot acknowledge packets "
        "that Server B received.",
        "RFC 9000 <font face='Courier'>preferred_address</font> migrates the entire connection, "
        "not individual streams. No per-stream mechanism exists.",
    ]:
        story.append(Paragraph(f"\u2022 {c}", bullet))

    story.append(Paragraph("Comparison: Split Streams vs. Separate Connections", h3))
    add_table([
        ["Approach", "Feasibility", "Trade-off"],
        ["Per-stream routing\n(one connection)", "Not feasible\nwith current QUIC", "Would need new protocol,\nbreaks crypto/congestion"],
        ["Separate QUIC\nconnections per service", "Works today", "More handshakes,\nbut each connection\nis self-contained"],
    ], [1.6*inch, 1.5*inch, 2.1*inch])

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "Is there existing research on per-stream routing? If so, how do they handle shared state?",
        "Could a proxy model work where one server forwards specific stream frames to backends?",
        "Is the overhead of multiple separate connections actually a problem in practice?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ── 3d: Server-to-Server Chaining ──
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=10, spaceAfter=6))
    story.append(Paragraph("3d. Server-to-Server Migration in Multi-Tier Architectures", h2))
    story.append(Paragraph(
        "In multi-tier architectures, a front-end server receives a client request and makes "
        "its own QUIC connection to a backend. If the backend advertises "
        "<font face='Courier'>preferred_address</font>, the front-end (acting as a QUIC client) "
        "follows the migration. This is a single-hop migration on the backend side, not a chain.", body))

    story.append(Paragraph(
        "<font face='Courier'>Client \u2192 Server A (front-end) \u2192 Server B (backend) "
        "\u2192 Server C (migrated backend)</font>", mono))
    story.append(Paragraph(
        "The client's connection to A does not migrate. A's connection to B migrates to C. "
        "These are two independent connections, each with at most one migration.", body))

    story.append(Paragraph("Limitations", h3))
    for s in [
        "<font face='Courier'>preferred_address</font> is a one-time handshake parameter. "
        "Once a connection migrates, it cannot migrate again \u2014 there is no mechanism "
        "for the preferred server to advertise a second preferred address.",
        "Cascading failover (B fails, so migrate to C) requires B to proactively migrate "
        "<b>before</b> failure. A dead server cannot export state. This is the same as "
        "zero-downtime maintenance (covered in 3a).",
        "Multi-hop relay (US \u2192 EU \u2192 Asia) would require repeated migrations on the "
        "same connection, which the protocol does not support.",
    ]:
        story.append(Paragraph(f"\u2022 {s}", bullet))

    story.append(Paragraph("What Is Feasible", h3))
    for s in [
        "<b>Independent per-tier migration:</b> Client\u2192A can migrate (client-facing tier). "
        "A\u2192B can separately migrate (backend tier). Each tier manages its own connections.",
        "<b>Backend rebalancing:</b> Front-end's connection to backend B migrates to C. "
        "Front-end follows transparently. Useful for microservice rebalancing.",
    ]:
        story.append(Paragraph(f"\u2022 {s}", bullet))

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "Is independent per-tier migration practical? What is the cumulative latency?",
        "Does backend migration add meaningful attack surface beyond single-hop?",
        "Are there real microservice architectures where backend QUIC migration helps?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ── 3 Summary ──
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=10, spaceAfter=6))
    story.append(Paragraph("Task 3 Summary: What to Explore", h2))
    add_table([
        ["Sub-Task", "Core Question", "Check Further"],
        ["3a. Use Cases &\nContent Model", "What are the real uses?\nSame vs. different content?", "Min state per app,\ngeneric API, paper angle"],
        ["3b. Server Types", "Works for all servers\nor just stateless?", "App state interface,\nstreaming/DB requirements"],
        ["3c. Stream-Level LB", "Why can't streams go\nto different servers?", "Protocol constraints,\nseparate connections\nas alternative"],
        ["3d. Multi-Tier\nMigration", "Can backend connections\nmigrate independently?", "Per-tier feasibility,\nmicroservice use cases"],
    ], [1.2*inch, 1.8*inch, 1.8*inch])

    # ══════════════════════════════════════════════════════════════════
    # TASK 4: Neqo Server & Server Architecture
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Task 4: Neqo Server &amp; Server Architecture", h1))
    add_box(
        "<b>Goal:</b> Investigate what Neqo's server actually supports and why someone said "
        "'Neqo doesn't support server.' Compare QUIC migration architecture against "
        "traditional nginx reverse proxy. Understand what server architecture is needed "
        "to support migration and whether it can coexist with existing infrastructure.",
        bg=ORANGE_BG, border_color=ORANGE)

    # ── 4a: Neqo ──
    story.append(Paragraph("4a. Neqo Server: What Does It Actually Support?", h2))
    story.append(Paragraph(
        "Someone said 'Neqo doesn't support server.' Neqo is built for Firefox (a client). "
        "The server component exists but may be limited to testing. We need to understand "
        "exactly what it can and cannot do, and whether it matters for our research.", body))

    story.append(Paragraph("What Neqo Server Has", h3))
    for p in [
        "<font face='Courier'>neqo-bin/src/server/</font> \u2014 working QUIC server "
        "(HTTP/0.9 and HTTP/3 modes)",
        "<font face='Courier'>neqo-transport</font> with <font face='Courier'>Role::Server"
        "</font> \u2014 full QUIC transport layer",
        "<font face='Courier'>preferred_address</font> support (our modification)",
        "<font face='Courier'>Http3Server</font> in <font face='Courier'>neqo-http3</font>",
        "TLS certificate configuration via CLI",
    ]:
        story.append(Paragraph(f"\u2022 {p}", bullet))

    story.append(Paragraph("What May Be Missing", h3))
    for p in [
        "Production concurrency (single-threaded event loop vs. multi-threaded workers?)",
        "Full HTTP/3 features (routing, virtual hosts, content negotiation?)",
        "Performance under load (max concurrent connections?)",
        "Graceful shutdown / connection draining",
        "Integration with existing infrastructure (nginx, health checks, monitoring)",
    ]:
        story.append(Paragraph(f"\u2022 {p}", bullet))

    add_table([
        ["Feature", "Neqo Server", "Production Server\n(nginx/quiche)", "Impact on Research"],
        ["QUIC transport", "Full", "Full", "None"],
        ["HTTP/3", "Basic (test)", "Full production", "Limits app testing"],
        ["preferred_address", "Supported\n(our mod)", "NOT implemented\nin production servers", "This IS our\ncontribution"],
        ["Concurrency", "Limited?", "Thousands", "Affects benchmarks"],
        ["Content serving", "Static/test", "Full web server", "Limits app testing"],
        ["nginx integration", "Unknown", "Native", "Needs investigation"],
    ], [1.2*inch, 1.1*inch, 1.3*inch, 1.2*inch])

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "Read neqo-bin/src/server/mod.rs \u2014 is it single-threaded?",
        "Run concurrent connection test: 10, 100, 1000 connections",
        "Compare Neqo server features against Cloudflare quiche and Google QUICHE",
        "Can Neqo work behind or alongside nginx?",
        "Does Neqo's limited server matter for our research, or is it sufficient for protocol testing?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ── 4b: nginx & Architecture ──
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceBefore=6, spaceAfter=6))
    story.append(Paragraph("4b. nginx &amp; Server Architecture Comparison", h2))
    story.append(Paragraph(
        "nginx is the industry standard for load balancing. It supports QUIC/HTTP3 "
        "(since 1.25+) but does NOT implement preferred_address / server migration. "
        "Why not? What architecture is needed instead?", body))

    story.append(Paragraph("Architecture Comparison", h3))
    story.append(Paragraph("<b>nginx (proxy in every packet):</b>", body))
    story.append(Paragraph(
        "<font face='Courier'>Client \u2194 nginx \u2194 Backend "
        "(nginx forwards ALL traffic, always in path)</font>", mono))
    story.append(Paragraph("<b>QUIC migration (proxy exits after handshake):</b>", body))
    story.append(Paragraph(
        "<font face='Courier'>Client \u2194 Front-end (handshake) \u2192 migration \u2192 Backend "
        "(direct)</font>", mono))

    add_table([
        ["Dimension", "nginx Reverse Proxy", "QUIC Migration"],
        ["Proxy in data path?", "Yes, always", "No \u2014 only handshake"],
        ["Per-packet overhead", "Every packet forwarded", "Zero after migration"],
        ["Server requirements", "Only nginx needs QUIC", "Both need QUIC stack"],
        ["Failure handling", "Retry to another backend", "One-shot migration"],
        ["Scalability ceiling", "nginx is bottleneck", "No bottleneck after"],
        ["Health checks", "Built-in", "Not built-in"],
        ["Routing logic", "URL, headers, weight", "Server decision at\nhandshake only"],
        ["Production ready?", "Decades of use", "Research (ours)"],
    ], [1.3*inch, 2.2*inch, 2.2*inch])

    story.append(Paragraph("Why nginx Doesn't Support Migration", h3))
    story.append(Paragraph(
        "nginx's architecture is fundamentally a proxy \u2014 it sits in the middle and "
        "forwards packets. Server-side migration requires the proxy to <b>exit</b> the data "
        "path, which contradicts nginx's core design. Additionally, preferred_address requires "
        "sharing TLS secrets with the backend, which nginx's security model does not allow. "
        "The architecture needed for migration is fundamentally different from proxy.", body))

    story.append(Paragraph("What Server Architecture IS Needed?", h3))
    for p in [
        "A front-end willing to give up its connection (not a persistent proxy)",
        "Backend servers with full QUIC+TLS capability (not just TCP backends)",
        "A secure state transfer channel between front-end and backend",
        "Coordination mechanism for load decisions at handshake time",
        "This is a fundamentally different architecture than traditional reverse proxy",
    ]:
        story.append(Paragraph(f"\u2022 {p}", bullet))

    story.append(Paragraph("What to Check Further", h3))
    for q in [
        "Can QUIC migration work alongside nginx? (nginx as primary, QUIC backend as preferred)",
        "Is a hybrid model practical: nginx for routing + QUIC migration for handoff?",
        "At what traffic volume does proxy bottleneck matter vs. migration?",
        "What operational features (health checks, retries) does migration need to replicate?",
        "Would CDN providers benefit from migration as alternative to proxy?",
    ]:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # TASK 5: Attack Surface
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Task 5: Attack Surface vs. Benefits \u2014 Tradeoff Analysis", h1))
    add_box(
        "<b>Goal:</b> Precisely define the attack surface opened by QUIC server-side migration "
        "and analyze the tradeoff: engineering advantages vs. security risks. "
        "Server-side migration is largely unimplemented specifically due to these concerns.",
        bg=RED_BG, border_color=RED)

    story.append(Paragraph("Why Server-Side Migration Is Rarely Implemented", h2))
    story.append(Paragraph(
        "Despite RFC 9000 Section 9.6, preferred_address is almost never implemented in "
        "production. Major implementations (Google QUICHE, Cloudflare quiche, nginx, msquic) "
        "all skip it. It opens an attack surface that didn't exist before.", body))

    story.append(Paragraph("Attack Surface Opened", h2))
    for a in [
        "<b>Connection Hijacking:</b> Malicious server redirects client to attacker-controlled "
        "server. Client trusts preferred_address from TLS handshake \u2014 no independent verify.",
        "<b>Covert Exfiltration:</b> Preferred serves different content. QUIC-Exfil paper: "
        "ML classifiers achieve only 0-47% F1-score at detecting this.",
        "<b>State Transfer Interception:</b> 445 bytes of TLS secrets on the wire between "
        "servers. If intercepted, attacker decrypts all connection traffic.",
        "<b>Trust Boundary Expansion:</b> Every server receiving migration state = compromise point.",
        "<b>No Migration Attestation:</b> Client can choose not to use preferred_address "
        "(RFC 9000 \u00a79.6: 'MAY'), but if it does, there is no mechanism to verify the "
        "preferred address belongs to the same legitimate operator. PATH_CHALLENGE validates "
        "reachability, not identity.",
        "<b>Content Substitution:</b> After migration, preferred controls what client receives.",
    ]:
        story.append(Paragraph(f"\u2022 {a}", bullet))

    story.append(Paragraph("Benefits Gained", h2))
    for b in [
        "<b>No Proxy Bottleneck:</b> Front-end exits data path after migration. "
        "Direct client-server communication.",
        "<b>Sub-Second Failover:</b> Faster than TCP reconnect + TLS 1.3 re-handshake (2 RTTs).",
        "<b>Zero-Downtime Maintenance:</b> Drain connections gracefully before shutdown.",
        "<b>Vertical Separation:</b> Lightweight TLS terminator + heavyweight app server.",
        "<b>Geographic Optimization:</b> Mid-session migration to better server.",
    ]:
        story.append(Paragraph(f"\u2022 {b}", bullet))

    story.append(Paragraph("Risk/Benefit by Deployment Scenario", h2))
    add_table([
        ["Scenario", "Risk", "Benefit", "Verdict"],
        ["Same-subnet replicas\n(stateless LB)", "LOW", "HIGH \u2014 no proxy\nbottleneck", "Favorable"],
        ["Vertical separation\n(same data center)", "MEDIUM", "HIGH \u2014 efficient\nresource usage", "Likely favorable"],
        ["Cross-network\n(WAN migration)", "HIGH", "MEDIUM \u2014 geo\noptimization", "Needs safeguards"],
        ["Cross-jurisdiction", "VERY HIGH", "LOW", "Not recommended\nwithout attestation"],
    ], [1.4*inch, 1.3*inch, 1.4*inch, 1.4*inch])

    story.append(Paragraph("Research Questions", h2))
    for i, q in enumerate([
        "Minimum attacker capability to exploit server-side migration?",
        "Can attack surface be reduced without losing engineering benefits?",
        "Which applications have acceptable risk/benefit?",
        "Should RFC require client consent or migration attestation?",
        "Can we propose a migration_attestation transport parameter?",
    ], 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # HOW TASKS CONNECT
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("How the 5 Tasks Connect", h1))
    for c in [
        "<b>Task 1 (Docker + Backends):</b> Benchmark 4 state transfer backends in Docker. "
        "Produces concrete latency and reliability numbers.",
        "<b>Task 2 (QUIC Proxy):</b> Investigate whether the preferred server can derive keys "
        "during the handshake instead of after. Document the ECDHE limitation.",
        "<b>Task 3 (Applications):</b> Define use cases, check which server types work, "
        "analyze why stream-level LB is not feasible, look at multi-tier scenarios.",
        "<b>Task 4 (Neqo + Architecture):</b> Check what Neqo's server actually supports. "
        "Compare migration architecture against nginx reverse proxy.",
        "<b>Task 5 (Attack Surface):</b> Document what attacks preferred_address enables "
        "and under what deployment conditions the risk is acceptable.",
    ]:
        story.append(Paragraph(f"\u2022 {c}", bullet))


    doc.build(story)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

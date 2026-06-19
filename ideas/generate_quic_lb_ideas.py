#!/usr/bin/env python3
"""Generate QUIC Load Balancing Ideas PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import date

OUTPUT = "ideas/QUIC_LOAD_BALANCING_IDEAS.pdf"

# Colors
DARK_BLUE = HexColor("#1a365d")
MED_BLUE = HexColor("#2b6cb0")
LIGHT_BLUE = HexColor("#ebf4ff")
ACCENT = HexColor("#e53e3e")
GRAY_BG = HexColor("#f7fafc")
BORDER = HexColor("#cbd5e0")
DARK_GRAY = HexColor("#2d3748")
GREEN = HexColor("#276749")
GREEN_BG = HexColor("#f0fff4")
ORANGE = HexColor("#c05621")
ORANGE_BG = HexColor("#fffaf0")
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=letter,
        topMargin=0.7*inch,
        bottomMargin=0.7*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=22, leading=26, textColor=DARK_BLUE,
        spaceAfter=4, alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, leading=14, textColor=MED_BLUE,
        spaceAfter=16, alignment=TA_CENTER,
        fontName="Helvetica",
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=16, leading=20, textColor=DARK_BLUE,
        spaceBefore=18, spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, leading=16, textColor=MED_BLUE,
        spaceBefore=14, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=11, leading=14, textColor=DARK_GRAY,
        spaceBefore=10, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, textColor=DARK_GRAY,
        spaceAfter=6, alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )
    body_italic = ParagraphStyle(
        "BodyItalic", parent=body,
        fontName="Helvetica-Oblique", textColor=MED_BLUE,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body,
        leftIndent=20, bulletIndent=8,
        spaceBefore=2, spaceAfter=2,
    )
    highlight_style = ParagraphStyle(
        "Highlight", parent=body,
        fontSize=10, leading=14,
        backColor=GREEN_BG, borderColor=GREEN,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=GREEN,
        fontName="Helvetica-Bold",
    )
    idea_style = ParagraphStyle(
        "Idea", parent=body,
        fontSize=10, leading=14,
        backColor=ORANGE_BG, borderColor=ORANGE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ORANGE,
        fontName="Helvetica-Bold",
    )
    question_style = ParagraphStyle(
        "Question", parent=body,
        fontSize=10, leading=14,
        backColor=PURPLE_BG, borderColor=PURPLE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
    )

    elements = []

    # Helper for tables
    def make_table(headers, rows, col_widths=None, highlight_row=None):
        header_paras = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
            "TH", parent=body, fontSize=9, textColor=white, fontName="Helvetica-Bold"
        )) for h in headers]

        data = [header_paras]
        for row in rows:
            data.append([Paragraph(str(cell), ParagraphStyle(
                "TD", parent=body, fontSize=9, leading=12, spaceAfter=1
            )) for cell in row])

        t = Table(data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRAY_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]
        if highlight_row is not None:
            style_cmds.append(("BACKGROUND", (0, highlight_row), (-1, highlight_row), GREEN_BG))
            style_cmds.append(("TEXTCOLOR", (0, highlight_row), (-1, highlight_row), GREEN))
        t.setStyle(TableStyle(style_cmds))
        return t

    # ══════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("QUIC-Based Load Balancing", title_style))
    elements.append(Paragraph("Content-Aware &amp; Self-Adaptive Approaches", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Research Ideas &amp; Feasibility Analysis",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Working Document &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.8*inch))

    # Abstract
    abstract_text = (
        "Can QUIC's protocol features enable a new class of load balancing that is both "
        "<b>content-aware</b> (routing based on application-level signals) and <b>self-adaptive</b> "
        "(automatically rebalancing without external controllers)? This document explores what "
        "information remains visible in encrypted QUIC traffic, how it can be leveraged for "
        "intelligent routing, and how QUIC's native connection migration enables servers to "
        "autonomously redistribute load. We connect these ideas to our working cross-machine "
        "migration implementation."
    )
    abstract_tbl = Table(
        [[Paragraph(abstract_text, ParagraphStyle(
            "Abstract", parent=body, fontSize=9.5, leading=13, textColor=DARK_GRAY,
        ))]],
        colWidths=[5.5*inch],
    )
    abstract_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, MED_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    elements.append(abstract_tbl)
    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # SECTION 1: THE CORE QUESTION
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. The Core Question", h1))
    elements.append(Paragraph(
        "QUIC encrypts nearly all payload data. Traditional load balancers that inspect HTTP "
        "headers, URLs, or cookies cannot operate on QUIC traffic without terminating the connection. "
        "This raises a fundamental question: <b>Is content-aware or self-adaptive load balancing "
        "possible with QUIC, and if so, what information can we use?</b>",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "The answer is yes -- partially without decryption, and fully with QUIC-native mechanisms "
        "that don't require traditional middlebox inspection at all.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # SECTION 2: WHAT'S VISIBLE
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. What Information Remains Visible in QUIC?", h1))

    elements.append(Paragraph("2.1 Always in the Clear (Every Packet)", h2))
    elements.append(Paragraph(
        "These fields are never encrypted and are available for any middlebox to inspect:",
        body
    ))
    elements.append(make_table(
        ["Field", "Location", "What It Reveals", "LB Utility"],
        [
            ["Connection ID", "Short/Long header", "Server-assigned opaque bytes",
             "High -- can encode routing info (QUIC-LB)"],
            ["Spin Bit", "Short header (1 bit)", "RTT measurement signal",
             "Medium -- latency monitoring"],
            ["Version", "Long header", "QUIC version negotiation",
             "Low -- version-based routing rare"],
            ["Packet Type", "Long header", "Initial / Handshake / 0-RTT / 1-RTT",
             "Medium -- connection phase detection"],
            ["Packet Size", "UDP datagram", "Payload size per packet",
             "Medium -- traffic pattern analysis"],
            ["Timing", "Arrival timestamps", "Inter-packet gaps, bursts",
             "Medium -- workload classification"],
        ],
        col_widths=[1.1*inch, 1.1*inch, 1.7*inch, 2.2*inch],
    ))

    elements.append(Paragraph("2.2 Trivially Decryptable (Initial Packets Only)", h2))
    elements.append(Paragraph(
        "QUIC Initial packets are encrypted with keys derived from the Destination Connection ID, "
        "which is sent in the clear. Per RFC 9001, <b>anyone can compute these keys and decrypt "
        "the Initial packet payload</b>. This reveals the TLS ClientHello, which contains:",
        body
    ))

    initial_fields = [
        "<b>SNI (Server Name Indication):</b> The hostname the client wants to connect to. "
        "This is the most useful field for content-aware routing -- enables host-based routing "
        "without connection termination.",
        "<b>ALPN (Application-Layer Protocol Negotiation):</b> Which protocol the client wants "
        "(h3, h3-29, etc.). Enables protocol-based routing.",
        "<b>TLS Extensions:</b> Client capabilities, supported cipher suites, key shares. "
        "Could enable client-type-based routing.",
        "<b>QUIC Transport Parameters:</b> Client's max streams, flow control limits, "
        "migration preferences. Reveals client capacity.",
    ]
    for field in initial_fields:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {field}', bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Warning: Encrypted Client Hello (ECH) is being standardized and will encrypt the SNI. "
        "Once widely deployed, SNI-based routing without termination will no longer be possible. "
        "This makes CID-based and migration-based approaches more future-proof.",
        idea_style
    ))

    elements.append(Paragraph("2.3 NOT Visible (Requires Connection Termination)", h2))
    elements.append(Paragraph(
        "Everything after the handshake is encrypted with keys known only to the endpoints:",
        body
    ))
    not_visible = [
        "HTTP/3 headers (URL path, Host, cookies, Authorization)",
        "Request and response bodies",
        "Stream multiplexing details (which stream carries what)",
        "QPACK-compressed header tables",
        "Application-level error codes and metadata",
    ]
    for item in not_visible:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # SECTION 3: CONTENT-AWARE APPROACHES
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. Content-Aware Load Balancing Approaches", h1))
    elements.append(Paragraph(
        "Content-aware means the LB uses application-level information (not just IP/port) to make "
        "routing decisions. With QUIC, the degree of content awareness depends on how much the LB "
        "is willing to do:",
        body
    ))

    elements.append(make_table(
        ["Approach", "Content Awareness", "Termination?", "Future-Proof (ECH)?", "Complexity"],
        [
            ["CID-encoded routing (QUIC-LB)", "Server identity encoded in CID",
             "No", "Yes", "Low"],
            ["SNI-based routing", "Hostname from ClientHello",
             "No (decrypt Initial)", "No (ECH breaks it)", "Low"],
            ["ALPN-based routing", "Protocol from ClientHello",
             "No (decrypt Initial)", "No (ECH breaks it)", "Low"],
            ["Spin-bit RTT routing", "Per-connection latency",
             "No", "Yes", "Medium"],
            ["Traffic pattern classification", "Inferred workload type",
             "No", "Yes", "High (ML)"],
            ["Full L7 reverse proxy", "Complete HTTP/3 visibility",
             "Yes", "Yes", "High"],
            ["<b>Migration-based (server-side)</b>", "<b>Server has full L7 context</b>",
             "<b>No LB needed</b>", "<b>Yes</b>", "<b>Medium</b>"],
        ],
        col_widths=[1.4*inch, 1.5*inch, 1.0*inch, 1.1*inch, 0.9*inch],
        highlight_row=7,
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Key insight: The server itself has FULL content awareness (it decrypts everything). "
        "If the server makes the routing decision via connection migration, you get content-aware "
        "load balancing without any middlebox inspection. The server IS the content-aware load balancer.",
        highlight_style
    ))

    elements.append(Paragraph("3.1 CID-Based Routing (QUIC-LB)", h2))
    elements.append(Paragraph(
        "The IETF QUIC-LB draft defines a protocol where servers encode their identity into "
        "Connection IDs using a shared secret with the load balancer. The LB extracts the server ID "
        "from the CID to route packets. This is the most mature QUIC-specific LB approach, but it "
        "only routes to the <b>original</b> server -- it cannot move connections.",
        body
    ))
    elements.append(Paragraph(
        "Our research angle: Can CID encoding carry dynamic load signals? Instead of a static "
        "server ID, encode current load level or preferred migration target. The LB could then "
        "route new connections away from overloaded servers based on CID metadata.",
        idea_style
    ))

    elements.append(Paragraph("3.2 SNI + ALPN Routing (Pre-ECH)", h2))
    elements.append(Paragraph(
        "By decrypting the Initial packet (trivial -- keys derived from public DCID), a middlebox "
        "can read the SNI and ALPN. This enables hostname-based and protocol-based routing without "
        "full connection termination. This works today but will be broken by ECH adoption.",
        body
    ))

    elements.append(Paragraph("3.3 Traffic Pattern Analysis", h2))
    elements.append(Paragraph(
        "Even fully encrypted traffic leaks information through packet sizes, timing, and burst "
        "patterns. A classifier could distinguish video streaming (large packets, steady rate), "
        "API calls (small packets, bursty), file downloads (large packets, high throughput), "
        "and interactive sessions (small packets, variable gaps). However, this overlaps with "
        "traffic analysis attacks and has privacy implications.",
        body
    ))

    # ══════════════════════════════════════════
    # SECTION 4: SELF-ADAPTIVE APPROACHES
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. Self-Adaptive Load Balancing via QUIC Migration", h1))

    # ── What is Self-Adaptive? ──
    elements.append(Paragraph("What is Self-Adaptive Load Balancing?", h2))
    elements.append(Paragraph(
        "Traditional load balancing is <b>static</b> or <b>reactive-centralized</b>: a dedicated "
        "load balancer (hardware or software) sits in front of servers and distributes traffic "
        "using fixed rules (round-robin, consistent hashing) or a central controller that "
        "monitors all servers. If the LB fails or makes a bad decision, the entire system suffers.",
        body
    ))
    elements.append(Paragraph(
        "<b>Self-adaptive load balancing</b> is fundamentally different. The system automatically "
        "adjusts to changing conditions without external intervention. Key properties:",
        body
    ))

    self_adaptive_props = [
        "<b>Decentralized decisions:</b> No single component decides where traffic goes. "
        "Each server (or node) makes autonomous decisions based on local observations "
        "(its own CPU, memory, queue depth, latency). No god-view controller.",
        "<b>Feedback-driven:</b> The system continuously monitors its own performance and "
        "adjusts. If a migration makes things worse, the system detects this and corrects. "
        "This is a closed-loop control system, not open-loop.",
        "<b>Emergent global balance:</b> No single node knows the global state, but the "
        "aggregate behavior of all nodes making local decisions produces a globally balanced "
        "system. Similar to how ant colonies find optimal paths without central planning.",
        "<b>Resilient to failures:</b> If a server crashes, its connections are lost but "
        "the remaining servers continue self-balancing. No LB failover needed because there "
        "is no LB.",
        "<b>No bottleneck:</b> Traditional LBs process every packet of every connection. "
        "A self-adaptive system has no such bottleneck -- servers communicate directly with "
        "clients after the initial handshake.",
    ]
    for prop in self_adaptive_props:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {prop}', bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Analogy: Traditional LB is like a traffic cop at an intersection directing every car. "
        "Self-adaptive LB is like a road network where each intersection has sensors and "
        "dynamically adjusts its own traffic lights based on local congestion. No central "
        "traffic control center needed.",
        idea_style
    ))

    elements.append(Paragraph(
        "In the context of QUIC: self-adaptive means servers use the connection migration "
        "primitive (preferred_address) to autonomously redistribute connections. "
        "Each server monitors itself, decides when it's overloaded, picks a target, "
        "and migrates connections -- all without asking permission from a central controller.",
        body
    ))
    elements.append(Spacer(1, 6))

    elements.append(make_table(
        ["Property", "Traditional LB", "Self-Adaptive (QUIC Migration)"],
        [
            ["Decision maker", "Central LB appliance/software",
             "Each server autonomously"],
            ["Failure mode", "LB failure = total outage",
             "Server failure = only its connections lost"],
            ["Scalability", "LB must handle all traffic",
             "Servers handle their own traffic; scales linearly"],
            ["Timing", "At connection establishment only",
             "Anytime during connection lifetime"],
            ["Adaptivity", "Static rules or slow controller updates",
             "Continuous, real-time, feedback-driven"],
            ["Content awareness", "Requires L7 termination at LB",
             "Server has full L7 context natively"],
            ["Infrastructure", "Dedicated LB hardware/software",
             "Just the servers themselves + lightweight coordination"],
        ],
        col_widths=[1.3*inch, 2.2*inch, 2.6*inch],
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph("4.1 The Basic Primitive: Server-Initiated Migration", h2))
    elements.append(Paragraph(
        "Our working implementation already demonstrates the core mechanism:",
        body
    ))
    steps = [
        "Server completes QUIC handshake with client (normal)",
        "Server advertises <b>preferred_address</b> transport parameter pointing to a different machine",
        "Client sends PATH_CHALLENGE to the preferred address",
        "Preferred server (with imported crypto state) responds with PATH_RESPONSE",
        "Client switches to using the preferred address -- migration complete",
        "Total state transferred: <b>445 bytes</b> (TLS secrets, CIDs, client address, version)",
    ]
    for i, step in enumerate(steps, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {step}', bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "This is already proven working with Firefox across separate physical machines. "
        "The question now is: how to build a self-adaptive load balancing system on top of this primitive.",
        highlight_style
    ))

    elements.append(Paragraph("4.2 Idea: Spin-Bit RTT Feedback Loop", h2))
    elements.append(Paragraph(
        "The spin bit (RFC 9312) allows passive RTT measurement by observing bit transitions. "
        "A monitoring system could:",
        body
    ))
    spin_steps = [
        "Continuously observe spin-bit RTT for all active connections",
        "Detect RTT degradation (indicating server overload or network congestion)",
        "Trigger migration of affected connections to servers with better RTT",
        "Verify improvement via post-migration spin-bit measurements",
    ]
    for step in spin_steps:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {step}', bullet_style))
    elements.append(Paragraph(
        "Challenge: Spin bit is a coarse signal (1 sample per RTT). Sufficient for trend detection, "
        "not real-time decisions. Also, servers can disable the spin bit for privacy.",
        body_italic
    ))

    elements.append(Paragraph("4.3 Idea: Server-Autonomous Load Shedding", h2))
    elements.append(Paragraph(
        "Each server independently monitors its own load (CPU, memory, connection count, "
        "response latency percentiles). When load exceeds a threshold:",
        body
    ))
    shed_steps = [
        "Server selects connections to migrate (longest-lived, lowest-priority, or random)",
        "Server queries a coordination service (Redis, etcd) for available migration targets",
        "Server initiates preferred_address migration for selected connections",
        "Target server receives state transfer and handles the migrated connections",
        "No central controller needed -- each server makes autonomous decisions",
    ]
    for step in shed_steps:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {step}', bullet_style))

    elements.append(Paragraph(
        "This is a fully decentralized, self-adaptive load balancing system. Servers act as "
        "autonomous agents that shed load when overwhelmed and absorb load when idle. The only "
        "shared state is a lightweight coordination service for target discovery.",
        idea_style
    ))

    elements.append(Paragraph("4.4 Idea: Hybrid Initial Placement + Migration Rebalancing", h2))
    elements.append(Paragraph(
        "Combine traditional LB for initial placement with migration for ongoing rebalancing:",
        body
    ))

    elements.append(make_table(
        ["Phase", "Mechanism", "Decision Maker", "Content Awareness"],
        [
            ["Initial Connection", "QUIC-LB or SNI-based routing",
             "Load balancer", "Host/protocol level"],
            ["Steady State", "Server monitors own load",
             "Each server autonomously", "Full L7 (server decrypts)"],
            ["Overload Detected", "preferred_address migration",
             "Overloaded server", "Can factor in request type, client priority"],
            ["Post-Migration", "Client talks directly to new server",
             "N/A (direct)", "Full L7 on new server"],
        ],
        col_widths=[1.2*inch, 1.7*inch, 1.5*inch, 1.7*inch],
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "This hybrid approach gives the best of both worlds: fast initial placement from a "
        "lightweight LB, plus ongoing self-adaptive rebalancing without any LB involvement. "
        "The LB only handles the first packet of each connection.",
        body
    ))

    elements.append(Paragraph("4.5 Idea: Geographic Re-Routing via Migration", h2))
    elements.append(Paragraph(
        "Anycast DNS routes the client to the geographically nearest server for a fast TLS handshake "
        "(low latency for the Initial/Handshake exchange). The server then migrates the connection "
        "to a backend that holds the client's data, even if it's in a different region. "
        "The client experiences low handshake latency AND gets routed to the optimal backend.",
        body
    ))

    elements.append(Paragraph("4.6 Idea: Decentralized Coordination via Distributed Redis", h2))
    elements.append(Paragraph(
        "A self-adaptive system needs coordination: servers must discover migration targets and "
        "share load information. A centralized Redis instance works on a single LAN (as in our demo), "
        "but becomes a bottleneck and single point of failure at scale. "
        "<b>Decentralized Redis</b> (or Redis Cluster) eliminates this:",
        body
    ))
    redis_points = [
        "<b>Redis Cluster:</b> Data is sharded across multiple Redis nodes using hash slots. "
        "Each server writes its load metrics to a local shard; overloaded servers query "
        "any shard to find available targets. No single node holds all state.",
        "<b>Gossip-based discovery:</b> Instead of Redis, servers could use a gossip protocol "
        "(like SWIM or Serf) to disseminate load information. Each server maintains a partial "
        "view of cluster health. Fully decentralized -- no coordination service at all.",
        "<b>CRDTs for load state:</b> Conflict-free Replicated Data Types allow servers to "
        "merge load information without consensus. A G-Counter CRDT per server tracks connection "
        "count; servers read neighbors' counters to find migration targets.",
        "<b>DHT-based target lookup:</b> A Distributed Hash Table (like Kademlia) maps "
        "load ranges to server sets. Overloaded servers look up the 'low load' range to find "
        "targets. Fully peer-to-peer, no central registry.",
        "<b>Why this matters:</b> Our current implementation uses a single Redis at 141.217.168.200. "
        "For a production deployment with hundreds of servers, decentralized coordination is "
        "essential. The migration primitive (445 bytes over TCP/HTTP/Redis) stays the same -- "
        "only the target discovery changes.",
    ]
    for item in redis_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    elements.append(Paragraph(
        "Key trade-off: Centralized Redis gives strong consistency (every server sees the same "
        "load picture) but is a bottleneck. Decentralized approaches give eventual consistency "
        "(servers may briefly disagree on who is overloaded) but scale horizontally. "
        "For load balancing, eventual consistency is fine -- a slightly stale load view still "
        "produces good migration decisions.",
        idea_style
    ))

    # ══════════════════════════════════════════
    # SECTION 5: APPLICABILITY BEYOND CDNs
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("5. Applicability: Not Just CDNs", h1))
    elements.append(Paragraph(
        "QUIC-based load balancing is often associated with CDNs and web content delivery because "
        "HTTP/3 (over QUIC) is the primary deployment driver. But the migration primitive is "
        "<b>transport-layer</b> -- it works for <i>any</i> application running over QUIC, not just "
        "web content. Here's where it applies:",
        body
    ))

    elements.append(Paragraph("5.1 Web and CDN (Obvious)", h2))
    elements.append(Paragraph(
        "HTTP/3 web serving, static assets, API endpoints. This is where QUIC is most deployed "
        "today (Google, Cloudflare, Meta). Migration enables mid-request server changes for "
        "long-lived HTTP/3 connections (streaming, SSE, WebTransport).",
        body
    ))

    elements.append(Paragraph("5.2 Real-Time Communication (WebRTC over QUIC)", h2))
    elements.append(Paragraph(
        "WebRTC is moving toward QUIC-based transport (Media over QUIC / MoQ). For video "
        "conferencing and live streaming, migration could move a participant's media relay to "
        "a less-loaded server without dropping the call. The ~1 RTT interruption is acceptable "
        "for non-real-time data channels; for media, it would cause a brief glitch.",
        body
    ))

    elements.append(Paragraph("5.3 Gaming and Interactive Applications", h2))
    elements.append(Paragraph(
        "Game servers using QUIC (e.g., for multiplayer state sync) could migrate players between "
        "game server instances during low-activity moments (loading screens, respawn timers). "
        "This enables dynamic server consolidation: as player count drops, migrate remaining "
        "players to fewer servers and shut down idle ones.",
        body
    ))

    elements.append(Paragraph("5.4 IoT and Edge Computing", h2))
    elements.append(Paragraph(
        "IoT devices with long-lived QUIC connections to edge gateways. When an edge node is "
        "overloaded or needs maintenance, connections migrate to a neighboring edge node. "
        "The IoT device doesn't need to re-authenticate or re-establish state. "
        "This is the scenario described by Puliafito et al. (2022) for edge microservices.",
        body
    ))

    elements.append(Paragraph("5.5 Database and Storage Proxies", h2))
    elements.append(Paragraph(
        "QUIC-based database proxies (emerging area) could migrate client connections between "
        "proxy instances for maintenance or load balancing. The client's prepared statements, "
        "transaction context, and connection state move with the migration. "
        "More speculative, but QUIC's multiplexed streams map well to database connection pooling.",
        body
    ))

    elements.append(Paragraph("5.6 VPN and Tunneling", h2))
    elements.append(Paragraph(
        "QUIC-based VPNs (e.g., MASQUE, WireGuard-over-QUIC proposals) could migrate tunnel "
        "endpoints between VPN servers for load balancing or geographic optimization. "
        "The client's tunnel stays alive across the migration -- no reconnection needed.",
        body
    ))

    elements.append(Paragraph("5.7 Microservice Mesh (gRPC over QUIC)", h2))
    elements.append(Paragraph(
        "gRPC is exploring QUIC transport. In a microservice mesh, long-lived gRPC streams "
        "between services could be migrated when a service instance is scaled down or "
        "redeployed. This is more graceful than connection draining -- the stream continues "
        "on a new instance without the caller retrying.",
        body
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "The common thread: QUIC migration-based LB is useful for ANY application with "
        "long-lived connections where reconnection is expensive (re-auth, state rebuild, "
        "user-visible interruption). The shorter the connection, the less benefit migration "
        "provides over traditional at-connection-time LB. The sweet spot is connections lasting "
        "seconds to hours: streaming, gaming, IoT, gRPC streams, tunnels.",
        highlight_style
    ))

    elements.append(make_table(
        ["Application Domain", "Connection Duration", "Migration Benefit", "Feasibility"],
        [
            ["CDN / Web (short requests)", "Milliseconds", "Low (conn too short)", "Low value"],
            ["HTTP/3 streaming / SSE", "Seconds to hours", "High", "High"],
            ["WebRTC / MoQ", "Minutes to hours", "High (except media glitch)", "Medium"],
            ["Gaming", "Minutes to hours", "High (during low-activity)", "Medium"],
            ["IoT edge", "Hours to days", "Very High", "High"],
            ["Database proxy", "Minutes to hours", "High", "Speculative"],
            ["VPN / tunnel", "Hours to days", "Very High", "Medium"],
            ["gRPC microservice", "Seconds to minutes", "Medium-High", "High"],
        ],
        col_widths=[1.5*inch, 1.3*inch, 1.7*inch, 1.1*inch],
    ))

    # ══════════════════════════════════════════
    # SECTION 6: FEASIBILITY ANALYSIS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Feasibility Analysis", h1))
    elements.append(Paragraph(
        "Based on our working implementation, how practical are these ideas?",
        body
    ))

    elements.append(make_table(
        ["Idea", "Feasibility", "What We've Proven", "What Remains"],
        [
            ["CID-encoded routing", "High (IETF draft exists)",
             "N/A (standard approach)", "Extend CID to carry load signals"],
            ["SNI-based routing", "High (works today)",
             "N/A (well-known technique)", "ECH will break this"],
            ["Spin-bit RTT feedback", "Medium",
             "Spin bit is observable in our pcaps", "Build RTT monitor + migration trigger"],
            ["Server-autonomous shedding", "High",
             "Cross-machine migration works, 445 bytes state",
             "Load monitoring + target selection logic"],
            ["Hybrid LB + migration", "High",
             "Migration works with Firefox, 5 state transfer backends",
             "Integration with QUIC-LB for initial placement"],
            ["Geographic re-routing", "High",
             "Migration works across different machines",
             "Multi-region deployment + latency measurement"],
            ["Traffic pattern ML", "Low-Medium",
             "QUIC-Exfil paper shows ML fails (0-47% F1)",
             "Better features, more training data"],
        ],
        col_widths=[1.3*inch, 0.9*inch, 1.8*inch, 2.1*inch],
    ))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("6.1 What Our Implementation Already Proves", h2))

    proven = [
        "<b>Cross-machine state transfer works:</b> 445 bytes of TLS state transferred via "
        "TCP, Redis, or HTTP between physical machines on the same LAN.",
        "<b>Firefox validates the migration:</b> A real browser (Firefox 151) completes "
        "PATH_CHALLENGE/RESPONSE and continues using the migrated connection.",
        "<b>Multiple transfer backends:</b> 5 backends (TCP push, HTTP pull, Redis KV, "
        "Redis pub/sub, file) with different trade-offs for security, latency, and scalability.",
        "<b>The migration is invisible to clients:</b> Firefox shows the page loaded from "
        "the primary server's URL, completely unaware that a different machine served the response.",
        "<b>Preferred_address is a real mechanism:</b> Not theoretical -- it's in RFC 9000 "
        "Section 9.6 and implemented in production browsers.",
    ]
    for item in proven:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    elements.append(Paragraph("6.2 Overhead Budget", h2))
    elements.append(make_table(
        ["Component", "Cost", "Acceptable for LB?"],
        [
            ["State transfer", "445 bytes, &lt;1ms on LAN",
             "Yes -- negligible vs. connection lifetime"],
            ["PATH_CHALLENGE/RESPONSE", "1 RTT (client to new server)",
             "Yes -- one-time cost per migration"],
            ["Handshake on primary", "1-RTT handshake (normal QUIC)",
             "Yes -- no extra cost"],
            ["Coordination service", "Redis/etcd lookup for target",
             "Yes -- sub-millisecond on LAN"],
            ["Connection interruption", "~1 RTT gap during migration",
             "Acceptable for non-realtime; may affect streaming"],
        ],
        col_widths=[1.4*inch, 2.0*inch, 2.7*inch],
    ))

    # ══════════════════════════════════════════
    # SECTION 7: RESEARCH ROADMAP
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("7. Research Roadmap", h1))
    elements.append(Paragraph(
        "Building from our current implementation toward a complete self-adaptive LB system:",
        body
    ))

    roadmap = [
        ("<b>Phase 1 (Done):</b> Cross-machine QUIC server migration with Firefox validation. "
         "Five state transfer backends. Comprehensive benchmarking."),
        ("<b>Phase 2 (Next):</b> Add load monitoring to our Neqo servers. Implement a simple "
         "threshold-based migration trigger (e.g., migrate when CPU > 80% or connection count > N)."),
        ("<b>Phase 3:</b> Build a coordination service for target discovery. Servers register "
         "their available capacity; overloaded servers query for migration targets."),
        ("<b>Phase 4:</b> Integrate with QUIC-LB for initial connection placement. The LB "
         "handles the first packet; servers handle rebalancing via migration."),
        ("<b>Phase 5:</b> Multi-connection migration. Currently limited to preferred_address "
         "(one migration per handshake). Explore NEW_CONNECTION_ID-based migration for "
         "re-migration of already-migrated connections."),
        ("<b>Phase 6:</b> Evaluate at scale. How many simultaneous migrations can the system "
         "sustain? What's the convergence time for a sudden load spike?"),
    ]
    for item in roadmap:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 8: OPEN QUESTIONS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("8. Open Questions", h1))

    questions = [
        "Can preferred_address migration happen more than once per connection? RFC 9000 says "
        "one preferred_address per handshake, but NEW_CONNECTION_ID might enable subsequent "
        "migrations. No implementation supports this yet.",

        "How does ECH (Encrypted Client Hello) affect QUIC load balancing? Once SNI is "
        "encrypted, CID-based and migration-based approaches become the only options for "
        "content-aware routing without termination.",

        "What's the right migration trigger? CPU utilization? Queue depth? Tail latency "
        "(p99)? Connection count? Some combination? This is an empirical question.",

        "Can migration-based LB coexist with QUIC-LB? The migrated server needs to generate "
        "CIDs compatible with the LB's decoding scheme. Possible but requires coordination.",

        "Security: The 445-byte state includes TLS secrets. How to secure the transfer? "
        "Our analysis shows Redis KV (encrypted) for scalability, HTTP Pull for "
        "secrets-never-leave-memory guarantees.",

        "Client behavior variance: Different QUIC stacks handle preferred_address differently. "
        "Firefox sends multiple PATH_CHALLENGEs; Chrome may behave differently. "
        "How robust is migration-based LB across client implementations?",

        "Oscillation: If two servers are both near the overload threshold, they might "
        "continuously migrate connections back and forth. Need dampening or hysteresis.",

        "Fairness: Which connections get migrated? Random selection is fair but may disrupt "
        "latency-sensitive connections. Priority-based selection requires classification.",
    ]
    for q in questions:
        elements.append(Paragraph(
            q, question_style
        ))

    # ══════════════════════════════════════════
    # SECTION 9: BOTTOM LINE
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("9. Bottom Line", h1))
    elements.append(Paragraph(
        "QUIC-based load balancing is not only possible -- it enables a fundamentally new approach "
        "that traditional TCP load balancing cannot achieve:",
        body
    ))
    elements.append(Spacer(1, 4))

    bottom_line = [
        "<b>Content-aware without middlebox inspection:</b> The server has full L7 visibility "
        "and makes routing decisions via migration. No middlebox needs to decrypt anything.",

        "<b>Self-adaptive without central controllers:</b> Each server autonomously monitors "
        "its load and migrates connections when overwhelmed. Coordination is lightweight "
        "(just target discovery).",

        "<b>Mid-connection rebalancing:</b> Unlike every other LB system that pins connections "
        "at establishment, QUIC migration can move established connections. This is unique "
        "in the entire load balancing taxonomy.",

        "<b>LB bottleneck elimination:</b> The LB only handles initial packets. Post-migration, "
        "clients communicate directly with backends. The LB is no longer in the data path.",

        "<b>We have the working primitive:</b> Our cross-machine migration implementation "
        "proves this is not theoretical. The remaining work is building the control plane "
        "(load monitoring, target selection, coordination) on top of the proven data plane.",
    ]
    for item in bottom_line:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    # Build
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

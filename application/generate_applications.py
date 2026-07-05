#!/usr/bin/env python3
"""Generate Applications of QUIC Server-Side Migration PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import date

OUTPUT = "APPLICATION_ANALYSIS.pdf"

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
RED_BG = HexColor("#fff5f5")


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
        borderWidth=0, borderPadding=0,
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
    sub_bullet = ParagraphStyle(
        "SubBullet", parent=body,
        leftIndent=40, bulletIndent=26,
        spaceBefore=1, spaceAfter=1, fontSize=9, leading=12,
    )
    ref_style = ParagraphStyle(
        "Ref", parent=body,
        fontSize=9, leading=12,
        leftIndent=14, spaceAfter=3,
        textColor=HexColor("#4a5568"),
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
    warning_style = ParagraphStyle(
        "Warning", parent=body,
        fontSize=10, leading=14,
        backColor=ORANGE_BG, borderColor=ORANGE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ORANGE,
        fontName="Helvetica-Bold",
    )
    negative_style = ParagraphStyle(
        "Negative", parent=body,
        fontSize=10, leading=14,
        backColor=RED_BG, borderColor=ACCENT,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ACCENT,
        fontName="Helvetica-Bold",
    )

    elements = []

    # ── Helper for tables ──
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
    elements.append(Spacer(1, 1.2*inch))
    elements.append(Paragraph("Applications of QUIC", title_style))
    elements.append(Paragraph("Server-Side Connection Migration", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "IPFS, DNS+Anycast, Load Balancing, Health-Checked Migration, and BitTorrent",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Research Application Analysis &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.6*inch))

    # Abstract
    abstract_text = (
        "This document analyzes five potential applications of QUIC server-side connection migration "
        "(RFC 9000, Section 9.6): (1) integration with IPFS for seamless peer failover, "
        "(2) DNS+Anycast hybrid routing with post-connection optimization, "
        "(3) QUIC-native load balancing at L3/L4/L7 layers, "
        "(4) health-checked migration with pre-validation of preferred servers, and "
        "(5) BitTorrent peer migration for seeder failover and WebSeed load distribution. "
        "For each application, we provide technical feasibility analysis, identify challenges, "
        "and propose proof-of-concept experiments that can be conducted on our existing four-machine testbed. "
        "We conclude that <b>health-checked load balancing</b> is the most immediately viable application, "
        "while <b>IPFS integration</b> and <b>BitTorrent peer migration</b> present the most novel "
        "research contributions."
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
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("Contents", h1))
    toc_items = [
        "1. Background: Our Server-Side Migration Implementation",
        "2. Application 1: IPFS + QUIC Server Migration",
        "    2.1 How IPFS Uses QUIC Today",
        "    2.2 Can IPFS Use Server-Side Migration?",
        "    2.3 Technical Feasibility Analysis",
        "    2.4 Challenges and Limitations",
        "    2.5 Proposed Experiment",
        "3. Application 2: DNS + Anycast Hybrid Routing",
        "    3.1 The Anycast Problem with Stateful Protocols",
        "    3.2 How Server Migration Solves It",
        "    3.3 Proposed Experiment",
        "4. Application 3: QUIC-Native Load Balancing (L3/L4/L7)",
        "    4.1 Traditional Load Balancing Layers",
        "    4.2 QUIC Migration as a Load Balancer",
        "    4.3 Comparison with Existing Approaches",
        "    4.4 Proposed Experiment",
        "5. Application 4: Health-Checked Migration",
        "    5.1 The Problem: Migrating to a Dead Server",
        "    5.2 Health Check Design",
        "    5.3 Implementation Plan",
        "    5.4 Proposed Experiment",
        "6. Application 5: BitTorrent Peer Migration",
        "    6.1 BitTorrent Architecture and Transport",
        "    6.2 How QUIC Server Migration Applies",
        "    6.3 Three Migration Scenarios",
        "    6.4 Comparison with IPFS Migration",
        "    6.5 Challenges",
        "    6.6 Proposed Experiment",
        "7. Comparative Analysis of All Applications",
        "8. Recommended Research Roadmap",
        "9. References",
    ]
    for item in toc_items:
        indent = 20 if item.startswith("    ") else 0
        elements.append(Paragraph(
            item.strip(),
            ParagraphStyle("TOC", parent=body, fontSize=10, leftIndent=indent, spaceAfter=2)
        ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # SECTION 1: BACKGROUND
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. Background: Our Server-Side Migration Implementation", h1))
    elements.append(Paragraph(
        "We have a working cross-machine QUIC server-side migration implementation using Mozilla's "
        "Neqo (Rust). The system operates on a four-machine LAN testbed:",
        body
    ))
    elements.append(make_table(
        ["Role", "Machine", "IP Address", "Function"],
        [
            ["Client", "optiplex7010", "141.217.168.127", "Firefox browser (HTTP/3)"],
            ["Primary Server", "opti7040", "141.217.168.152", "Completes TLS handshake, exports state"],
            ["Preferred Server", "homeserver2", "141.217.168.143", "Imports state, handles PATH_CHALLENGE"],
            ["Redis Server", "Proxmox VM", "141.217.168.200", "State transfer coordination"],
        ],
        col_widths=[1.1*inch, 1.2*inch, 1.3*inch, 2.5*inch],
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "The migration transfers 445 bytes of state (TLS secrets, Connection IDs, client address, "
        "packet numbers) from the primary to the preferred server. We support five state transfer "
        "backends: TCP Push, HTTP Pull, Redis KV, Redis Pub/Sub, and File. The system has been "
        "verified with Firefox 151.0.3 performing real HTTP/3 page loads with transparent migration.",
        body
    ))

    # ══════════════════════════════════════════
    # SECTION 2: IPFS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("2. Application 1: IPFS + QUIC Server Migration", h1))

    elements.append(Paragraph("2.1 How IPFS Uses QUIC Today", h2))
    elements.append(Paragraph(
        "The InterPlanetary File System (IPFS) is a peer-to-peer content-addressed storage network. "
        "Since 2022, QUIC has become the <b>default transport</b> in IPFS via the libp2p networking stack. "
        "Key facts about IPFS's QUIC usage:",
        body
    ))
    bullets = [
        "<b>libp2p transport:</b> IPFS uses libp2p, which supports QUIC via the go-libp2p-quic-transport "
        "module (using quic-go) or rust-libp2p (using quinn). QUIC replaced TCP+Noise as the default "
        "transport in Kubo v0.18+ (2023).",
        "<b>Peer identity:</b> Every IPFS node has a PeerID derived from its cryptographic public key. "
        "libp2p uses TLS 1.3 over QUIC with peer authentication via the libp2p TLS extension "
        "(inserting the peer's public key into the TLS certificate).",
        "<b>Content routing:</b> Content is identified by CIDs (Content Identifiers). Clients discover "
        "which peers hold content via the Kademlia DHT, IPNI (InterPlanetary Network Indexer), or "
        "Bitswap protocol.",
        "<b>Multiple providers:</b> The same CID can be served by <b>many different peers</b>. This is "
        "fundamental to IPFS's design -- content is replicated across the network.",
        "<b>Connection multiplexing:</b> A single QUIC connection to a peer can carry multiple streams "
        "(Bitswap blocks, DHT queries, pubsub messages). Losing a connection means losing all "
        "in-progress streams to that peer.",
    ]
    for b in bullets:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {b}', bullet_style))

    elements.append(Paragraph("2.2 Can IPFS Use Server-Side Migration? -- Verdict: YES, with caveats", h2))
    elements.append(Paragraph(
        "The question is whether an IPFS node (acting as a content server) can use QUIC's "
        "preferred_address mechanism to redirect a client to a different IPFS node that also holds "
        "the requested content. We analyze this along three dimensions:",
        body
    ))

    elements.append(Paragraph("Scenario A: IPFS Gateway Migration (Most Feasible)", h3))
    elements.append(Paragraph(
        "IPFS gateways (e.g., ipfs.io, dweb.link, Cloudflare IPFS) are centralized HTTP frontends "
        "that serve IPFS content to regular web browsers. These gateways are increasingly serving "
        "content over HTTP/3 (QUIC). In this scenario:",
        body
    ))
    gateway_points = [
        "A gateway cluster operates multiple backend nodes, all of which can resolve any CID.",
        "The primary gateway completes the QUIC handshake and resolves the client's CID request.",
        "If the primary is overloaded, it migrates the connection to a less-loaded gateway backend.",
        "The preferred gateway imports the TLS state and continues serving the content.",
        "This is <b>directly analogous</b> to our current implementation -- the IPFS gateway acts "
        "as the primary server, and another gateway instance acts as the preferred server.",
    ]
    for p in gateway_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))
    elements.append(Paragraph(
        "Feasibility: HIGH. IPFS gateways are controlled infrastructure with known topology. "
        "Content availability is guaranteed (gateways can fetch any CID). This is essentially "
        "load balancing for IPFS gateways using QUIC migration instead of traditional L4/L7 LBs.",
        highlight_style
    ))

    elements.append(Paragraph("Scenario B: Peer-to-Peer Content Provider Migration (Novel but Challenging)", h3))
    elements.append(Paragraph(
        "In pure peer-to-peer IPFS, a node serving content could migrate the client to another "
        "peer that also holds the same CID. This is the most novel application:",
        body
    ))
    p2p_points = [
        "<b>Content-addressed advantage:</b> Because IPFS uses CIDs, the client can verify that "
        "the content received from the new peer is identical to what it would have received from "
        "the original peer. Data integrity is guaranteed regardless of which peer serves it.",
        "<b>Provider discovery:</b> The serving peer can query the DHT to find other providers of "
        "the same CID and select one as the preferred_address target.",
        "<b>Peer identity challenge:</b> libp2p binds QUIC connections to PeerIDs via TLS certificates. "
        "Migrating to a different peer means the TLS identity changes. The libp2p TLS extension "
        "authenticates the peer's identity during the handshake -- a migration would need to either "
        "(a) share the private key (unacceptable), (b) re-authenticate (breaks QUIC migration model), "
        "or (c) separate transport identity from content identity.",
        "<b>Stream state:</b> If multiple Bitswap streams are active on the connection, migrating "
        "mid-transfer requires the preferred peer to understand the Bitswap protocol state for all "
        "active streams -- significantly more complex than our current 445-byte migration state.",
    ]
    for p in p2p_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))
    elements.append(Paragraph(
        "Feasibility: MEDIUM. The peer identity problem is the fundamental challenge. A solution "
        "would require changes to libp2p's authentication model to decouple transport-layer identity "
        "from application-layer content verification.",
        warning_style
    ))

    elements.append(Paragraph("Scenario C: IPFS Cluster Node Failover (Practical)", h3))
    elements.append(Paragraph(
        "IPFS Cluster is a tool for orchestrating pinning across multiple IPFS nodes. In this "
        "scenario, all nodes in the cluster share a cluster identity and pin the same content. "
        "Server-side migration between cluster nodes is highly practical:",
        body
    ))
    cluster_points = [
        "Cluster nodes can share TLS certificates (same organizational identity).",
        "All cluster nodes pin the same CIDs -- content availability is guaranteed.",
        "The cluster leader can coordinate migrations based on node health and load.",
        "This is operationally similar to our current four-machine testbed.",
    ]
    for p in cluster_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))
    elements.append(Paragraph(
        "Feasibility: HIGH. IPFS Cluster already has shared identity and content replication. "
        "Adding QUIC server migration is a natural extension for zero-downtime node maintenance "
        "and load redistribution within a cluster.",
        highlight_style
    ))

    elements.append(Paragraph("2.3 Technical Feasibility Analysis", h2))
    elements.append(make_table(
        ["Aspect", "Gateway Migration", "P2P Migration", "Cluster Failover"],
        [
            ["TLS Identity", "Same cert (gateway operator)", "Different PeerIDs (HARD)", "Shared cluster cert"],
            ["Content Availability", "Gateway fetches any CID", "Must verify via DHT", "Same pinset"],
            ["State Transfer", "445 bytes (same as ours)", "445 + Bitswap state", "445 bytes"],
            ["QUIC Implementation", "quic-go (Go) or quinn (Rust)", "Same", "Same"],
            ["Client Modification", "None (browser HTTP/3)", "libp2p client changes", "None"],
            ["Deployment Control", "Centralized", "Decentralized (hard)", "Semi-centralized"],
            ["Research Novelty", "Low (standard LB)", "<b>High (new paradigm)</b>", "Medium"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.6*inch, 1.6*inch],
    ))

    elements.append(Paragraph("2.4 Challenges and Limitations", h2))
    challenges = [
        "<b>libp2p's QUIC implementation:</b> libp2p uses quic-go, which does not currently expose "
        "the preferred_address transport parameter API. Implementing migration would require modifying "
        "quic-go to support preferred_address (similar to how we modified Neqo).",
        "<b>Peer authentication model:</b> libp2p's security model ties the QUIC connection to a "
        "specific PeerID. The libp2p TLS handshake extension (draft-ietf-libp2p-tls) embeds the "
        "peer's public key in the TLS certificate. Migration to a different peer's key would require "
        "a new security model.",
        "<b>NAT traversal:</b> IPFS peers are often behind NATs. The preferred_address must be a "
        "publicly reachable address, which may not be available for all peers. IPFS uses hole-punching "
        "(DCUtR protocol) for NAT traversal, but this is incompatible with preferred_address which "
        "requires a fixed, reachable address.",
        "<b>Content verification after migration:</b> After migration to a new peer, the client "
        "should verify it is receiving the correct CID. For Bitswap, this is built-in (every block "
        "is verified against its CID hash). For HTTP gateway access, standard HTTP caching mechanisms apply.",
    ]
    for c in challenges:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {c}', bullet_style))

    elements.append(Paragraph("2.5 Proposed Experiment: IPFS Gateway Migration PoC", h2))
    elements.append(Paragraph(
        "We can demonstrate IPFS gateway migration on our existing testbed with minimal modifications:",
        body
    ))
    exp_steps = [
        "<b>Setup:</b> Run two IPFS gateway instances (Kubo) on opti7040 (primary) and homeserver2 "
        "(preferred). Both pin the same test CID.",
        "<b>Modification:</b> Wrap the IPFS gateway HTTP handler behind our Neqo-based QUIC server. "
        "The primary completes the QUIC/TLS handshake, then proxies the HTTP request to the local "
        "Kubo gateway API. Upon migration, the preferred server does the same with its local Kubo instance.",
        "<b>Alternative (simpler):</b> Use our existing migration infrastructure as-is, but serve "
        "IPFS content via the HTTP/3 response body. The primary fetches the CID content from its "
        "local Kubo node and includes it in the HTTP response. This proves the concept without "
        "modifying IPFS internals.",
        "<b>Measurement:</b> Compare latency of (a) standard IPFS gateway, (b) IPFS gateway behind "
        "L4 LB (HAProxy), (c) IPFS gateway with QUIC migration. Measure time-to-first-byte, "
        "total transfer time, and migration overhead.",
    ]
    for i, s in enumerate(exp_steps, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {s}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 3: DNS + ANYCAST
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Application 2: DNS + Anycast Hybrid Routing", h1))

    elements.append(Paragraph("3.1 The Anycast Problem with Stateful Protocols", h2))
    elements.append(Paragraph(
        "<b>Anycast</b> is a network addressing technique where the same IP address is advertised "
        "from multiple locations via BGP. The network routes each client to the \"nearest\" server "
        "(based on BGP path metrics, not geographic distance). Anycast is widely used for DNS "
        "(all 13 root name server addresses are anycast) and CDNs (Cloudflare, Google).",
        body
    ))
    elements.append(Paragraph(
        "The fundamental problem with anycast and stateful protocols (TCP, QUIC):",
        body
    ))
    anycast_problems = [
        "<b>BGP route flapping:</b> When BGP routes change (link failure, policy update, route "
        "withdrawal), subsequent packets from the same client may be routed to a <i>different</i> "
        "anycast instance. The new instance has no connection state -- the connection breaks.",
        "<b>ECMP hash changes:</b> Even within a stable anycast setup, ECMP hashing at intermediate "
        "routers can shift flows between paths. If paths lead to different anycast instances, "
        "connections break.",
        "<b>QUIC makes this worse:</b> QUIC's encrypted headers mean intermediate routers cannot "
        "even inspect Connection IDs for consistent routing. Only the initial packet's 5-tuple "
        "is reliably usable for ECMP hashing.",
        "<b>Current mitigation:</b> Anycast operators use long BGP hold timers, prepend paths to "
        "reduce flapping, and accept that some connections will break. Google's Espresso system "
        "uses software-defined anycast with fine-grained traffic engineering to minimize disruption.",
    ]
    for p in anycast_problems:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("3.2 How Server Migration Solves It: The Anycast+Migration Architecture", h2))
    elements.append(Paragraph(
        "QUIC server-side migration enables a powerful two-phase routing architecture that combines "
        "the simplicity of anycast with the reliability of direct connections:",
        body
    ))

    elements.append(Paragraph("Phase 1: Anycast-Routed Handshake (Fast)", h3))
    phase1 = [
        "Client sends QUIC Initial packet to anycast VIP (e.g., 192.0.2.1).",
        "BGP routes the packet to the nearest anycast PoP (Point of Presence).",
        "The PoP server completes the TLS 1.3 handshake (1-RTT or 0-RTT).",
        "The handshake is fast because the PoP is geographically close to the client.",
        "During the handshake, the server includes preferred_address in its transport parameters, "
        "pointing to the <b>unicast IP</b> of the optimal backend server.",
    ]
    for i, p in enumerate(phase1, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {p}', bullet_style))

    elements.append(Paragraph("Phase 2: Unicast-Routed Data Transfer (Reliable)", h3))
    phase2 = [
        "The client validates the preferred_address via PATH_CHALLENGE/PATH_RESPONSE.",
        "After validation, the client switches to the unicast address of the backend server.",
        "All subsequent data flows directly between client and backend -- no anycast routing.",
        "BGP route changes no longer affect the connection (it's on a stable unicast path).",
        "The backend may be in a different region than the PoP (e.g., where the client's data lives).",
    ]
    for i, p in enumerate(phase2, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {p}', bullet_style))

    elements.append(Paragraph(
        "Key insight: Anycast is used only for the initial handshake (1 RTT). The connection then "
        "migrates to a stable unicast address, immune to BGP changes. This gives the best of both "
        "worlds: low-latency connection establishment AND stable long-lived connections.",
        highlight_style
    ))

    elements.append(Paragraph("DNS + Anycast Combined Flow", h3))
    elements.append(Paragraph(
        "The full flow combining DNS and anycast with server migration:",
        body
    ))
    full_flow = [
        "<b>DNS Resolution:</b> Client resolves example.com. DNS returns an anycast VIP based on "
        "geographic proximity (GeoDNS or anycast DNS itself). This provides coarse-grained routing.",
        "<b>Anycast Handshake:</b> Client connects to the anycast VIP. BGP routes to nearest PoP. "
        "PoP server selects the optimal backend based on: (a) client's actual IP (more precise than "
        "DNS-based geolocation), (b) current backend load, (c) data locality.",
        "<b>QUIC Migration:</b> PoP server sends preferred_address pointing to the selected backend's "
        "unicast IP. The 445-byte migration state is transferred to the backend.",
        "<b>Direct Connection:</b> Client migrates to backend. All subsequent traffic bypasses both "
        "DNS and anycast routing. Connection is stable for its entire lifetime.",
    ]
    for i, f in enumerate(full_flow, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {f}', bullet_style))

    elements.append(Paragraph(
        "This architecture is particularly valuable for: (a) long-lived connections (WebSocket, gRPC "
        "streaming, real-time collaboration), (b) mobile clients whose apparent location may differ "
        "from optimal server, and (c) services where data locality matters (database access, "
        "personalized content).",
        body_italic
    ))

    elements.append(Paragraph("3.3 Proposed Experiment: Simulated Anycast + Migration", h2))
    elements.append(Paragraph(
        "While we cannot deploy real BGP anycast on our LAN, we can simulate the architecture:",
        body
    ))
    dns_exp = [
        "<b>DNS simulation:</b> Run a local DNS server (dnsmasq) that returns different IPs for "
        "the same domain based on client source IP. This simulates GeoDNS.",
        "<b>Anycast simulation:</b> Use iptables DNAT rules to redirect traffic from a shared VIP "
        "to the primary server. This simulates anycast routing to the nearest PoP.",
        "<b>Migration:</b> Primary server (simulated PoP) completes handshake and migrates to "
        "preferred server (simulated backend). Use our existing infrastructure.",
        "<b>Route flap simulation:</b> Mid-connection, change the iptables DNAT rule to point the "
        "VIP to a different server. Show that the migrated connection survives because it's on "
        "a unicast path, while a non-migrated connection breaks.",
        "<b>Measurement:</b> (a) Connection survival rate under simulated BGP flaps, (b) latency "
        "overhead of the migration phase, (c) comparison with static unicast assignment.",
    ]
    for i, s in enumerate(dns_exp, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {s}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 4: LOAD BALANCING
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. Application 3: QUIC-Native Load Balancing (L3/L4/L7)", h1))

    elements.append(Paragraph("4.1 Traditional Load Balancing Layers", h2))
    elements.append(Paragraph(
        "Load balancers operate at different network layers, each with distinct capabilities "
        "and limitations. Understanding where QUIC server migration fits requires comparing across "
        "all three major layers:",
        body
    ))

    elements.append(make_table(
        ["Aspect", "L3 (Network)", "L4 (Transport)", "L7 (Application)"],
        [
            ["Inspects", "IP headers only", "IP + TCP/UDP ports", "Full HTTP request (URL, headers, cookies)"],
            ["Decision Basis", "Dest IP, ECMP hash", "5-tuple hash or conn table", "Request content, session affinity"],
            ["State", "Stateless (per-packet)", "Per-connection (flow table)", "Per-request or per-session"],
            ["Throughput", "Line-rate (hardware)", "10-40M pps (software)", "100K-1M rps (software)"],
            ["Can Route QUIC?", "Yes (IP-level)", "Partial (encrypted headers)", "Requires TLS termination"],
            ["Examples", "ECMP, Anycast, BGP", "Maglev, Katran, IPVS", "NGINX, HAProxy, Envoy"],
            ["QUIC Challenge", "No connection awareness", "Cannot read QUIC CIDs<br/>(encrypted after handshake)",
             "Must terminate QUIC,<br/>breaking end-to-end encryption"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.6*inch, 1.6*inch],
    ))

    elements.append(Paragraph("4.2 QUIC Migration as a Load Balancer", h2))
    elements.append(Paragraph(
        "QUIC server-side migration introduces a fundamentally new load balancing paradigm that "
        "doesn't fit cleanly into any existing layer. We call it <b>L4.5 Server-Initiated Load "
        "Balancing</b>:",
        body
    ))

    elements.append(Paragraph("How It Works as a Load Balancer", h3))
    lb_flow = [
        "<b>Frontend tier (thin):</b> A set of frontend servers (or a single entry point) handles "
        "QUIC handshakes. These are lightweight -- they only need to complete the TLS handshake and "
        "decide which backend should serve this connection.",
        "<b>Backend selection:</b> The frontend selects a backend based on any policy: round-robin, "
        "least-connections, consistent hashing, resource-aware (CPU/memory/GPU utilization), or even "
        "application-level logic (user affinity, data locality).",
        "<b>State transfer:</b> The frontend exports the 445-byte migration state (TLS secrets, CIDs) "
        "and sends it to the selected backend via any of our five backends (TCP, HTTP, Redis KV, "
        "Redis Pub/Sub, File).",
        "<b>Transparent migration:</b> The client validates the new path and switches to the backend. "
        "From this point, all traffic flows directly client-to-backend. The frontend is completely "
        "out of the data path.",
        "<b>Post-migration:</b> The frontend can handle new handshakes immediately. It never becomes "
        "a bottleneck because it only processes the handshake (1 RTT) per connection.",
    ]
    for i, l in enumerate(lb_flow, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {l}', bullet_style))

    elements.append(Paragraph("Advantages Over Traditional Load Balancers", h3))
    advantages = [
        "<b>No hairpinning:</b> Traditional L4/L7 LBs sit in the data path for the entire "
        "connection lifetime. Every packet goes Client -> LB -> Backend -> LB -> Client. With QUIC "
        "migration, post-handshake traffic is direct: Client -> Backend. This eliminates the LB as "
        "a bandwidth bottleneck and reduces latency.",
        "<b>No TLS termination at the LB:</b> L7 LBs (NGINX, Envoy) must terminate TLS to inspect "
        "HTTP headers, breaking end-to-end encryption. QUIC migration preserves the original TLS "
        "session -- the LB never sees plaintext application data.",
        "<b>Elastic scaling:</b> The frontend only needs to handle handshake load (1 RTT per conn), "
        "not data transfer load. A single frontend can dispatch connections to hundreds of backends. "
        "Adding backends requires no LB reconfiguration -- just add the new backend's address to "
        "the selection pool.",
        "<b>No connection table:</b> Unlike Maglev (stateful L4 LB), the frontend doesn't need to "
        "maintain a per-connection flow table after migration. This makes it immune to state "
        "exhaustion attacks (SYN floods).",
        "<b>Application-aware routing without L7 overhead:</b> The frontend can inspect the initial "
        "HTTP/3 request (since it terminates TLS for the handshake) and make L7-quality routing "
        "decisions, but then get out of the data path. This gives L7 intelligence with L4 efficiency.",
    ]
    for a in advantages:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {a}', bullet_style))

    elements.append(Paragraph("Limitations", h3))
    limitations = [
        "<b>One-shot migration:</b> RFC 9000 allows only one preferred_address per handshake. "
        "Once a connection is migrated to a backend, it cannot be migrated again to another backend "
        "using this mechanism. Re-balancing requires connection termination and re-establishment.",
        "<b>Migration latency:</b> The migration adds one PATH_CHALLENGE/PATH_RESPONSE round trip "
        "(~1 RTT) between the client and the preferred server. For LAN deployments this is sub-millisecond; "
        "for WAN it could be 10-100ms.",
        "<b>Client support:</b> Not all QUIC clients support preferred_address. Firefox does "
        "(confirmed in our tests), but Chrome's QUIC implementation (Chromium QUIC) currently "
        "ignores preferred_address.",
        "<b>No mid-connection rebalancing:</b> If a backend becomes overloaded after migration, "
        "the LB cannot re-migrate that connection. Traditional L4 LBs can at least rate-limit at "
        "the LB level.",
    ]
    for l in limitations:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {l}', bullet_style))

    elements.append(Paragraph("4.3 Comparison with Existing Approaches", h2))
    elements.append(make_table(
        ["Feature", "Maglev (L4)", "Envoy (L7)", "QUIC-LB", "QUIC Migration LB"],
        [
            ["LB in data path?", "Yes (always)", "Yes (always)", "Yes (always)", "<b>No (handshake only)</b>"],
            ["TLS termination?", "No (pass-through)", "Yes (re-encrypt)", "No", "<b>Handshake only</b>"],
            ["Sees plaintext?", "No", "Yes", "No", "<b>Handshake only</b>"],
            ["Per-conn state at LB?", "Yes (flow table)", "Yes (session)", "No (CID-based)", "<b>No (after migration)</b>"],
            ["Backend selection", "At SYN time", "Per-request", "At Initial", "<b>At handshake, with L7 info</b>"],
            ["Can move backend?", "No", "Per-request only", "No", "<b>Yes (once)</b>"],
            ["Bandwidth bottleneck?", "LB throughput", "LB throughput", "LB throughput", "<b>None (direct path)</b>"],
            ["Client changes?", "None", "None", "CID encoding", "<b>None (RFC 9000 standard)</b>"],
        ],
        col_widths=[1.3*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.5*inch],
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "QUIC server migration acts as a \"fire-and-forget\" load balancer: it makes one high-quality "
        "routing decision during the handshake, then steps out of the data path entirely. This is "
        "similar to DNS-based load balancing (which also steps out of the data path after resolution) "
        "but with much finer granularity and without DNS caching issues.",
        highlight_style
    ))

    elements.append(Paragraph("4.4 Proposed Experiment: Migration Load Balancer PoC", h2))
    lb_exp = [
        "<b>Setup:</b> Primary server (opti7040) acts as the \"LB frontend.\" Preferred server "
        "(homeserver2) acts as \"backend.\" We add a second preferred server (or reuse Redis VM) as "
        "a second backend.",
        "<b>Load balancing policy:</b> Implement round-robin or least-connections selection on the "
        "primary. The primary selects which backend to migrate each new connection to.",
        "<b>Workload:</b> Generate multiple concurrent HTTP/3 connections from the client machine "
        "using wrk or h2load with HTTP/3 support. Each connection requests a CPU-intensive response "
        "(e.g., compute Pi to N digits).",
        "<b>Measurements:</b> (a) Request distribution across backends (verify balancing), "
        "(b) throughput vs. single-server baseline, (c) migration overhead per connection, "
        "(d) frontend CPU utilization (should be minimal after handshakes).",
        "<b>Comparison:</b> Run the same workload through HAProxy (L4 mode) and HAProxy (L7 mode). "
        "Compare bandwidth at the LB, end-to-end latency, and maximum concurrent connections.",
    ]
    for i, s in enumerate(lb_exp, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {s}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 5: HEALTH-CHECKED MIGRATION
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("5. Application 4: Health-Checked Migration", h1))

    elements.append(Paragraph("5.1 The Problem: Migrating to a Dead Server", h2))
    elements.append(Paragraph(
        "In our current implementation, the primary server unconditionally includes the "
        "preferred_address in its transport parameters during the TLS handshake. If the preferred "
        "server is unreachable (crashed, network partition, overloaded), the client will attempt "
        "PATH_CHALLENGE to the preferred address, receive no PATH_RESPONSE, and eventually fall "
        "back to the primary. This causes:",
        body
    ))
    problems = [
        "<b>User-visible latency:</b> The client waits for PATH_CHALLENGE timeout before falling "
        "back to the primary. RFC 9000 specifies a probe timeout (PTO) which can be several "
        "hundred milliseconds to seconds.",
        "<b>Wasted resources:</b> The primary exported and transmitted the migration state (445 bytes) "
        "for nothing. Under high load, this wastes CPU cycles on serialization and network bandwidth.",
        "<b>Connection instability:</b> During the probe period, the client may attempt to use the "
        "preferred address for data, leading to packet loss and retransmissions.",
        "<b>No graceful degradation:</b> There is no mechanism to inform the client that migration "
        "failed -- the client must discover this through timeout.",
    ]
    for p in problems:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("5.2 Health Check Design", h2))
    elements.append(Paragraph(
        "We propose a <b>pre-migration health check</b> mechanism where the primary server verifies "
        "the preferred server's availability before including preferred_address in the handshake. "
        "Three approaches, ordered by increasing sophistication:",
        body
    ))

    elements.append(Paragraph("Approach 1: Passive Health Check (Heartbeat)", h3))
    elements.append(Paragraph(
        "The preferred server periodically sends heartbeat messages to the primary (or to a shared "
        "coordination service like Redis). The primary only includes preferred_address if a heartbeat "
        "was received within the last N seconds.",
        body
    ))
    heartbeat_points = [
        "<b>Implementation:</b> Preferred server publishes a heartbeat to Redis every 1 second "
        "(SET preferred:health \"alive\" EX 3). Primary checks this key before each handshake.",
        "<b>Pros:</b> Simple, low overhead, works with all state transfer backends.",
        "<b>Cons:</b> Stale information -- preferred could crash between heartbeat and migration. "
        "Detection window is bounded by heartbeat interval.",
        "<b>Latency added to handshake:</b> One Redis GET (~0.1ms on LAN).",
    ]
    for p in heartbeat_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("Approach 2: Active Health Check (Probe)", h3))
    elements.append(Paragraph(
        "The primary server actively probes the preferred server before each handshake (or "
        "periodically). The probe checks both network reachability and application readiness.",
        body
    ))
    probe_points = [
        "<b>Implementation:</b> Primary sends a lightweight UDP probe to the preferred server's "
        "migration port (9999). The preferred responds with its current capacity (available memory, "
        "CPU load, active connections). Primary only migrates if capacity is sufficient.",
        "<b>Pros:</b> Fresh, real-time health information. Can include load metrics for intelligent "
        "routing decisions.",
        "<b>Cons:</b> Adds latency to the handshake path (1 RTT to preferred). Probe itself can fail "
        "(timeout). Under high connection rates, probe traffic becomes significant.",
        "<b>Latency added to handshake:</b> 1 RTT to preferred server (~0.2ms on LAN, 10-100ms WAN).",
    ]
    for p in probe_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("Approach 3: State Transfer as Health Check (Integrated)", h3))
    elements.append(Paragraph(
        "Use the state transfer mechanism itself as the health check. The primary attempts to "
        "send the migration state to the preferred server. If the transfer succeeds, migration "
        "proceeds; if it fails (connection refused, timeout), the primary serves the connection "
        "directly without preferred_address.",
        body
    ))
    integrated_points = [
        "<b>Implementation:</b> For TCP Push backend: if connect() to preferred:9999 fails, "
        "skip migration. For Redis KV: if SET succeeds and preferred ACKs (via a response key), "
        "proceed. For HTTP Pull: primary stores state and waits for preferred to pull it; if not "
        "pulled within timeout, serve directly.",
        "<b>Pros:</b> No separate health check mechanism -- the state transfer IS the health check. "
        "Zero additional overhead when migration succeeds. Naturally handles partial failures.",
        "<b>Cons:</b> For Immediate (eager) transfer, the state is sent during the handshake, so "
        "the handshake blocks on the transfer. For Lazy transfer, the state isn't sent until the "
        "client connects to the preferred, so the health check happens too late.",
        "<b>Best with:</b> TCP Push + short timeout (50ms). If the TCP connection to preferred:9999 "
        "isn't established within 50ms, skip migration and serve directly.",
    ]
    for p in integrated_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph(
        "Recommendation: Start with Approach 1 (passive heartbeat via Redis) for simplicity, "
        "then upgrade to Approach 3 (integrated state-transfer-as-health-check) for production. "
        "Approach 2 adds too much latency for the marginal benefit over Approach 1.",
        highlight_style
    ))

    elements.append(Paragraph("5.3 Implementation Plan", h2))
    elements.append(Paragraph(
        "Adding health checks to our existing Neqo implementation requires changes in two places:",
        body
    ))
    impl_points = [
        "<b>Primary server (primary_server.rs):</b> Before calling connection.set_preferred_address(), "
        "check preferred health. If unhealthy, skip the preferred_address transport parameter entirely. "
        "The connection completes normally without migration.",
        "<b>Preferred server (preferred_server.rs):</b> Add a heartbeat thread that periodically "
        "writes to Redis (or responds to UDP probes). Also report capacity metrics: current "
        "connection count, CPU load, available memory.",
        "<b>Graceful fallback:</b> If the primary decides not to migrate (preferred unhealthy), it "
        "serves the HTTP/3 response directly. The client never knows migration was considered.",
        "<b>Monitoring:</b> Add counters for: migrations attempted, migrations succeeded, migrations "
        "skipped (unhealthy), migrations failed (preferred died after health check passed).",
    ]
    for i, p in enumerate(impl_points, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {p}', bullet_style))

    elements.append(Paragraph("5.4 Proposed Experiment: Health Check Validation", h2))
    health_exp = [
        "<b>Baseline:</b> Run 100 sequential connections with preferred server healthy. Measure "
        "migration success rate (should be 100%).",
        "<b>Failure injection:</b> Kill the preferred server process mid-experiment. Without health "
        "checks: measure how many connections experience timeouts. With health checks: measure "
        "how many connections are gracefully served by the primary instead.",
        "<b>Flapping:</b> Start/stop the preferred server every 5 seconds. Compare user-visible "
        "error rates with and without health checks.",
        "<b>Latency comparison:</b> Measure handshake latency with each health check approach "
        "(heartbeat, probe, integrated) vs. no health check.",
        "<b>Metric:</b> The key metric is <b>zero failed migrations</b> -- every connection should "
        "either migrate successfully or be served directly by the primary. No connection should "
        "experience a timeout due to migrating to a dead server.",
    ]
    for i, s in enumerate(health_exp, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {s}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 6: BITTORRENT PEER MIGRATION
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Application 5: BitTorrent Peer Migration", h1))

    elements.append(Paragraph("6.1 BitTorrent Architecture and Transport", h2))
    elements.append(Paragraph(
        "BitTorrent is the most widely deployed peer-to-peer file sharing protocol, responsible for "
        "an estimated 2-5% of all Internet traffic. Unlike IPFS, which adopted QUIC as its default "
        "transport in 2023, BitTorrent still relies on TCP and uTP (Micro Transport Protocol) for "
        "peer-to-peer data transfer. Key architectural properties relevant to server migration:",
        body
    ))
    bt_arch = [
        "<b>Piece-based content verification:</b> Files are divided into fixed-size pieces (typically "
        "256KB-4MB). Each piece has a SHA-1 hash (v1) or SHA-256 Merkle tree hash (v2, BEP 52). "
        "Clients verify every piece against its hash, guaranteeing content integrity regardless of "
        "which peer served it. This is directly analogous to IPFS's CID-based verification.",
        "<b>Swarm model:</b> A client (leecher) connects to many peers simultaneously, downloading "
        "different pieces from different seeders. Losing a single connection does not halt the download -- "
        "the client simply requests those pieces from other peers. However, reconnection incurs latency "
        "(tracker/DHT re-query + new handshake).",
        "<b>Transport layer:</b> BitTorrent uses TCP for the main peer protocol (BEP 3) and uTP (BEP 29) "
        "as a UDP-based congestion-controlled alternative. Neither supports connection migration. "
        "There is <b>no existing BEP for QUIC transport</b>, making this a greenfield research area.",
        "<b>WebSeed (BEP 19):</b> Torrents can specify HTTP/FTP URLs as additional download sources. "
        "Clients download pieces from web servers using HTTP range requests. As web servers adopt "
        "HTTP/3 (QUIC), WebSeeds become a natural entry point for QUIC migration.",
        "<b>Tracker and DHT:</b> Peers discover each other via centralized trackers (BEP 3) or the "
        "distributed hash table (BEP 5, Mainline DHT). When a peer disconnects, the client must "
        "re-query these to find replacement peers -- a process that takes 1-10 seconds depending on "
        "DHT latency and tracker responsiveness.",
    ]
    for p in bt_arch:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("6.2 How QUIC Server Migration Applies", h2))
    elements.append(Paragraph(
        "The core insight is that BitTorrent shares two critical properties with IPFS that make "
        "server-side migration viable: <b>content-addressed data</b> (piece hashes guarantee integrity) "
        "and <b>multiple providers</b> (many peers hold the same pieces). A seeder serving pieces over "
        "QUIC could use the preferred_address mechanism to redirect the client to another seeder that "
        "holds the same pieces, achieving seamless failover without tracker/DHT re-query.",
        body
    ))
    elements.append(Paragraph(
        "Crucially, BitTorrent has an advantage over IPFS for migration: peer identity is NOT "
        "cryptographically bound to the TLS certificate. In IPFS, libp2p embeds the PeerID in the "
        "TLS certificate, making migration between different peers fundamentally difficult. BitTorrent "
        "peers are identified by a 20-byte PeerID that is independent of the transport layer, making "
        "TLS state transfer between peers straightforward.",
        highlight_style
    ))

    elements.append(Paragraph("6.3 Three Migration Scenarios", h2))

    elements.append(Paragraph("Scenario A: WebSeed Migration via HTTP/3 (HIGH Feasibility)", h3))
    elements.append(Paragraph(
        "WebSeeds (BEP 19) allow torrent clients to download pieces from standard HTTP servers. As "
        "CDNs and web servers adopt HTTP/3, WebSeeds will increasingly use QUIC. A WebSeed server "
        "can use preferred_address to migrate the client to a mirror server that hosts the same files.",
        body
    ))
    webseed_points = [
        "<b>How it works:</b> Client connects to WebSeed A over HTTP/3. WebSeed A includes "
        "preferred_address pointing to WebSeed B (a mirror). After handshake, client migrates "
        "to WebSeed B. Client continues downloading pieces via HTTP range requests -- identical "
        "to our current implementation.",
        "<b>Directly analogous:</b> This is functionally identical to IPFS gateway migration. "
        "WebSeed A = primary server, WebSeed B = preferred server. Both serve the same file via HTTP.",
        "<b>No client modification:</b> Any HTTP/3 client (browser, curl, aria2) handles the "
        "migration transparently via standard QUIC preferred_address.",
        "<b>Use case:</b> CDN-backed torrent distribution (e.g., Linux distro mirrors) where "
        "multiple HTTP servers host the same .iso file.",
    ]
    for p in webseed_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("Scenario B: Seeder Failover (MEDIUM Feasibility)", h3))
    elements.append(Paragraph(
        "A seeder planning to go offline (maintenance, churn) can proactively migrate its connected "
        "leechers to another seeder that holds the same pieces. This avoids the costly "
        "tracker/DHT re-query and new QUIC handshake.",
        body
    ))
    seeder_points = [
        "<b>How it works:</b> Seeder A detects it will go offline (graceful shutdown signal, "
        "scheduled maintenance, battery low on mobile). It queries the tracker/DHT for other "
        "seeders with overlapping piece sets, selects one (Seeder B), and announces "
        "preferred_address pointing to Seeder B. Migration state (445 bytes) is transferred "
        "to Seeder B via any of our five backends.",
        "<b>Piece availability check:</b> Before migrating, Seeder A must verify that Seeder B "
        "has the pieces the leecher needs. This can be done by exchanging BITFIELD messages "
        "(standard BT protocol) or consulting the tracker's peer metadata.",
        "<b>Cost savings:</b> Without migration, recovery takes: DHT re-query (~1-10s) + "
        "new QUIC handshake (1 RTT) + piece re-negotiation. With migration: just 1 RTT "
        "(PATH_CHALLENGE/PATH_RESPONSE). For large swarms with frequent churn, this saves "
        "thousands of reconnections per hour.",
        "<b>Requires:</b> A QUIC-based BitTorrent peer protocol. This does not exist today "
        "and would need a new BEP proposal.",
    ]
    for p in seeder_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("Scenario C: Tracker-Coordinated Load Distribution (NOVEL)", h3))
    elements.append(Paragraph(
        "A heavily loaded seeder can use the tracker as a coordination point to migrate leechers "
        "to less-loaded seeders. This is a novel form of <b>peer-assisted load balancing</b> that "
        "has no equivalent in today's BitTorrent ecosystem.",
        body
    ))
    tracker_points = [
        "<b>How it works:</b> Seeder A is serving 100 leechers and approaching its upload bandwidth "
        "limit. It queries the tracker for other seeders of the same torrent, finds Seeders B, C, D "
        "with lower load. Seeder A migrates 30 leechers to each via preferred_address.",
        "<b>Tracker as coordinator:</b> The tracker already knows which peers have which torrents. "
        "Adding load metrics (current connections, upload bandwidth used) to tracker announce "
        "messages enables intelligent migration decisions.",
        "<b>Novel contribution:</b> This is fundamentally different from existing BitTorrent load "
        "management (which relies on choking/unchoking algorithms). Migration-based load distribution "
        "moves entire connections rather than throttling individual peers.",
        "<b>Research potential:</b> This could significantly improve piece distribution in swarms with "
        "uneven seeder load. The tracker could implement global optimization strategies "
        "(e.g., minimize total download time across all leechers).",
    ]
    for p in tracker_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph("6.4 Comparison with IPFS Migration", h2))
    elements.append(Paragraph(
        "BitTorrent and IPFS share similar properties for migration, but differ in key aspects:",
        body
    ))
    elements.append(make_table(
        ["Aspect", "IPFS", "BitTorrent"],
        [
            ["Content verification", "CID hash (SHA-256)", "Piece hash (SHA-1/SHA-256)"],
            ["Multiple providers", "Yes (DHT providers)", "Yes (swarm seeders)"],
            ["QUIC adoption", "Default since Kubo 0.18+<br/>(2023)", "Not yet -- uses TCP/uTP"],
            ["Identity bound to TLS", "Yes (PeerID = hard to<br/>migrate)", "No (PeerID independent<br/>of transport -- easier)"],
            ["Connection multiplexing", "Many streams per conn<br/>(Bitswap, DHT, etc.)", "One torrent per conn<br/>(simpler state)"],
            ["Best migration scenario", "Gateway (HTTP/3)", "WebSeed (HTTP/3)"],
            ["State beyond TLS", "Bitswap streams, DHT<br/>queries (complex)", "Piece bitmap, request<br/>queue (simpler)"],
            ["Research novelty", "High (no prior work)", "Very high (no prior work,<br/>no QUIC in BT at all)"],
        ],
        col_widths=[1.5*inch, 2.2*inch, 2.2*inch],
    ))

    elements.append(Paragraph("6.5 Challenges", h2))
    challenges = [
        "<b>No QUIC transport for BitTorrent:</b> The biggest barrier. BitTorrent uses TCP and uTP; "
        "there is no BEP for QUIC transport. WebSeed via HTTP/3 is the only path that works today "
        "without protocol changes. For native peer-to-peer migration (Scenarios B and C), a QUIC-based "
        "peer protocol would need to be designed.",
        "<b>Piece availability verification:</b> Before migrating a leecher to another seeder, the "
        "seeder must verify that the target has the needed pieces. Full seeders (100% of pieces) are "
        "trivially compatible, but partial seeders require bitfield comparison. This adds a coordination "
        "step not present in our current implementation.",
        "<b>In-flight piece requests:</b> If the leecher has outstanding piece requests to the "
        "migrating seeder, those requests must be re-issued to the new seeder. Unlike IPFS (where "
        "Bitswap streams carry complex state), BitTorrent piece requests are stateless -- the leecher "
        "simply re-sends REQUEST messages after migration.",
        "<b>Swarm dynamics:</b> BitTorrent's tit-for-tat algorithm (choking/unchoking) is designed "
        "around direct reciprocity. A migrated leecher has no upload history with the new seeder, "
        "which may affect its initial unchoke priority. However, optimistic unchoking (standard in "
        "all BT clients) ensures new connections eventually get service.",
        "<b>NAT traversal:</b> Many BitTorrent peers are behind NATs. QUIC's preferred_address "
        "mechanism requires the preferred server to be directly reachable, which may not be true "
        "for residential peers. This limits Scenarios B and C to peers with public IPs or "
        "relay-assisted setups.",
    ]
    for p in challenges:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {p}', bullet_style))

    elements.append(Paragraph(
        "Key insight: WebSeed migration (Scenario A) sidesteps all peer-to-peer challenges. "
        "Web servers have public IPs, serve complete files, and already use HTTP/3. This is the "
        "recommended starting point -- identical to our current implementation.",
        highlight_style
    ))

    elements.append(Paragraph("6.6 Proposed Experiment: WebSeed Migration PoC", h2))
    bt_exp = [
        "<b>Setup:</b> Deploy two HTTP/3 web servers (opti7040 and homeserver2) serving the same "
        "large file (e.g., a 1GB Linux ISO). Create a .torrent file with both servers listed as "
        "WebSeeds (url-list). Configure opti7040 as the primary with preferred_address pointing "
        "to homeserver2.",
        "<b>Client:</b> Use aria2 (supports WebSeed + HTTP/3) or a modified qBittorrent to download "
        "the torrent. Alternatively, use Firefox to download directly via HTTP/3 (testing the WebSeed "
        "URL directly, not the torrent protocol).",
        "<b>Metric 1 -- Seamless failover:</b> Start downloading from opti7040, trigger migration "
        "mid-download. Verify the download completes successfully from homeserver2 without restart.",
        "<b>Metric 2 -- Latency comparison:</b> Compare recovery time when the primary WebSeed fails: "
        "(a) without migration (client must discover and connect to backup WebSeed), vs. "
        "(b) with migration (preferred_address, 1 RTT failover).",
        "<b>Metric 3 -- Piece integrity:</b> Verify all downloaded pieces pass SHA-1/SHA-256 "
        "verification, confirming that migration did not corrupt the data stream.",
        "<b>Extension:</b> If time permits, prototype a QUIC-based BitTorrent peer protocol "
        "using Neqo, demonstrating native peer-to-peer migration (Scenario B) between two seeders.",
    ]
    for i, s in enumerate(bt_exp, 1):
        elements.append(Paragraph(f'<bullet>{i}.</bullet> {s}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 7: COMPARATIVE ANALYSIS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("7. Comparative Analysis of All Applications", h1))

    elements.append(Paragraph(
        "The following table compares all five applications across key research dimensions:",
        body
    ))

    elements.append(make_table(
        ["Dimension", "IPFS", "DNS+Anycast", "Load Balancing", "Health Checks", "BitTorrent"],
        [
            ["Research<br/>Novelty", "HIGH -- new paradigm<br/>for content nets", "MEDIUM -- known idea,<br/>new mechanism",
             "MEDIUM -- novel approach<br/>to known problem", "LOW -- engineering<br/>contribution",
             "VERY HIGH -- no QUIC<br/>in BT, unexplored"],
            ["Impl.<br/>Complexity", "HIGH -- modify libp2p<br/>or wrap gateway",
             "MEDIUM -- simulate<br/>anycast on LAN", "LOW -- extend existing<br/>primary server",
             "LOW -- add health<br/>check to primary", "LOW (WebSeed) to<br/>HIGH (native peer)"],
            ["Uses Existing<br/>Testbed?", "Partially -- need<br/>IPFS nodes", "Yes -- with iptables<br/>simulation",
             "Yes -- directly", "Yes -- directly", "Yes -- WebSeed uses<br/>existing HTTP/3"],
            ["Time to PoC", "2-3 weeks", "1-2 weeks", "1 week", "3-5 days", "1 week (WebSeed)<br/>3-4 weeks (native)"],
            ["Paper<br/>Potential", "Standalone paper<br/>(top venue)", "Section in<br/>systems paper",
             "Section in<br/>systems paper", "Engineering section<br/>in existing paper",
             "Standalone paper<br/>(top venue)"],
            ["Professor<br/>Appeal", "HIGH -- novel,<br/>interdisciplinary", "HIGH -- practical,<br/>industry-relevant",
             "MEDIUM -- well-studied<br/>area", "HIGH -- shows rigor<br/>and completeness",
             "HIGH -- large user<br/>base, novel angle"],
        ],
        col_widths=[0.85*inch, 1.05*inch, 1.05*inch, 1.1*inch, 1.0*inch, 1.1*inch],
    ))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Scoring Summary", h2))
    elements.append(make_table(
        ["Application", "Novelty<br/>(1-5)", "Feasibility<br/>(1-5)", "Impact<br/>(1-5)",
         "Effort<br/>(1-5, low=good)", "Total<br/>(out of 20)"],
        [
            ["IPFS Gateway Migration", "5", "4", "4", "3", "<b>16</b>"],
            ["DNS + Anycast Hybrid", "4", "3", "5", "3", "<b>15</b>"],
            ["QUIC Migration LB", "3", "5", "4", "4", "<b>16</b>"],
            ["Health-Checked Migration", "2", "5", "3", "5", "<b>15</b>"],
            ["BitTorrent WebSeed Migration", "5", "4", "5", "4", "<b>18</b>"],
        ],
        col_widths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.0*inch, 0.8*inch],
    ))

    # ══════════════════════════════════════════
    # SECTION 8: ROADMAP
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("8. Recommended Research Roadmap", h1))
    elements.append(Paragraph(
        "Based on the analysis above, we recommend the following phased approach:",
        body
    ))

    elements.append(Paragraph("Phase 1: Health-Checked Migration (Immediate)", h2))
    elements.append(Paragraph(
        "Add health checks to the existing implementation. This is the lowest-hanging fruit and "
        "strengthens any subsequent experiments by ensuring robust migration behavior. Implement "
        "Redis-based heartbeat (Approach 1) first, then integrate health checking into the state "
        "transfer mechanism (Approach 3).",
        body
    ))
    elements.append(Paragraph(
        "Deliverable: Modified primary_server.rs with health-aware migration decision. "
        "Experiment results showing zero failed migrations under server failure.",
        body_italic
    ))

    elements.append(Paragraph("Phase 2: QUIC Migration Load Balancer (Short-term)", h2))
    elements.append(Paragraph(
        "Extend the primary server to act as a load balancer frontend. Implement backend selection "
        "policies (round-robin, least-connections). Benchmark against HAProxy. This directly builds "
        "on the existing implementation and the health check work from Phase 1.",
        body
    ))
    elements.append(Paragraph(
        "Deliverable: Load balancer PoC with performance comparison. Demonstrates the \"LB bypass\" "
        "use case described in RFC 9000 Section 9.6.",
        body_italic
    ))

    elements.append(Paragraph("Phase 3: DNS + Anycast Hybrid (Medium-term)", h2))
    elements.append(Paragraph(
        "Build the two-phase routing architecture with simulated anycast. Demonstrate connection "
        "stability under route changes. This requires the LB infrastructure from Phase 2 and "
        "adds the anycast simulation layer.",
        body
    ))
    elements.append(Paragraph(
        "Deliverable: Anycast+migration PoC showing connection survival under route flaps. "
        "Quantified latency comparison with pure anycast.",
        body_italic
    ))

    elements.append(Paragraph("Phase 4: IPFS Integration (Long-term / Separate Paper)", h2))
    elements.append(Paragraph(
        "Implement IPFS gateway migration as a standalone contribution. This could form the basis "
        "of a separate research paper on content-addressed network migration. Requires IPFS/Kubo "
        "deployment on the testbed and potentially modifications to quic-go or a Rust-native "
        "IPFS client.",
        body
    ))
    elements.append(Paragraph(
        "Deliverable: IPFS gateway migration PoC with performance evaluation. Paper submission "
        "to a networking or distributed systems venue.",
        body_italic
    ))

    elements.append(Paragraph("Phase 5: BitTorrent WebSeed Migration (Parallel with Phase 4)", h2))
    elements.append(Paragraph(
        "Implement WebSeed migration using the existing testbed. Deploy two HTTP/3 servers hosting "
        "the same large file, create a torrent with both as WebSeeds, and demonstrate seamless "
        "failover via preferred_address. This reuses our existing Neqo code with minimal changes -- "
        "just serve a large file instead of the demo page. Can run in parallel with IPFS work since "
        "it shares the same infrastructure.",
        body
    ))
    elements.append(Paragraph(
        "Deliverable: WebSeed migration PoC, latency comparison (migration vs. re-discovery), "
        "and piece integrity verification. If successful, design a BEP draft for QUIC-based "
        "BitTorrent peer protocol with migration support.",
        body_italic
    ))

    # ══════════════════════════════════════════
    # SECTION 9: REFERENCES
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("9. References", h1))

    elements.append(Paragraph("QUIC and Migration", h2))
    refs = [
        '[1] RFC 9000, "QUIC: A UDP-Based Multiplexed and Secure Transport," IETF 2021. '
        'Section 9.6: Server\'s Preferred Address.',
        '[2] Grubl et al., "QUIC-Exfil: Exploiting QUIC\'s Server Preferred Address Feature," '
        'ASIA CCS 2025.',
        '[3] Puliafito et al., "Server-side QUIC connection migration to support microservice '
        'deployment at the edge," Pervasive and Mobile Computing, 2022.',
        '[4] Duke et al., "QUIC-LB: Generating Routable QUIC Connection IDs," IETF Draft, 2025.',
    ]
    for r in refs:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("IPFS and libp2p", h2))
    refs_ipfs = [
        '[5] Benet, J., "IPFS - Content Addressed, Versioned, P2P File System," arXiv:1407.3561, 2014.',
        '[6] libp2p Specification, "QUIC Transport." https://github.com/libp2p/specs/tree/master/quic',
        '[7] libp2p TLS 1.3 Handshake, "Using TLS 1.3 with libp2p." '
        'https://github.com/libp2p/specs/blob/master/tls/tls.md',
        '[8] IPFS Cluster Documentation. https://ipfscluster.io/',
        '[9] Protocol Labs, "Kubo: IPFS Implementation in Go." https://github.com/ipfs/kubo',
    ]
    for r in refs_ipfs:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("DNS and Anycast", h2))
    refs_dns = [
        '[10] RFC 4786, "Operation of Anycast Services," IETF 2006.',
        '[11] Flavel, A. et al., "FastRoute: A Scalable Load-Aware Anycast Routing Architecture '
        'for Modern CDNs," NSDI 2015.',
        '[12] Yap, K.K. et al., "Taking the Edge off with Espresso: Scale, Reliability and '
        'Programmability for Global Internet Peering," SIGCOMM 2017.',
        '[13] Fan, X. et al., "Consistent Hashing with Bounded Loads," STOC 2017.',
    ]
    for r in refs_dns:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("Load Balancing", h2))
    refs_lb = [
        '[14] Eisenbud et al., "Maglev: A Fast and Reliable Software Network Load Balancer," '
        'NSDI 2016.',
        '[15] Olteanu et al., "Stateless Datacenter Load-balancing with Beamer," NSDI 2018.',
        '[16] Miao et al., "SilkRoad: Making Stateful Layer-4 Load Balancing Fast and Cheap," '
        'SIGCOMM 2017.',
        '[17] Barbette et al., "Cheetah: A High-Speed Load-Balancer Design with Guaranteed '
        'Per-Connection-Consistency," NSDI 2020.',
        '[18] Facebook Engineering, "Open-sourcing Katran," 2018.',
    ]
    for r in refs_lb:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("Health Checking and Fault Tolerance", h2))
    refs_health = [
        '[19] Consul by HashiCorp, "Health Checks." https://developer.hashicorp.com/consul/docs/services/usage/checks',
        '[20] Envoy Proxy, "Health Checking." https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking',
        '[21] Kubernetes, "Configure Liveness, Readiness and Startup Probes." '
        'https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/',
    ]
    for r in refs_health:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("BitTorrent and Peer-to-Peer", h2))
    refs_bt = [
        '[22] Cohen, B., "The BitTorrent Protocol Specification," BEP 3, 2008. '
        'https://www.bittorrent.org/beps/bep_0003.html',
        '[23] BEP 52, "The BitTorrent Protocol Specification v2," 2020. '
        'https://www.bittorrent.org/beps/bep_0052.html',
        '[24] BEP 19, "WebSeed - HTTP/FTP Seeding (GetRight style)," 2008. '
        'https://www.bittorrent.org/beps/bep_0019.html',
        '[25] BEP 17, "HTTP Seeding (Hoffman-style)," 2008. '
        'https://www.bittorrent.org/beps/bep_0017.html',
        '[26] BEP 29, "uTorrent transport protocol (uTP)," 2009. '
        'https://www.bittorrent.org/beps/bep_0029.html',
        '[27] BEP 5, "DHT Protocol," 2008. '
        'https://www.bittorrent.org/beps/bep_0005.html',
        '[28] Norberg, A., "libtorrent: A C++ BitTorrent implementation." '
        'https://www.libtorrent.org/',
    ]
    for r in refs_bt:
        elements.append(Paragraph(r, ref_style))

    # Build
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

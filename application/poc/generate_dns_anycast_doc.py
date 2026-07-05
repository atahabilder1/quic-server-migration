#!/usr/bin/env python3
"""Generate DNS+Anycast Hybrid Routing PoC documentation PDF."""

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

OUTPUT = "application/poc/DNS_ANYCAST_POC.pdf"

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
    code_style = ParagraphStyle(
        "Code", parent=body,
        fontName="Courier", fontSize=9, leading=13,
        leftIndent=16, spaceBefore=2, spaceAfter=2,
        textColor=DARK_GRAY, backColor=GRAY_BG,
        borderColor=BORDER, borderWidth=0.5, borderPadding=6,
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
    elements.append(Paragraph("DNS + Anycast Hybrid Routing", title_style))
    elements.append(Paragraph("Proof-of-Concept Documentation", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "QUIC Server-Side Migration for Anycast Connection Stability",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"PoC Implementation Guide &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.6*inch))

    # Abstract
    abstract_text = (
        "This document describes a proof-of-concept implementation that combines DNS-based GeoDNS "
        "resolution with simulated anycast routing and QUIC server-side migration. The PoC demonstrates "
        "how QUIC's preferred_address mechanism (RFC 9000, Section 9.6) can solve the fundamental "
        "instability problem of anycast-routed connections: when BGP route changes redirect traffic "
        "to a different Point of Presence (PoP), existing connections break. By migrating connections "
        "from the anycast PoP to a unicast backend server immediately after the TLS handshake, "
        "the connection becomes immune to subsequent anycast route changes. This two-phase routing "
        "approach combines the fast initial routing of anycast with the stability of unicast for "
        "connection lifetime."
    )
    abstract_tbl = Table(
        [[Paragraph(abstract_text, ParagraphStyle(
            "Abstract", parent=body, fontSize=10, leading=14,
            textColor=DARK_GRAY, backColor=LIGHT_BLUE,
            borderColor=MED_BLUE, borderWidth=1, borderPadding=12,
        ))]],
        colWidths=[6.5*inch]
    )
    abstract_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, MED_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(abstract_tbl)

    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # 1. OVERVIEW
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. Overview", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("Problem: Anycast Route Instability", h2))
    elements.append(Paragraph(
        "Anycast is a widely deployed routing technique where multiple servers share the same IP address, "
        "and BGP routing directs clients to the nearest server. While this provides excellent initial "
        "latency, it introduces a critical instability: when BGP routes change (due to network failures, "
        "congestion-based rerouting, or routine maintenance), existing connections are silently redirected "
        "to a different PoP that has no knowledge of the connection state. The result is an immediate, "
        "unrecoverable connection failure.",
        body
    ))

    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Anycast routing can cause connection disruption during BGP route changes",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>The new PoP receives packets for a connection it never established",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>TCP connections break silently; retransmission timers eventually expire",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Even with connection ID-based load balancing, cross-PoP state sharing is impractical at scale",
        bullet_style
    ))

    elements.append(Paragraph("Solution: QUIC Migration to Unicast Backend", h2))
    elements.append(Paragraph(
        "QUIC server-side migration provides an elegant solution. The anycast PoP acts as the primary "
        "server, completing the TLS handshake and immediately advertising a preferred_address pointing "
        "to a unicast backend server. The client validates the new path and migrates. Once migration is "
        "complete, the connection runs directly between the client and the unicast backend, entirely "
        "bypassing the anycast routing layer.",
        body
    ))

    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Use QUIC migration to move connections from anycast PoP to unicast backend",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>After migration, the connection is immune to anycast route changes",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Two-phase routing: coarse-grained anycast for initial contact, fine-grained unicast for connection lifetime",
        bullet_style
    ))

    elements.append(Paragraph(
        "Key Insight: After migration, the connection is on a direct unicast path "
        "and is completely immune to anycast BGP route changes.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 2. ARCHITECTURE
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Architecture", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("Testbed Layout", h2))
    elements.append(Paragraph(
        "The PoC uses our existing four-machine LAN testbed (141.217.168.x subnet) with the following "
        "role assignments:",
        body
    ))

    arch_table = make_table(
        ["Role", "Machine", "IP Address", "Description"],
        [
            ["VIP (Anycast)", "Client loopback", "10.99.99.1",
             "Simulated anycast address (loopback + iptables DNAT)"],
            ["PoP (Primary)", "opti7040", "141.217.168.152",
             "Simulated nearest anycast Point of Presence"],
            ["Backend (Preferred)", "homeserver2", "141.217.168.143",
             "Final unicast destination after migration"],
            ["Alt PoP", "Proxmox VM", "141.217.168.200",
             "Destination after simulated BGP route change"],
            ["Client", "optiplex7010", "141.217.168.127",
             "QUIC client (neqo-client or Firefox)"],
        ],
        col_widths=[1.2*inch, 1.1*inch, 1.3*inch, 2.9*inch]
    )
    elements.append(arch_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Connection Flow", h2))
    elements.append(Paragraph(
        "The connection proceeds through three distinct phases:",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 1 (Anycast):</b> Client connects to VIP 10.99.99.1:4433. "
        "iptables DNAT redirects traffic to primary server at .152 (simulates anycast nearest-PoP routing).",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 2 (Handshake + Migration):</b> Primary completes QUIC handshake, "
        "advertises preferred_address = 141.217.168.143:4433. Client sends PATH_CHALLENGE to .143.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 3 (Unicast):</b> Client validates path to .143, migrates. "
        "Connection now runs directly client &lt;-&gt; .143 on a stable unicast path.",
        bullet_style
    ))

    # ══════════════════════════════════════════
    # 3. HOW ANYCAST SIMULATION WORKS
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. How Anycast Simulation Works", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("iptables DNAT Redirection", h2))
    elements.append(Paragraph(
        "Since we cannot deploy actual BGP anycast on a LAN, we simulate it using Linux network namespaces "
        "and iptables DNAT rules on the client machine. A virtual IP (VIP) 10.99.99.1 is assigned to the "
        "loopback interface, and iptables OUTPUT chain rules redirect all traffic destined for the VIP to "
        "the actual primary server IP.",
        body
    ))

    elements.append(Paragraph(
        "<bullet>&bull;</bullet>iptables DNAT redirects traffic from VIP (10.99.99.1) to primary (.152), "
        "simulating anycast routing to nearest PoP",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Primary completes QUIC handshake and advertises preferred_address = .143",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Client migrates to .143 (direct unicast path, bypasses DNAT entirely)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Changing the DNAT rule (simulating a BGP flap) has NO effect on the migrated connection",
        bullet_style
    ))

    elements.append(Paragraph("DNS Resolution via dnsmasq", h2))
    elements.append(Paragraph(
        "A local dnsmasq instance resolves a test domain (e.g., cdn.quic-test.local) to the primary "
        "server IP. This simulates GeoDNS behavior where a CDN's authoritative DNS returns the IP of "
        "the nearest anycast PoP. In a production deployment, this would be a real GeoDNS service "
        "returning the anycast VIP.",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>dnsmasq resolves test domain to the primary IP (simulates GeoDNS)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Client resolves domain, connects to VIP, DNAT routes to primary",
        bullet_style
    ))

    elements.append(Paragraph(
        "Note: The DNAT simulation is client-side only. In production, anycast routing "
        "happens at the network layer via BGP, requiring no client-side configuration.",
        warning_style
    ))

    # ══════════════════════════════════════════
    # 4. SCRIPTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("4. Scripts", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The PoC includes four shell scripts that manage the simulation environment:",
        body
    ))

    scripts_table = make_table(
        ["Script", "Purpose", "Requires sudo"],
        [
            ["setup_anycast_sim.sh",
             "Creates the VIP (10.99.99.1) on loopback, adds iptables DNAT rules "
             "to redirect VIP traffic to the primary server (.152)",
             "Yes"],
            ["setup_dnsmasq.sh",
             "Configures a local dnsmasq instance to resolve the test domain "
             "(cdn.quic-test.local) to the primary server IP, simulating GeoDNS",
             "Yes"],
            ["test_route_flap.sh",
             "Demonstrates connection survival during a simulated BGP route change. "
             "Changes the DNAT target from .152 to .200 while a migrated connection is active",
             "Yes"],
            ["teardown.sh",
             "Removes all iptables rules, deletes the VIP from loopback, stops dnsmasq, "
             "and restores the original DNS configuration",
             "Yes"],
        ],
        col_widths=[1.6*inch, 4.0*inch, 0.9*inch]
    )
    elements.append(scripts_table)

    # ══════════════════════════════════════════
    # 5. HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("5. How to Run", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("Step 1: Setup (on client machine)", h2))
    elements.append(Paragraph("sudo ./setup_anycast_sim.sh", code_style))
    elements.append(Paragraph("sudo ./setup_dnsmasq.sh", code_style))

    elements.append(Paragraph("Step 2: Start servers (on remote machines)", h2))
    elements.append(Paragraph(
        "On <b>homeserver2</b> (preferred/backend server):",
        body
    ))
    elements.append(Paragraph(
        "preferred-server 141.217.168.143:4433 9999",
        code_style
    ))
    elements.append(Paragraph(
        "On <b>opti7040</b> (primary/PoP server):",
        body
    ))
    elements.append(Paragraph(
        "primary-server 0.0.0.0:4433 141.217.168.143:4433 141.217.168.143:9999",
        code_style
    ))

    elements.append(Paragraph("Step 3: Test connection through VIP", h2))
    elements.append(Paragraph(
        "neqo-client https://10.99.99.1:4433/",
        code_style
    ))
    elements.append(Paragraph(
        "The client connects to the VIP, which is DNAT'd to the primary. The primary completes the "
        "handshake and advertises the preferred address. The client migrates to the backend, and the "
        "connection proceeds on a direct unicast path.",
        body
    ))

    elements.append(Paragraph("Step 4: Route flap test", h2))
    elements.append(Paragraph(
        "sudo ./test_route_flap.sh",
        code_style
    ))
    elements.append(Paragraph(
        "This script changes the DNAT target from .152 to .200 while a connection is active, "
        "demonstrating that migrated connections survive the route change.",
        body
    ))

    elements.append(Paragraph("Step 5: Cleanup", h2))
    elements.append(Paragraph("sudo ./teardown.sh", code_style))

    # ══════════════════════════════════════════
    # 6. ROUTE FLAP TEST
    # ══════════════════════════════════════════
    elements.append(Paragraph("6. Route Flap Test", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The route flap test is the core demonstration of the PoC. It proves that QUIC migration "
        "makes connections resilient to anycast route changes.",
        body
    ))

    elements.append(Paragraph("Test Procedure", h2))

    steps = [
        ("<b>Step 1:</b> Establish connection through VIP &rarr; primary (.152) &rarr; "
         "migration &rarr; preferred (.143). Connection is now on unicast path."),
        ("<b>Step 2:</b> Change DNAT rule: VIP (10.99.99.1) now routes to .200 instead of .152. "
         "This simulates a BGP route change that would redirect anycast traffic to a different PoP."),
        ("<b>Step 3:</b> Verify that the <b>migrated connection SURVIVES</b>. It is on the direct "
         "unicast path to .143 and is unaffected by the DNAT change."),
        ("<b>Step 4:</b> Establish a <b>new</b> connection through VIP. It goes to .200 (the new "
         "PoP), demonstrating that the route change did take effect for new connections."),
    ]
    for i, step in enumerate(steps):
        elements.append(Paragraph(
            f"<bullet>&bull;</bullet>{step}",
            bullet_style
        ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Result: The migrated connection survives the simulated BGP route change. "
        "New connections go to the new PoP (.200), but existing migrated connections "
        "remain stable on their unicast backend (.143).",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 7. KEY INSIGHT
    # ══════════════════════════════════════════
    elements.append(Paragraph("7. Key Insight", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("Traditional Anycast Limitations", h2))
    elements.append(Paragraph(
        "In traditional anycast deployments, BGP route changes break existing connections because "
        "the new PoP has no state for the connection. This is a fundamental limitation of anycast "
        "routing: it optimizes for initial connection establishment but provides no stability guarantees "
        "for connection lifetime.",
        body
    ))
    elements.append(Paragraph(
        "Traditional anycast: BGP changes break existing connections with no recovery mechanism.",
        negative_style
    ))

    elements.append(Paragraph("Two-Phase Routing with QUIC Migration", h2))
    elements.append(Paragraph(
        "QUIC server-side migration introduces a two-phase routing model:",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 1 (Coarse-grained anycast):</b> Initial contact uses anycast "
        "for fast, proximity-based routing to the nearest PoP. This phase is brief (one RTT for handshake).",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 2 (Fine-grained unicast):</b> Connection migrates to a dedicated "
        "unicast backend. The connection is now \"pinned\" to this backend for its entire lifetime, "
        "immune to anycast routing changes.",
        bullet_style
    ))

    elements.append(Paragraph("Production Applicability", h2))
    elements.append(Paragraph(
        "This pattern is directly applicable to several large-scale deployment scenarios:",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>CDNs:</b> Edge PoPs use anycast for client proximity; migration moves "
        "long-lived connections (streaming, WebSocket) to stable origin or mid-tier servers",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Edge computing:</b> Anycast routes to nearest edge node; migration moves "
        "stateful workloads to the optimal compute backend",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Globally distributed services:</b> Anycast provides fast DNS-like routing; "
        "migration provides connection pinning without DNS TTL delays",
        bullet_style
    ))

    elements.append(Paragraph(
        "With QUIC migration, the connection is \"pinned\" to a unicast backend after handshake -- "
        "combining fast anycast initial routing with rock-solid unicast connection stability.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 8. COMPARISON
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("8. Comparison", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The following table compares three approaches to routing clients to distributed servers, "
        "highlighting the advantages of combining QUIC migration with anycast:",
        body
    ))

    comparison_table = make_table(
        ["Scenario", "Pure Anycast", "DNS-based", "QUIC Migration + Anycast"],
        [
            ["Initial routing",
             "BGP (fast, automatic)",
             "DNS TTL (slow, cached)",
             "BGP + migration (fast)"],
            ["Route change impact",
             "Connection breaks immediately",
             "Wait for DNS TTL to expire",
             "No impact on existing connections"],
            ["Connection stability",
             "Poor (any BGP flap breaks it)",
             "Medium (stable until DNS re-resolve)",
             "Excellent (pinned to unicast)"],
            ["Data path",
             "Through PoP always (extra hop)",
             "Direct after DNS resolution",
             "Direct after migration (~1 RTT)"],
            ["Failover speed",
             "BGP convergence (seconds-minutes)",
             "DNS TTL (seconds-hours)",
             "Instant (already on unicast)"],
            ["Client complexity",
             "None",
             "DNS resolver logic",
             "QUIC stack support (RFC 9000)"],
        ],
        col_widths=[1.2*inch, 1.6*inch, 1.6*inch, 2.1*inch],
        highlight_row=3  # Connection stability row (1-indexed in data, but highlight_row is 1-indexed for display)
    )
    elements.append(comparison_table)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "QUIC Migration + Anycast achieves the best of both worlds: the fast initial routing of "
        "anycast with the connection stability of direct unicast paths. The migration overhead is "
        "minimal (one additional RTT for PATH_CHALLENGE/PATH_RESPONSE), and the resulting connection "
        "is immune to all subsequent routing changes.",
        highlight_style
    ))

    # ── Build ──
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

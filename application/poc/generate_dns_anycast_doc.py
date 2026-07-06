#!/usr/bin/env python3
"""Generate DNS+Anycast Hybrid Routing PoC documentation PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, CondPageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Group
)
from reportlab.graphics import renderPDF
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
PURPLE = HexColor("#553c9a")
LIGHT_PURPLE = HexColor("#faf5ff")


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

    # ── Helper: draw a box with label ──
    def draw_box(d, x, y, w, h_val, label, sublabel=None, fill=LIGHT_BLUE,
                 stroke=MED_BLUE, font_size=9):
        d.add(Rect(x, y, w, h_val, fillColor=fill, strokeColor=stroke, strokeWidth=1.2))
        d.add(String(x + w/2, y + h_val/2 + (5 if sublabel else 0),
                      label, fontName="Helvetica-Bold", fontSize=font_size,
                      fillColor=DARK_BLUE, textAnchor="middle"))
        if sublabel:
            d.add(String(x + w/2, y + h_val/2 - 10,
                          sublabel, fontName="Helvetica", fontSize=7,
                          fillColor=DARK_GRAY, textAnchor="middle"))

    # ── Helper: draw arrow (horizontal or angled) ──
    def draw_arrow(d, x1, y1, x2, y2, color=DARK_GRAY, width=1.5, dashed=False):
        if dashed:
            d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width,
                       strokeDashArray=[4, 3]))
        else:
            d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
        # Arrowhead
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 7
        a1 = angle + math.radians(150)
        a2 = angle - math.radians(150)
        d.add(Polygon(
            [x2, y2,
             x2 + arrow_len * math.cos(a1), y2 + arrow_len * math.sin(a1),
             x2 + arrow_len * math.cos(a2), y2 + arrow_len * math.sin(a2)],
            fillColor=color, strokeColor=color, strokeWidth=0.5
        ))

    def draw_label(d, x, y, text, color=DARK_GRAY, font_size=7, font="Helvetica",
                   anchor="middle"):
        d.add(String(x, y, text, fontName=font, fontSize=font_size,
                      fillColor=color, textAnchor=anchor))

    # ── Helper: double-line arrow for emphasis ──
    def draw_double_arrow(d, x1, y1, x2, y2, color=GREEN):
        d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=3))
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 9
        a1 = angle + math.radians(150)
        a2 = angle - math.radians(150)
        d.add(Polygon(
            [x2, y2,
             x2 + arrow_len * math.cos(a1), y2 + arrow_len * math.sin(a1),
             x2 + arrow_len * math.cos(a2), y2 + arrow_len * math.sin(a2)],
            fillColor=color, strokeColor=color, strokeWidth=0.5
        ))

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
    # 1. OVERVIEW & REAL-WORLD ANYCAST
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. Anycast in the Real World", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("What Is Anycast?", h2))
    elements.append(Paragraph(
        "Anycast is a network addressing and routing methodology where a single IP address is "
        "announced from multiple geographic locations simultaneously via BGP (Border Gateway Protocol). "
        "When a client sends a packet to an anycast IP, the Internet's routing infrastructure delivers "
        "it to the topologically nearest instance -- the one with the shortest AS-path or lowest IGP "
        "metric. Major CDNs (Cloudflare, Akamai, Fastly) and DNS providers (Google Public DNS 8.8.8.8, "
        "Cloudflare 1.1.1.1) rely on anycast to distribute traffic across dozens or hundreds of Points "
        "of Presence (PoPs) worldwide.",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Multiple PoPs, one IP:</b> The same IP prefix (e.g., 1.1.1.0/24) is "
        "announced from data centers in New York, London, Tokyo, etc.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>BGP does the routing:</b> Internet routers select the shortest AS-path, "
        "effectively directing each client to the geographically nearest PoP",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>No client configuration:</b> Clients see a single IP address and are "
        "unaware that multiple servers share it",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Ideal for stateless protocols:</b> DNS (UDP, single request-response) "
        "works perfectly with anycast since each query is independent",
        bullet_style
    ))

    elements.append(Paragraph("Why Anycast Breaks Stateful Connections", h2))
    elements.append(Paragraph(
        "While anycast excels at routing individual packets to the nearest server, it is fundamentally "
        "incompatible with stateful protocols like TCP and QUIC. The core issue is that BGP routing "
        "decisions can change at any time -- due to link failures, congestion-based rerouting, planned "
        "maintenance, or even normal BGP path exploration. When a route changes, subsequent packets for "
        "an existing connection may be delivered to a different PoP that has no state for that connection.",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>TCP:</b> The new PoP receives a packet with an unknown 5-tuple. It sends "
        "RST, and the connection dies immediately. Retransmission timers on the client side eventually "
        "expire (30-120 seconds), but the connection is already doomed.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>QUIC:</b> QUIC uses Connection IDs instead of 5-tuples, which helps "
        "with NAT rebinding and client migration, but does NOT help with anycast flaps: the new PoP "
        "still has no TLS state for the connection and cannot decrypt the packets.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Cross-PoP state sharing:</b> Synchronizing connection state across "
        "globally distributed PoPs in real-time is impractical at scale. The state includes TLS session "
        "keys, sequence numbers, flow control windows, and application state -- hundreds of bytes that "
        "change with every packet.",
        bullet_style
    ))

    elements.append(Paragraph(
        "Anycast is fundamentally incompatible with stateful connections: BGP route changes "
        "silently redirect packets to PoPs that cannot process them.",
        negative_style
    ))

    elements.append(Paragraph("The Solution: Two-Phase Routing with QUIC Migration", h2))
    elements.append(Paragraph(
        "QUIC server-side migration introduces a two-phase routing model that combines the strengths "
        "of anycast (fast initial routing) with the stability of unicast (reliable connection lifetime). "
        "The insight is simple: use anycast only for the initial handshake (Phase 1), then immediately "
        "migrate the connection to a dedicated unicast backend (Phase 2). Once migrated, the connection "
        "is on a direct client-to-backend path that is completely independent of anycast routing.",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 1 -- Anycast Discovery (1 RTT):</b> Client connects to the anycast VIP. "
        "BGP routes the Initial packet to the nearest PoP. The PoP completes the TLS 1.3 handshake and "
        "includes a preferred_address transport parameter advertising the unicast backend address.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Phase 2 -- Unicast Stability (connection lifetime):</b> Client validates "
        "the new path via PATH_CHALLENGE/PATH_RESPONSE and migrates. All subsequent traffic flows on "
        "the direct unicast path. Anycast routing changes have zero effect.",
        bullet_style
    ))
    elements.append(Paragraph(
        "Two-phase routing: use anycast for fast discovery (1 RTT), then pin to "
        "unicast for the entire connection lifetime. Best of both worlds.",
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
    elements.append(Spacer(1, 10))

    # ── DIAGRAM 1: Anycast Simulation ──
    # Build diagram first, then wrap heading + diagram in KeepTogether
    d1 = Drawing(470, 280)
    # Background
    d1.add(Rect(0, 0, 470, 280, fillColor=HexColor("#fafbfc"), strokeColor=BORDER,
                strokeWidth=0.5))

    # Client box
    draw_box(d1, 15, 110, 110, 60, "Client", "(.127)", fill=LIGHT_BLUE, stroke=MED_BLUE)

    # Primary box
    draw_box(d1, 310, 190, 130, 60, 'Primary "PoP"', "(.152)", fill=ORANGE_BG, stroke=ORANGE)

    # Preferred box
    draw_box(d1, 310, 30, 130, 60, 'Preferred "Backend"', "(.143)", fill=GREEN_BG, stroke=GREEN)

    # Arrow: Client -> Primary (DNAT)
    draw_arrow(d1, 125, 155, 308, 215, color=ORANGE, width=1.5)
    draw_label(d1, 200, 200, "iptables DNAT", color=ORANGE, font_size=7,
               font="Helvetica-Bold")
    draw_label(d1, 200, 190, "10.99.99.1:4433", color=DARK_GRAY, font_size=7)
    draw_label(d1, 200, 180, "VIP -> .152", color=DARK_GRAY, font_size=7)

    # Arrow: Primary -> Preferred (state transfer)
    draw_arrow(d1, 375, 188, 375, 92, color=PURPLE, width=1.5)
    draw_label(d1, 400, 145, "State Transfer", color=PURPLE, font_size=7,
               font="Helvetica-Bold", anchor="start")
    draw_label(d1, 400, 135, "(445 bytes)", color=PURPLE, font_size=7, anchor="start")

    # Label: preferred_address
    draw_label(d1, 160, 130, "preferred_address = .143:4433", color=MED_BLUE,
               font_size=7, font="Helvetica-Oblique")

    # Arrow: Client -> Preferred (PATH_CHALLENGE/RESPONSE)
    draw_arrow(d1, 125, 130, 308, 65, color=GREEN, width=1.5, dashed=True)
    draw_label(d1, 190, 85, "PATH_CHALLENGE/RESPONSE", color=GREEN, font_size=7,
               font="Helvetica-Bold")

    # Double arrow: Client <-> Preferred (post-migration)
    draw_double_arrow(d1, 125, 115, 308, 52, color=GREEN)
    draw_label(d1, 160, 65, "Direct unicast traffic", color=GREEN, font_size=7,
               font="Helvetica-Bold")
    draw_label(d1, 160, 55, "(post-migration)", color=GREEN, font_size=7)

    # Title
    draw_label(d1, 235, 265, "Anycast Simulation with QUIC Migration", color=DARK_BLUE,
               font_size=10, font="Helvetica-Bold")

    elements.append(KeepTogether([
        Paragraph("Anycast Simulation Diagram", h2),
        d1,
        Spacer(1, 8),
    ]))

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
    # 3. DNS RESOLUTION FLOW
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. DNS Resolution Flow", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "A local dnsmasq instance resolves a test domain (e.g., quic-migration.test) to the primary "
        "server IP. This simulates GeoDNS behavior where a CDN's authoritative DNS returns the IP of "
        "the nearest anycast PoP. In a production deployment, this would be a real GeoDNS service "
        "(e.g., AWS Route53 Geolocation, Cloudflare Load Balancing) returning the anycast VIP.",
        body
    ))

    # ── DIAGRAM 2: DNS Resolution Flow ──
    d2 = Drawing(470, 200)
    d2.add(Rect(0, 0, 470, 200, fillColor=HexColor("#fafbfc"), strokeColor=BORDER,
                strokeWidth=0.5))

    # Title
    draw_label(d2, 235, 185, "DNS Resolution Flow", color=DARK_BLUE,
               font_size=10, font="Helvetica-Bold")

    # Boxes (vertical lifelines)
    draw_box(d2, 15, 135, 95, 35, "Client", None, fill=LIGHT_BLUE, stroke=MED_BLUE)
    draw_box(d2, 175, 135, 110, 35, "dnsmasq", "(127.0.0.1)", fill=LIGHT_PURPLE, stroke=PURPLE)
    draw_box(d2, 350, 135, 105, 35, "Primary", "(.152)", fill=ORANGE_BG, stroke=ORANGE)

    # Lifelines
    d2.add(Line(62, 135, 62, 25, strokeColor=BORDER, strokeWidth=0.8, strokeDashArray=[3, 3]))
    d2.add(Line(230, 135, 230, 55, strokeColor=BORDER, strokeWidth=0.8, strokeDashArray=[3, 3]))
    d2.add(Line(402, 135, 402, 25, strokeColor=BORDER, strokeWidth=0.8, strokeDashArray=[3, 3]))

    # DNS query: Client -> dnsmasq
    draw_arrow(d2, 62, 115, 228, 115, color=MED_BLUE, width=1.2)
    draw_label(d2, 145, 120, "DNS query: quic-migration.test", color=MED_BLUE, font_size=7)

    # DNS response: dnsmasq -> Client
    draw_arrow(d2, 228, 95, 64, 95, color=PURPLE, width=1.2)
    draw_label(d2, 145, 100, "DNS response: 141.217.168.152", color=PURPLE, font_size=7)

    # QUIC connect: Client -> Primary
    draw_arrow(d2, 62, 65, 400, 65, color=ORANGE, width=1.5)
    draw_label(d2, 230, 72, "QUIC CONNECT to .152:4433 (via VIP DNAT)", color=ORANGE, font_size=7,
               font="Helvetica-Bold")

    # Handshake response
    draw_arrow(d2, 400, 45, 64, 45, color=GREEN, width=1.2, dashed=True)
    draw_label(d2, 230, 50, "Handshake + preferred_address = .143:4433", color=GREEN, font_size=7)

    elements.append(d2)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "<bullet>&bull;</bullet>dnsmasq resolves the test domain to the primary IP (simulates GeoDNS)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>Client resolves domain, connects to VIP, DNAT routes to primary",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet>In production, the DNS response would return the anycast VIP directly; "
        "BGP routing handles PoP selection transparently",
        bullet_style
    ))

    elements.append(Paragraph("DNS TTL vs Anycast Failover vs QUIC Migration", h3))
    elements.append(Paragraph(
        "These three mechanisms operate at fundamentally different time scales for traffic redirection:",
        body
    ))

    latency_table = make_table(
        ["Mechanism", "Failover Time", "Granularity", "Connection Impact"],
        [
            ["DNS TTL expiry", "30s - 24h (TTL-dependent)",
             "Per-domain, all clients", "None (only affects new connections after TTL)"],
            ["BGP/Anycast convergence", "1s - 90s (BGP timers)",
             "Per-prefix, per-router", "Catastrophic: existing connections break"],
            ["QUIC preferred_address", "~1 RTT (~1-50ms LAN/WAN)",
             "Per-connection", "None: migration is transparent to application"],
        ],
        col_widths=[1.5*inch, 1.6*inch, 1.4*inch, 2.0*inch],
        highlight_row=3
    )
    elements.append(latency_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "QUIC migration operates at per-connection granularity in ~1 RTT, "
        "making it orders of magnitude faster and more precise than DNS or BGP failover.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 4. IPTABLES DNAT IN DETAIL
    # ══════════════════════════════════════════
    elements.append(Paragraph("4. iptables DNAT Explained", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("VIP Setup on Loopback Interface", h2))
    elements.append(Paragraph(
        "The virtual IP (VIP) 10.99.99.1 is assigned to the loopback interface rather than a physical "
        "NIC. This is a deliberate design choice:",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Why loopback, not a real interface:</b> Assigning the VIP to a physical "
        "interface would cause ARP responses on the LAN, potentially conflicting with other hosts. The "
        "loopback interface is purely local -- it accepts traffic from the kernel's network stack without "
        "any L2 (Ethernet/ARP) involvement.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Kernel behavior:</b> When the client application connects to 10.99.99.1, "
        "the kernel finds the VIP on the loopback interface and would normally deliver the packet locally. "
        "The DNAT rule intercepts the packet in the OUTPUT chain before local delivery, rewriting the "
        "destination IP to the real primary server address.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Production parallel:</b> In real anycast, the VIP would be the anycast "
        "IP announced via BGP. No loopback trick is needed -- BGP routing naturally directs packets to "
        "the nearest PoP.",
        bullet_style
    ))

    elements.append(Paragraph("VIP Assignment", h3))
    elements.append(Paragraph(
        "sudo ip addr add 10.99.99.1/32 dev lo",
        code_style
    ))

    elements.append(Paragraph("DNAT Rules Explained", h2))
    elements.append(Paragraph(
        "The iptables rules operate in the <b>nat</b> table, <b>OUTPUT</b> chain. The OUTPUT chain is "
        "used (rather than PREROUTING) because the traffic originates from the local machine. The rule "
        "matches packets destined for the VIP on UDP port 4433 (QUIC) and rewrites the destination IP.",
        body
    ))

    elements.append(Paragraph("Setup Rule (route VIP to primary):", h3))
    elements.append(Paragraph(
        "sudo iptables -t nat -A OUTPUT -d 10.99.99.1 -p udp --dport 4433 "
        "-j DNAT --to-destination 141.217.168.152:4433",
        code_style
    ))

    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>-t nat:</b> Operate on the nat table (address translation)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>-A OUTPUT:</b> Append to the OUTPUT chain (locally-originated packets)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>-d 10.99.99.1:</b> Match packets destined for the VIP",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>-p udp --dport 4433:</b> Match QUIC traffic (UDP port 4433)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>-j DNAT --to-destination:</b> Rewrite destination IP to the primary server",
        bullet_style
    ))

    elements.append(Paragraph("Route Flap Rule (simulate BGP change):", h3))
    elements.append(Paragraph(
        "# Delete old rule, add new one pointing to alternate PoP\n"
        "sudo iptables -t nat -D OUTPUT -d 10.99.99.1 -p udp --dport 4433 "
        "-j DNAT --to-destination 141.217.168.152:4433\n"
        "sudo iptables -t nat -A OUTPUT -d 10.99.99.1 -p udp --dport 4433 "
        "-j DNAT --to-destination 141.217.168.200:4433",
        code_style
    ))

    elements.append(Paragraph(
        "Key: After migration, the client talks directly to .143 on a unicast path. "
        "The DNAT rule only affects NEW connections through the VIP -- migrated "
        "connections bypass DNAT entirely.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 5. ROUTE FLAP TEST
    # ══════════════════════════════════════════
    elements.append(Paragraph("5. Route Flap Resilience", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The route flap test is the core demonstration of the PoC. It proves that QUIC migration "
        "makes connections resilient to anycast route changes.",
        body
    ))

    # ── DIAGRAM 3: Route Flap Before/After ──
    d3 = Drawing(470, 230)
    d3.add(Rect(0, 0, 470, 230, fillColor=HexColor("#fafbfc"), strokeColor=BORDER,
                strokeWidth=0.5))

    # Title
    draw_label(d3, 235, 215, "Route Flap: Before vs After", color=DARK_BLUE,
               font_size=10, font="Helvetica-Bold")

    # Divider line
    d3.add(Line(235, 205, 235, 10, strokeColor=BORDER, strokeWidth=1,
                strokeDashArray=[5, 3]))

    # ── LEFT: Before BGP Flap ──
    draw_label(d3, 117, 198, "BEFORE BGP FLAP", color=DARK_BLUE,
               font_size=9, font="Helvetica-Bold")

    # VIP routing label
    draw_label(d3, 117, 182, "VIP -> .152 (Primary)", color=ORANGE,
               font_size=8, font="Helvetica-Bold")

    # Existing connection box
    d3.add(Rect(15, 115, 210, 55, fillColor=GREEN_BG, strokeColor=GREEN, strokeWidth=1))
    draw_label(d3, 120, 155, "Existing connection:", color=DARK_GRAY,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 120, 142, ".127  <-->  .143 (direct unicast)", color=GREEN,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 120, 125, "WORKS! (unicast, not VIP)", color=GREEN,
               font_size=8)

    # New connection box
    d3.add(Rect(15, 45, 210, 55, fillColor=LIGHT_BLUE, strokeColor=MED_BLUE, strokeWidth=1))
    draw_label(d3, 120, 85, "New connections:", color=DARK_GRAY,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 120, 72, ".127 -> VIP -> .152 (Primary)", color=MED_BLUE,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 120, 55, "Normal routing to primary PoP", color=DARK_GRAY,
               font_size=8)

    # ── RIGHT: After BGP Flap ──
    draw_label(d3, 352, 198, "AFTER BGP FLAP", color=ACCENT,
               font_size=9, font="Helvetica-Bold")

    # VIP routing label (changed)
    draw_label(d3, 352, 182, "VIP -> .200 (New PoP)", color=ACCENT,
               font_size=8, font="Helvetica-Bold")

    # Existing connection box (still works!)
    d3.add(Rect(245, 115, 210, 55, fillColor=GREEN_BG, strokeColor=GREEN, strokeWidth=1))
    draw_label(d3, 350, 155, "Existing connection:", color=DARK_GRAY,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 350, 142, ".127  <-->  .143 (direct unicast)", color=GREEN,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 350, 125, "STILL WORKS! Immune to flap!", color=GREEN,
               font_size=8)

    # New connection box (goes to .200)
    d3.add(Rect(245, 45, 210, 55, fillColor=ORANGE_BG, strokeColor=ORANGE, strokeWidth=1))
    draw_label(d3, 350, 85, "New connections:", color=DARK_GRAY,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 350, 72, ".127 -> VIP -> .200 (New PoP)", color=ORANGE,
               font_size=8, font="Helvetica-Bold")
    draw_label(d3, 350, 55, "Different PoP, different server", color=DARK_GRAY,
               font_size=8)

    # Checkmarks
    draw_label(d3, 25, 20, "Existing: unicast path (immune)", color=GREEN, font_size=7,
               font="Helvetica-Bold", anchor="start")
    draw_label(d3, 255, 20, "Existing: STILL immune! New: rerouted.", color=ORANGE, font_size=7,
               font="Helvetica-Bold", anchor="start")

    elements.append(KeepTogether([
        Paragraph("Before vs After BGP Flap", h2),
        d3,
        Spacer(1, 8),
    ]))

    elements.append(Paragraph("Test Procedure", h2))

    steps = [
        ("<b>Step 1:</b> Establish connection through VIP -> primary (.152) -> "
         "migration -> preferred (.143). Connection is now on unicast path."),
        ("<b>Step 2:</b> Change DNAT rule: VIP (10.99.99.1) now routes to .200 instead of .152. "
         "This simulates a BGP route change that would redirect anycast traffic to a different PoP."),
        ("<b>Step 3:</b> Verify that the <b>migrated connection SURVIVES</b>. It is on the direct "
         "unicast path to .143 and is unaffected by the DNAT change."),
        ("<b>Step 4:</b> Establish a <b>new</b> connection through VIP. It goes to .200 (the new "
         "PoP), demonstrating that the route change did take effect for new connections."),
    ]
    for step in steps:
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
    # 6. SCRIPTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("6. Scripts", h1))
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
             "(quic-migration.test) to the primary server IP, simulating GeoDNS",
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
    # 7. HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("7. How to Run", h1))
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
    # 8. CDN USE CASE
    # ══════════════════════════════════════════
    elements.append(Paragraph("8. CDN Use Case: Anycast with Backend Pinning", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "Major CDN providers like Cloudflare, Akamai, and Fastly use anycast extensively to route "
        "clients to the nearest edge PoP. However, long-lived connections (video streaming, WebSocket, "
        "gRPC streams, large file downloads) are vulnerable to BGP flaps. QUIC migration offers a "
        "production-grade solution: <b>anycast for discovery, unicast for connection lifetime</b>.",
        body
    ))

    elements.append(Paragraph("Cloudflare/Akamai-Style Deployment", h2))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Edge PoPs (anycast):</b> 200+ data centers worldwide announce the same "
        "IP prefix. Each PoP handles TLS handshakes and serves as the initial QUIC endpoint.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Origin/Mid-tier (unicast):</b> Dedicated backend servers with stable "
        "unicast IPs handle the actual application logic. The PoP's preferred_address points to the "
        "assigned backend for each connection.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Backend selection:</b> The PoP selects the optimal backend based on "
        "connection metadata (geo, load, content affinity) during the handshake, then migrates.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>BGP flap immunity:</b> Once migrated, the connection is pinned to the "
        "unicast backend. BGP flaps at the anycast layer only affect new connections (which get routed "
        "to whichever PoP is now nearest).",
        bullet_style
    ))

    elements.append(Paragraph("Connection Lifecycle in Production", h2))

    lifecycle_table = make_table(
        ["Phase", "Duration", "Path", "Vulnerability"],
        [
            ["DNS resolution", "~50ms", "Client -> DNS -> anycast VIP",
             "DNS cache poisoning"],
            ["Anycast routing", "~1ms (LAN) / ~20ms (WAN)", "Client -> nearest PoP (BGP)",
             "BGP flap (pre-migration)"],
            ["TLS 1.3 handshake", "1 RTT (~1-50ms)", "Client <-> PoP",
             "BGP flap during handshake"],
            ["Migration", "1 RTT (~1-50ms)", "Client -> Backend (PATH_CHALLENGE)",
             "None (validated path)"],
            ["Application data", "Seconds to hours", "Client <-> Backend (direct unicast)",
             "None (immune to anycast)"],
        ],
        col_widths=[1.3*inch, 1.3*inch, 2.0*inch, 1.9*inch],
        highlight_row=5
    )
    elements.append(lifecycle_table)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "The vulnerability window is extremely small: only during the TLS handshake (~1 RTT) "
        "is the connection susceptible to BGP flaps. After migration completes, the connection "
        "is fully immune for its entire remaining lifetime.",
        highlight_style
    ))

    elements.append(Paragraph("State Transfer Considerations", h2))
    elements.append(Paragraph(
        "The migration state (TLS secrets, CIDs, packet numbers) is only 445 bytes. This makes "
        "state transfer practical even at CDN scale. Our implementation supports multiple transfer "
        "backends (TCP push, Redis KV, Redis Pub/Sub, HTTP pull, file) to match different deployment "
        "architectures:",
        body
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>TCP Push (lowest latency):</b> Direct TCP connection from PoP to backend. "
        "Best for co-located PoP/backend pairs.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Redis KV (best scalability):</b> State stored in shared Redis. Backend "
        "polls or receives notification. Best for multi-backend deployments.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>HTTP Pull (best security):</b> Backend pulls state from PoP on demand. "
        "TLS secrets never leave the PoP's memory until explicitly requested.",
        bullet_style
    ))

    # ══════════════════════════════════════════
    # 9. PRODUCTION DEPLOYMENT
    # ══════════════════════════════════════════
    elements.append(Paragraph("9. Production Deployment Considerations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("From PoC to Production", h2))
    elements.append(Paragraph(
        "The PoC uses iptables DNAT to simulate anycast on a LAN. A production deployment would "
        "replace this with real BGP anycast infrastructure:",
        body
    ))

    poc_vs_prod = make_table(
        ["Component", "PoC (This Implementation)", "Production"],
        [
            ["Anycast routing", "iptables DNAT on client loopback",
             "BGP anycast: same /24 announced from multiple PoPs"],
            ["DNS resolution", "Local dnsmasq (quic-migration.test)",
             "GeoDNS (Route53, Cloudflare) or anycast DNS"],
            ["PoP selection", "Single primary (.152)",
             "BGP shortest-path to nearest of N PoPs"],
            ["Backend selection", "Hardcoded preferred_address (.143)",
             "Dynamic: load-based, geo-based, or content-affinity"],
            ["State transfer", "TCP push / Redis / HTTP (445 bytes)",
             "Same backends, production-hardened (TLS, auth, retry)"],
            ["Route flap simulation", "iptables rule change",
             "Actual BGP withdrawal / announcement"],
            ["Client", "neqo-client / Firefox",
             "Any RFC 9000-compliant QUIC client"],
        ],
        col_widths=[1.3*inch, 2.5*inch, 2.7*inch]
    )
    elements.append(poc_vs_prod)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Real BGP Anycast Requirements", h2))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>AS number:</b> Each PoP announces the same IP prefix from the same ASN "
        "(or via BGP communities for multi-ASN setups)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>IP prefix:</b> A /24 is the minimum prefix size accepted by most transit "
        "providers. The anycast VIP sits within this prefix.",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>BGP sessions:</b> Each PoP peers with upstream transit providers and IXPs, "
        "announcing the anycast prefix with appropriate AS-path and communities",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>Health checks:</b> BGP announcements are withdrawn when a PoP is unhealthy, "
        "causing traffic to shift to the next-nearest PoP (which then migrates connections to its backend)",
        bullet_style
    ))
    elements.append(Paragraph(
        "<bullet>&bull;</bullet><b>ECMP handling:</b> Equal-Cost Multi-Path routing may split flows across "
        "PoPs. Connection IDs in QUIC help, but pre-migration traffic must reach the same PoP.",
        bullet_style
    ))

    elements.append(Paragraph(
        "Note: The PoC's iptables DNAT accurately models the packet-level behavior of anycast "
        "routing. The only difference is WHERE the routing decision happens (client kernel "
        "vs Internet backbone routers).",
        warning_style
    ))

    # ══════════════════════════════════════════
    # 10. COMPARISON
    # ══════════════════════════════════════════
    elements.append(Paragraph("10. Comparison", h1))
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
        highlight_row=3
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

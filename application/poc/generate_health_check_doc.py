#!/usr/bin/env python3
"""Generate Health-Checked Migration PoC PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line, Rect, String, Group
from reportlab.graphics import renderPDF
from datetime import date

OUTPUT = "/home/anik/code/quic/application/poc/HEALTH_CHECK_POC.pdf"

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
CODE_BG = HexColor("#edf2f7")

# Drawing colors
DRAW_CLIENT = HexColor("#2b6cb0")
DRAW_PRIMARY = HexColor("#276749")
DRAW_PREFERRED = HexColor("#c05621")
DRAW_ARROW = HexColor("#4a5568")
DRAW_LABEL = HexColor("#2d3748")
DRAW_RED = HexColor("#e53e3e")
DRAW_LIGHT_BG = HexColor("#f7fafc")


def _draw_arrowhead(d, x, y, direction="right", color=DRAW_ARROW, size=4):
    """Draw a small triangular arrowhead."""
    from reportlab.graphics.shapes import Polygon
    if direction == "right":
        pts = [x, y, x - size, y + size/2, x - size, y - size/2]
    elif direction == "left":
        pts = [x, y, x + size, y + size/2, x + size, y - size/2]
    elif direction == "down":
        pts = [x, y, x - size/2, y + size, x + size/2, y + size]
    elif direction == "up":
        pts = [x, y, x - size/2, y - size, x + size/2, y - size]
    else:
        return
    poly = Polygon(pts, fillColor=color, strokeColor=color, strokeWidth=0.5)
    d.add(poly)


def build_success_diagram():
    """Build the successful migration architecture diagram."""
    W, H = 480, 340
    d = Drawing(W, H)

    # Background
    d.add(Rect(0, 0, W, H, fillColor=DRAW_LIGHT_BG, strokeColor=BORDER, strokeWidth=0.5))

    # Title
    d.add(String(W/2, H - 18, "Successful Migration Flow (Health Check Passes)",
                 fontSize=10, fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))

    # Column x-positions
    cx, px, prx = 70, 240, 400
    top_y = H - 40
    box_w, box_h = 100, 32

    # Entity boxes
    for x, label, sub, color in [
        (cx, "Client", "(.127)", DRAW_CLIENT),
        (px, "Primary", "(.152)", DRAW_PRIMARY),
        (prx, "Preferred", "(.143)", DRAW_PREFERRED),
    ]:
        d.add(Rect(x - box_w/2, top_y - box_h, box_w, box_h,
                    fillColor=color, strokeColor=color, rx=4))
        d.add(String(x, top_y - 13, label,
                     fontSize=9, fontName="Helvetica-Bold", fillColor=white, textAnchor="middle"))
        d.add(String(x, top_y - 25, sub,
                     fontSize=7, fontName="Helvetica", fillColor=white, textAnchor="middle"))

    # Vertical lifelines
    lifeline_top = top_y - box_h - 4
    lifeline_bot = 14
    for x, color in [(cx, DRAW_CLIENT), (px, DRAW_PRIMARY), (prx, DRAW_PREFERRED)]:
        d.add(Line(x, lifeline_top, x, lifeline_bot,
                   strokeColor=color, strokeWidth=1, strokeDashArray=[3, 3]))

    # Message arrows
    y = lifeline_top - 20
    step = 36

    def arrow(x1, x2, y_pos, label, color=DRAW_ARROW, dashed=False):
        dash = [4, 2] if dashed else None
        d.add(Line(x1, y_pos, x2, y_pos, strokeColor=color, strokeWidth=1.2, strokeDashArray=dash))
        direction = "right" if x2 > x1 else "left"
        _draw_arrowhead(d, x2, y_pos, direction, color)
        mid = (x1 + x2) / 2
        d.add(String(mid, y_pos + 5, label,
                     fontSize=7, fontName="Helvetica", fillColor=DRAW_LABEL, textAnchor="middle"))

    def note(x_pos, y_pos, text, color=DRAW_LABEL):
        d.add(String(x_pos, y_pos, text,
                     fontSize=6.5, fontName="Helvetica-Oblique", fillColor=color, textAnchor="middle"))

    # 1. Health Probe
    arrow(px, prx, y, "Health Probe (TCP 9998)", DRAW_PRIMARY)
    y -= 14
    arrow(prx, px, y, "CONNECTED", DRAW_PREFERRED, dashed=True)
    note(prx + 50, y + 14, "Health Listener", DRAW_PREFERRED)
    note(prx + 50, y + 5, "(port 9998)", DRAW_PREFERRED)

    y -= step

    # 2. QUIC Handshake with preferred_address
    arrow(px, cx, y, "QUIC Handshake", DRAW_PRIMARY)
    note(px - 15, y - 10, "preferred_address = .143:4433", DRAW_PRIMARY)

    y -= step

    # 3. State Transfer
    arrow(px, prx, y, "State Transfer (TCP 9999)", DRAW_PRIMARY)
    note(prx + 50, y + 5, "State Receiver", DRAW_PREFERRED)
    note(prx + 50, y - 5, "(port 9999)", DRAW_PREFERRED)
    note((px + prx) / 2, y - 10, "(445 bytes)", DRAW_LABEL)

    y -= step

    # 4. PATH_CHALLENGE
    arrow(cx, prx, y, "PATH_CHALLENGE", DRAW_CLIENT)

    y -= step * 0.7

    # 5. PATH_RESPONSE
    arrow(prx, cx, y, "PATH_RESPONSE", DRAW_PREFERRED)

    y -= step * 0.7

    # 6. Direct traffic
    d.add(Line(cx, y, prx, y, strokeColor=DRAW_CLIENT, strokeWidth=2))
    _draw_arrowhead(d, prx, y, "right", DRAW_CLIENT, 5)
    d.add(Line(cx, y - 6, prx, y - 6, strokeColor=DRAW_PREFERRED, strokeWidth=2))
    _draw_arrowhead(d, cx, y - 6, "left", DRAW_PREFERRED, 5)
    d.add(String((cx + prx) / 2, y + 6, "Direct traffic (migration complete)",
                 fontSize=7, fontName="Helvetica-Bold", fillColor=GREEN, textAnchor="middle"))

    return d


def build_failure_diagram():
    """Build the failure scenario diagram (preferred server down)."""
    W, H = 480, 240
    d = Drawing(W, H)

    # Background
    d.add(Rect(0, 0, W, H, fillColor=HexColor("#fff8f8"), strokeColor=ACCENT, strokeWidth=0.5))

    # Title
    d.add(String(W/2, H - 18, "Failure Scenario: Preferred Server Down",
                 fontSize=10, fontName="Helvetica-Bold", fillColor=ACCENT, textAnchor="middle"))

    # Column x-positions
    cx, px, prx = 70, 240, 400
    top_y = H - 40
    box_w, box_h = 100, 32

    # Entity boxes
    for x, label, sub, color in [
        (cx, "Client", "(.127)", DRAW_CLIENT),
        (px, "Primary", "(.152)", DRAW_PRIMARY),
    ]:
        d.add(Rect(x - box_w/2, top_y - box_h, box_w, box_h,
                    fillColor=color, strokeColor=color, rx=4))
        d.add(String(x, top_y - 13, label,
                     fontSize=9, fontName="Helvetica-Bold", fillColor=white, textAnchor="middle"))
        d.add(String(x, top_y - 25, sub,
                     fontSize=7, fontName="Helvetica", fillColor=white, textAnchor="middle"))

    # Preferred (DOWN) box
    d.add(Rect(prx - box_w/2, top_y - box_h, box_w, box_h,
                fillColor=ACCENT, strokeColor=ACCENT, rx=4))
    d.add(String(prx, top_y - 13, "Preferred [DOWN]",
                 fontSize=9, fontName="Helvetica-Bold", fillColor=white, textAnchor="middle"))
    d.add(String(prx, top_y - 25, "(.143)",
                 fontSize=7, fontName="Helvetica", fillColor=white, textAnchor="middle"))

    # Big X over preferred
    x_sz = 14
    x_cx, x_cy = prx, top_y - box_h - 20
    d.add(Line(x_cx - x_sz, x_cy - x_sz, x_cx + x_sz, x_cy + x_sz,
               strokeColor=ACCENT, strokeWidth=3))
    d.add(Line(x_cx - x_sz, x_cy + x_sz, x_cx + x_sz, x_cy - x_sz,
               strokeColor=ACCENT, strokeWidth=3))

    # Vertical lifelines
    lifeline_top = top_y - box_h - 4
    lifeline_bot = 14
    for x, color in [(cx, DRAW_CLIENT), (px, DRAW_PRIMARY)]:
        d.add(Line(x, lifeline_top, x, lifeline_bot,
                   strokeColor=color, strokeWidth=1, strokeDashArray=[3, 3]))
    # Preferred lifeline (broken)
    d.add(Line(prx, lifeline_top, prx, lifeline_top - 30,
               strokeColor=ACCENT, strokeWidth=1, strokeDashArray=[2, 4]))

    # Messages
    y = lifeline_top - 24
    step = 36

    def arrow(x1, x2, y_pos, label, color=DRAW_ARROW, dashed=False):
        dash = [4, 2] if dashed else None
        d.add(Line(x1, y_pos, x2, y_pos, strokeColor=color, strokeWidth=1.2, strokeDashArray=dash))
        direction = "right" if x2 > x1 else "left"
        _draw_arrowhead(d, x2, y_pos, direction, color)
        mid = (x1 + x2) / 2
        d.add(String(mid, y_pos + 5, label,
                     fontSize=7, fontName="Helvetica", fillColor=DRAW_LABEL, textAnchor="middle"))

    def note(x_pos, y_pos, text, color=DRAW_LABEL):
        d.add(String(x_pos, y_pos, text,
                     fontSize=6.5, fontName="Helvetica-Oblique", fillColor=color, textAnchor="middle"))

    # 1. Health Probe REFUSED
    arrow(px, prx - 10, y, "Health Probe (TCP 9998)", DRAW_PRIMARY)
    d.add(String(prx + 10, y + 5, "REFUSED",
                 fontSize=8, fontName="Helvetica-Bold", fillColor=ACCENT, textAnchor="start"))

    y -= step

    # 2. QUIC Handshake WITHOUT preferred_address
    arrow(px, cx, y, "QUIC Handshake", DRAW_PRIMARY)
    note(px - 15, y - 10, "NO preferred_address (serves directly)", DRAW_PRIMARY)

    y -= step

    # 3. Direct traffic to primary
    d.add(Line(cx, y, px, y, strokeColor=DRAW_CLIENT, strokeWidth=2))
    _draw_arrowhead(d, px, y, "right", DRAW_CLIENT, 5)
    d.add(Line(cx, y - 6, px, y - 6, strokeColor=DRAW_PRIMARY, strokeWidth=2))
    _draw_arrowhead(d, cx, y - 6, "left", DRAW_PRIMARY, 5)
    d.add(String((cx + px) / 2, y + 6, "Direct traffic (no migration, zero errors)",
                 fontSize=7, fontName="Helvetica-Bold", fillColor=GREEN, textAnchor="middle"))

    return d


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
        backColor=CODE_BG, borderColor=BORDER,
        borderWidth=0.5, borderPadding=8,
        spaceBefore=6, spaceAfter=6,
        leftIndent=10, textColor=DARK_GRAY,
        alignment=TA_LEFT,
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

    # -- Helper for tables --
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

    # ==============================
    # TITLE PAGE
    # ==============================
    elements.append(Spacer(1, 1.2*inch))
    elements.append(Paragraph("Health-Checked Migration", title_style))
    elements.append(Paragraph("Proof of Concept", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Pre-Validation of Preferred Servers Before QUIC Connection Migration",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"PoC Documentation &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.6*inch))

    # Abstract
    abstract_text = (
        "This document describes the Health-Checked Migration proof of concept, which adds "
        "pre-validation of the preferred server before advertising <font name='Courier' size='9'>"
        "preferred_address</font> in the QUIC handshake. "
        "Without health checking, a primary server unconditionally advertises a preferred address; "
        "if the preferred server is down, the client experiences a PATH_CHALLENGE timeout (100-600ms). "
        "Our PoC implements two health check modes -- <b>TCP Probe</b> and <b>Redis Heartbeat</b> -- "
        "that allow the primary server to detect preferred server failures and gracefully fall back "
        "to serving clients directly. Health probes use a <b>dedicated port 9998</b>, fully separated "
        "from the state transfer port 9999, preventing probe interference with migration state "
        "channels. The result is zero user-visible errors during preferred server outages, "
        "with negligible added latency (&lt;0.2ms per connection)."
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

    # ==============================
    # TABLE OF CONTENTS
    # ==============================
    elements.append(Paragraph("Contents", h1))
    toc_items = [
        "1. Overview",
        "    1.1 The Problem",
        "    1.2 The Solution",
        "2. Architecture",
        "    2.1 Testbed",
        "    2.2 Port Separation: Health (9998) vs State (9999)",
        "    2.3 Health Check Modes",
        "    2.4 Migration Flow Diagram (Success)",
        "    2.5 Failure Scenario Diagram",
        "3. Implementation Details",
        "    3.1 Binaries and Configuration",
        "    3.2 Background Health Thread",
        "    3.3 Heartbeat Thread Behavior",
        "    3.4 Redis Heartbeat Protocol",
        "    3.5 Conditional preferred_address",
        "    3.6 HTML Status Page",
        "4. Security Considerations",
        "5. Metrics and Monitoring",
        "6. How to Run",
        "7. Test Scenarios",
        "8. Expected Results",
        "9. Comparison Table",
    ]
    for item in toc_items:
        indent = 20 if item.startswith("    ") else 0
        elements.append(Paragraph(
            item.strip(),
            ParagraphStyle("TOC", parent=body, fontSize=10, leftIndent=indent, spaceAfter=2)
        ))

    elements.append(PageBreak())

    # ==============================
    # SECTION 1: OVERVIEW
    # ==============================
    elements.append(Paragraph("1. Overview", h1))

    elements.append(Paragraph("1.1 The Problem", h2))
    elements.append(Paragraph(
        "In our current QUIC server-side migration implementation, the primary server "
        "<b>unconditionally</b> advertises a <font name='Courier' size='9'>preferred_address</font> "
        "transport parameter during the TLS handshake. This tells the client to migrate its "
        "connection to the preferred server's address. However, if the preferred server is down "
        "or unreachable at the time of migration, the client sends a PATH_CHALLENGE to an "
        "unresponsive host and experiences a timeout.",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Problem: The client has no way to know the preferred server is down until "
        "PATH_CHALLENGE times out (100-600ms depending on implementation). This causes "
        "user-visible latency spikes and potential connection failures.",
        negative_style
    ))

    elements.append(Paragraph("1.2 The Solution", h2))
    elements.append(Paragraph(
        "The solution is to add a <b>health check</b> mechanism: the primary server verifies "
        "that the preferred server is alive and ready before advertising "
        "<font name='Courier' size='9'>preferred_address</font> in the handshake. If the "
        "preferred server is unhealthy, the primary simply serves the client directly without "
        "migration -- the client never knows migration was an option.",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Result: Zero failed migrations. If the preferred server is down, clients are served "
        "directly by the primary with no timeout or error.",
        highlight_style
    ))

    # ==============================
    # SECTION 2: ARCHITECTURE
    # ==============================
    elements.append(Paragraph("2. Architecture", h1))

    elements.append(Paragraph("2.1 Testbed", h2))
    elements.append(Paragraph(
        "The PoC uses the same four-machine LAN testbed as our existing migration implementation:",
        body
    ))
    elements.append(make_table(
        ["Role", "Machine", "IP Address", "Ports", "Function"],
        [
            ["Client", "optiplex7010", "141.217.168.127", "--",
             "Firefox browser (HTTP/3)"],
            ["Primary Server", "opti7040", "141.217.168.152", "4433 (QUIC)",
             "TLS handshake, health checks"],
            ["Preferred Server", "homeserver2", "141.217.168.143",
             "4433 (QUIC)\n9998 (health)\n9999 (state)",
             "Imports state, handles PATH_CHALLENGE"],
            ["Redis Server", "Proxmox VM", "141.217.168.200", "6379 (Redis)",
             "Heartbeat key storage (Redis mode)"],
        ],
        col_widths=[0.9*inch, 0.9*inch, 1.1*inch, 1.0*inch, 2.2*inch],
    ))

    # ---- Port Separation Section ----
    elements.append(Paragraph("2.2 Port Separation: Health (9998) vs State (9999)", h2))
    elements.append(Paragraph(
        "A critical design decision in this PoC is the use of a <b>dedicated health check port "
        "(9998)</b>, fully separated from the state transfer port (9999). This separation was "
        "introduced to fix a serious bug in an earlier design:",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Bug (fixed): The original TCP health probe connected to the state transfer port 9999. "
        "When the TCP probe connected and immediately disconnected (as probes do), the preferred "
        "server's TCP state receiver would accept the empty connection and panic, because it "
        "expected to read 445 bytes of migration state but received zero bytes instead.",
        negative_style
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "The fix is straightforward: the preferred server now listens on two separate TCP ports "
        "with distinct responsibilities:",
        body
    ))
    elements.append(make_table(
        ["Port", "Purpose", "Protocol", "Behavior on Connect"],
        [
            ["9998", "Health check endpoint",
             "TCP connect-only (no data exchange)",
             "Accepts connection, immediately closes. No data read/written."],
            ["9999", "Migration state transfer",
             "TCP push (445 bytes of TLS state)",
             "Reads exactly 445 bytes, deserializes MigrationState, imports crypto."],
        ],
        col_widths=[0.6*inch, 1.5*inch, 1.8*inch, 2.2*inch],
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "This separation ensures that health probe connections can never interfere with the "
        "state transfer channel. The health listener is a trivial TCP acceptor that requires "
        "no data exchange -- a successful TCP three-way handshake is sufficient to prove "
        "the preferred server process is running and reachable.",
        body
    ))

    # ---- Health Check Modes ----
    elements.append(Paragraph("2.3 Health Check Modes", h2))
    elements.append(Paragraph(
        "The PoC supports two complementary health check strategies, each with different "
        "trade-offs in detection latency, infrastructure requirements, and failure modes:",
        body
    ))

    elements.append(Paragraph("TCP Probe", h3))
    elements.append(Paragraph(
        "The primary server performs a TCP connect to the preferred server's <b>dedicated "
        "health port (9998)</b> with a <b>200ms timeout</b>. This is a per-connection probe: "
        "before each new QUIC handshake, the primary attempts a TCP connection to the preferred "
        "server. If the connection succeeds, the preferred server is considered healthy and "
        "<font name='Courier' size='9'>preferred_address</font> is advertised. If the "
        "connection fails or times out, the primary serves the client directly.",
        body
    ))
    for b in [
        "Per-connection granularity -- every handshake is individually validated",
        "No external infrastructure required (no Redis dependency)",
        "Probes use port 9998 (health), never port 9999 (state transfer)",
        "Detection latency: bounded by the 200ms TCP timeout",
        "Trade-off: one extra TCP round-trip per connection (~0.1ms on LAN)",
    ]:
        elements.append(Paragraph(b, bullet_style, bulletText="\u2022"))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Redis Heartbeat", h3))
    elements.append(Paragraph(
        "The preferred server publishes a <font name='Courier' size='9'>preferred:health</font> "
        "key to Redis every <b>1 second</b> with a <b>3-second TTL</b>. The primary server "
        "checks this key before each handshake. If the key exists, the preferred server has been "
        "alive within the last 3 seconds. If the key has expired (TTL elapsed), the preferred "
        "server is considered down.",
        body
    ))
    for b in [
        "Decoupled: preferred server does not need to be directly reachable from primary",
        "Requires Redis infrastructure (already available on our testbed at .200)",
        "Detection latency: up to 3s (heartbeat TTL) after preferred server failure",
        "Trade-off: one Redis GET per connection (~0.1ms on LAN)",
    ]:
        elements.append(Paragraph(b, bullet_style, bulletText="\u2022"))

    # ---- Success Diagram ----
    elements.append(PageBreak())
    elements.append(Paragraph("2.4 Migration Flow Diagram (Success)", h2))
    elements.append(Paragraph(
        "The following diagram shows the complete message flow when the health check passes "
        "and migration proceeds. Note the separation of health probe (port 9998) from state "
        "transfer (port 9999):",
        body
    ))
    elements.append(Spacer(1, 6))
    elements.append(build_success_diagram())

    elements.append(Spacer(1, 10))

    # ---- Failure Diagram ----
    elements.append(Paragraph("2.5 Failure Scenario Diagram", h2))
    elements.append(Paragraph(
        "When the preferred server is down, the health probe to port 9998 fails (connection "
        "refused or timeout). The primary omits <font name='Courier' size='9'>preferred_address"
        "</font> from the handshake and serves the client directly. No state transfer occurs, "
        "no PATH_CHALLENGE is sent, and the client experiences zero errors:",
        body
    ))
    elements.append(Spacer(1, 6))
    elements.append(build_failure_diagram())

    # ==============================
    # SECTION 3: IMPLEMENTATION DETAILS
    # ==============================
    elements.append(PageBreak())
    elements.append(Paragraph("3. Implementation Details", h1))

    elements.append(Paragraph("3.1 Binaries and Configuration", h2))
    elements.append(Paragraph(
        "The PoC introduces two new binaries in the <font name='Courier' size='9'>"
        "migration-test/</font> crate:",
        body
    ))

    elements.append(make_table(
        ["Binary", "Description"],
        [
            ["health-check-primary",
             "Modified primary server with health check logic. Conditionally advertises "
             "preferred_address based on health status. Probes port 9998 (not 9999)."],
            ["health-check-preferred",
             "Preferred server with health listener on port 9998 and state receiver on "
             "port 9999. In Redis mode, also publishes heartbeats."],
        ],
        col_widths=[1.8*inch, 4.3*inch],
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Environment Variables", h3))
    elements.append(make_table(
        ["Variable", "Values", "Description"],
        [
            ["HEALTH_CHECK", "tcp | redis | none",
             "Selects the health check mode. Default: none (unconditional migration)."],
            ["HEALTH_PORT", "9998 (default)",
             "TCP port for the dedicated health check listener on the preferred server. "
             "Must differ from the state transfer port."],
            ["REDIS_URL", "redis://141.217.168.200:6379",
             "Redis connection URL for heartbeat mode. Only used when HEALTH_CHECK=redis."],
        ],
        col_widths=[1.3*inch, 2.0*inch, 2.8*inch],
    ))

    elements.append(Paragraph("3.2 Background Health Thread", h2))
    elements.append(Paragraph(
        "The primary server spawns a background thread that continuously monitors the preferred "
        "server's availability. This thread maintains a shared atomic boolean "
        "(<font name='Courier' size='9'>is_healthy</font>) that the main connection-handling "
        "code reads before each handshake.",
        body
    ))

    elements.append(Paragraph("3.3 Heartbeat Thread Behavior", h2))
    elements.append(Paragraph(
        "The background heartbeat thread operates on a fixed <b>5-second polling interval</b>. "
        "Its behavior differs by mode but follows a common pattern:",
        body
    ))
    elements.append(Paragraph(
        "<b>TCP mode:</b> Every 5 seconds, the thread attempts a TCP connect to the preferred "
        "server's health port (9998) with a 200ms timeout. If the connect succeeds, it sets "
        "<font name='Courier' size='9'>is_healthy = true</font>. If it fails (connection refused, "
        "timeout, or network error), it sets <font name='Courier' size='9'>is_healthy = false</font>.",
        body
    ))
    elements.append(Paragraph(
        "<b>Redis mode:</b> Every 5 seconds, the thread performs a "
        "<font name='Courier' size='9'>GET preferred:health</font> against Redis. If the key "
        "exists (i.e., the preferred server has published within the TTL window), health is true. "
        "If the key is absent or Redis is unreachable, health is false.",
        body
    ))
    elements.append(Paragraph(
        "In both modes, the thread <b>only logs when status changes</b>, avoiding log spam "
        "during steady state:",
        body
    ))
    elements.append(Paragraph(
        "[health] preferred server status changed: HEALTHY -> UNHEALTHY<br/>"
        "[health] preferred server status changed: UNHEALTHY -> HEALTHY<br/>"
        "[health] re-check in 5s...",
        code_style
    ))
    elements.append(Paragraph(
        "The 5-second interval is a balance between responsiveness and overhead. On a LAN, each "
        "probe costs ~0.1ms, so 5s polling adds negligible load. The worst-case detection latency "
        "is one full interval (5s) plus the probe timeout (200ms for TCP).",
        body
    ))

    elements.append(Paragraph("3.4 Redis Heartbeat Protocol", h2))
    elements.append(Paragraph(
        "When using the Redis heartbeat mode, the preferred server communicates with Redis "
        "using the <b>RESP (REdis Serialization Protocol)</b>. The heartbeat is a single "
        "<font name='Courier' size='9'>SET</font> command with an expiry:",
        body
    ))
    elements.append(Paragraph(
        "SET preferred:health \"alive\" EX 3",
        code_style
    ))
    elements.append(Paragraph(
        "This command sets the key <font name='Courier' size='9'>preferred:health</font> to "
        "the value <font name='Courier' size='9'>\"alive\"</font> with a <b>3-second TTL</b> "
        "(the <font name='Courier' size='9'>EX 3</font> argument). The preferred server "
        "re-issues this command every 1 second, ensuring the key is always refreshed before "
        "it expires. If the preferred server crashes or becomes unreachable, the key expires "
        "after 3 seconds and the primary detects the absence on its next check.",
        body
    ))
    elements.append(Paragraph("RESP wire format for the SET command:", body))
    elements.append(Paragraph(
        "*5\\r\\n$3\\r\\nSET\\r\\n$16\\r\\npreferred:health\\r\\n"
        "$5\\r\\nalive\\r\\n$2\\r\\nEX\\r\\n$1\\r\\n3\\r\\n",
        code_style
    ))
    elements.append(Paragraph(
        "The primary server reads the key with a simple <font name='Courier' size='9'>"
        "GET preferred:health</font>. A non-nil response means healthy; a nil response "
        "(key expired or never set) means unhealthy.",
        body
    ))

    elements.append(Paragraph("3.5 Conditional preferred_address", h2))
    elements.append(Paragraph(
        "The key modification is in the connection setup path. Before constructing "
        "<font name='Courier' size='9'>ConnectionParameters</font>, the primary checks the "
        "health status:",
        body
    ))
    elements.append(Paragraph(
        "if is_healthy.load(Ordering::Relaxed) {<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;// Set preferred_address in ConnectionParameters<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;// Export and transfer migration state after handshake<br/>"
        "} else {<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;// Serve client directly, no preferred_address<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;// Log: \"preferred server unhealthy, serving directly\"<br/>"
        "}",
        code_style
    ))
    elements.append(Paragraph(
        "When healthy, the server behaves identically to the existing migration flow. "
        "When unhealthy, the server acts as a normal HTTP/3 server with no migration.",
        body
    ))

    elements.append(Paragraph("3.6 HTML Status Page", h2))
    elements.append(Paragraph(
        "The HTTP/3 response page dynamically reflects the migration status. When the "
        "preferred server is healthy, the page shows a green \"HEALTHY\" badge and indicates "
        "that migration is active. When unhealthy, the page shows a red \"UNHEALTHY\" badge "
        "and states that the client is being served directly by the primary.",
        body
    ))

    # ==============================
    # SECTION 4: SECURITY CONSIDERATIONS
    # ==============================
    elements.append(PageBreak())
    elements.append(Paragraph("4. Security Considerations", h1))

    elements.append(Paragraph(
        "The health check mechanism is designed to operate entirely outside the TLS security "
        "boundary. Several security properties are maintained by design:",
        body
    ))

    elements.append(Paragraph("Health probes do not expose TLS secrets", h3))
    elements.append(Paragraph(
        "The TCP health probe on port 9998 performs a bare TCP connect with <b>no data exchange</b>. "
        "The probe establishes a TCP three-way handshake, then immediately closes. No TLS secrets, "
        "connection IDs, or migration state bytes traverse the health channel. The 445-byte "
        "migration state (containing TLS secrets and CIDs) only ever flows through the separate "
        "state transfer channel on port 9999.",
        body
    ))

    elements.append(Paragraph("Port separation prevents state corruption", h3))
    elements.append(Paragraph(
        "Because health probes (port 9998) and state transfer (port 9999) use separate ports, "
        "a malicious actor probing port 9998 cannot inject data into the state transfer channel. "
        "Conversely, the state receiver on port 9999 never accepts probe-style empty connections "
        "that could cause deserialization panics.",
        body
    ))

    elements.append(Paragraph("Redis heartbeat security", h3))
    elements.append(Paragraph(
        "In Redis heartbeat mode, the only data written to Redis is the string "
        "<font name='Courier' size='9'>\"alive\"</font> under the key "
        "<font name='Courier' size='9'>preferred:health</font>. No TLS key material, "
        "connection IDs, or client addresses are stored in Redis for health checking purposes. "
        "The Redis heartbeat is purely a liveness signal. If Redis is compromised, an attacker "
        "could forge or delete the heartbeat key, causing the primary to either always migrate "
        "or never migrate -- but could not intercept or modify TLS-encrypted QUIC traffic.",
        body
    ))

    elements.append(Paragraph("Fail-safe defaults", h3))
    elements.append(Paragraph(
        "All failure modes default to <b>no migration</b>. If the health check infrastructure "
        "itself fails (Redis unreachable, TCP probe error, etc.), the primary serves clients "
        "directly. This means infrastructure failures cause loss of migration capability but "
        "never cause client-visible errors or security degradation.",
        body
    ))

    # ==============================
    # SECTION 5: METRICS AND MONITORING
    # ==============================
    elements.append(Paragraph("5. Metrics and Monitoring", h1))

    elements.append(Paragraph(
        "The health-check-primary server tracks and logs key migration metrics to enable "
        "operational monitoring and debugging:",
        body
    ))

    elements.append(make_table(
        ["Metric", "Type", "Description"],
        [
            ["migration_attempted", "Counter",
             "Total number of connections where the primary advertised preferred_address "
             "and attempted to transfer state."],
            ["migration_succeeded", "Counter",
             "Connections where the preferred server successfully received the migration state "
             "and the client completed PATH_CHALLENGE/PATH_RESPONSE."],
            ["migration_skipped", "Counter",
             "Connections where the health check failed and the primary served the client "
             "directly without advertising preferred_address."],
            ["health_status", "Gauge (boolean)",
             "Current health status of the preferred server as seen by the background thread. "
             "Logged on every status change."],
            ["health_check_latency", "Duration",
             "Time taken by each health probe (TCP connect or Redis GET). Typically <0.2ms "
             "on LAN."],
        ],
        col_widths=[1.5*inch, 1.0*inch, 3.6*inch],
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "These metrics are logged to stdout in a structured format. Example log output during "
        "normal operation:",
        body
    ))
    elements.append(Paragraph(
        "[health] preferred server status: HEALTHY (probe latency: 0.08ms)<br/>"
        "[conn] new connection from 141.217.168.127:52341<br/>"
        "[conn] health check passed, advertising preferred_address<br/>"
        "[conn] migration state exported (445 bytes), sending to .143:9999<br/>"
        "[stats] attempted=14 succeeded=13 skipped=1",
        code_style
    ))
    elements.append(Paragraph(
        "During a preferred server outage:",
        body
    ))
    elements.append(Paragraph(
        "[health] preferred server status changed: HEALTHY -> UNHEALTHY<br/>"
        "[conn] new connection from 141.217.168.127:52355<br/>"
        "[conn] health check FAILED, serving directly (migration_skipped=2)<br/>"
        "[stats] attempted=14 succeeded=13 skipped=2",
        code_style
    ))

    # ==============================
    # SECTION 6: HOW TO RUN
    # ==============================
    elements.append(PageBreak())
    elements.append(Paragraph("6. How to Run", h1))

    elements.append(Paragraph(
        "The PoC is launched from the same machines as the existing migration demo. "
        "The preferred server is started first, followed by the primary.",
        body
    ))

    elements.append(Paragraph("Step 1: Start the Preferred Server (homeserver2)", h3))
    elements.append(Paragraph(
        "health-check-preferred 141.217.168.143:4433 9999 9998",
        code_style
    ))
    elements.append(Paragraph(
        "This starts the preferred server listening on three ports: "
        "<b>4433</b> (QUIC traffic after migration), "
        "<b>9999</b> (TCP state transfer receiver), and "
        "<b>9998</b> (TCP health check listener). "
        "In Redis mode, it also begins publishing heartbeats to Redis every 1 second. "
        "The health listener on port 9998 is a minimal TCP acceptor that requires no "
        "data exchange -- it simply accepts and closes connections.",
        body
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Step 2: Start the Primary Server (opti7040)", h3))
    elements.append(Paragraph(
        "HEALTH_CHECK=tcp health-check-primary 0.0.0.0:4433 \\"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;141.217.168.143:4433 141.217.168.143:9999 "
        "141.217.168.143:9998",
        code_style
    ))
    elements.append(Paragraph(
        "Arguments: (1) local bind address, (2) preferred server QUIC address, "
        "(3) preferred server state-transfer address (port 9999), "
        "(4) preferred server health-check address (port 9998). The "
        "<font name='Courier' size='9'>HEALTH_CHECK</font> variable selects the probe mode. "
        "The health probe always targets port 9998, never port 9999.",
        body
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Step 3: Open Firefox", h3))
    elements.append(Paragraph(
        "Navigate to <font name='Courier' size='9'>https://141.217.168.152:4433/</font>. "
        "The bootstrap server (Alt-Svc) must be running on opti7040 for the first HTTP/3 "
        "upgrade, same as the standard demo. After the first load, refresh to use HTTP/3 "
        "directly.",
        body
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Tip: To switch between TCP and Redis modes, simply change the HEALTH_CHECK "
        "environment variable and restart the primary server. No changes needed on the "
        "preferred server side.",
        warning_style
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Important: The HEALTH_PORT environment variable (default 9998) can be used to "
        "customize the health check port. If changed, ensure both the preferred server and "
        "primary server use the same port value.",
        warning_style
    ))

    # ==============================
    # SECTION 7: TEST SCENARIOS
    # ==============================
    elements.append(Paragraph("7. Test Scenarios", h1))

    scenarios = [
        ("Baseline: Both Servers Up", [
            "Start both servers normally.",
            "Load the page in Firefox -- migration succeeds as usual.",
            "Expected: 100% successful migration, identical to existing demo.",
            "Purpose: Confirms health check adds no regression.",
        ]),
        ("Preferred Down: Kill Preferred Server", [
            "Start both servers, verify migration works.",
            "Kill the preferred server (preferred-down on homeserver2).",
            "Wait 5 seconds for the background health thread to detect the failure.",
            "Load the page in Firefox again.",
            "Expected: Primary detects unhealthy preferred, serves directly. "
            "Zero timeout, zero errors. Page loads normally.",
        ]),
        ("Flapping: Start/Stop Preferred Every 5s", [
            "Start both servers.",
            "In a loop, alternate: kill preferred, wait 5s, start preferred, wait 5s.",
            "Load the page repeatedly during the flapping cycle.",
            "Without health check: random PATH_CHALLENGE timeouts on ~50% of loads.",
            "With health check: graceful fallback, zero timeouts.",
        ]),
        ("Recovery: Preferred Comes Back Up", [
            "Start both servers, then kill the preferred server.",
            "Verify primary serves directly (no migration).",
            "Restart the preferred server.",
            "Wait up to 5 seconds for the background health thread to detect recovery.",
            "Load the page -- migration should resume.",
            "Expected: Automatic recovery with no manual intervention.",
        ]),
    ]

    for title, steps in scenarios:
        elements.append(Paragraph(title, h2))
        for i, step in enumerate(steps, 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {step}", bullet_style
            ))
        elements.append(Spacer(1, 4))

    # ==============================
    # SECTION 8: EXPECTED RESULTS
    # ==============================
    elements.append(Paragraph("8. Expected Results", h1))

    elements.append(Paragraph(
        "The health check mechanism is expected to eliminate all user-visible failures "
        "during preferred server outages:",
        body
    ))

    elements.append(Paragraph(
        "Without health check: When the preferred server is down, clients experience "
        "PATH_CHALLENGE timeouts of 100-600ms. In the worst case, the connection may fail "
        "entirely if the client's retry budget is exhausted.",
        negative_style
    ))
    elements.append(Paragraph(
        "With health check: Zero failed migrations. The primary detects the preferred "
        "server is down and serves clients directly. The transition is invisible to the "
        "client -- no timeout, no retry, no error.",
        highlight_style
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Key Metrics", h2))

    for metric in [
        "<b>Failed migrations:</b> 0% (vs. 100% without health check when preferred is down)",
        "<b>Added latency (healthy path):</b> ~0.1ms per connection (TCP connect or Redis GET)",
        "<b>Detection latency (TCP):</b> &lt;200ms (bounded by TCP timeout, per-connection)",
        "<b>Detection latency (Redis):</b> &lt;3s (bounded by heartbeat TTL)",
        "<b>Recovery time:</b> &lt;5s (background thread polling interval)",
        "<b>User-visible errors:</b> Zero during preferred server failures",
        "<b>Health port:</b> 9998 (dedicated, separate from state port 9999)",
    ]:
        elements.append(Paragraph(metric, bullet_style, bulletText="\u2022"))

    # ==============================
    # SECTION 9: COMPARISON TABLE
    # ==============================
    elements.append(PageBreak())
    elements.append(Paragraph("9. Comparison Table", h1))

    elements.append(Paragraph(
        "The following table compares behavior across all scenarios with and without "
        "health checking enabled:",
        body
    ))
    elements.append(Spacer(1, 6))

    elements.append(make_table(
        ["Scenario", "Without Health Check", "With Health Check (TCP)", "With Health Check (Redis)"],
        [
            ["Preferred healthy",
             "Migration OK",
             "Migration OK",
             "Migration OK"],
            ["Preferred down",
             "Client timeout (100-600ms)",
             "Serves directly (probe to 9998 refused)",
             "Serves directly (key expired)"],
            ["Preferred flapping",
             "Random timeouts",
             "Graceful fallback",
             "Graceful fallback"],
            ["Detection latency",
             "N/A (no detection)",
             "<200ms (per-conn probe to 9998)",
             "<3s (heartbeat TTL)"],
            ["Added latency",
             "0",
             "~0.1ms (TCP connect to 9998)",
             "~0.1ms (Redis GET)"],
            ["Health port used",
             "N/A",
             "9998 (dedicated)",
             "N/A (uses Redis)"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.6*inch, 1.6*inch],
    ))

    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Trade-off Summary", h2))
    elements.append(make_table(
        ["Aspect", "TCP Probe", "Redis Heartbeat"],
        [
            ["Infrastructure", "None (direct TCP to port 9998)", "Requires Redis server"],
            ["Granularity", "Per-connection", "Periodic (1s heartbeat)"],
            ["Detection speed", "Immediate (<200ms)", "Delayed (up to 3s TTL)"],
            ["Health port", "9998 (dedicated, no data exchange)", "N/A (Redis key-based)"],
            ["State port safety", "9999 never touched by probes", "9999 never touched by probes"],
            ["Network topology", "Primary must reach preferred port 9998",
             "Both must reach Redis; no direct link needed"],
            ["Failure mode", "Probe fails = no migration (safe)",
             "Redis down = key absent = no migration (safe)"],
            ["TLS secret exposure", "None (probe is data-free)", "None (only \"alive\" string in Redis)"],
            ["Best for", "Low-latency, simple setups",
             "Multi-datacenter, indirect routing"],
        ],
        col_widths=[1.3*inch, 2.4*inch, 2.4*inch],
    ))

    elements.append(Spacer(1, 14))
    elements.append(Paragraph(
        "Both modes fail safe: if the health check itself fails (e.g., Redis is unreachable "
        "or port 9998 is blocked by a firewall), the primary defaults to serving directly "
        "without migration. This ensures that health check infrastructure failures never "
        "cause client-visible errors.",
        highlight_style
    ))

    # Build
    doc.build(elements)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

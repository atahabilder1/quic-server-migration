#!/usr/bin/env python3
"""Generate QUIC-Native Load Balancer PoC documentation PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.graphics.shapes import (
    Drawing, Rect, Line, String, Group, Polygon
)
from reportlab.graphics import renderPDF
from datetime import date

OUTPUT = "/home/anik/code/quic/application/poc/LOAD_BALANCER_POC.pdf"

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
LIGHT_GRAY = HexColor("#e2e8f0")
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")
TEAL = HexColor("#285e61")
TEAL_BG = HexColor("#e6fffa")


def _arrow_line(d, x1, y1, x2, y2, color=DARK_GRAY, width=1.5, dashed=False):
    """Draw a line with an arrowhead at (x2, y2)."""
    import math
    line = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width)
    if dashed:
        line.strokeDashArray = [4, 3]
    d.add(line)
    # Arrowhead
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 8
    arrow_angle = math.pi / 7
    ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
    ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
    ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
    ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)
    d.add(Polygon(
        [x2, y2, ax1, ay1, ax2, ay2],
        fillColor=color, strokeColor=color, strokeWidth=0.5
    ))


def _double_arrow_line(d, x1, y1, x2, y2, color=DARK_GRAY, width=1.5):
    """Draw a line with arrowheads at both ends."""
    import math
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 8
    arrow_angle = math.pi / 7
    # Arrow at (x2, y2)
    ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
    ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
    ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
    ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)
    d.add(Polygon([x2, y2, ax1, ay1, ax2, ay2], fillColor=color, strokeColor=color, strokeWidth=0.5))
    # Arrow at (x1, y1)
    angle2 = angle + math.pi
    bx1 = x1 - arrow_len * math.cos(angle2 - arrow_angle)
    by1 = y1 - arrow_len * math.sin(angle2 - arrow_angle)
    bx2 = x1 - arrow_len * math.cos(angle2 + arrow_angle)
    by2 = y1 - arrow_len * math.sin(angle2 + arrow_angle)
    d.add(Polygon([x1, y1, bx1, by1, bx2, by2], fillColor=color, strokeColor=color, strokeWidth=0.5))


def _rounded_box(d, x, y, w, h, text, sub_text=None, fill=LIGHT_BLUE, stroke=MED_BLUE,
                 font_size=9, text_color=DARK_BLUE, sub_color=DARK_GRAY):
    """Draw a rounded rectangle with centered text."""
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=1.2, rx=6, ry=6))
    if sub_text:
        d.add(String(x + w / 2, y + h / 2 + 4, text,
                     fontSize=font_size, fontName="Helvetica-Bold",
                     fillColor=text_color, textAnchor="middle"))
        d.add(String(x + w / 2, y + h / 2 - 10, sub_text,
                     fontSize=7.5, fontName="Helvetica",
                     fillColor=sub_color, textAnchor="middle"))
    else:
        d.add(String(x + w / 2, y + h / 2 - 3, text,
                     fontSize=font_size, fontName="Helvetica-Bold",
                     fillColor=text_color, textAnchor="middle"))


def build_architecture_diagram():
    """Architecture diagram: Client -> Frontend -> Backends."""
    d = Drawing(490, 310)

    # Background
    d.add(Rect(0, 0, 490, 310, fillColor=HexColor("#fafbfc"), strokeColor=None))

    # Title
    d.add(String(245, 293, "QUIC Migration Load Balancer Architecture",
                 fontSize=11, fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))

    # Client box
    _rounded_box(d, 15, 175, 100, 50, "Client", ".127 (optiplex7010)",
                 fill=HexColor("#e6fffa"), stroke=TEAL, text_color=TEAL)

    # Frontend box (larger)
    frontend_x, frontend_y = 175, 150
    d.add(Rect(frontend_x, frontend_y, 140, 100, fillColor=LIGHT_BLUE, strokeColor=MED_BLUE,
               strokeWidth=2, rx=8, ry=8))
    d.add(String(frontend_x + 70, frontend_y + 78, "LB Frontend",
                 fontSize=10, fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))
    d.add(String(frontend_x + 70, frontend_y + 63, ".152 (opti7040)",
                 fontSize=8, fontName="Helvetica", fillColor=DARK_GRAY, textAnchor="middle"))
    d.add(Line(frontend_x + 15, frontend_y + 57, frontend_x + 125, frontend_y + 57,
               strokeColor=BORDER, strokeWidth=0.5))
    d.add(String(frontend_x + 70, frontend_y + 40, "Backend Selection:",
                 fontSize=8, fontName="Helvetica", fillColor=DARK_GRAY, textAnchor="middle"))
    d.add(String(frontend_x + 70, frontend_y + 27, "Round Robin / Random",
                 fontSize=8, fontName="Helvetica-Bold", fillColor=MED_BLUE, textAnchor="middle"))
    d.add(String(frontend_x + 70, frontend_y + 10, "Handshake Only (1 RTT)",
                 fontSize=7, fontName="Helvetica-Oblique", fillColor=ORANGE, textAnchor="middle"))

    # Arrow: Client -> Frontend
    _arrow_line(d, 115, 200, 175, 200, color=TEAL, width=2)
    d.add(String(145, 208, "QUIC", fontSize=7, fontName="Helvetica-Bold",
                 fillColor=TEAL, textAnchor="middle"))
    d.add(String(145, 197, "Handshake", fontSize=7, fontName="Helvetica",
                 fillColor=TEAL, textAnchor="middle"))

    # Backend boxes
    backends = [
        ("Backend 1", ".143", "homeserver2", 350, 245),
        ("Backend 2", ".200", "Proxmox VM", 350, 165),
        ("Backend N", "(...)", "scalable", 350, 85),
    ]
    for name, ip, machine, bx, by in backends:
        fill = GREEN_BG if name != "Backend N" else HexColor("#f0f0f0")
        stroke = GREEN if name != "Backend N" else BORDER
        tc = GREEN if name != "Backend N" else DARK_GRAY
        _rounded_box(d, bx, by, 120, 50, name, f"{ip} ({machine})",
                     fill=fill, stroke=stroke, text_color=tc)

    # Arrows: Frontend -> Backends (state transfer)
    _arrow_line(d, 315, 220, 350, 265, color=MED_BLUE, width=1.5)
    _arrow_line(d, 315, 195, 350, 190, color=MED_BLUE, width=1.5)
    _arrow_line(d, 315, 175, 350, 115, color=MED_BLUE, width=1.5, dashed=True)

    # Label for state transfer
    d.add(String(340, 230, "TCP Push", fontSize=7, fontName="Helvetica-Oblique",
                 fillColor=MED_BLUE, textAnchor="middle"))
    d.add(String(340, 221, "445 bytes", fontSize=7, fontName="Helvetica-Oblique",
                 fillColor=MED_BLUE, textAnchor="middle"))

    # Direct path: Client -> Backend 1 (post-migration)
    _double_arrow_line(d, 65, 175, 65, 40, color=ACCENT, width=2)
    _double_arrow_line(d, 65, 40, 405, 40, color=ACCENT, width=2)
    _arrow_line(d, 405, 40, 405, 85, color=ACCENT, width=2)

    # Label for direct path
    d.add(Rect(140, 25, 200, 18, fillColor=RED_BG, strokeColor=ACCENT, strokeWidth=0.8, rx=3, ry=3))
    d.add(String(240, 30, "Direct traffic (post-migration)", fontSize=8,
                 fontName="Helvetica-Bold", fillColor=ACCENT, textAnchor="middle"))

    # "..." between Backend 2 and Backend N
    d.add(String(410, 145, "...", fontSize=14, fontName="Helvetica-Bold",
                 fillColor=DARK_GRAY, textAnchor="middle"))

    return d


def build_dataflow_diagram():
    """Per-connection data flow lifecycle diagram."""
    d = Drawing(490, 290)
    d.add(Rect(0, 0, 490, 290, fillColor=HexColor("#fafbfc"), strokeColor=None))

    d.add(String(245, 273, "Per-Connection Lifecycle (Data Flow)",
                 fontSize=11, fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))

    # Swim lanes
    lanes = [
        ("Client (.127)", 40),
        ("Frontend (.152)", 195),
        ("Backend[i]", 370),
    ]
    lane_top = 250
    lane_bot = 20
    for label, x in lanes:
        d.add(Rect(x - 5, lane_top, 120, 22, fillColor=DARK_BLUE, strokeColor=None, rx=4, ry=4))
        d.add(String(x + 55, lane_top + 6, label, fontSize=9, fontName="Helvetica-Bold",
                     fillColor=white, textAnchor="middle"))
        d.add(Line(x + 55, lane_top, x + 55, lane_bot, strokeColor=BORDER,
                   strokeWidth=0.8, strokeDashArray=[3, 3]))

    # Steps (y positions descending)
    steps = [
        (1, "QUIC Initial (ClientHello)", 40 + 55, 195 + 55, 228, MED_BLUE),
        (2, "Select Backend[i]", None, None, 210, DARK_GRAY),
        (3, "ServerHello + preferred_address", 195 + 55, 40 + 55, 192, MED_BLUE),
        (4, "TCP Push 445B state", 195 + 55, 370 + 55, 170, ORANGE),
        (5, "PATH_CHALLENGE", 40 + 55, 370 + 55, 145, GREEN),
        (6, "PATH_RESPONSE", 370 + 55, 40 + 55, 125, GREEN),
        (7, "Direct traffic", 40 + 55, 370 + 55, 100, ACCENT),
    ]

    for step_num, label, x_from, x_to, y, color in steps:
        if x_from is None:
            # Internal action (no arrow)
            d.add(Rect(195 + 10, y - 5, 100, 16, fillColor=LIGHT_BLUE, strokeColor=MED_BLUE,
                       strokeWidth=0.5, rx=3, ry=3))
            d.add(String(195 + 60, y, f"[{step_num}] {label}", fontSize=7,
                         fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))
        else:
            _arrow_line(d, x_from, y + 3, x_to, y + 3, color=color, width=1.5)
            lx = (x_from + x_to) / 2
            ly = y + 10
            d.add(String(lx, ly, f"[{step_num}] {label}", fontSize=7,
                         fontName="Helvetica-Bold", fillColor=color, textAnchor="middle"))

    # Step 7: double arrow for bidirectional
    if True:
        _double_arrow_line(d, 40 + 55, 80, 370 + 55, 80, color=ACCENT, width=2)
        d.add(String(245, 65, "Frontend out of path", fontSize=8,
                     fontName="Helvetica-Bold", fillColor=ACCENT, textAnchor="middle"))

    # Divider showing connection #2 hint
    d.add(Line(10, 48, 480, 48, strokeColor=BORDER, strokeWidth=0.5, strokeDashArray=[6, 3]))
    d.add(String(245, 33, "Connection #2: Same flow, Frontend selects Backend[(i+1) % N]",
                 fontSize=8, fontName="Helvetica-Oblique", fillColor=DARK_GRAY, textAnchor="middle"))

    return d


def build_comparison_diagram():
    """Traditional LB vs QUIC Migration LB comparison."""
    d = Drawing(490, 195)
    d.add(Rect(0, 0, 490, 195, fillColor=HexColor("#fafbfc"), strokeColor=None))

    d.add(String(245, 178, "Traditional LB vs. QUIC Migration LB: Data Path Comparison",
                 fontSize=11, fontName="Helvetica-Bold", fillColor=DARK_BLUE, textAnchor="middle"))

    # ---- LEFT: Traditional ----
    d.add(Rect(10, 40, 220, 125, fillColor=white, strokeColor=BORDER, strokeWidth=1, rx=6, ry=6))
    d.add(String(120, 148, "Traditional L4/L7 LB", fontSize=9, fontName="Helvetica-Bold",
                 fillColor=ACCENT, textAnchor="middle"))

    _rounded_box(d, 25, 100, 70, 30, "Client", fill=HexColor("#e6fffa"), stroke=TEAL, text_color=TEAL)
    _rounded_box(d, 110, 100, 50, 30, "LB", fill=RED_BG, stroke=ACCENT, text_color=ACCENT)
    _rounded_box(d, 175, 100, 45, 30, "BE", fill=GREEN_BG, stroke=GREEN, text_color=GREEN)

    _double_arrow_line(d, 95, 115, 110, 115, color=ACCENT, width=2)
    _double_arrow_line(d, 160, 115, 175, 115, color=ACCENT, width=2)

    # "Every packet" label
    d.add(Rect(40, 55, 170, 30, fillColor=RED_BG, strokeColor=ACCENT, strokeWidth=0.8, rx=4, ry=4))
    d.add(String(125, 72, "EVERY packet traverses LB", fontSize=8,
                 fontName="Helvetica-Bold", fillColor=ACCENT, textAnchor="middle"))
    d.add(String(125, 60, "LB = bandwidth bottleneck", fontSize=7.5,
                 fontName="Helvetica", fillColor=ACCENT, textAnchor="middle"))

    # ---- RIGHT: QUIC Migration ----
    d.add(Rect(255, 40, 225, 125, fillColor=white, strokeColor=BORDER, strokeWidth=1, rx=6, ry=6))
    d.add(String(367, 148, "QUIC Migration LB", fontSize=9, fontName="Helvetica-Bold",
                 fillColor=GREEN, textAnchor="middle"))

    _rounded_box(d, 270, 100, 70, 30, "Client", fill=HexColor("#e6fffa"), stroke=TEAL, text_color=TEAL)
    _rounded_box(d, 355, 100, 50, 30, "LB", fill=LIGHT_BLUE, stroke=MED_BLUE, text_color=MED_BLUE)
    _rounded_box(d, 420, 100, 45, 30, "BE", fill=GREEN_BG, stroke=GREEN, text_color=GREEN)

    # Handshake only arrow (thin, dashed)
    _arrow_line(d, 340, 118, 355, 118, color=MED_BLUE, width=1, dashed=True)
    d.add(String(348, 107, "1 RTT", fontSize=6, fontName="Helvetica-Oblique",
                 fillColor=MED_BLUE, textAnchor="middle"))

    # State transfer
    _arrow_line(d, 405, 112, 420, 112, color=ORANGE, width=1, dashed=True)

    # Direct path
    _double_arrow_line(d, 340, 100, 420, 88, color=GREEN, width=2.5)

    # "Direct" label
    d.add(Rect(290, 55, 170, 30, fillColor=GREEN_BG, strokeColor=GREEN, strokeWidth=0.8, rx=4, ry=4))
    d.add(String(375, 72, "Data flows DIRECTLY to backend", fontSize=8,
                 fontName="Helvetica-Bold", fillColor=GREEN, textAnchor="middle"))
    d.add(String(375, 60, "LB has zero ongoing overhead", fontSize=7.5,
                 fontName="Helvetica", fillColor=GREEN, textAnchor="middle"))

    # VS divider
    d.add(Rect(233, 90, 20, 30, fillColor=DARK_BLUE, strokeColor=None, rx=4, ry=4))
    d.add(String(243, 101, "vs", fontSize=9, fontName="Helvetica-Bold",
                 fillColor=white, textAnchor="middle"))

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
        fontName="Courier", fontSize=9, leading=12,
        leftIndent=16, spaceAfter=2, spaceBefore=2,
        textColor=DARK_GRAY,
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

    # ======================================================
    # TITLE PAGE
    # ======================================================
    elements.append(Spacer(1, 1.2*inch))
    elements.append(Paragraph("QUIC-Native Load Balancer", title_style))
    elements.append(Paragraph("Proof of Concept", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Fire-and-Forget Load Balancing via QUIC Server-Side Migration",
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
        "This document describes the design and implementation of a QUIC-native load balancer "
        "that leverages server-side connection migration (RFC 9000, Section 9.6) to achieve "
        "\"fire-and-forget\" load balancing. Unlike traditional load balancers (HAProxy, NGINX, "
        "Maglev) that remain in the data path for the entire connection lifetime, our approach "
        "handles only the initial handshake (1 RTT), selects a backend, and then steps out of "
        "the data path entirely. After migration, the client communicates directly with the "
        "backend server with zero frontend overhead."
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

    # ======================================================
    # 1. OVERVIEW
    # ======================================================
    elements.append(Paragraph("1. Overview", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Traditional load balancers sit in the data path for the <b>entire connection lifetime</b>. "
        "Every packet between client and server must traverse the LB, making it a throughput "
        "bottleneck and a single point of failure. This is true for both L4 (Maglev, LVS) and "
        "L7 (NGINX, Envoy, HAProxy) load balancers.",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "QUIC's server-side migration mechanism (the <font face='Courier'>preferred_address</font> "
        "transport parameter) offers a fundamentally different approach:",
        body
    ))

    elements.append(Paragraph(
        "The frontend handles <b>only the TLS handshake</b> (1 RTT), during which it selects "
        "a backend and advertises the backend's address as the preferred address.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "After the handshake, the client migrates directly to the backend. The frontend "
        "exports the cryptographic state and sends it to the backend.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "Once migration completes, the frontend has <b>zero per-connection state</b> and "
        "processes zero data packets for that connection.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "This is \"fire-and-forget\" load balancing: the frontend dispatches and the backend "
        "serves directly.",
        bullet_style, bulletText="\u2022"
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Key insight: The frontend's work is bounded by O(1) per connection (handshake only), "
        "not O(n) per packet. This eliminates the LB as a bandwidth bottleneck.",
        highlight_style
    ))

    # ======================================================
    # 2. ARCHITECTURE
    # ======================================================
    elements.append(Paragraph("2. Architecture", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The PoC runs on a four-machine testbed, all on the same LAN (141.217.168.x):",
        body
    ))
    elements.append(Spacer(1, 4))

    arch_table = make_table(
        ["Role", "Machine", "IP Address", "Binary"],
        [
            ["Frontend (LB)", "opti7040", "141.217.168.152", "lb-frontend"],
            ["Backend 1", "homeserver2", "141.217.168.143", "preferred-server"],
            ["Backend 2", "Proxmox VM", "141.217.168.200", "preferred-server"],
            ["Client", "optiplex7010", "141.217.168.127", "Firefox / neqo-client"],
        ],
        col_widths=[1.4*inch, 1.3*inch, 1.5*inch, 1.5*inch],
    )
    elements.append(arch_table)
    elements.append(Spacer(1, 12))

    # Architecture Diagram
    elements.append(Paragraph("Architecture Diagram", h2))
    elements.append(Spacer(1, 4))
    elements.append(build_architecture_diagram())
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "The diagram above shows the overall topology. The client initiates a QUIC handshake "
        "with the frontend. The frontend selects a backend via round-robin or random policy, "
        "advertises that backend as the <font face='Courier'>preferred_address</font>, and "
        "transfers cryptographic state. After path validation succeeds, the client communicates "
        "directly with the backend (shown in red). The frontend is completely out of the data path.",
        body
    ))

    elements.append(PageBreak())

    # ======================================================
    # 3. DATA FLOW
    # ======================================================
    elements.append(Paragraph("3. Per-Connection Data Flow", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Each incoming connection follows a strict seven-step lifecycle. The frontend's "
        "involvement ends at step 4; after that, the backend handles all traffic directly.",
        body
    ))
    elements.append(Spacer(1, 6))

    # Data flow diagram
    elements.append(build_dataflow_diagram())
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Connection Flow Detail", h2))
    steps = [
        ("1.", "<b>Client -> Frontend:</b> QUIC Initial packet containing the TLS ClientHello. "
               "This is the first contact; the client connects to the frontend's public address."),
        ("2.", "<b>Frontend selects Backend[i]:</b> Based on the configured LB policy. For round-robin, "
               "this is <font face='Courier'>counter % num_backends</font>; for random, a uniform "
               "random selection."),
        ("3.", "<b>Frontend -> Client:</b> The TLS ServerHello includes the "
               "<font face='Courier'>preferred_address</font> transport parameter set to Backend[i]'s "
               "IP address and port. This completes the 1-RTT handshake."),
        ("4.", "<b>Frontend -> Backend[i]:</b> The frontend exports ~445 bytes of migration state "
               "(TLS secrets, CIDs, packet numbers) and sends it to Backend[i] via TCP push to port 9999."),
        ("5.", "<b>Client -> Backend[i]:</b> The client, having received the preferred address, sends "
               "a PATH_CHALLENGE to Backend[i] to validate the new path."),
        ("6.", "<b>Backend[i] -> Client:</b> The backend imports the crypto state, decrypts the "
               "PATH_CHALLENGE, and responds with a PATH_RESPONSE. The client validates the response."),
        ("7.", "<b>Client <-> Backend[i]:</b> Migration is complete. All subsequent HTTP/3 data "
               "flows directly between client and backend. The frontend has zero further involvement."),
    ]
    for num, text in steps:
        elements.append(Paragraph(f"<b>{num}</b> {text}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "For Connection #2, the same flow repeats, but the frontend selects Backend[(i+1) % N] "
        "(round-robin) or a random backend. Each connection is independently load-balanced.",
        body_italic
    ))

    # ======================================================
    # 4. TRADITIONAL vs QUIC COMPARISON
    # ======================================================
    elements.append(PageBreak())
    elements.append(Paragraph("4. Traditional LB vs. QUIC Migration LB", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The fundamental difference is where the load balancer sits in the data path:",
        body
    ))
    elements.append(Spacer(1, 6))

    # Comparison diagram
    elements.append(build_comparison_diagram())
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "The following table provides a detailed feature comparison across three LB approaches:",
        body
    ))
    elements.append(Spacer(1, 6))

    comparison_table = make_table(
        ["Feature", "Maglev (L4)", "NGINX/Envoy (L7)", "QUIC Migration LB"],
        [
            ["LB in data path", "Always", "Always", "<b>Handshake only</b>"],
            ["TLS termination at LB", "No (pass-through)", "Yes", "Handshake only"],
            ["Sees plaintext", "No", "Yes", "<b>No</b> (after migration)"],
            ["Per-conn state at LB", "Flow table", "Session + buffers", "<b>None</b> after migration"],
            ["Bandwidth bottleneck", "LB throughput", "LB throughput", "<b>None</b> (direct path)"],
            ["Backend health check", "Yes (active)", "Yes (active)", "Pre-migration only"],
            ["Re-balancing mid-conn", "Via flow reset", "Via retry", "Not possible"],
            ["Protocol requirement", "Any", "HTTP/1.1, HTTP/2", "QUIC (HTTP/3)"],
        ],
        col_widths=[1.4*inch, 1.3*inch, 1.5*inch, 1.6*inch],
        highlight_row=5,
    )
    elements.append(comparison_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "The QUIC migration LB combines the privacy benefits of L4 (no plaintext visibility) "
        "with the routing intelligence of L7 (backend selection at handshake time), while "
        "eliminating the persistent bandwidth bottleneck of both approaches.",
        highlight_style
    ))

    # ======================================================
    # 5. LOAD BALANCING POLICIES
    # ======================================================
    elements.append(Paragraph("5. Load Balancing Policies", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The frontend supports multiple load balancing policies, selected via the "
        "<font face='Courier'>LB_POLICY</font> environment variable.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Round Robin (default)", h2))
    elements.append(Paragraph(
        "Cycles through backends in order: [0, 1, 2, ..., N-1, 0, 1, ...]. This provides "
        "perfectly even distribution across backends and is fully deterministic.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Algorithm Detail", h3))
    elements.append(Paragraph(
        "The round-robin algorithm maintains a single atomic counter that increments with "
        "each new connection. Backend selection is computed as:",
        body
    ))
    elements.append(Paragraph(
        "selected_backend = counter % num_backends",
        code_style
    ))
    elements.append(Paragraph(
        "counter += 1",
        code_style
    ))
    elements.append(Paragraph(
        "For example, with 3 backends and 9 connections, the assignment is: "
        "B0, B1, B2, B0, B1, B2, B0, B1, B2 -- exactly 3 connections each. "
        "This guarantees perfect distribution regardless of connection count "
        "(modulo the number of backends).",
        body
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Random", h2))
    elements.append(Paragraph(
        "Pseudo-random selection per connection. Each incoming connection is assigned to a "
        "backend chosen uniformly at random. Over many connections, this converges to even "
        "distribution but may have short-term imbalances. Selected with "
        "<font face='Courier'>LB_POLICY=random</font>.",
        body
    ))
    elements.append(Spacer(1, 6))

    policy_table = make_table(
        ["Policy", "Selection Logic", "Distribution", "State", "Use Case"],
        [
            ["Round Robin", "counter % N", "Perfectly even",
             "1 counter", "Default; homogeneous backends"],
            ["Random", "rand() % N", "Statistically even",
             "None", "Stateless; no coordination needed"],
        ],
        col_widths=[1.0*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.7*inch],
    )
    elements.append(policy_table)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Backend Statistics Tracking", h2))
    elements.append(Paragraph(
        "Regardless of the selected policy, the frontend tracks per-backend statistics "
        "and prints a distribution table after each connection. This includes:",
        body
    ))
    elements.append(Paragraph(
        "<b>Connection count:</b> Total number of connections dispatched to each backend.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "<b>Percentage:</b> Proportion of total connections sent to each backend.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "<b>Last dispatch time:</b> Timestamp of the most recent connection to each backend.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Example output after 6 connections with round-robin and 2 backends:",
        body
    ))
    elements.append(Paragraph("Backend Distribution:", code_style))
    elements.append(Paragraph("  141.217.168.143:4433  |  3 connections  (50.0%)", code_style))
    elements.append(Paragraph("  141.217.168.200:4433  |  3 connections  (50.0%)", code_style))

    # ======================================================
    # 6. IMPLEMENTATION DETAILS
    # ======================================================
    elements.append(PageBreak())
    elements.append(Paragraph("6. Implementation Details", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Binary: lb-frontend", h2))
    elements.append(Paragraph(
        "The load balancer frontend is implemented as the <font face='Courier'>lb-frontend</font> "
        "binary in the migration-test crate. It is a purpose-built binary separate from the "
        "standard primary-server.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Per-Connection Server Creation", h3))
    elements.append(Paragraph(
        "The frontend creates a <b>new Http3Server instance for each incoming connection</b>. "
        "This is necessary because the <font face='Courier'>preferred_address</font> transport "
        "parameter is set during server construction and is included in the TLS handshake. "
        "Since each connection may be routed to a different backend, a fresh server instance "
        "with the correct preferred address must be created each time.",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "The lifecycle of each server instance is short-lived:",
        body
    ))
    elements.append(Paragraph(
        "<b>Create:</b> New Http3Server with Backend[i]'s address as preferred_address.",
        bullet_style, bulletText="1."
    ))
    elements.append(Paragraph(
        "<b>Handshake:</b> Process the QUIC handshake (1 RTT) with the client.",
        bullet_style, bulletText="2."
    ))
    elements.append(Paragraph(
        "<b>Export:</b> Extract ~445 bytes of migration state (TLS secrets, CIDs, etc.).",
        bullet_style, bulletText="3."
    ))
    elements.append(Paragraph(
        "<b>Transfer:</b> Send migration state to Backend[i] via TCP.",
        bullet_style, bulletText="4."
    ))
    elements.append(Paragraph(
        "<b>Destroy:</b> Drop the server instance. No per-connection state persists.",
        bullet_style, bulletText="5."
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "A production implementation would ideally reuse a single server instance with dynamic "
        "per-connection preferred_address selection. The current per-connection instantiation is "
        "a PoC limitation that simplifies the integration with Neqo's API.",
        body_italic
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("State Transfer", h3))
    elements.append(Paragraph(
        "Migration state (~445 bytes) is sent via a direct TCP connection from the frontend "
        "to the selected backend's port 9999. This is a one-shot send with no response expected. "
        "The state includes:",
        body
    ))
    state_fields = make_table(
        ["Field", "Size (bytes)", "Description"],
        [
            ["TLS Application Secrets", "~128", "Read + Write AEAD keys for 1-RTT data"],
            ["Connection IDs (CIDs)", "~80", "Client and server CIDs for packet routing"],
            ["Client Address", "~20", "Client IP:port for response routing"],
            ["QUIC Version", "4", "Protocol version negotiated during handshake"],
            ["Packet Numbers", "~16", "Next expected RX/TX sequence numbers"],
            ["Misc. Parameters", "~197", "Additional transport/crypto parameters"],
        ],
        col_widths=[1.8*inch, 1.0*inch, 3.1*inch],
    )
    elements.append(state_fields)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Per-Connection Stats", h3))
    elements.append(Paragraph(
        "The frontend prints per-connection statistics including the selected backend, handshake "
        "duration, and state export time. It also maintains and prints a running backend "
        "distribution table showing how many connections have been sent to each backend.",
        body
    ))

    # ======================================================
    # 7. SCALABILITY ANALYSIS
    # ======================================================
    elements.append(Paragraph("7. Scalability Analysis", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The key scalability advantage of the QUIC migration LB is that the frontend only "
        "handles the handshake phase of each connection. Once the handshake completes and "
        "state is transferred (~1 RTT), the frontend is free to serve new connections.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Frontend Cost Per Connection", h2))

    cost_table = make_table(
        ["Phase", "Duration", "CPU Cost", "Bandwidth Cost"],
        [
            ["TLS Handshake", "~1 RTT", "ECDHE key exchange", "~2-3 KB (hello + cert)"],
            ["Backend Selection", "O(1)", "Counter increment or RNG", "0"],
            ["State Export", "&lt; 1 ms", "Serialization", "0 (internal)"],
            ["State Transfer", "&lt; 1 ms (LAN)", "TCP send", "445 bytes"],
            ["Connection Teardown", "O(1)", "Memory free", "0"],
            ["<b>Total per conn</b>", "<b>~1 RTT</b>", "<b>~1 crypto op</b>", "<b>~3 KB</b>"],
        ],
        col_widths=[1.5*inch, 1.2*inch, 1.6*inch, 1.6*inch],
        highlight_row=6,
    )
    elements.append(cost_table)

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Bandwidth Savings Calculation", h2))
    elements.append(Paragraph(
        "Consider a scenario with 1,000 concurrent connections, each transferring 10 MB of data:",
        body
    ))
    elements.append(Spacer(1, 4))

    bw_table = make_table(
        ["Metric", "Traditional LB", "QUIC Migration LB", "Savings"],
        [
            ["Frontend bandwidth (handshake)", "~3 MB", "~3 MB", "0%"],
            ["Frontend bandwidth (data)", "10 GB (all data)", "0 B", "100%"],
            ["<b>Total frontend bandwidth</b>", "<b>~10 GB</b>", "<b>~3 MB</b>",
             "<b>99.97%</b>"],
            ["Frontend connections held", "1,000 (ongoing)", "0 (after migration)", "100%"],
            ["Frontend memory (per conn)", "~50 KB x 1000 = 50 MB", "0 (after migration)", "100%"],
        ],
        col_widths=[1.6*inch, 1.5*inch, 1.5*inch, 1.0*inch],
        highlight_row=3,
    )
    elements.append(bw_table)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "The frontend processes approximately 3 KB per connection (handshake only), then steps "
        "out. In a traditional LB, the same frontend must relay all 10 GB of data traffic. "
        "This represents a 99.97% reduction in frontend bandwidth utilization.",
        highlight_style
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Connection Throughput", h2))
    elements.append(Paragraph(
        "Since the frontend only handles handshakes, its connection throughput is limited by "
        "crypto operations (TLS 1.3 ECDHE), not bandwidth. A modern CPU can perform "
        "tens of thousands of ECDHE key exchanges per second per core, meaning a single-core "
        "frontend could theoretically handle 10,000+ new connections/second. In contrast, a "
        "traditional LB processing data for all connections is bandwidth-limited.",
        body
    ))

    # ======================================================
    # 8. ENVIRONMENT VARIABLES
    # ======================================================
    elements.append(PageBreak())
    elements.append(Paragraph("8. Environment Variables Reference", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The following environment variables configure the load balancer frontend and backend "
        "binaries at runtime:",
        body
    ))
    elements.append(Spacer(1, 6))

    env_table = make_table(
        ["Variable", "Binary", "Default", "Description"],
        [
            ["<font face='Courier'>LB_POLICY</font>", "lb-frontend", "roundrobin",
             "Load balancing policy: <b>roundrobin</b> or <b>random</b>"],
            ["<font face='Courier'>STATE_TRANSFER</font>", "Both", "tcp",
             "State transfer backend: tcp, http, redis_kv, redis_ps, file"],
            ["<font face='Courier'>STATE_PORT</font>", "preferred-server", "9999",
             "TCP port for receiving migration state"],
            ["<font face='Courier'>REDIS_URL</font>", "Both", "redis://141.217.168.200",
             "Redis server URL (for redis_kv/redis_ps backends)"],
            ["<font face='Courier'>PKG_CONFIG_PATH</font>", "Build only", "/nonexistent",
             "Set to /nonexistent to use bundled NSS"],
            ["<font face='Courier'>PKG_CONFIG_LIBDIR</font>", "Build only", "/nonexistent",
             "Set to /nonexistent to use bundled NSS"],
            ["<font face='Courier'>LIBCLANG_PATH</font>", "Build only (homeserver2)", "(unset)",
             "Path to libclang on homeserver2: /usr/lib/llvm-14/lib"],
            ["<font face='Courier'>LD_LIBRARY_PATH</font>", "Runtime", "(unset)",
             "Set to NSS dist/Release/lib for runtime linking"],
        ],
        col_widths=[1.5*inch, 1.1*inch, 1.2*inch, 2.1*inch],
    )
    elements.append(env_table)

    # ======================================================
    # 9. HOW TO RUN
    # ======================================================
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("9. How to Run", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Start the components in the following order:",
        body
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Step 1: Start Backend 1 (homeserver2, .143)", h3))
    elements.append(Paragraph(
        "preferred-server 141.217.168.143:4433 9999",
        code_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Step 2: Start Backend 2 (Proxmox VM, .200)", h3))
    elements.append(Paragraph(
        "preferred-server 141.217.168.200:4433 9999",
        code_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Step 3: Start Frontend (opti7040, .152)", h3))
    elements.append(Paragraph(
        "lb-frontend 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433",
        code_style
    ))
    elements.append(Paragraph(
        "The frontend binds to port 4433 and accepts two backend addresses as positional arguments. "
        "Additional backends can be appended to scale out.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Step 4: Connect from Client (.127)", h3))
    elements.append(Paragraph(
        "Open Firefox and navigate to <font face='Courier'>https://141.217.168.152:4433/</font>. "
        "The first load triggers the TCP bootstrap (Alt-Svc). On refresh, Firefox uses HTTP/3 "
        "and the migration-based load balancing takes effect.",
        body
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "To select a policy, set the environment variable before starting the frontend:",
        body
    ))
    elements.append(Paragraph(
        "LB_POLICY=random lb-frontend 0.0.0.0:4433 141.217.168.143:4433 141.217.168.200:4433",
        code_style
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Using Shell Aliases", h3))
    elements.append(Paragraph(
        "On the testbed machines, shell aliases are configured for convenience:",
        body
    ))
    alias_table = make_table(
        ["Machine", "Alias", "Description"],
        [
            ["homeserver2", "<font face='Courier'>preferred-up</font>", "Start backend (TCP push, immediate)"],
            ["homeserver2", "<font face='Courier'>preferred-down</font>", "Stop backend (kill ports 9999/4433)"],
            ["opti7040", "<font face='Courier'>bootstrap-up</font>", "Start TCP HTTPS Alt-Svc bootstrap"],
            ["opti7040", "<font face='Courier'>bootstrap-down</font>", "Stop bootstrap server"],
        ],
        col_widths=[1.3*inch, 1.8*inch, 2.8*inch],
    )
    elements.append(alias_table)

    # ======================================================
    # 10. ADVANTAGES OVER TRADITIONAL LBs
    # ======================================================
    elements.append(PageBreak())
    elements.append(Paragraph("10. Advantages Over Traditional Load Balancers", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    advantages = [
        ("<b>Zero steady-state bandwidth overhead:</b> After migration (~1 RTT), the frontend "
         "processes zero data packets. A 10 Gbps link serving 1,000 connections transfers zero "
         "bytes through the LB for ongoing data."),
        ("<b>No single point of failure for data:</b> If the frontend goes down after migration, "
         "existing connections continue uninterrupted because they flow directly client-to-backend."),
        ("<b>Privacy by design:</b> Unlike L7 reverse proxies, the frontend never sees plaintext "
         "application data. TLS is terminated only for the handshake; post-migration encryption "
         "keys are held solely by the backend."),
        ("<b>Horizontal scaling of backends:</b> Adding a new backend requires only starting "
         "another preferred-server instance and adding its address to the frontend's backend list. "
         "No connection draining or LB reconfiguration is needed."),
        ("<b>Reduced frontend hardware requirements:</b> Since the frontend only handles "
         "handshakes (CPU-bound, not bandwidth-bound), it can run on a much smaller machine "
         "than a traditional LB that must relay all traffic."),
    ]
    for adv in advantages:
        elements.append(Paragraph(adv, bullet_style, bulletText="\u2022"))

    # ======================================================
    # 11. LIMITATIONS
    # ======================================================
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("11. Limitations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "One-shot migration: Once a connection migrates to a backend, it cannot be re-balanced. "
        "If the backend becomes overloaded after migration, the LB cannot intervene. This is "
        "inherent to the preferred_address mechanism.",
        warning_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "Client support required: The client must support the preferred_address transport "
        "parameter. Firefox supports this; Chrome/Chromium does not (as of mid-2026). This "
        "limits real-world applicability until broader adoption.",
        negative_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "Per-connection server instantiation: The current PoC creates a new Http3Server "
        "instance per connection. This is a PoC limitation, not a fundamental architectural "
        "constraint. A production implementation would reuse a single server instance with "
        "per-connection preferred_address selection.",
        warning_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "No health checking: The PoC does not perform active backend health checks. If a "
        "backend is down, the frontend will still dispatch connections to it. A production "
        "system would need periodic health probes and backend removal on failure.",
        warning_style
    ))

    # ======================================================
    # 12. TEST PLAN
    # ======================================================
    elements.append(Paragraph("12. Test Plan", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The following tests validate correctness, distribution, and performance of the "
        "load balancer PoC.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Test 1: Distribution Verification", h2))
    elements.append(Paragraph(
        "Send 10 sequential connections to the frontend and verify even distribution across "
        "backends. With round-robin policy, expect exactly 5 connections per backend. With "
        "random policy, expect approximately even distribution (statistical test).",
        body
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Test 2: Handshake + Migration Latency", h2))
    elements.append(Paragraph(
        "Measure per-connection latency from initial ClientHello to completed migration "
        "(PATH_RESPONSE validated by client). Break down into: handshake time (frontend), "
        "state transfer time (TCP push), and path validation time (PATH_CHALLENGE/RESPONSE "
        "round trip to backend). Target: total migration latency under 2 RTT.",
        body
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Test 3: Baseline Comparison", h2))
    elements.append(Paragraph(
        "Compare with HAProxy in TCP mode (L4 pass-through) as the baseline. Metrics: "
        "connection setup latency, sustained throughput (the QUIC LB should show zero "
        "throughput overhead after migration), and frontend CPU utilization under load.",
        body
    ))

    elements.append(Spacer(1, 8))
    test_table = make_table(
        ["Test", "Method", "Success Criteria"],
        [
            ["Distribution", "10 sequential connections",
             "5/5 split (round robin); ~even (random)"],
            ["Latency", "Per-connection timing",
             "Total migration &lt; 2 RTT on LAN"],
            ["Baseline", "HAProxy TCP mode comparison",
             "Zero throughput overhead after migration"],
        ],
        col_widths=[1.3*inch, 2.0*inch, 2.6*inch],
    )
    elements.append(test_table)

    # Build
    doc.build(elements)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

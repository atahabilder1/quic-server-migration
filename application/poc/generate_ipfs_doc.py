#!/usr/bin/env python3
"""Generate IPFS Gateway Migration PoC PDF — comprehensive edition."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Group
)
from reportlab.graphics import renderPDF
from datetime import date

OUTPUT = "application/poc/IPFS_GATEWAY_POC.pdf"

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
TEAL = HexColor("#285e61")
TEAL_BG = HexColor("#e6fffa")
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")


# ── Drawing helpers ──────────────────────────────────────────────────────────

def _draw_box(d, x, y, w, h, fill, stroke=DARK_GRAY, stroke_w=1):
    """Draw a rounded-corner-ish rectangle (plain rect)."""
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=stroke_w))


def _draw_text(d, x, y, text, size=8, color=DARK_GRAY, anchor="start", font="Helvetica"):
    d.add(String(x, y, text, fontSize=size, fillColor=color, textAnchor=anchor,
                 fontName=font))


def _draw_text_bold(d, x, y, text, size=8, color=DARK_GRAY, anchor="start"):
    _draw_text(d, x, y, text, size, color, anchor, font="Helvetica-Bold")


def _draw_arrow(d, x1, y1, x2, y2, color=DARK_GRAY, stroke_w=1.2, dashed=False):
    """Draw a line with an arrowhead at (x2, y2)."""
    import math
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=stroke_w,
               strokeDashArray=[4, 3] if dashed else None))
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 7
    ha = math.pi / 7
    ax = x2 - head_len * math.cos(angle - ha)
    ay = y2 - head_len * math.sin(angle - ha)
    bx = x2 - head_len * math.cos(angle + ha)
    by = y2 - head_len * math.sin(angle + ha)
    d.add(Polygon([x2, y2, ax, ay, bx, by], fillColor=color, strokeColor=color,
                  strokeWidth=0.5))


def _draw_dashed_line(d, x1, y1, x2, y2, color=BORDER, stroke_w=0.8):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=stroke_w,
               strokeDashArray=[3, 3]))


# ── Diagram builders ─────────────────────────────────────────────────────────

def build_architecture_diagram():
    """Full architecture: Client, Primary Gateway (Kubo+Neqo), Preferred Gateway, state transfer."""
    W, H = 500, 310
    d = Drawing(W, H)

    # Background
    _draw_box(d, 0, 0, W, H, HexColor("#fafcff"), stroke=BORDER, stroke_w=0.5)

    # Title
    _draw_text_bold(d, W / 2, H - 16, "Architecture: IPFS Gateway Migration", size=10,
                    color=DARK_BLUE, anchor="middle")

    # ── Column positions ──
    cx, px, prx = 55, 210, 390  # client, primary, preferred center-x
    col_w = 120

    # ── Client box ──
    cy_top = H - 50
    _draw_box(d, cx - 50, cy_top - 70, 100, 70, LIGHT_BLUE, MED_BLUE)
    _draw_text_bold(d, cx, cy_top - 12, "Client", size=9, color=DARK_BLUE, anchor="middle")
    _draw_text(d, cx, cy_top - 26, "optiplex7010", size=7, color=MED_BLUE, anchor="middle")
    _draw_text(d, cx, cy_top - 38, "(.127)", size=7, color=MED_BLUE, anchor="middle")
    _draw_text(d, cx, cy_top - 52, "Firefox / neqo-client", size=7, color=DARK_GRAY, anchor="middle")

    # ── Primary Gateway ──
    pg_top = H - 40
    # Outer frame
    _draw_box(d, px - 60, pg_top - 220, 120, 220, HexColor("#f0f7ff"), MED_BLUE, 1.5)
    _draw_text_bold(d, px, pg_top - 14, "Primary Gateway", size=9, color=DARK_BLUE, anchor="middle")
    _draw_text(d, px, pg_top - 27, "opti7040 (.152)", size=7, color=MED_BLUE, anchor="middle")

    # Kubo box inside primary
    kubo_y = pg_top - 50
    _draw_box(d, px - 50, kubo_y - 80, 100, 80, HexColor("#e8f5e9"), GREEN)
    _draw_text_bold(d, px, kubo_y - 12, "Kubo IPFS", size=8, color=GREEN, anchor="middle")
    _draw_text(d, px, kubo_y - 25, "Node", size=8, color=GREEN, anchor="middle")
    _draw_text(d, px, kubo_y - 40, "(port 8080)", size=7, color=DARK_GRAY, anchor="middle")
    _draw_text(d, px, kubo_y - 55, "CID: QmT78z...", size=7, color=DARK_GRAY, anchor="middle")
    _draw_text(d, px, kubo_y - 68, "pinned", size=7, color=GREEN, anchor="middle")

    # Neqo box inside primary
    neqo_y = kubo_y - 95
    _draw_box(d, px - 50, neqo_y - 60, 100, 60, LIGHT_BLUE, MED_BLUE)
    _draw_text_bold(d, px, neqo_y - 12, "Neqo H3 Server", size=8, color=DARK_BLUE, anchor="middle")
    _draw_text(d, px, neqo_y - 25, "(port 4433)", size=7, color=MED_BLUE, anchor="middle")
    _draw_text(d, px, neqo_y - 40, "webseed-primary", size=7, color=DARK_GRAY, anchor="middle")

    # Arrow Kubo -> Neqo inside primary
    _draw_arrow(d, px, kubo_y - 80, px, neqo_y, color=GREEN, stroke_w=1)

    # ── Preferred Gateway ──
    _draw_box(d, prx - 60, pg_top - 220, 120, 220, HexColor("#fff8f0"), ORANGE, 1.5)
    _draw_text_bold(d, prx, pg_top - 14, "Preferred Gateway", size=9, color=ORANGE, anchor="middle")
    _draw_text(d, prx, pg_top - 27, "homeserver2 (.143)", size=7, color=ORANGE, anchor="middle")

    # Kubo box inside preferred
    _draw_box(d, prx - 50, kubo_y - 80, 100, 80, HexColor("#e8f5e9"), GREEN)
    _draw_text_bold(d, prx, kubo_y - 12, "Kubo IPFS", size=8, color=GREEN, anchor="middle")
    _draw_text(d, prx, kubo_y - 25, "Node", size=8, color=GREEN, anchor="middle")
    _draw_text(d, prx, kubo_y - 40, "(port 8080)", size=7, color=DARK_GRAY, anchor="middle")
    _draw_text(d, prx, kubo_y - 55, "CID: QmT78z...", size=7, color=DARK_GRAY, anchor="middle")
    _draw_text(d, prx, kubo_y - 68, "pinned", size=7, color=GREEN, anchor="middle")

    # Preferred server box
    _draw_box(d, prx - 50, neqo_y - 60, 100, 60, ORANGE_BG, ORANGE)
    _draw_text_bold(d, prx, neqo_y - 12, "Preferred Server", size=8, color=ORANGE, anchor="middle")
    _draw_text(d, prx, neqo_y - 25, "(port 4433)", size=7, color=ORANGE, anchor="middle")
    _draw_text(d, prx, neqo_y - 40, "preferred-server", size=7, color=DARK_GRAY, anchor="middle")

    # Arrow Kubo -> Preferred inside preferred
    _draw_arrow(d, prx, kubo_y - 80, prx, neqo_y, color=GREEN, stroke_w=1)

    # ── Arrows between components ──

    # Client -> Primary (QUIC/HTTP3)
    arr_y = cy_top - 45
    _draw_arrow(d, cx + 50, arr_y, px - 60, arr_y, color=MED_BLUE, stroke_w=1.5)
    _draw_text(d, (cx + 50 + px - 60) / 2, arr_y + 5, "QUIC / HTTP3", size=7,
               color=MED_BLUE, anchor="middle")

    # Primary -> Preferred (State Transfer)
    st_y = neqo_y - 30
    _draw_arrow(d, px + 50, st_y, prx - 50, st_y, color=ACCENT, stroke_w=1.5, dashed=True)
    _draw_text(d, (px + 50 + prx - 50) / 2, st_y + 6, "State Transfer", size=7,
               color=ACCENT, anchor="middle")
    _draw_text(d, (px + 50 + prx - 50) / 2, st_y - 8, "(445 bytes)", size=6,
               color=ACCENT, anchor="middle")

    # Client -> Preferred (PATH_CHALLENGE)
    pc_y = 38
    _draw_arrow(d, cx + 10, pc_y + 8, prx - 60, pc_y + 8, color=TEAL, stroke_w=1)
    _draw_text(d, (cx + prx) / 2, pc_y + 15, "PATH_CHALLENGE", size=7,
               color=TEAL, anchor="middle")

    # Preferred -> Client (PATH_RESPONSE)
    _draw_arrow(d, prx - 60, pc_y - 6, cx + 10, pc_y - 6, color=GREEN, stroke_w=1)
    _draw_text(d, (cx + prx) / 2, pc_y - 16, "PATH_RESPONSE", size=7,
               color=GREEN, anchor="middle")

    return d


def build_content_addressing_diagram():
    """Content addressing: hash -> CID, same on both gateways."""
    W, H = 500, 220
    d = Drawing(W, H)
    _draw_box(d, 0, 0, W, H, HexColor("#fafcff"), stroke=BORDER, stroke_w=0.5)

    _draw_text_bold(d, W / 2, H - 16, "IPFS Content Addressing", size=10,
                    color=DARK_BLUE, anchor="middle")

    # Hash pipeline
    pipe_y = H - 55
    # File box
    _draw_box(d, 20, pipe_y - 25, 90, 30, LIGHT_BLUE, MED_BLUE)
    _draw_text(d, 65, pipe_y - 8, '"Hello World"', size=8, color=DARK_BLUE, anchor="middle")
    _draw_text(d, 65, pipe_y - 20, "File content", size=6, color=MED_BLUE, anchor="middle")

    _draw_arrow(d, 112, pipe_y - 10, 142, pipe_y - 10, color=DARK_GRAY)

    # SHA-256 box
    _draw_box(d, 144, pipe_y - 25, 80, 30, PURPLE_BG, PURPLE)
    _draw_text_bold(d, 184, pipe_y - 8, "SHA-256", size=8, color=PURPLE, anchor="middle")
    _draw_text(d, 184, pipe_y - 20, "Hash function", size=6, color=PURPLE, anchor="middle")

    _draw_arrow(d, 226, pipe_y - 10, 256, pipe_y - 10, color=DARK_GRAY)

    # CID box
    _draw_box(d, 258, pipe_y - 30, 225, 35, GREEN_BG, GREEN)
    _draw_text_bold(d, 370, pipe_y - 6, "CID: QmT78zSuBmuS4z925WZfrq...", size=7.5,
                    color=GREEN, anchor="middle")
    _draw_text(d, 370, pipe_y - 20, "Content Identifier (immutable, unique)", size=6,
               color=GREEN, anchor="middle")

    # Two gateway boxes
    gw_y = pipe_y - 80
    gw_w, gw_h = 190, 80

    # Primary
    _draw_box(d, 30, gw_y - gw_h, gw_w, gw_h, HexColor("#f0f7ff"), MED_BLUE)
    _draw_text_bold(d, 125, gw_y - 12, "Primary Gateway (.152)", size=8,
                    color=DARK_BLUE, anchor="middle")
    _draw_text(d, 125, gw_y - 28, "ipfs pin add QmT78z...", size=7,
               color=DARK_GRAY, anchor="middle")
    _draw_text(d, 125, gw_y - 44, 'GET /ipfs/QmT78z...', size=7,
               color=DARK_GRAY, anchor="middle")
    _draw_text(d, 125, gw_y - 58, '-> "Hello World"', size=7,
               color=GREEN, anchor="middle")

    # Preferred
    _draw_box(d, 280, gw_y - gw_h, gw_w, gw_h, HexColor("#fff8f0"), ORANGE)
    _draw_text_bold(d, 375, gw_y - 12, "Preferred Gateway (.143)", size=8,
                    color=ORANGE, anchor="middle")
    _draw_text(d, 375, gw_y - 28, "ipfs pin add QmT78z...", size=7,
               color=DARK_GRAY, anchor="middle")
    _draw_text(d, 375, gw_y - 44, 'GET /ipfs/QmT78z...', size=7,
               color=DARK_GRAY, anchor="middle")
    _draw_text(d, 375, gw_y - 58, '-> "Hello World"', size=7,
               color=GREEN, anchor="middle")

    # Arrows from CID to both gateways
    cid_bottom = pipe_y - 30
    _draw_arrow(d, 300, cid_bottom, 125, gw_y, color=MED_BLUE, dashed=True)
    _draw_arrow(d, 400, cid_bottom, 375, gw_y, color=ORANGE, dashed=True)

    # Guarantee labels at bottom
    _draw_text_bold(d, W / 2, 16, "SAME CID = SAME content (cryptographically guaranteed)", size=8,
                    color=GREEN, anchor="middle")
    _draw_text(d, W / 2, 4, "Migration cannot corrupt data -- content is addressed by hash",
               size=7, color=DARK_GRAY, anchor="middle")

    return d


def build_ipfs_network_topology():
    """IPFS peer network: nodes pinning same CID, connected via Bitswap/DHT."""
    W, H = 500, 240
    d = Drawing(W, H)
    _draw_box(d, 0, 0, W, H, HexColor("#fafcff"), stroke=BORDER, stroke_w=0.5)

    _draw_text_bold(d, W / 2, H - 16, "IPFS Network Topology: Shared CID Pinning", size=10,
                    color=DARK_BLUE, anchor="middle")

    # Central CID "cloud"
    cloud_x, cloud_y = 250, 135
    _draw_box(d, cloud_x - 55, cloud_y - 18, 110, 36, TEAL_BG, TEAL)
    _draw_text_bold(d, cloud_x, cloud_y + 6, "IPFS DHT", size=9, color=TEAL, anchor="middle")
    _draw_text(d, cloud_x, cloud_y - 8, "CID: QmT78z...", size=7, color=TEAL, anchor="middle")

    # Nodes around the cloud
    nodes = [
        (70, 190, "Primary\nGateway", ".152", MED_BLUE, HexColor("#f0f7ff")),
        (430, 190, "Preferred\nGateway", ".143", ORANGE, HexColor("#fff8f0")),
        (70, 70, "Bootstrap\nPeer", "peer-A", PURPLE, PURPLE_BG),
        (430, 70, "Remote\nPeer", "peer-B", PURPLE, PURPLE_BG),
        (250, 35, "IPNI\nIndexer", "indexer", DARK_GRAY, GRAY_BG),
    ]

    for nx, ny, label, sub, col, bg in nodes:
        _draw_box(d, nx - 45, ny - 22, 90, 44, bg, col)
        lines = label.split("\n")
        _draw_text_bold(d, nx, ny + 7, lines[0], size=7.5, color=col, anchor="middle")
        if len(lines) > 1:
            _draw_text(d, nx, ny - 5, lines[1], size=7.5, color=col, anchor="middle")
        _draw_text(d, nx, ny - 17, sub, size=6, color=DARK_GRAY, anchor="middle")

    # Lines from each node to cloud
    for nx, ny, *_ in nodes:
        d.add(Line(nx, ny + 22 if ny < cloud_y else ny - 22,
                   cloud_x, cloud_y - 18 if ny < cloud_y else cloud_y + 18,
                   strokeColor=BORDER, strokeWidth=0.8, strokeDashArray=[3, 3]))

    # Bitswap label between primary and preferred
    _draw_text(d, 250, 198, "Bitswap block exchange", size=6.5,
               color=DARK_GRAY, anchor="middle")
    d.add(Line(115, 190, 385, 190, strokeColor=GREEN, strokeWidth=1, strokeDashArray=[5, 3]))

    return d


# ── PDF builder ──────────────────────────────────────────────────────────────

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=letter,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=22, leading=26, textColor=DARK_BLUE,
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, leading=14, textColor=MED_BLUE,
        spaceAfter=16, alignment=TA_CENTER, fontName="Helvetica",
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=16, leading=20, textColor=DARK_BLUE,
        spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold",
        borderWidth=0, borderPadding=0,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, leading=16, textColor=MED_BLUE,
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold",
    )
    h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=11, leading=14, textColor=DARK_GRAY,
        spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold",
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, textColor=DARK_GRAY,
        spaceAfter=6, alignment=TA_JUSTIFY, fontName="Helvetica",
    )
    body_italic = ParagraphStyle(
        "BodyItalic", parent=body,
        fontName="Helvetica-Oblique", textColor=MED_BLUE,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body,
        leftIndent=20, bulletIndent=8, spaceBefore=2, spaceAfter=2,
    )
    sub_bullet = ParagraphStyle(
        "SubBullet", parent=body,
        leftIndent=40, bulletIndent=26,
        spaceBefore=1, spaceAfter=1, fontSize=9, leading=12,
    )
    code_style = ParagraphStyle(
        "Code", parent=body,
        fontName="Courier", fontSize=8.5, leading=11,
        backColor=GRAY_BG, borderColor=BORDER,
        borderWidth=0.5, borderPadding=6,
        spaceBefore=4, spaceAfter=6, textColor=DARK_GRAY,
    )
    highlight_style = ParagraphStyle(
        "Highlight", parent=body,
        fontSize=10, leading=14,
        backColor=GREEN_BG, borderColor=GREEN,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=GREEN, fontName="Helvetica-Bold",
    )
    warning_style = ParagraphStyle(
        "Warning", parent=body,
        fontSize=10, leading=14,
        backColor=ORANGE_BG, borderColor=ORANGE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ORANGE, fontName="Helvetica-Bold",
    )
    negative_style = ParagraphStyle(
        "Negative", parent=body,
        fontSize=10, leading=14,
        backColor=RED_BG, borderColor=ACCENT,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ACCENT, fontName="Helvetica-Bold",
    )
    info_style = ParagraphStyle(
        "Info", parent=body,
        fontSize=10, leading=14,
        backColor=TEAL_BG, borderColor=TEAL,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=TEAL, fontName="Helvetica-Bold",
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

    # ══════════════════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Spacer(1, 1.2 * inch))
    elements.append(Paragraph("IPFS Gateway Migration", title_style))
    elements.append(Paragraph("Proof of Concept", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Content-Addressed Storage with QUIC Server-Side Migration", subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"PoC Documentation &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.6 * inch))

    # Abstract
    abstract_text = (
        "This document describes a proof-of-concept demonstrating QUIC server-side connection "
        "migration between two IPFS gateways. Both gateways pin the same content (identified by CID), "
        "and the primary gateway advertises the preferred gateway's address during the QUIC handshake. "
        "IPFS's content-addressing model guarantees that content served by either gateway is "
        "cryptographically identical, making IPFS a natural fit for migration scenarios. "
        "The PoC runs on our existing four-machine testbed using modified Neqo binaries. "
        "We cover IPFS fundamentals (CIDs, Merkle DAGs, Bitswap, IPNI), the role of libp2p and QUIC "
        "in the IPFS stack, gateway vs. peer-to-peer considerations, and scalability implications "
        "for production gateway clusters."
    )
    abstract_tbl = Table(
        [[Paragraph(abstract_text, ParagraphStyle(
            "Abstract", parent=body, fontSize=9.5, leading=13, textColor=DARK_GRAY,
        ))]],
        colWidths=[5.5 * inch],
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

    # ══════════════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("Table of Contents", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))
    toc_items = [
        "1. IPFS Fundamentals",
        "2. IPFS Implementations",
        "3. libp2p and QUIC in the IPFS Stack",
        "4. Gateway vs. Peer-to-Peer Migration",
        "5. Architecture",
        "6. How It Works",
        "7. Content Verification",
        "8. Bitswap Protocol",
        "9. IPNI (InterPlanetary Network Indexer)",
        "10. Production IPFS Gateways",
        "11. Setup Requirements",
        "12. How to Run",
        "13. Scenarios and Scalability",
        "14. Limitations",
        "15. Comparison: IPFS vs Traditional CDN",
    ]
    for item in toc_items:
        elements.append(Paragraph(item, ParagraphStyle(
            "TOC", parent=body, fontSize=10, leading=16, leftIndent=20,
            textColor=MED_BLUE, fontName="Helvetica",
        )))
    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. IPFS FUNDAMENTALS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("1. IPFS Fundamentals", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "IPFS (InterPlanetary File System) is a peer-to-peer, content-addressed storage and "
        "distribution protocol. Unlike traditional web hosting where content is identified by its "
        "location (URL), IPFS identifies content by <b>what it is</b> -- using cryptographic hashes.",
        body
    ))

    elements.append(Paragraph("1.1 Content Identifiers (CIDs)", h2))
    elements.append(Paragraph(
        "A CID (Content Identifier) is a self-describing, cryptographic hash of a piece of content. "
        "CIDs use multihash encoding, which embeds the hash algorithm and digest length in the "
        "identifier itself. CIDv0 uses bare SHA-256 multihash (starting with Qm...), while CIDv1 "
        "adds multibase and multicodec prefixes for extensibility (starting with bafy...).",
        body
    ))
    elements.append(Paragraph(
        "CID = multibase + multicodec + multihash(content)",
        code_style
    ))
    elements.append(Paragraph(
        "The critical property: if two nodes have content with the same CID, that content is "
        "byte-for-byte identical. This is enforced by the hash function -- SHA-256 collision "
        "resistance ensures no two different inputs produce the same CID.",
        body
    ))

    elements.append(Paragraph("1.2 Merkle DAGs", h2))
    elements.append(Paragraph(
        "IPFS organizes data as a Merkle DAG (Directed Acyclic Graph). Large files are split into "
        "blocks (default 256 KiB), each block gets its own CID, and a root node links to all "
        "block CIDs. The root CID recursively captures the integrity of the entire tree. Modifying "
        "a single byte in any block changes all CIDs from that block up to the root.",
        body
    ))
    elements.append(Paragraph(
        "File -> [Block 0 (CID_0)] [Block 1 (CID_1)] ... [Block N (CID_N)]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "Root CID = hash(link: CID_0, link: CID_1, ..., link: CID_N)",
        code_style
    ))
    elements.append(Paragraph(
        "This Merkle tree structure provides two benefits for gateway migration: (1) partial "
        "verification -- a client can verify individual blocks without downloading the entire file, "
        "and (2) deduplication -- identical blocks across files share the same CID and storage.",
        body
    ))

    elements.append(Paragraph("1.3 Content Addressing vs. Location Addressing", h2))
    elements.append(Paragraph(
        "Traditional web: <b>https://example.com/file.txt</b> identifies WHERE to get the file. "
        "If the server changes the file, the URL stays the same but returns different content. "
        "IPFS: <b>/ipfs/QmT78zSuBmuS4z925WZfrq...</b> identifies WHAT the file is. "
        "Any node that has this CID serves the exact same content. This is why IPFS is a natural "
        "fit for server migration -- the preferred server is guaranteed to serve the same data.",
        body
    ))

    elements.append(Paragraph(
        "Content addressing eliminates the fundamental trust problem in server migration: "
        "there is no need to trust that the preferred server has the correct data. "
        "The CID IS the verification.",
        highlight_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 2. IPFS IMPLEMENTATIONS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("2. IPFS Implementations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Several IPFS implementations exist, each targeting different use cases:",
        body
    ))

    impl_rows = [
        ["Kubo (Go)", "Reference implementation. Most mature, feature-complete. "
         "Default for servers and gateways. Used in this PoC.",
         "Production gateways, full nodes, pinning services"],
        ["Iroh (Rust)", "High-performance implementation by n0. Focuses on efficiency "
         "and embeddability. Does not implement full IPFS spec.",
         "Embedded systems, high-throughput applications"],
        ["Helia (JavaScript)", "Successor to js-ipfs. Runs in Node.js and browsers. "
         "Modular architecture with pluggable components.",
         "Browser-based dApps, lightweight nodes"],
        ["Nabu (Java)", "JVM-based implementation. Targets enterprise Java ecosystems.",
         "Enterprise integration, JVM applications"],
    ]
    elements.append(make_table(
        ["Implementation", "Description", "Use Cases"],
        impl_rows,
        col_widths=[1.2 * inch, 3.2 * inch, 2.6 * inch],
        highlight_row=1,
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "This PoC uses <b>Kubo</b> (formerly go-ipfs) because it is the reference implementation "
        "with the most complete feature set, the widest deployment base, and built-in HTTP gateway "
        "functionality. Kubo's gateway listens on port 8080 by default and serves content over "
        "plain HTTP, which our modified Neqo server proxies to clients over HTTP/3.",
        body
    ))

    elements.append(Paragraph(
        "This PoC uses Kubo (Go), the reference IPFS implementation. "
        "Kubo's built-in HTTP gateway (port 8080) is proxied by our Neqo HTTP/3 server.",
        info_style
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 3. LIBP2P AND QUIC IN THE IPFS STACK
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("3. libp2p and QUIC in the IPFS Stack", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "IPFS nodes communicate using libp2p, a modular networking stack that abstracts transport, "
        "peer discovery, and connection multiplexing. Since Kubo v0.18 (November 2022), QUIC is "
        "the <b>default transport</b> for peer-to-peer connections, replacing the older TCP+Noise "
        "stack.",
        body
    ))

    elements.append(Paragraph("3.1 libp2p Transport Layer", h2))
    elements.append(Paragraph(
        "libp2p supports multiple transports simultaneously. A Kubo node typically listens on:",
        body
    ))
    transport_rows = [
        ["/ip4/0.0.0.0/udp/4001/quic-v1", "QUIC v1 (default, preferred)"],
        ["/ip4/0.0.0.0/udp/4001/quic-v1/webtransport", "WebTransport over QUIC"],
        ["/ip4/0.0.0.0/tcp/4001", "TCP + Noise (fallback)"],
        ["/ip6/::/udp/4001/quic-v1", "QUIC v1 over IPv6"],
    ]
    elements.append(make_table(
        ["Multiaddr", "Transport"],
        transport_rows,
        col_widths=[3.5 * inch, 3.5 * inch],
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "QUIC provides several advantages for IPFS: (1) built-in encryption (TLS 1.3), eliminating "
        "the need for a separate Noise handshake; (2) multiplexed streams without head-of-line "
        "blocking; (3) faster connection establishment (0-RTT or 1-RTT); (4) native connection "
        "migration support (RFC 9000 Section 9).",
        body
    ))

    elements.append(Paragraph("3.2 PeerID and TLS Certificates", h2))
    elements.append(Paragraph(
        "Each IPFS node has a PeerID derived from its public key (typically Ed25519). During the "
        "QUIC/TLS handshake, the node presents a self-signed X.509 certificate containing a libp2p "
        "extension (OID 1.3.6.1.4.1.53594.1.1) that embeds its public key. The connecting peer "
        "verifies that the certificate's embedded key matches the expected PeerID.",
        body
    ))
    elements.append(Paragraph(
        "This creates a fundamental challenge for peer-to-peer migration: migrating a QUIC "
        "connection to a different peer means the new peer has a different PeerID and certificate. "
        "The client would detect the identity change and reject the connection. This is why our "
        "PoC operates at the gateway layer, where standard TLS certificates (not PeerID-based) "
        "are used.",
        body
    ))

    elements.append(Paragraph(
        "Peer-to-peer migration is blocked by PeerID authentication. "
        "Gateway migration (HTTP/3 with standard TLS certs) sidesteps this limitation.",
        warning_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 4. GATEWAY VS PEER-TO-PEER MIGRATION
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("4. Gateway vs. Peer-to-Peer Migration", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "There are two conceptually different levels at which QUIC migration could apply to IPFS:",
        body
    ))

    elements.append(Paragraph("4.1 Gateway Migration (This PoC)", h2))
    elements.append(Paragraph(
        "IPFS gateways are HTTP servers that bridge IPFS and the traditional web. They accept "
        "standard HTTP requests (e.g., GET /ipfs/QmT78z...) and return the corresponding IPFS "
        "content. Gateway migration is feasible today because:",
        body
    ))
    gw_reasons = [
        "Gateways use standard TLS certificates (not PeerID-based), so migration does not "
        "trigger identity verification failures.",
        "Gateways are stateless with respect to content: any gateway that pins the CID can serve it.",
        "Production gateways already operate as clusters behind load balancers -- migration "
        "formalizes this at the QUIC protocol layer.",
        "No changes to IPFS clients (browsers) are required -- they use standard HTTP/3.",
    ]
    for r in gw_reasons:
        elements.append(Paragraph(f"<bullet>&bull;</bullet> {r}", bullet_style))

    elements.append(Paragraph("4.2 Peer-to-Peer Migration (Future Work)", h2))
    elements.append(Paragraph(
        "Migrating native IPFS peer-to-peer connections is significantly harder because:",
        body
    ))
    p2p_reasons = [
        "PeerID is cryptographically bound to the TLS certificate. Migrating to a different "
        "peer changes the identity.",
        "Active Bitswap sessions carry complex state (want-lists, block requests, session context) "
        "that would need serialization.",
        "libp2p's connection security model assumes end-to-end identity verification, which "
        "migration inherently violates.",
        "The receiving peer would need the sending peer's private key to maintain identity, "
        "which defeats the security model.",
    ]
    for r in p2p_reasons:
        elements.append(Paragraph(f"<bullet>&bull;</bullet> {r}", bullet_style))

    elements.append(Paragraph(
        "Gateway migration is feasible TODAY with no protocol changes. "
        "Peer-to-peer migration requires fundamental libp2p authentication changes.",
        highlight_style
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 5. ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("5. Architecture", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The PoC uses our existing four-machine testbed on the same LAN (141.217.168.x):",
        body
    ))

    arch_rows = [
        ["Primary Gateway", "opti7040 (.152)",
         "Kubo IPFS daemon + Neqo HTTP/3 server (webseed-primary)"],
        ["Preferred Gateway", "homeserver2 (.143)",
         "Kubo IPFS daemon + preferred-server binary"],
        ["Client", "optiplex7010 (.127)",
         "Firefox browser or neqo-client"],
        ["Redis (optional)", "Proxmox VM (.200)",
         "State transfer backend (Redis KV or Pub/Sub)"],
    ]
    elements.append(make_table(
        ["Role", "Machine", "Components"],
        arch_rows,
        col_widths=[1.5 * inch, 1.5 * inch, 4.0 * inch],
    ))
    elements.append(Spacer(1, 10))

    # ── Architecture diagram ──
    elements.append(build_architecture_diagram())
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Both the primary and preferred gateways run a local Kubo IPFS node, each pinning "
        "the same test content. The primary gateway fetches content from its local IPFS HTTP "
        "gateway (localhost:8080) and serves it to clients over HTTP/3 via the webseed-primary "
        "binary. During the QUIC handshake, the primary advertises the preferred gateway's "
        "address (.143) using the preferred_address transport parameter.",
        body
    ))

    elements.append(Paragraph(
        "After the handshake, the primary exports 445 bytes of migration state (TLS secrets, "
        "connection IDs, client address, version, packet numbers) and transfers it to the "
        "preferred server. The preferred server imports this state and handles the client's "
        "PATH_CHALLENGE/PATH_RESPONSE validation, completing the migration transparently.",
        body
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 6. HOW IT WORKS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("6. How It Works", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    steps = [
        ("Pin content on both nodes:",
         "Both IPFS nodes pin the same content, identified by a CID (Content Identifier). "
         "The CID is a cryptographic hash of the content. Pinning ensures the content is "
         "retained locally and not garbage-collected."),
        ("Primary fetches from local IPFS:",
         "The primary server's webseed-primary binary fetches content from the local IPFS "
         "gateway at localhost:8080/ipfs/&lt;CID&gt;. This is a simple HTTP GET to the Kubo "
         "gateway running on the same machine."),
        ("Serve via HTTP/3:",
         "The primary serves the fetched content to the client over HTTP/3 using the modified "
         "Neqo stack. The client (Firefox) sees a standard HTTPS page."),
        ("Advertise preferred address:",
         "During the QUIC handshake, the primary includes preferred_address = 141.217.168.143 "
         "in its transport parameters (RFC 9000 Section 9.6)."),
        ("Export and transfer state:",
         "The primary exports migration state (445 bytes: TLS secrets, CIDs, client address, "
         "version, packet numbers) and sends it to the preferred server via the configured "
         "state transfer backend (TCP push, HTTP pull, Redis KV, or Redis Pub/Sub)."),
        ("Client validates new path:",
         "The client sends PATH_CHALLENGE to the preferred server. The preferred server, "
         "having imported the crypto state, decrypts the challenge and sends an encrypted "
         "PATH_RESPONSE back. The client validates the response and migrates."),
        ("Content integrity guaranteed:",
         "Because both gateways pin the same CID, the content is cryptographically identical. "
         "IPFS guarantees this by design -- the CID IS the hash of the content."),
    ]
    for i, (label, desc) in enumerate(steps, 1):
        elements.append(Paragraph(f"<b>{i}. {label}</b> {desc}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Content integrity is GUARANTEED by IPFS: the CID is a cryptographic hash of the "
        "content. Same CID = same content, regardless of which gateway serves it.",
        highlight_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 7. CONTENT VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("7. Content Verification", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    # ── Content addressing diagram ──
    elements.append(build_content_addressing_diagram())
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Content verification in IPFS is fundamentally different from traditional web systems. "
        "In a traditional CDN, verifying that the preferred server has the correct content "
        "requires external mechanisms: SHA-256 checksums, Subresource Integrity (SRI) hashes, "
        "or certificate transparency logs. These are bolt-on verification layers that must be "
        "explicitly implemented and maintained.",
        body
    ))
    elements.append(Paragraph(
        "With IPFS, verification is <b>intrinsic</b>. The CID itself is the verification. When "
        "a client requests /ipfs/QmT78z..., any node that responds must provide content whose "
        "SHA-256 hash matches the CID. If the content does not match, the IPFS node rejects it. "
        "No additional verification infrastructure is needed.",
        body
    ))
    elements.append(Paragraph(
        "For gateway migration, this means: (1) both gateways pin the same CID, so both serve "
        "identical content; (2) if either gateway's content is corrupted, the CID mismatch is "
        "detectable; (3) the client can independently verify content integrity by hashing the "
        "received data and comparing it to the CID.",
        body
    ))
    elements.append(Paragraph(
        "IPFS provides zero-configuration content verification. No SRI hashes, no checksums, "
        "no certificate transparency. The CID IS the verification.",
        highlight_style
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 8. BITSWAP PROTOCOL
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("8. Bitswap Protocol", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Bitswap is the data exchange protocol used by IPFS nodes to request and send blocks. "
        "It operates as a block-level barter system: nodes maintain want-lists (blocks they need) "
        "and exchange blocks with connected peers.",
        body
    ))

    elements.append(Paragraph("8.1 How Bitswap Works", h2))
    bitswap_steps = [
        "A node adds a CID to its want-list (WANT_HAVE or WANT_BLOCK message).",
        "Connected peers check if they have the requested block.",
        "If a peer has the block, it sends a HAVE response (or the block itself for WANT_BLOCK).",
        "The requesting node sends a BLOCK request to the peer that has it.",
        "The peer sends the block data, and the requesting node verifies it against the CID.",
        "The block is stored locally and can now be served to other peers.",
    ]
    for i, step in enumerate(bitswap_steps, 1):
        elements.append(Paragraph(f"<bullet>{i}.</bullet> {step}", bullet_style))

    elements.append(Paragraph("8.2 Bitswap and Gateway Migration", h2))
    elements.append(Paragraph(
        "In the gateway model, Bitswap is used <b>between IPFS nodes</b> to ensure both gateways "
        "have the content pinned. The gateway-to-client communication uses standard HTTP/3, not "
        "Bitswap. This separation is key: the complex Bitswap session state does not need to be "
        "migrated. Only the QUIC/TLS state (445 bytes) is transferred.",
        body
    ))
    elements.append(Paragraph(
        "If both gateways are connected as IPFS peers, pinning content on the primary "
        "automatically makes it available to the preferred gateway via Bitswap. The preferred "
        "gateway can fetch blocks it does not yet have directly from the primary.",
        body
    ))

    elements.append(Paragraph(
        "Bitswap handles content replication between IPFS nodes. "
        "Gateway migration only transfers QUIC state (445 bytes), not Bitswap sessions.",
        info_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 9. IPNI (INTERPLANETARY NETWORK INDEXER)
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("9. IPNI (InterPlanetary Network Indexer)", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "IPNI is the content routing system that helps clients find which IPFS nodes provide "
        "specific content. When a node pins content, it advertises the CID to IPNI indexers. "
        "Clients query the indexer to find providers before connecting to them.",
        body
    ))

    elements.append(Paragraph("9.1 Content Routing Flow", h2))
    routing_steps = [
        "A node pins content and publishes an advertisement to IPNI (via HTTP or gossipsub).",
        "IPNI indexers (e.g., cid.contact) ingest the advertisement and index the CID-to-provider mapping.",
        "A client wanting content queries the indexer: \"Who has CID QmT78z...?\"",
        "The indexer returns a list of providers (PeerIDs and multiaddrs).",
        "The client connects to a provider and fetches the content via Bitswap or HTTP.",
    ]
    for i, step in enumerate(routing_steps, 1):
        elements.append(Paragraph(f"<bullet>{i}.</bullet> {step}", bullet_style))

    elements.append(Paragraph("9.2 IPNI and Gateway Migration", h2))
    elements.append(Paragraph(
        "In the gateway migration context, IPNI plays a supporting role. Both gateways advertise "
        "the same CID to the indexer. A client that discovers one gateway through IPNI and "
        "connects via HTTP/3 can be seamlessly migrated to the other gateway, which also "
        "advertises the same CID. The IPNI indexer can also be used to select the optimal "
        "preferred server based on geographic proximity or load.",
        body
    ))

    # ── Network topology diagram ──
    elements.append(build_ipfs_network_topology())
    elements.append(Spacer(1, 6))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 10. PRODUCTION IPFS GATEWAYS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("10. Production IPFS Gateways", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Several production IPFS gateways serve content to millions of users. These gateways "
        "already operate as multi-server clusters, making them natural candidates for QUIC "
        "server-side migration:",
        body
    ))

    gw_rows = [
        ["ipfs.io", "Protocol Labs", "Reference gateway. Multi-region deployment with "
         "geographic routing via anycast DNS."],
        ["dweb.link", "Protocol Labs", "Trustless gateway supporting verifiable responses "
         "(IPFS Trustless Gateway spec)."],
        ["cf-ipfs.com", "Cloudflare", "Cloudflare IPFS Gateway. Runs on Cloudflare's edge "
         "network across 300+ cities worldwide."],
        ["w3s.link", "web3.storage", "Gateway for web3.storage pinning service. Backed by "
         "Elastic IPFS infrastructure."],
        ["nftstorage.link", "NFT.Storage", "Specialized gateway for NFT metadata and assets. "
         "High-availability with global distribution."],
    ]
    elements.append(make_table(
        ["Gateway", "Operator", "Description"],
        gw_rows,
        col_widths=[1.3 * inch, 1.3 * inch, 4.4 * inch],
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "These gateways already use load balancing and geographic routing to distribute traffic. "
        "QUIC server-side migration would provide a protocol-native mechanism for mid-connection "
        "server switching, eliminating the need for DNS-based or HTTP-redirect-based failover. "
        "Benefits include: zero extra round-trips (unlike HTTP 302 redirects), preserved "
        "connection state (unlike DNS failover), and transparent operation (the client does not "
        "need to re-establish TLS).",
        body
    ))

    elements.append(Paragraph(
        "Production IPFS gateways already operate as clusters. QUIC migration adds "
        "protocol-native, zero-round-trip server switching to their existing infrastructure.",
        highlight_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 11. SETUP REQUIREMENTS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("11. Setup Requirements", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("11.1 Kubo Installation", h2))
    elements.append(Paragraph(
        "Kubo is distributed as a single binary. Install on both gateway machines:",
        body
    ))
    elements.append(Paragraph(
        "wget https://dist.ipfs.tech/kubo/v0.32.1/kubo_v0.32.1_linux-amd64.tar.gz<br/>"
        "tar xzf kubo_v0.32.1_linux-amd64.tar.gz<br/>"
        "sudo mv kubo/ipfs /usr/local/bin/<br/>"
        "ipfs init",
        code_style
    ))

    elements.append(Paragraph("11.2 Gateway Configuration", h2))
    elements.append(Paragraph(
        "Configure the IPFS gateway to listen on the appropriate interface:",
        body
    ))
    elements.append(Paragraph(
        "ipfs config Addresses.Gateway /ip4/127.0.0.1/tcp/8080<br/>"
        "ipfs config --json Gateway.PublicGateways '{}'",
        code_style
    ))

    elements.append(Paragraph("11.3 Peer Connection", h2))
    elements.append(Paragraph(
        "Connect the two IPFS nodes so they can exchange blocks via Bitswap:",
        body
    ))
    elements.append(Paragraph(
        "# On primary (.152):<br/>"
        "ipfs swarm connect /ip4/141.217.168.143/udp/4001/quic-v1/p2p/&lt;PEER_ID_143&gt;<br/>"
        "<br/>"
        "# Verify connection:<br/>"
        "ipfs swarm peers | grep 141.217.168.143",
        code_style
    ))

    elements.append(Paragraph("11.4 Pin Test Content", h2))
    elements.append(Paragraph(
        "Pin the same content on both nodes. The CID ensures both serve identical data:",
        body
    ))
    elements.append(Paragraph(
        "# On primary (.152):<br/>"
        'echo "Hello World" | ipfs add -Q<br/>'
        "# Returns: QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o<br/>"
        "<br/>"
        "# On preferred (.143):<br/>"
        "ipfs pin add QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o",
        code_style
    ))

    elements.append(Paragraph("11.5 Verify Content", h2))
    elements.append(Paragraph(
        "Verify both gateways serve the same content:",
        body
    ))
    elements.append(Paragraph(
        "curl http://localhost:8080/ipfs/QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o<br/>"
        "# Should print: Hello World",
        code_style
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 12. HOW TO RUN
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("12. How to Run", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Three shell scripts automate the IPFS environment setup, testing, and teardown:",
        body
    ))

    elements.append(Paragraph("12.1 Setup IPFS on both servers", h2))
    elements.append(Paragraph(
        "Run from the client machine (optiplex7010). This installs Kubo, initializes "
        "repositories, starts the IPFS daemons, and pins test content on both gateway servers.",
        body
    ))
    elements.append(Paragraph(
        "./setup_ipfs.sh",
        code_style
    ))

    elements.append(Paragraph("12.2 Start the preferred server", h2))
    elements.append(Paragraph(
        "On homeserver2 (.143), start the preferred server binary. This listens for "
        "incoming migration state on port 9999 and serves HTTP/3 on port 4433.",
        body
    ))
    elements.append(Paragraph(
        "preferred-server 141.217.168.143:4433 9999",
        code_style
    ))

    elements.append(Paragraph("12.3 Start the primary server", h2))
    elements.append(Paragraph(
        "On opti7040 (.152), start the webseed-primary binary. It fetches content from "
        "the local IPFS gateway and serves it over HTTP/3, advertising .143 as the "
        "preferred address.",
        body
    ))
    elements.append(Paragraph(
        "webseed-primary 0.0.0.0:4433 141.217.168.143:4433 /tmp/ipfs_serve_content.bin",
        code_style
    ))

    elements.append(Paragraph("12.4 Test the migration", h2))
    elements.append(Paragraph(
        "Run the test script from the client machine, or open Firefox and navigate "
        "to https://141.217.168.152:4433/. The page should load via HTTP/3 with "
        "a transparent migration to the preferred server.",
        body
    ))
    elements.append(Paragraph(
        "./test_ipfs_migration.sh",
        code_style
    ))

    elements.append(Paragraph("12.5 Teardown", h2))
    elements.append(Paragraph(
        "Stops the IPFS daemons on both servers and cleans up temporary files. "
        "Does not uninstall Kubo or remove the IPFS repositories.",
        body
    ))
    elements.append(Paragraph(
        "./teardown_ipfs.sh",
        code_style
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 13. SCENARIOS AND SCALABILITY
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("13. Scenarios and Scalability", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("13.1 Gateway Load Balancing", h2))
    elements.append(Paragraph(
        "When an IPFS gateway becomes overloaded, it can use QUIC preferred_address to migrate "
        "incoming connections to a less-loaded gateway that pins the same content. Unlike "
        "DNS-based load balancing, this happens mid-connection without requiring a new TLS "
        "handshake, reducing latency and preserving connection state.",
        body
    ))

    elements.append(Paragraph("13.2 Gateway Maintenance", h2))
    elements.append(Paragraph(
        "Before shutting down a gateway node for maintenance, existing connections can be "
        "gracefully drained to the preferred server. New connections are directed to the "
        "preferred server immediately via preferred_address, while existing connections "
        "complete their current transfers before migrating. This enables zero-downtime "
        "maintenance of gateway infrastructure.",
        body
    ))

    elements.append(Paragraph("13.3 Geographic Optimization", h2))
    elements.append(Paragraph(
        "An IPFS gateway can accept initial connections (via anycast or DNS) and then redirect "
        "clients to a geographically closer gateway. After the initial handshake reveals the "
        "client's IP address, the primary gateway selects the optimal preferred server based on "
        "network topology. The client migrates transparently, improving latency for subsequent "
        "requests without requiring client-side changes.",
        body
    ))

    elements.append(Paragraph("13.4 IPFS Gateway Clusters with QUIC Migration", h2))
    elements.append(Paragraph(
        "In a production deployment, IPFS gateway clusters can use QUIC migration for load "
        "distribution across multiple backend servers. The architecture is:",
        body
    ))
    cluster_points = [
        "A pool of N gateway servers, each running Kubo and pinning popular content.",
        "An entry gateway accepts initial connections and performs the QUIC handshake.",
        "Based on load metrics, the entry gateway selects a backend server and advertises "
        "its address via preferred_address.",
        "Migration state (445 bytes) is transferred via Redis KV (recommended for clusters) "
        "or HTTP pull.",
        "The backend server handles subsequent requests, serving content from its local IPFS node.",
        "If the backend becomes overloaded, it can chain another migration to a different backend.",
    ]
    for point in cluster_points:
        elements.append(Paragraph(f"<bullet>&bull;</bullet> {point}", bullet_style))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Scalability advantage: IPFS's content-addressing means any server pinning the CID "
        "can serve as a migration target. No session affinity or content synchronization "
        "logic is needed -- the CID guarantees content consistency.",
        highlight_style
    ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 14. LIMITATIONS
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("14. Limitations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("14.1 Peer Identity", h2))
    elements.append(Paragraph(
        "IPFS nodes have PeerIDs that are cryptographically tied to their TLS certificates. "
        "Migration between different peers requires changes to libp2p's authentication layer, "
        "since the receiving node has a different identity. This PoC operates at the gateway "
        "layer (HTTP/3), where PeerID authentication is not enforced for HTTP clients.",
        body
    ))
    elements.append(Paragraph(
        "Peer Identity: IPFS PeerIDs are tied to TLS certificates. Migration between "
        "different peers requires libp2p authentication changes.",
        warning_style
    ))

    elements.append(Paragraph("14.2 Bitswap Streams", h2))
    elements.append(Paragraph(
        "Active Bitswap streams (the protocol IPFS uses for peer-to-peer block exchange) "
        "carry complex state including want-lists, block requests, and session information. "
        "This state cannot be easily serialized and transferred between nodes. Migration "
        "of native IPFS peer-to-peer connections would require significant Bitswap protocol "
        "modifications.",
        body
    ))

    elements.append(Paragraph("14.3 Gateway-Mode Only", h2))
    elements.append(Paragraph(
        "This PoC operates in gateway mode -- serving IPFS content over HTTP/3 to standard "
        "clients (browsers). It does not attempt to migrate native peer-to-peer IPFS transport "
        "connections (which use libp2p + QUIC). The gateway-mode approach is practical because "
        "it requires no changes to IPFS clients and leverages standard HTTP/3 semantics.",
        body
    ))
    elements.append(Paragraph(
        "This PoC uses gateway-mode (HTTP/3), not native peer-to-peer IPFS transport. "
        "Native IPFS migration would require libp2p and Bitswap protocol changes.",
        negative_style
    ))

    elements.append(Paragraph("14.4 Mutable Content (IPNS)", h2))
    elements.append(Paragraph(
        "IPFS CIDs are immutable -- they always refer to the same content. Mutable references "
        "(IPNS names) add a layer of indirection: an IPNS name resolves to a CID, and the "
        "mapping can be updated. During migration, both gateways must resolve the same IPNS "
        "name to the same CID, which requires IPNS record propagation. Stale IPNS records "
        "could cause the preferred gateway to serve an older version of the content.",
        body
    ))

    elements.append(Paragraph("14.5 Large Content and Partial Pinning", h2))
    elements.append(Paragraph(
        "If the preferred gateway has not fully pinned the content (e.g., it is still fetching "
        "blocks via Bitswap), requests for unpinned blocks will result in Bitswap lookups, "
        "increasing latency. For production deployments, the preferred gateway should pre-pin "
        "popular content or use the primary gateway as a Bitswap peer for fast block retrieval.",
        body
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # 15. COMPARISON: IPFS vs Traditional CDN
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(Paragraph("15. Comparison: IPFS vs Traditional CDN", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The following table compares IPFS gateway migration with traditional CDN approaches "
        "across key dimensions relevant to server-side connection migration:",
        body
    ))

    comparison_rows = [
        ["Content ID model", "Location-based (URL)", "Content-based (CID)"],
        ["Content verification", "None (trust server)", "CID hash (cryptographic)"],
        ["Content availability", "Operator-managed replication", "P2P replication (Bitswap)"],
        ["Migration safety", "Data could differ", "Guaranteed identical (same CID)"],
        ["Integrity after migration", "Requires SRI/checksums", "Automatic (CID = hash)"],
        ["Server discovery", "DNS / load balancer", "IPNI indexer + DHT"],
        ["Client changes needed", "None", "None (standard HTTP/3)"],
        ["Content deduplication", "Manual / CDN-specific", "Automatic (Merkle DAG)"],
        ["Partial verification", "Not supported", "Per-block CID verification"],
        ["Multi-provider", "CDN edge locations", "Any pinning node"],
    ]
    elements.append(make_table(
        ["Feature", "Traditional CDN", "IPFS Gateway + Migration"],
        comparison_rows,
        col_widths=[1.8 * inch, 2.3 * inch, 2.9 * inch],
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "The key advantage of IPFS for migration is <b>content verification</b>: with traditional "
        "CDNs, there is no protocol-level guarantee that the preferred server will serve the same "
        "content as the primary. With IPFS, the CID cryptographically binds the content to its hash. "
        "If the preferred gateway returns different data, the CID will not match, and the client "
        "(or an intermediate verification layer) can detect the discrepancy.",
        body
    ))

    elements.append(Paragraph(
        "IPFS + QUIC migration provides cryptographic content integrity guarantees that "
        "traditional CDNs cannot match. The CID ensures identical content across all gateways.",
        highlight_style
    ))

    # ── Build ──
    doc.build(elements)
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

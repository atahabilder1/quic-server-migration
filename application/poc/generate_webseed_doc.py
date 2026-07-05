#!/usr/bin/env python3
"""Generate BitTorrent WebSeed Migration PoC PDF."""

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

OUTPUT = "/home/anik/code/quic/application/poc/WEBSEED_POC.pdf"

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
    elements.append(Paragraph("BitTorrent WebSeed Migration", title_style))
    elements.append(Paragraph("Proof of Concept", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "HTTP/3 File Download with Transparent QUIC Server Migration",
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
        "This document describes a proof-of-concept implementation demonstrating QUIC server-side "
        "migration applied to the BitTorrent WebSeed (BEP 19) use case. A primary HTTP/3 server "
        "begins serving a large file download, then transparently migrates the connection to a "
        "preferred server on a different machine. The client receives the complete file without "
        "interruption, and verifies integrity via SHA-256 hash comparison. This PoC validates that "
        "QUIC server migration is directly applicable to HTTP/3-based file distribution systems "
        "like WebSeed, requiring <b>no protocol changes</b> to existing BitTorrent clients."
    )
    abstract_tbl = Table(
        [[Paragraph(abstract_text, ParagraphStyle(
            "Abstract", parent=body, fontSize=10, leading=14, textColor=DARK_GRAY,
        ))]],
        colWidths=[6.5*inch],
    )
    abstract_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BORDER", (0, 0), (-1, -1), 1, MED_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    elements.append(abstract_tbl)

    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # 1. OVERVIEW
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. Overview", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "BitTorrent WebSeed (BEP 19) allows .torrent files to include standard HTTP URLs as "
        "backup download sources alongside traditional BitTorrent peers. When the swarm has "
        "insufficient seeders, clients fall back to these HTTP-based sources to download "
        "pieces of the file.",
        body
    ))
    elements.append(Paragraph(
        "Modern WebSeed servers increasingly support HTTP/3, which runs over QUIC. This creates "
        "a natural fit for QUIC server-side migration: the WebSeed server can transparently "
        "migrate an active file download from one machine to another without the client needing "
        "to re-establish the connection or re-request the data.",
        body
    ))

    elements.append(Paragraph("Key Concepts", h2))
    for txt in [
        "<b>BEP 19 (WebSeed):</b> HTTP/HTTPS URLs embedded in .torrent files as fallback download sources",
        "<b>HTTP/3 over QUIC:</b> Modern WebSeeds use HTTP/3, which provides the QUIC transport layer",
        "<b>Server Migration:</b> QUIC's preferred_address mechanism (RFC 9000 Section 9.6) allows "
        "the primary server to redirect the client to a preferred server mid-connection",
        "<b>This PoC:</b> Two HTTP/3 servers host the same large file; the primary migrates to the "
        "preferred server mid-download, demonstrating seamless failover",
    ]:
        elements.append(Paragraph(txt, bullet_style, bulletText="\u2022"))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Advantage: WebSeed migration requires zero changes to the BitTorrent protocol "
        "or client software -- it operates entirely at the QUIC transport layer.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 2. ARCHITECTURE
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Architecture", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The PoC uses the existing four-machine testbed on the same LAN (141.217.168.x). "
        "Three machines participate directly in the WebSeed migration scenario:",
        body
    ))

    arch_table = make_table(
        ["Role", "Machine", "IP Address", "Description"],
        [
            ["Primary WebSeed", "opti7040", "141.217.168.152",
             "Serves file via HTTP/3, advertises preferred address, exports migration state"],
            ["Preferred WebSeed", "homeserver2", "141.217.168.143",
             "Imports migration state, handles PATH_CHALLENGE, continues serving file"],
            ["Client", "optiplex7010", "141.217.168.127",
             "Downloads file via HTTP/3, verifies SHA-256 integrity after migration"],
        ],
        col_widths=[1.2*inch, 1.1*inch, 1.3*inch, 3.4*inch],
    )
    elements.append(arch_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Migration Flow", h2))
    flow_steps = [
        "<b>1.</b> Client connects to Primary WebSeed (opti7040:4433) via HTTP/3",
        "<b>2.</b> Primary completes QUIC handshake, advertising preferred_address = 141.217.168.143:4433",
        "<b>3.</b> Primary begins serving the requested file, computing SHA-256 hash",
        "<b>4.</b> Primary exports migration state (~445 bytes: TLS secrets, CIDs, packet numbers)",
        "<b>5.</b> Migration state is transferred to Preferred server via configured backend (TCP/Redis/HTTP)",
        "<b>6.</b> Client sends PATH_CHALLENGE to preferred address (141.217.168.143:4433)",
        "<b>7.</b> Preferred server imports crypto state, decrypts PATH_CHALLENGE, sends PATH_RESPONSE",
        "<b>8.</b> Client validates PATH_RESPONSE -- migration complete, file download continues from preferred server",
    ]
    for step in flow_steps:
        elements.append(Paragraph(step, bullet_style, bulletText="\u2022"))

    # ══════════════════════════════════════════
    # 3. IMPLEMENTATION DETAILS
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. Implementation Details", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("webseed-primary Binary", h2))
    elements.append(Paragraph(
        "The primary server binary (<font face='Courier'>webseed-primary</font>) is a specialized "
        "HTTP/3 server built on top of the modified Neqo QUIC stack. It reads a file from disk, "
        "computes its SHA-256 hash using a pure Rust implementation, and serves it over HTTP/3 with "
        "metadata headers for client-side integrity verification.",
        body
    ))

    elements.append(Paragraph("HTTP/3 Response Headers", h3))
    headers_table = make_table(
        ["Header", "Value", "Purpose"],
        [
            ["content-type", "application/octet-stream", "Binary file download"],
            ["content-disposition", 'attachment; filename="&lt;name&gt;"',
             "Suggests filename to the client"],
            ["content-length", "&lt;size in bytes&gt;", "Total file size for progress tracking"],
            ["x-sha256", "&lt;hex-encoded hash&gt;",
             "SHA-256 of file contents for client-side integrity verification"],
        ],
        col_widths=[1.5*inch, 2.5*inch, 3.0*inch],
    )
    elements.append(headers_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "The <font face='Courier'>x-sha256</font> header is critical: it allows the client to verify "
        "that the file received after migration is byte-identical to what the primary server intended "
        "to serve. The client computes SHA-256 of the downloaded file and compares it against this header value.",
        body
    ))

    elements.append(Paragraph("Preferred Server", h3))
    elements.append(Paragraph(
        "The preferred server reuses the existing <font face='Courier'>preferred-server</font> binary "
        "from the core migration implementation. It imports the migration state (TLS secrets, connection "
        "IDs, packet numbers), handles the PATH_CHALLENGE/PATH_RESPONSE exchange with the client, and "
        "can continue serving data on the migrated connection.",
        body
    ))

    elements.append(Paragraph("SHA-256 Implementation", h3))
    elements.append(Paragraph(
        "File hashing uses a pure Rust SHA-256 implementation to avoid external dependencies. The hash "
        "is computed once when the file is loaded into memory, then served in the response header for "
        "every request. This ensures consistent integrity verification regardless of which server "
        "ultimately delivers the file content.",
        body
    ))

    # ══════════════════════════════════════════
    # 4. HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. How to Run", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph("Step 1: Create a Test File", h2))
    elements.append(Paragraph(
        "Generate a 100MB random binary file to use as the download payload:",
        body
    ))
    code_box_data = [
        [Paragraph(
            '<font face="Courier" size="9">'
            'dd if=/dev/urandom of=/tmp/test_100mb.bin bs=1M count=100'
            '</font>',
            body
        )]
    ]
    code_box = Table(code_box_data, colWidths=[6.5*inch])
    code_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
        ("BORDER", (0, 0), (-1, -1), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(code_box)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Step 2: Start the Preferred Server (homeserver2)", h2))
    code_box2_data = [
        [Paragraph(
            '<font face="Courier" size="9">'
            'preferred-server 141.217.168.143:4433 9999'
            '</font>',
            body
        )]
    ]
    code_box2 = Table(code_box2_data, colWidths=[6.5*inch])
    code_box2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
        ("BORDER", (0, 0), (-1, -1), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(code_box2)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "The preferred server listens on port 4433 (QUIC) and port 9999 (state transfer). "
        "It waits for migration state from the primary before accepting client connections.",
        body
    ))

    elements.append(Paragraph("Step 3: Start the Primary WebSeed Server (opti7040)", h2))
    code_box3_data = [
        [Paragraph(
            '<font face="Courier" size="9">'
            'webseed-primary 0.0.0.0:4433 141.217.168.143:4433 \\'
            '<br/>&nbsp;&nbsp;/tmp/test_100mb.bin 141.217.168.143:9999'
            '</font>',
            body
        )]
    ]
    code_box3 = Table(code_box3_data, colWidths=[6.5*inch])
    code_box3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
        ("BORDER", (0, 0), (-1, -1), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(code_box3)
    elements.append(Spacer(1, 4))

    args_table = make_table(
        ["Argument", "Example", "Description"],
        [
            ["Listen address", "0.0.0.0:4433", "Address and port for incoming QUIC connections"],
            ["Preferred address", "141.217.168.143:4433", "Address advertised in preferred_address transport parameter"],
            ["File path", "/tmp/test_100mb.bin", "Path to the file to serve via HTTP/3"],
            ["State transfer target", "141.217.168.143:9999", "Preferred server's state transfer endpoint"],
        ],
        col_widths=[1.4*inch, 1.7*inch, 3.9*inch],
    )
    elements.append(args_table)

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Step 4: Download the File", h2))
    elements.append(Paragraph(
        "Use any HTTP/3-capable client to download the file from the primary server. "
        "The QUIC migration happens transparently during the download. After completion, "
        "compare the SHA-256 hash of the downloaded file against the <font face='Courier'>x-sha256</font> "
        "response header to verify integrity.",
        body
    ))

    # ══════════════════════════════════════════
    # 5. .TORRENT INTEGRATION
    # ══════════════════════════════════════════
    elements.append(Paragraph("5. .torrent Integration", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "The PoC includes a <font face='Courier'>create_torrent.sh</font> script that generates a "
        ".torrent file with both servers listed as WebSeeds. This demonstrates how the migration "
        "mechanism integrates with the standard BitTorrent ecosystem.",
        body
    ))

    elements.append(Paragraph("url-list Field", h2))
    elements.append(Paragraph(
        "BEP 19 defines the <font face='Courier'>url-list</font> field in .torrent metadata. This "
        "field contains one or more HTTP/HTTPS URLs that serve the same file content. BitTorrent "
        "clients that support WebSeed (including aria2, qBittorrent, Transmission) will use these "
        "URLs as additional download sources.",
        body
    ))

    url_box_data = [
        [Paragraph(
            '<font face="Courier" size="9">'
            'url-list:<br/>'
            '&nbsp;&nbsp;- https://141.217.168.152:4433/test_100mb.bin<br/>'
            '&nbsp;&nbsp;- https://141.217.168.143:4433/test_100mb.bin'
            '</font>',
            body
        )]
    ]
    url_box = Table(url_box_data, colWidths=[6.5*inch])
    url_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
        ("BORDER", (0, 0), (-1, -1), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(url_box)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Client Compatibility", h2))
    elements.append(Paragraph(
        "<b>aria2</b> is the recommended client for testing, as it supports both HTTP/3 (via nghttp3) "
        "and BitTorrent WebSeed. When aria2 connects to the primary WebSeed URL over HTTP/3, the QUIC "
        "server migration occurs transparently at the transport layer. aria2 sees a normal HTTP/3 "
        "download completing successfully.",
        body
    ))

    # ══════════════════════════════════════════
    # 6. TEST SCENARIOS
    # ══════════════════════════════════════════
    elements.append(Paragraph("6. Test Scenarios", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    test_table = make_table(
        ["Test", "Description", "Success Criteria"],
        [
            ["Integrity Test",
             "Download 100MB file through migration, compute SHA-256 of received file",
             "SHA-256 of downloaded file matches x-sha256 header from primary server"],
            ["Failover Test",
             "Primary server fails mid-download, preferred server continues serving",
             "Download completes without error after primary goes offline"],
            ["Latency Comparison",
             "Measure recovery time: QUIC migration vs. client discovering backup WebSeed",
             "Migration recovery is faster than client-side WebSeed failover (no new handshake)"],
            ["Piece Verification",
             "Download via .torrent file, verify all pieces pass BitTorrent hash check",
             "All pieces pass hash verification in the BitTorrent client"],
        ],
        col_widths=[1.3*inch, 2.8*inch, 2.9*inch],
    )
    elements.append(test_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Integrity Test Details", h2))
    elements.append(Paragraph(
        "The integrity test is the core validation of the PoC. The primary server computes "
        "SHA-256 of the file at startup and includes it in the <font face='Courier'>x-sha256</font> "
        "response header. After the download completes (potentially through migration), the client "
        "independently computes SHA-256 of the received file and compares the two values. A match "
        "confirms that the migration did not corrupt any data.",
        body
    ))

    elements.append(Paragraph("Latency Comparison Details", h2))
    elements.append(Paragraph(
        "Without QUIC migration, a WebSeed failover requires the client to: (1) detect the primary "
        "server is down (timeout), (2) resolve the backup WebSeed URL, (3) perform a new TLS/QUIC "
        "handshake, and (4) resume the download from the last known offset. With QUIC migration, "
        "the PATH_CHALLENGE/PATH_RESPONSE exchange completes in a single RTT, and the connection "
        "continues with the same TLS session -- no new handshake required.",
        body
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Expected result: QUIC migration recovery completes in ~1 RTT (~0.5ms on LAN), while "
        "traditional WebSeed failover takes 10-30 seconds (timeout + new handshake).",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 7. BITTORRENT RELEVANCE
    # ══════════════════════════════════════════
    elements.append(Paragraph("7. BitTorrent Relevance", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=8))

    elements.append(Paragraph(
        "This PoC validates QUIC server migration in the context of BitTorrent file distribution. "
        "The following table summarizes the applicability landscape:",
        body
    ))

    relevance_table = make_table(
        ["Scenario", "Transport", "Migration Applicability", "Status"],
        [
            ["WebSeed (BEP 19)", "HTTP/3 (QUIC)",
             "Directly applicable today -- no protocol changes needed",
             "This PoC"],
            ["Seeder-to-Seeder", "BitTorrent (TCP/uTP)",
             "Would require QUIC transport for BitTorrent (does not exist yet)",
             "Future work"],
            ["Tracker Failover", "HTTP/HTTPS",
             "Tracker announces could use HTTP/3, enabling migration",
             "Possible"],
            ["DHT Node Migration", "UDP",
             "DHT uses raw UDP, not QUIC; would need protocol redesign",
             "Not applicable"],
        ],
        col_widths=[1.3*inch, 1.3*inch, 3.0*inch, 1.4*inch],
        highlight_row=1,
    )
    elements.append(relevance_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Why WebSeed is the Right Target", h2))
    for txt in [
        "<b>No protocol changes:</b> WebSeed already uses HTTP, and modern HTTP uses QUIC. "
        "Server migration operates at the QUIC transport layer, invisible to the application.",
        "<b>Real-world deployment:</b> Many CDNs and file hosting services serve as WebSeeds. "
        "QUIC migration enables seamless failover between CDN edge nodes.",
        "<b>Immediate benefit:</b> Unlike seeder-to-seeder migration (which would require a "
        "QUIC-based BitTorrent protocol), WebSeed migration works with existing clients today.",
        "<b>Integrity preserved:</b> BitTorrent's piece hashing and the x-sha256 header provide "
        "independent verification that migration did not corrupt data.",
    ]:
        elements.append(Paragraph(txt, bullet_style, bulletText="\u2022"))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Regular seeder-to-seeder migration would require QUIC as a transport for the "
        "BitTorrent protocol itself. Since BitTorrent currently uses TCP and uTP (a "
        "UDP-based protocol unrelated to QUIC), this is not feasible without significant "
        "protocol changes. WebSeed migration sidesteps this entirely by operating at the "
        "HTTP/3 layer.",
        warning_style
    ))

    # ── Build ──
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

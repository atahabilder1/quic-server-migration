#!/usr/bin/env python3
"""Generate QUIC-Native Load Balancer PoC documentation PDF."""

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

    # ══════════════════════════════════════════
    # 1. OVERVIEW
    # ══════════════════════════════════════════
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

    # ══════════════════════════════════════════
    # 2. ARCHITECTURE
    # ══════════════════════════════════════════
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
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Connection Flow", h2))
    steps = [
        ("1.", "Client connects to <b>frontend</b> (141.217.168.152:4433) via QUIC."),
        ("2.", "Frontend completes the TLS 1.3 handshake with the client (1 RTT)."),
        ("3.", "Frontend selects a backend based on the configured LB policy (round robin or random)."),
        ("4.", "Frontend includes the selected backend's address as <font face='Courier'>preferred_address</font> "
               "in the TLS handshake."),
        ("5.", "Frontend exports ~445 bytes of migration state (TLS secrets, CIDs, packet numbers)."),
        ("6.", "Migration state is sent via TCP to the selected backend's port 9999."),
        ("7.", "Client sends PATH_CHALLENGE to the backend's address."),
        ("8.", "Backend imports the crypto state, decrypts PATH_CHALLENGE, sends PATH_RESPONSE."),
        ("9.", "Client validates PATH_RESPONSE and migrates. All subsequent data flows directly "
               "client <-> backend."),
        ("10.", "Frontend tears down the connection and is ready for the next one."),
    ]
    for num, text in steps:
        elements.append(Paragraph(
            f"<b>{num}</b> {text}", bullet_style
        ))

    # ══════════════════════════════════════════
    # 3. LOAD BALANCING POLICIES
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. Load Balancing Policies", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The frontend supports multiple load balancing policies, selected via the "
        "<font face='Courier'>LB_POLICY</font> environment variable.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Round Robin (default)", h2))
    elements.append(Paragraph(
        "Cycles through backends in order: [0, 1, 0, 1, ...]. This provides perfectly even "
        "distribution across backends and is deterministic. It is the default policy when no "
        "<font face='Courier'>LB_POLICY</font> environment variable is set.",
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
        ["Policy", "Selection", "Distribution", "Use Case"],
        [
            ["Round Robin", "Sequential cycling", "Perfectly even",
             "Default; homogeneous backends"],
            ["Random", "Pseudo-random per conn", "Statistically even",
             "Simple; no state needed"],
        ],
        col_widths=[1.2*inch, 1.5*inch, 1.4*inch, 1.8*inch],
    )
    elements.append(policy_table)

    # ══════════════════════════════════════════
    # 4. IMPLEMENTATION DETAILS
    # ══════════════════════════════════════════
    elements.append(Paragraph("4. Implementation Details", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Binary: lb-frontend", h2))
    elements.append(Paragraph(
        "The load balancer frontend is implemented as the <font face='Courier'>lb-frontend</font> "
        "binary in the migration-test crate. It is a purpose-built binary separate from the "
        "standard primary-server.",
        body
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("Per-Connection Lifecycle", h3))
    elements.append(Paragraph(
        "Creates a <b>new Http3Server instance per connection</b> with the selected backend's "
        "address configured as the <font face='Courier'>preferred_address</font> transport parameter.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "After the TLS handshake completes and migration state is exported, the server instance "
        "is <b>torn down</b>. No per-connection state persists at the frontend.",
        bullet_style, bulletText="\u2022"
    ))
    elements.append(Paragraph(
        "The frontend then loops back to wait for the next incoming connection.",
        bullet_style, bulletText="\u2022"
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("State Transfer", h3))
    elements.append(Paragraph(
        "Migration state (~445 bytes) is sent via a direct TCP connection from the frontend "
        "to the selected backend's port 9999. This is a one-shot send with no response expected. "
        "The state includes TLS secrets, connection IDs, client address, QUIC version, and "
        "packet numbers.",
        body
    ))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Per-Connection Stats", h3))
    elements.append(Paragraph(
        "The frontend prints per-connection statistics including the selected backend, handshake "
        "duration, and state export time. It also maintains and prints a running backend "
        "distribution table showing how many connections have been sent to each backend.",
        body
    ))

    # ══════════════════════════════════════════
    # 5. HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(Paragraph("5. How to Run", h1))
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

    # ══════════════════════════════════════════
    # 6. ADVANTAGES OVER TRADITIONAL LBs
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Advantages Over Traditional Load Balancers", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The following table compares the QUIC migration-based load balancer against two "
        "established approaches: L4 pass-through (Maglev) and L7 reverse proxy (NGINX/Envoy).",
        body
    ))
    elements.append(Spacer(1, 6))

    comparison_table = make_table(
        ["Feature", "Maglev (L4)", "NGINX/Envoy (L7)", "QUIC Migration LB"],
        [
            ["LB in data path", "Always", "Always", "<b>Handshake only</b>"],
            ["TLS termination at LB", "No (pass-through)", "Yes", "Handshake only"],
            ["Sees plaintext", "No", "Yes", "<b>No</b> (after migration)"],
            ["Per-conn state at LB", "Flow table", "Session", "<b>None</b> after migration"],
            ["Bandwidth bottleneck", "LB throughput", "LB throughput", "<b>None</b> (direct path)"],
        ],
        col_widths=[1.4*inch, 1.4*inch, 1.5*inch, 1.6*inch],
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

    # ══════════════════════════════════════════
    # 7. LIMITATIONS
    # ══════════════════════════════════════════
    elements.append(Paragraph("7. Limitations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "One-shot migration: Once a connection migrates to a backend, it cannot be re-balanced. "
        "If the backend becomes overloaded after migration, the LB cannot intervene. This is "
        "inherent to the preferred_address mechanism.",
        warning_style
    ))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph(
        "Client support required: The client must support the <font face='Courier'>"
        "preferred_address</font> transport parameter. Firefox supports this; Chrome/Chromium "
        "does not (as of mid-2026). This limits real-world applicability until broader adoption.",
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

    # ══════════════════════════════════════════
    # 8. TEST PLAN
    # ══════════════════════════════════════════
    elements.append(Paragraph("8. Test Plan", h1))
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

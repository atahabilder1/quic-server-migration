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
        "to serving clients directly. The result is zero user-visible errors during preferred server "
        "outages, with negligible added latency (&lt;0.2ms per connection)."
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
        "1. Overview",
        "    1.1 The Problem",
        "    1.2 The Solution",
        "2. Architecture",
        "    2.1 Testbed",
        "    2.2 Health Check Modes",
        "3. Implementation Details",
        "    3.1 Binaries and Configuration",
        "    3.2 Background Health Thread",
        "    3.3 Conditional preferred_address",
        "    3.4 HTML Status Page",
        "4. How to Run",
        "5. Test Scenarios",
        "6. Expected Results",
        "7. Comparison Table",
    ]
    for item in toc_items:
        indent = 20 if item.startswith("    ") else 0
        elements.append(Paragraph(
            item.strip(),
            ParagraphStyle("TOC", parent=body, fontSize=10, leftIndent=indent, spaceAfter=2)
        ))

    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # SECTION 1: OVERVIEW
    # ══════════════════════════════════════════
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

    # ══════════════════════════════════════════
    # SECTION 2: ARCHITECTURE
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Architecture", h1))

    elements.append(Paragraph("2.1 Testbed", h2))
    elements.append(Paragraph(
        "The PoC uses the same four-machine LAN testbed as our existing migration implementation:",
        body
    ))
    elements.append(make_table(
        ["Role", "Machine", "IP Address", "Function"],
        [
            ["Client", "optiplex7010", "141.217.168.127", "Firefox browser (HTTP/3)"],
            ["Primary Server", "opti7040", "141.217.168.152",
             "Completes TLS handshake, runs health checks"],
            ["Preferred Server", "homeserver2", "141.217.168.143",
             "Imports state, handles PATH_CHALLENGE"],
            ["Redis Server", "Proxmox VM", "141.217.168.200",
             "Heartbeat key storage (Redis mode)"],
        ],
        col_widths=[1.1*inch, 1.1*inch, 1.2*inch, 2.7*inch],
    ))

    elements.append(Paragraph("2.2 Health Check Modes", h2))
    elements.append(Paragraph(
        "The PoC supports two complementary health check strategies, each with different "
        "trade-offs in detection latency, infrastructure requirements, and failure modes:",
        body
    ))

    elements.append(Paragraph("TCP Probe", h3))
    elements.append(Paragraph(
        "The primary server performs a TCP connect to the preferred server's state-transfer "
        "port (9999) with a <b>200ms timeout</b>. This is a per-connection probe: before each "
        "new QUIC handshake, the primary attempts a TCP connection to the preferred server. "
        "If the connection succeeds, the preferred server is considered healthy and "
        "<font name='Courier' size='9'>preferred_address</font> is advertised. If the "
        "connection fails or times out, the primary serves the client directly.",
        body
    ))
    for b in [
        "Per-connection granularity -- every handshake is individually validated",
        "No external infrastructure required (no Redis dependency)",
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

    # ══════════════════════════════════════════
    # SECTION 3: IMPLEMENTATION DETAILS
    # ══════════════════════════════════════════
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
             "preferred_address based on health status."],
            ["health-check-preferred",
             "Preferred server with Redis heartbeat publishing. Sends periodic health "
             "updates to Redis."],
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
            ["REDIS_URL", "redis://141.217.168.200:6379",
             "Redis connection URL for heartbeat mode. Only used when HEALTH_CHECK=redis."],
        ],
        col_widths=[1.3*inch, 2.0*inch, 2.8*inch],
    ))

    elements.append(Paragraph("3.2 Background Health Thread", h2))
    elements.append(Paragraph(
        "The primary server spawns a background thread that re-checks the preferred server's "
        "health every <b>5 seconds</b>. This thread maintains a shared atomic boolean "
        "(<font name='Courier' size='9'>is_healthy</font>) that the main connection-handling "
        "code reads before each handshake. Status changes are logged:",
        body
    ))
    elements.append(Paragraph(
        "[health] preferred server status changed: HEALTHY -> UNHEALTHY<br/>"
        "[health] preferred server status changed: UNHEALTHY -> HEALTHY",
        code_style
    ))
    elements.append(Paragraph(
        "The background thread provides resilience against transient failures and enables "
        "automatic recovery when the preferred server comes back online.",
        body
    ))

    elements.append(Paragraph("3.3 Conditional preferred_address", h2))
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

    elements.append(Paragraph("3.4 HTML Status Page", h2))
    elements.append(Paragraph(
        "The HTTP/3 response page dynamically reflects the migration status. When the "
        "preferred server is healthy, the page shows a green \"HEALTHY\" badge and indicates "
        "that migration is active. When unhealthy, the page shows a red \"UNHEALTHY\" badge "
        "and states that the client is being served directly by the primary.",
        body
    ))

    # ══════════════════════════════════════════
    # SECTION 4: HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. How to Run", h1))

    elements.append(Paragraph(
        "The PoC is launched from the same machines as the existing migration demo. "
        "The preferred server is started first, followed by the primary.",
        body
    ))

    elements.append(Paragraph("Step 1: Start the Preferred Server (homeserver2)", h3))
    elements.append(Paragraph(
        "health-check-preferred 141.217.168.143:4433 9999",
        code_style
    ))
    elements.append(Paragraph(
        "This starts the preferred server listening on port 4433 (QUIC) and port 9999 "
        "(state transfer / TCP probe endpoint). In Redis mode, it also begins publishing "
        "heartbeats to Redis every 1 second.",
        body
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Step 2: Start the Primary Server (opti7040)", h3))
    elements.append(Paragraph(
        "HEALTH_CHECK=tcp health-check-primary 0.0.0.0:4433 \\"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;141.217.168.143:4433 141.217.168.143:9999",
        code_style
    ))
    elements.append(Paragraph(
        "Arguments: (1) local bind address, (2) preferred server QUIC address, "
        "(3) preferred server state-transfer address. The <font name='Courier' size='9'>"
        "HEALTH_CHECK</font> variable selects the probe mode.",
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

    # ══════════════════════════════════════════
    # SECTION 5: TEST SCENARIOS
    # ══════════════════════════════════════════
    elements.append(Paragraph("5. Test Scenarios", h1))

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

    # ══════════════════════════════════════════
    # SECTION 6: EXPECTED RESULTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("6. Expected Results", h1))

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
    ]:
        elements.append(Paragraph(metric, bullet_style, bulletText="\u2022"))

    # ══════════════════════════════════════════
    # SECTION 7: COMPARISON TABLE
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("7. Comparison Table", h1))

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
             "Serves directly",
             "Serves directly"],
            ["Preferred flapping",
             "Random timeouts",
             "Graceful fallback",
             "Graceful fallback"],
            ["Detection latency",
             "N/A (no detection)",
             "<200ms (per-conn probe)",
             "<3s (heartbeat TTL)"],
            ["Added latency",
             "0",
             "~0.1ms (TCP connect)",
             "~0.1ms (Redis GET)"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.6*inch, 1.6*inch],
    ))

    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Trade-off Summary", h2))
    elements.append(make_table(
        ["Aspect", "TCP Probe", "Redis Heartbeat"],
        [
            ["Infrastructure", "None (direct TCP)", "Requires Redis server"],
            ["Granularity", "Per-connection", "Periodic (1s heartbeat)"],
            ["Detection speed", "Immediate (<200ms)", "Delayed (up to 3s TTL)"],
            ["Network topology", "Primary must reach preferred directly",
             "Both must reach Redis; no direct link needed"],
            ["Failure mode", "Probe fails = no migration (safe)",
             "Redis down = key absent = no migration (safe)"],
            ["Best for", "Low-latency, simple setups",
             "Multi-datacenter, indirect routing"],
        ],
        col_widths=[1.3*inch, 2.4*inch, 2.4*inch],
    ))

    elements.append(Spacer(1, 14))
    elements.append(Paragraph(
        "Both modes fail safe: if the health check itself fails (e.g., Redis is unreachable), "
        "the primary defaults to serving directly without migration. This ensures that health "
        "check infrastructure failures never cause client-visible errors.",
        highlight_style
    ))

    # Build
    doc.build(elements)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

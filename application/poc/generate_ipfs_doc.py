#!/usr/bin/env python3
"""Generate IPFS Gateway Migration PoC PDF."""

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
        fontName="Courier", fontSize=8.5, leading=11,
        backColor=GRAY_BG, borderColor=BORDER,
        borderWidth=0.5, borderPadding=6,
        spaceBefore=4, spaceAfter=6,
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
    elements.append(Paragraph("IPFS Gateway Migration", title_style))
    elements.append(Paragraph("Proof of Concept", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Content-Addressed Storage with QUIC Server-Side Migration",
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
        "This document describes a proof-of-concept demonstrating QUIC server-side connection "
        "migration between two IPFS gateways. Both gateways pin the same content (identified by CID), "
        "and the primary gateway advertises the preferred gateway's address during the QUIC handshake. "
        "IPFS's content-addressing model guarantees that content served by either gateway is "
        "cryptographically identical, making IPFS a natural fit for migration scenarios. "
        "The PoC runs on our existing four-machine testbed using modified Neqo binaries."
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
        "IPFS (InterPlanetary File System) is a peer-to-peer content-addressed storage network. "
        "Since Kubo v0.18+ (released 2023), QUIC is the default transport for IPFS peer-to-peer "
        "communication, replacing the older TCP+Noise stack. This makes IPFS nodes natural "
        "candidates for QUIC server-side migration experiments.",
        body
    ))
    elements.append(Paragraph(
        "IPFS gateways bridge the gap between the IPFS network and regular HTTP clients. "
        "They serve IPFS content over standard HTTP/HTTPS (and increasingly HTTP/3) to browsers "
        "and other clients that do not run an IPFS node. Production gateways like ipfs.io and "
        "dweb.link already operate as multi-backend clusters.",
        body
    ))
    elements.append(Paragraph(
        "This PoC demonstrates migration between two IPFS gateways that both pin the same "
        "content, identified by its CID (Content Identifier). The key insight is that IPFS's "
        "content-addressing model provides a built-in integrity guarantee: the same CID always "
        "resolves to the same content, regardless of which gateway serves it.",
        body
    ))

    elements.append(Paragraph(
        "IPFS uses QUIC as its default transport since Kubo v0.18+ (2023). "
        "IPFS gateways serve content over HTTP/3 to regular browsers. "
        "This PoC migrates a client between two IPFS gateways pinning the same CID.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 2. ARCHITECTURE
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Architecture", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The PoC uses our existing four-machine testbed on the same LAN (141.217.168.x):",
        body
    ))

    arch_rows = [
        ["Primary Gateway", "opti7040 (.152)", "Kubo IPFS daemon + Neqo HTTP/3 server (webseed-primary)"],
        ["Preferred Gateway", "homeserver2 (.143)", "Kubo IPFS daemon + preferred-server binary"],
        ["Client", "optiplex7010 (.127)", "Firefox browser or neqo-client"],
        ["Redis (optional)", "Proxmox VM (.200)", "State transfer backend (Redis KV or Pub/Sub)"],
    ]
    elements.append(make_table(
        ["Role", "Machine", "Components"],
        arch_rows,
        col_widths=[1.5*inch, 1.5*inch, 4.0*inch],
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Both the primary and preferred gateways run a local Kubo IPFS node, each pinning "
        "the same test content. The primary gateway fetches content from its local IPFS HTTP "
        "gateway (localhost:8080) and serves it to clients over HTTP/3 via the webseed-primary "
        "binary. During the QUIC handshake, the primary advertises the preferred gateway's "
        "address (.143) using the preferred_address transport parameter.",
        body
    ))

    # ══════════════════════════════════════════
    # 3. HOW IT WORKS
    # ══════════════════════════════════════════
    elements.append(Paragraph("3. How It Works", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    steps = [
        ("Pin content on both nodes:", "Both IPFS nodes pin the same content, identified "
         "by a CID (Content Identifier). The CID is a cryptographic hash of the content."),
        ("Primary fetches from local IPFS:", "The primary server's webseed-primary binary "
         "fetches content from the local IPFS gateway at localhost:8080/ipfs/&lt;CID&gt;."),
        ("Serve via HTTP/3:", "The primary serves the fetched content to the client over "
         "HTTP/3 using the modified Neqo stack."),
        ("Advertise preferred address:", "During the QUIC handshake, the primary includes "
         "preferred_address = 141.217.168.143 in its transport parameters."),
        ("Client migrates:", "The client validates the path to the preferred server "
         "(PATH_CHALLENGE / PATH_RESPONSE) and migrates the connection."),
        ("Content integrity guaranteed:", "Because both gateways pin the same CID, the "
         "content is cryptographically identical. IPFS guarantees this by design -- the CID "
         "IS the hash of the content."),
    ]
    for i, (label, desc) in enumerate(steps, 1):
        elements.append(Paragraph(
            f"<b>{i}. {label}</b> {desc}",
            bullet_style
        ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Content integrity is GUARANTEED by IPFS: the CID is a cryptographic hash of the "
        "content. Same CID = same content, regardless of which gateway serves it.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # 4. IPFS-SPECIFIC ADVANTAGES
    # ══════════════════════════════════════════
    elements.append(Paragraph("4. IPFS-Specific Advantages", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Content Addressing", h2))
    elements.append(Paragraph(
        "In IPFS, content is identified by its CID -- a hash of the content itself. This means "
        "that the same CID always refers to the same content, no matter which node serves it. "
        "Unlike traditional URLs (which identify a location), CIDs identify the data. This is "
        "a fundamental property that makes IPFS uniquely suited for server migration: there is "
        "no question of whether the preferred server will serve different content.",
        body
    ))

    elements.append(Paragraph("Built-in Integrity Verification", h2))
    elements.append(Paragraph(
        "Traditional CDNs require external mechanisms (e.g., SHA-256 checksums, SRI hashes) to "
        "verify content integrity after migration. With IPFS, integrity is intrinsic. The CID "
        "itself is the verification. If the content does not match the CID hash, the IPFS node "
        "will reject it. No additional verification layer is needed.",
        body
    ))

    elements.append(Paragraph("Multiple Providers", h2))
    elements.append(Paragraph(
        "The same CID can be provided (pinned) by many IPFS nodes simultaneously. This is a "
        "natural fit for migration: any node that pins the CID can serve as a migration target. "
        "In production, IPFS gateway clusters like ipfs.io already run multiple backends behind "
        "a load balancer -- migration simply formalizes this at the QUIC layer.",
        body
    ))

    elements.append(Paragraph("Gateway Clusters", h2))
    elements.append(Paragraph(
        "Production IPFS gateways (ipfs.io, dweb.link, cf-ipfs.com) already operate as "
        "multi-server clusters. QUIC server-side migration provides a protocol-native mechanism "
        "for redirecting clients between backend servers without relying on DNS or HTTP redirects. "
        "This reduces latency (no extra round-trip) and is transparent to clients.",
        body
    ))

    # ══════════════════════════════════════════
    # 5. SETUP SCRIPTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("5. Setup Scripts", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "Three shell scripts automate the IPFS environment setup and teardown:",
        body
    ))

    elements.append(Paragraph("setup_ipfs.sh", h2))
    elements.append(Paragraph(
        "Installs Kubo IPFS on both server machines (opti7040 and homeserver2), initializes "
        "IPFS repositories, starts the IPFS daemons, and pins test content on both nodes. "
        "Run from the client machine -- it uses SSH to configure the remote servers.",
        body
    ))
    elements.append(Paragraph(
        "setup_ipfs.sh &mdash; Install Kubo, init repos, pin test content on both servers",
        code_style
    ))

    elements.append(Paragraph("test_ipfs_migration.sh", h2))
    elements.append(Paragraph(
        "Runs the end-to-end migration test. Starts the preferred server on homeserver2, "
        "starts the primary server on opti7040 (with IPFS content), and verifies that a "
        "client can connect, migrate, and receive the correct content (verified by CID).",
        body
    ))
    elements.append(Paragraph(
        "test_ipfs_migration.sh &mdash; End-to-end migration test with IPFS content verification",
        code_style
    ))

    elements.append(Paragraph("teardown_ipfs.sh", h2))
    elements.append(Paragraph(
        "Stops the IPFS daemons on both servers and cleans up temporary files. "
        "Does not uninstall Kubo or remove the IPFS repositories.",
        body
    ))
    elements.append(Paragraph(
        "teardown_ipfs.sh &mdash; Stop IPFS daemons on both servers",
        code_style
    ))

    # ══════════════════════════════════════════
    # 6. HOW TO RUN
    # ══════════════════════════════════════════
    elements.append(Paragraph("6. How to Run", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Step 1: Setup IPFS on both servers", h2))
    elements.append(Paragraph(
        "Run from the client machine (optiplex7010). This installs Kubo, initializes "
        "repositories, and pins test content on both gateway servers.",
        body
    ))
    elements.append(Paragraph("./setup_ipfs.sh", code_style))

    elements.append(Paragraph("Step 2: Start the preferred server", h2))
    elements.append(Paragraph(
        "On homeserver2 (.143), start the preferred server binary. This listens for "
        "incoming migration state on port 9999 and serves HTTP/3 on port 4433.",
        body
    ))
    elements.append(Paragraph(
        "preferred-server 141.217.168.143:4433 9999",
        code_style
    ))

    elements.append(Paragraph("Step 3: Start the primary server", h2))
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

    elements.append(Paragraph("Step 4: Test the migration", h2))
    elements.append(Paragraph(
        "Run the test script from the client machine, or open Firefox and navigate "
        "to https://141.217.168.152:4433/. The page should load via HTTP/3 with "
        "a transparent migration to the preferred server.",
        body
    ))
    elements.append(Paragraph("./test_ipfs_migration.sh", code_style))

    # ══════════════════════════════════════════
    # 7. SCENARIOS
    # ══════════════════════════════════════════
    elements.append(Paragraph("7. Scenarios", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Gateway Load Balancing", h2))
    elements.append(Paragraph(
        "When an IPFS gateway becomes overloaded, it can use QUIC preferred_address to migrate "
        "incoming connections to a less-loaded gateway that pins the same content. Unlike "
        "DNS-based load balancing, this happens mid-connection without requiring a new TLS "
        "handshake, reducing latency and preserving connection state.",
        body
    ))

    elements.append(Paragraph("Gateway Maintenance", h2))
    elements.append(Paragraph(
        "Before shutting down a gateway node for maintenance, existing connections can be "
        "gracefully drained to the preferred server. New connections are directed to the "
        "preferred server immediately via preferred_address, while existing connections "
        "complete their current transfers before migrating. This enables zero-downtime "
        "maintenance of gateway infrastructure.",
        body
    ))

    elements.append(Paragraph("Geographic Optimization", h2))
    elements.append(Paragraph(
        "An IPFS gateway can accept initial connections (via anycast or DNS) and then redirect "
        "clients to a geographically closer gateway. After the initial handshake reveals the "
        "client's IP address, the primary gateway selects the optimal preferred server based on "
        "network topology. The client migrates transparently, improving latency for subsequent "
        "requests without requiring client-side changes.",
        body
    ))

    # ══════════════════════════════════════════
    # 8. LIMITATIONS
    # ══════════════════════════════════════════
    elements.append(Paragraph("8. Limitations", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph("Peer Identity", h2))
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

    elements.append(Paragraph("Bitswap Streams", h2))
    elements.append(Paragraph(
        "Active Bitswap streams (the protocol IPFS uses for peer-to-peer block exchange) "
        "carry complex state including want-lists, block requests, and session information. "
        "This state cannot be easily serialized and transferred between nodes. Migration "
        "of native IPFS peer-to-peer connections would require significant Bitswap protocol "
        "modifications.",
        body
    ))

    elements.append(Paragraph("Gateway-Mode Only", h2))
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

    # ══════════════════════════════════════════
    # 9. COMPARISON: IPFS vs Traditional CDN
    # ══════════════════════════════════════════
    elements.append(Paragraph("9. Comparison: IPFS vs Traditional CDN", h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=MED_BLUE, spaceAfter=10))

    elements.append(Paragraph(
        "The following table compares IPFS gateway migration with traditional CDN approaches "
        "across key dimensions relevant to server-side connection migration:",
        body
    ))

    comparison_rows = [
        ["Content verification", "None (trust server)", "CID hash (cryptographic)"],
        ["Content availability", "Operator-managed", "P2P replication"],
        ["Migration safety", "Data could differ", "Guaranteed identical (same CID)"],
        ["Client changes", "None", "None (HTTP/3 standard)"],
    ]
    elements.append(make_table(
        ["Feature", "Traditional CDN", "IPFS Gateway + Migration"],
        comparison_rows,
        col_widths=[1.8*inch, 2.3*inch, 2.9*inch],
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

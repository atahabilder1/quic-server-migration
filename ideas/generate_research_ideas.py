#!/usr/bin/env python3
"""Generate Research Ideas PDF for Professor - QUIC Server Migration Project."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import date

OUTPUT = "ideas/RESEARCH_IDEAS_PROFESSOR.pdf"

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
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")
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
    bullet = ParagraphStyle(
        "Bullet", parent=body,
        leftIndent=20, bulletIndent=8,
        spaceBefore=2, spaceAfter=2,
    )
    sub_bullet = ParagraphStyle(
        "SubBullet", parent=body,
        leftIndent=40, bulletIndent=26,
        spaceBefore=1, spaceAfter=1, fontSize=9,
    )

    story = []

    # ── Title ──
    story.append(Paragraph("Research Ideas &amp; Exploration Plan", title_style))
    story.append(Paragraph(
        "QUIC Server-Side Migration Project", subtitle_style
    ))
    story.append(Paragraph(
        f"Prepared for Professor | {date.today().strftime('%B %d, %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=MED_BLUE, spaceAfter=12
    ))

    # ── Current Status ──
    story.append(Paragraph("Current Status", h1))
    story.append(Paragraph(
        "We have a <b>fully working cross-machine QUIC server migration</b> implementation "
        "using modified Mozilla Neqo. The system migrates live QUIC connections from a primary "
        "server to a preferred server using the RFC 9000 Preferred Address mechanism. "
        "Verified with Firefox over HTTP/3. Five state transfer backends have been implemented "
        "and tested (TCP Push, HTTP Pull, Redis KV, Redis Pub/Sub, File). "
        "Fatima has completed the Docker-based implementation with network namespace isolation.",
        body
    ))

    story.append(Spacer(1, 8))

    # Status table
    status_data = [
        ["Component", "Status", "Owner"],
        ["Cross-machine migration (Neqo/Rust)", "COMPLETE", "Anik"],
        ["5 state transfer backends", "COMPLETE", "Anik"],
        ["Firefox HTTP/3 verification", "COMPLETE", "Anik"],
        ["Docker / namespace setup", "COMPLETE", "Fatima"],
        ["/tmp folder migration", "IN PROGRESS", "Fatima"],
        ["TCP state transfer (Docker)", "IN PROGRESS", "Fatima"],
    ]
    status_table = Table(status_data, colWidths=[3.5*inch, 1.5*inch, 1.2*inch])
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (1, 1), (1, 3), GREEN_BG),
        ("BACKGROUND", (1, 4), (1, 5), ORANGE_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRAY_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(status_table)

    # ══════════════════════════════════════════════════════════════════
    # TASK 1
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph("Research Task 1: State Transfer Backend Comparison Study", h1))

    # Highlight box
    box_data = [[Paragraph(
        "<b>Goal:</b> Systematic comparison of /tmp (shared filesystem), TCP, QUIC, "
        "and Redis as state transfer mechanisms for migration state, evaluating security, "
        "performance, scalability, and detectability.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box = Table(box_data, colWidths=[6.2*inch])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, MED_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "Different state transfer backends create fundamentally different threat models. "
        "A /tmp-based transfer leaves forensic artifacts on disk. TCP creates observable "
        "side-channel connections. QUIC-over-QUIC nests the state inside encrypted traffic. "
        "Redis introduces a third-party dependency. Understanding these tradeoffs is critical "
        "for both attackers (stealth) and defenders (detection).",
        body
    ))

    story.append(Paragraph("Backends to Compare", h2))

    backends = [
        ("/tmp (Shared Filesystem)", [
            "State written to shared mount between containers or namespaces",
            "Zero network footprint for transfer itself",
            "Leaves disk forensic artifacts (inode timestamps, file contents)",
            "Only viable when servers share a filesystem (same host, NFS, shared volume)",
        ]),
        ("TCP Push", [
            "Primary opens TCP connection to preferred server, pushes state",
            "Observable side-channel: firewall/IDS can see TCP connection between servers",
            "Lowest latency (~1ms LAN), simplest implementation",
            "Already implemented and tested in our Neqo codebase",
        ]),
        ("QUIC as State Transfer Channel", [
            "Use QUIC itself to transfer migration state between servers",
            "State transfer is encrypted and indistinguishable from regular QUIC traffic",
            "Hardest for IDS to detect (encrypted, looks like normal traffic)",
            "Added complexity: servers need their own QUIC connection",
        ]),
        ("Redis (KV and Pub/Sub)", [
            "Centralized state store decouples primary and preferred servers",
            "Scalable to many servers, supports lazy retrieval",
            "Introduces third-party infrastructure dependency",
            "Network observer sees Redis protocol traffic, not migration state directly",
        ]),
    ]

    for name, points in backends:
        story.append(Paragraph(name, h3))
        for p in points:
            story.append(Paragraph(f"\u2022 {p}", bullet))

    story.append(Paragraph("Research Questions", h2))
    questions = [
        "Which backend is most stealthy from a network forensics perspective?",
        "What is the latency overhead of each backend, and does it affect migration success rate?",
        "Can a network observer distinguish migration state transfer from legitimate traffic?",
        "Which backend is most resilient to partial failures (e.g., preferred server not ready)?",
        "How does QUIC-over-QUIC compare to TCP in terms of detectability?",
    ]
    for i, q in enumerate(questions, 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    story.append(Paragraph("Methodology", h2))
    story.append(Paragraph(
        "Run each backend under controlled conditions. Capture traffic with tcpdump. "
        "Measure: (1) transfer latency, (2) migration success rate, (3) network fingerprint "
        "visibility, (4) disk/memory forensic artifacts. Use Wireshark dissectors to analyze "
        "whether an observer can identify the state transfer.",
        body
    ))

    # ══════════════════════════════════════════════════════════════════
    # TASK 2
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph(
        "Research Task 2: Pass-Through Handshake with Secondary Server", h1
    ))

    box2_data = [[Paragraph(
        "<b>Goal:</b> Explore a modified QUIC handshake where the client communicates with "
        "the primary server, but the handshake simultaneously involves the secondary "
        "(preferred) server, so the secondary is cryptographically ready from the start.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box2 = Table(box2_data, colWidths=[6.2*inch])
    box2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, MED_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box2)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "In our current implementation, the primary server completes the full TLS handshake, "
        "then exports ~445 bytes of crypto state to the preferred server. This introduces a "
        "window where the preferred server has no crypto context. A <b>pass-through handshake</b> "
        "model would let the secondary server participate in the handshake from the beginning, "
        "eliminating the state transfer delay and reducing the window of vulnerability.",
        body
    ))

    story.append(Paragraph("Approach", h2))
    story.append(Paragraph(
        "The client sends its Initial packet to the primary server. The primary forwards "
        "the handshake messages to the secondary in real-time. The secondary derives its own "
        "crypto keys from the shared handshake. When migration occurs, the secondary already "
        "has the keys -- no post-handshake state export needed.",
        body
    ))

    story.append(Paragraph("Key Design Options", h2))

    options = [
        ("Option A: Primary as Proxy", [
            "Primary relays all handshake packets to secondary in parallel",
            "Secondary silently derives keys but does not send packets",
            "On migration, secondary is immediately ready",
            "Advantage: Client is completely unaware, zero protocol changes",
            "Challenge: Primary must forward packets with minimal latency",
        ]),
        ("Option B: Shared TLS Session", [
            "Primary and secondary share the same TLS master secret from the start",
            "Both servers can independently derive traffic keys",
            "Requires pre-shared key material or coordinated key generation",
            "Advantage: True zero-delay migration",
            "Challenge: Sharing master secrets weakens forward secrecy guarantees",
        ]),
        ("Option C: Delegated Credentials (RFC 9345)", [
            "Primary issues a delegated credential to the secondary",
            "Secondary can authenticate as the primary to the client",
            "Standard-compliant approach",
            "Advantage: No custom crypto, works with existing TLS stacks",
            "Challenge: Delegated credentials authenticate identity, not session state",
        ]),
    ]
    for name, points in options:
        story.append(Paragraph(name, h3))
        for p in points:
            story.append(Paragraph(f"\u2022 {p}", bullet))

    story.append(Paragraph("Research Questions", h2))
    rqs = [
        "Can we achieve zero-delay migration by involving the secondary in the handshake?",
        "What are the security implications of sharing handshake state in real-time?",
        "Does pass-through handshake make the attack more or less detectable?",
        "How does this compare to our current post-handshake state export approach?",
    ]
    for i, q in enumerate(rqs, 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # TASK 3
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Research Task 3: Multi-Hop Chained Migration", h1))

    box3_data = [[Paragraph(
        "<b>Goal:</b> Investigate whether a QUIC connection can be migrated through a chain "
        "of servers (A &rarr; B &rarr; C &rarr; ...), creating a multi-hop exfiltration path "
        "analogous to Tor-style onion routing.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box3 = Table(box3_data, colWidths=[6.2*inch])
    box3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PURPLE_BG),
        ("BOX", (0, 0), (-1, -1), 1, HexColor(PURPLE.hexval())),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box3)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "Our current implementation migrates from one server to another (single hop). "
        "But the QUIC Preferred Address mechanism does not inherently prevent the preferred "
        "server from issuing its own preferred address, creating a chain. This raises the "
        "question: can an attacker bounce a connection across multiple servers to obscure "
        "the final destination?",
        body
    ))

    story.append(Paragraph("Research Questions", h2))
    rqs3 = [
        "Does RFC 9000 allow or prevent chained preferred address migrations?",
        "How many hops can a connection survive before the client times out or gives up?",
        "Does each hop increase detection difficulty, or does the pattern become more visible?",
        "Can chained migration be used for geographic evasion (cross jurisdictional boundaries)?",
    ]
    for i, q in enumerate(rqs3, 1):
        story.append(Paragraph(f"<b>RQ{i}:</b> {q}", bullet))

    story.append(Paragraph("Approach", h2))
    story.append(Paragraph(
        "Modify the preferred server to itself advertise a new preferred address upon receiving "
        "the migrated connection. Each server in the chain exports state to the next. "
        "Test with 3-4 servers on the LAN, measure cumulative latency and client behavior.",
        body
    ))

    # ══════════════════════════════════════════════════════════════════
    # TASK 4
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Research Task 4: Network Forensics &amp; Indistinguishability Analysis", h1
    ))

    box4_data = [[Paragraph(
        "<b>Goal:</b> Rigorously analyze whether a malicious server migration (QUIC-Exfil) "
        "is distinguishable from a legitimate preferred address migration at the network layer.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box4 = Table(box4_data, colWidths=[6.2*inch])
    box4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), RED_BG),
        ("BOX", (0, 0), (-1, -1), 1, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box4)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "The QUIC-Exfil paper showed ML classifiers achieve only 0-47% F1-score at detecting "
        "malicious migrations. We now have real packet captures from physical hardware. "
        "This task goes deeper: analyze exactly what a network observer can and cannot see, "
        "and formally characterize the indistinguishability properties.",
        body
    ))

    story.append(Paragraph("Analysis Dimensions", h2))
    dims = [
        ("Packet-level analysis", "Compare packet sizes, timing, and ordering between "
         "legitimate and malicious migrations. Are there statistical differences?"),
        ("Side-channel visibility", "Does the state transfer (TCP/Redis/QUIC) between servers "
         "create a detectable side-channel? Characterize per backend."),
        ("TLS fingerprinting", "Can the preferred server's TLS behavior be distinguished from "
         "the primary's? (e.g., different cipher negotiation, certificate handling)"),
        ("Timing correlation", "Can an observer correlate the timing of the state transfer "
         "with the PATH_CHALLENGE/RESPONSE exchange?"),
    ]
    for name, desc in dims:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", bullet))

    story.append(Paragraph("Deliverables", h2))
    story.append(Paragraph(
        "Packet capture analysis report. Feature comparison table (legitimate vs malicious). "
        "Statistical tests on timing distributions. Recommendations for what defenders should "
        "monitor (if anything can help).",
        body
    ))

    # ══════════════════════════════════════════════════════════════════
    # TASK 5
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph(
        "Research Task 5: Defense Mechanisms &amp; Protocol-Level Mitigations", h1
    ))

    box5_data = [[Paragraph(
        "<b>Goal:</b> Propose and evaluate concrete defenses against QUIC-Exfil, "
        "ranging from RFC amendments to middlebox strategies to client-side protections.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box5 = Table(box5_data, colWidths=[6.2*inch])
    box5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN_BG),
        ("BOX", (0, 0), (-1, -1), 1, HexColor(GREEN.hexval())),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box5)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "Demonstrating the attack is necessary but not sufficient for a strong paper. "
        "Proposing defenses shows the research is constructive, not just offensive. "
        "This positions the work as responsible disclosure with actionable recommendations.",
        body
    ))

    story.append(Paragraph("Proposed Defenses to Evaluate", h2))

    defenses = [
        ("Preferred Address Subnet Pinning", [
            "Restrict preferred_address to the same subnet or AS as the primary",
            "Client or middlebox rejects migration to a different network",
            "Breaks legitimate CDN use cases but prevents cross-network exfiltration",
        ]),
        ("Certificate Binding", [
            "Require the preferred server to present the same certificate as the primary",
            "Prevents migration to a server with a different identity",
            "Already partially implied by QUIC spec, but not enforced in practice",
        ]),
        ("Client-Side Migration Policy", [
            "Browser setting to disable or restrict preferred_address migrations",
            "User/admin can whitelist trusted migration targets",
            "Analogous to HSTS pinning for migration destinations",
        ]),
        ("Middlebox PATH_CHALLENGE Interception", [
            "Firewall inspects PATH_CHALLENGE/RESPONSE for anomalous patterns",
            "Challenge: QUIC encrypts these frames, so deep inspection is limited",
            "Could use timing heuristics instead of payload inspection",
        ]),
        ("RFC Amendment: Migration Attestation", [
            "Propose a new transport parameter: migration_attestation",
            "Primary server provides a signed proof that preferred server is authorized",
            "Client can verify the attestation before migrating",
            "Requires PKI infrastructure but provides strong guarantees",
        ]),
    ]
    for name, points in defenses:
        story.append(Paragraph(name, h3))
        for p in points:
            story.append(Paragraph(f"\u2022 {p}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # TASK 6
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Research Task 6: Cross-Network (WAN) Migration Feasibility", h1
    ))

    box6_data = [[Paragraph(
        "<b>Goal:</b> Test whether QUIC server migration works across different subnets, "
        "WANs, or even across the public Internet, fundamentally changing the threat model.",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box6 = Table(box6_data, colWidths=[6.2*inch])
    box6.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE_BG),
        ("BOX", (0, 0), (-1, -1), 1, HexColor(ORANGE.hexval())),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box6)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Motivation", h2))
    story.append(Paragraph(
        "Our current testbed is on a single LAN (141.217.168.x). The QUIC-Exfil threat model "
        "becomes significantly more dangerous if migration works across the Internet, because "
        "data could be exfiltrated to a server in a different country or jurisdiction. "
        "Testing WAN migration also reveals NAT traversal and firewall challenges.",
        body
    ))

    story.append(Paragraph("Experiments", h2))
    experiments = [
        "Same campus, different subnets (different VLANs)",
        "Cross-campus or cross-institution (VPN or public IP)",
        "Cloud-to-cloud (e.g., AWS us-east to AWS eu-west)",
        "Measure: added latency, NAT/firewall interference, PATH_CHALLENGE timeout rates",
    ]
    for e in experiments:
        story.append(Paragraph(f"\u2022 {e}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # TASK 7
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Research Task 7: Exfiltration Capacity &amp; Covert Channel Analysis", h1
    ))

    box7_data = [[Paragraph(
        "<b>Goal:</b> Quantify the practical bandwidth of the QUIC-Exfil covert channel. "
        "How much data can be exfiltrated per migration, and can repeated migrations "
        "create a sustained covert channel?",
        ParagraphStyle("BoxText", parent=body, textColor=DARK_BLUE)
    )]]
    box7 = Table(box7_data, colWidths=[6.2*inch])
    box7.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PURPLE_BG),
        ("BOX", (0, 0), (-1, -1), 1, HexColor(PURPLE.hexval())),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box7)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Questions", h2))
    cap_qs = [
        "Migration state is ~445 bytes. Can additional data be embedded in unused fields?",
        "Can the preferred server serve different content than the primary intended?",
        "Can repeated short-lived connections each trigger a migration, creating throughput?",
        "What is the theoretical maximum bandwidth of this covert channel?",
        "How does this compare to other known covert channels (DNS tunneling, ICMP, etc.)?",
    ]
    for q in cap_qs:
        story.append(Paragraph(f"\u2022 {q}", bullet))

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY TABLE
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("Summary: All Research Tasks at a Glance", h1))

    summary_data = [
        ["#", "Task", "Type", "Priority", "Effort"],
        ["1", "State Transfer Comparison\n(tmp, TCP, QUIC, Redis)", "Engineering +\nAnalysis", "HIGH", "Medium"],
        ["2", "Pass-Through Handshake\nwith Secondary", "Protocol\nDesign", "HIGH", "High"],
        ["3", "Multi-Hop Chained\nMigration", "Exploration", "MEDIUM", "Medium"],
        ["4", "Network Forensics &\nIndistinguishability", "Security\nAnalysis", "HIGH", "Medium"],
        ["5", "Defense Mechanisms &\nMitigations", "Defense", "HIGH", "Medium"],
        ["6", "Cross-Network (WAN)\nMigration", "Feasibility\nStudy", "MEDIUM", "Low-Med"],
        ["7", "Exfiltration Capacity &\nCovert Channel", "Threat\nAnalysis", "MEDIUM", "Low"],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[0.4*inch, 2.2*inch, 1.1*inch, 0.9*inch, 0.9*inch],
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRAY_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        # Highlight HIGH priority
        ("BACKGROUND", (3, 1), (3, 2), HexColor("#fed7d7")),
        ("BACKGROUND", (3, 4), (3, 5), HexColor("#fed7d7")),
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 16))

    # Recommendation
    story.append(Paragraph("Recommended Focus for Paper", h1))
    story.append(Paragraph(
        "For the strongest research contribution, we recommend combining <b>Tasks 1, 2, 4, "
        "and 5</b> into a cohesive paper narrative:",
        body
    ))

    narrative = [
        "<b>Attack implementation</b> (already done) -- prove QUIC-Exfil is feasible on real hardware",
        "<b>Task 1</b> -- show attackers have multiple backend choices with different stealth properties",
        "<b>Task 2</b> -- demonstrate an advanced variant (pass-through handshake) that eliminates state transfer delay",
        "<b>Task 4</b> -- prove the attack is indistinguishable from legitimate migration",
        "<b>Task 5</b> -- propose concrete, actionable defenses (responsible disclosure angle)",
    ]
    for n in narrative:
        story.append(Paragraph(f"\u2022 {n}", bullet))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Tasks 3, 6, and 7 are valuable explorations that can strengthen the paper as "
        "additional results or serve as future work directions.",
        body_italic
    ))

    # Build
    doc.build(story)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

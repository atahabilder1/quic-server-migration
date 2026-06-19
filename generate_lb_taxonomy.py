#!/usr/bin/env python3
"""Generate Load Balancing Taxonomy PDF for QUIC research project."""

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

OUTPUT = "LOAD_BALANCING_TAXONOMY.pdf"

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
    ref_style = ParagraphStyle(
        "Ref", parent=body,
        fontSize=9, leading=12,
        leftIndent=14, spaceAfter=3,
        textColor=HexColor("#4a5568"),
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

    elements = []

    # ── Title Page ──
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("A Taxonomy of Load Balancing", title_style))
    elements.append(Paragraph("in Data Center Networks", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "With Implications for QUIC Server-Side Connection Migration",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Research Reference Document &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.8*inch))

    # Abstract box
    abstract_text = (
        "This document presents a comprehensive taxonomy of load balancing techniques used in "
        "modern data center networks. We classify approaches along six orthogonal dimensions: "
        "network layer, decision location, statefulness, algorithm, scope, and timing. For each "
        "category, we identify seminal papers from top systems conferences (SIGCOMM, NSDI, OSDI) "
        "and recent advances. We conclude by positioning QUIC server-side connection migration as "
        "a novel category in this taxonomy: <b>reactive, mid-connection, server-initiated load balancing</b> "
        "that requires no specialized hardware or client cooperation."
    )
    abstract_tbl = Table(
        [[Paragraph(abstract_text, ParagraphStyle(
            "Abstract", parent=body, fontSize=9.5, leading=13,
            textColor=DARK_GRAY,
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
    # SECTION 1: INTRODUCTION
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. Introduction", h1))
    elements.append(Paragraph(
        "Load balancing is fundamental to data center operations. As global data center traffic "
        "approaches 20.6 ZB/year (Cisco, 2025), distributing workloads efficiently across servers, "
        "paths, and regions has become critical for performance, availability, and cost. "
        "The rise of QUIC (RFC 9000) as the transport for HTTP/3 introduces both challenges and "
        "opportunities: QUIC's encrypted headers and connection migration break traditional L4 "
        "load balancing assumptions, but its <b>preferred_address</b> mechanism enables an entirely "
        "new form of server-initiated, mid-connection load balancing.",
        body
    ))

    # ══════════════════════════════════════════
    # SECTION 2: TAXONOMY
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Taxonomy of Load Balancing", h1))
    elements.append(Paragraph(
        "We classify load balancing along six orthogonal dimensions. A real-world deployment "
        "typically combines choices from multiple dimensions (e.g., Google uses L3 Anycast + "
        "L4 Maglev + L7 Envoy in a multi-tier architecture).",
        body
    ))

    # ── Dimension 1: Network Layer ──
    elements.append(Paragraph("2.1 Dimension 1: By Network Layer", h2))
    elements.append(Paragraph(
        "The OSI layer at which the load balancer inspects packets determines what information "
        "is available for routing decisions and how much overhead is incurred.",
        body
    ))
    elements.append(make_table(
        ["Layer", "What It Inspects", "Example Systems", "Key Paper"],
        [
            ["L2 (Link)", "MAC addresses, VLANs", "Link Aggregation (LACP), bonding", "IEEE 802.3ad"],
            ["L3 (Network)", "IP addresses only", "ECMP, Anycast, BGP-based", "RFC 2992 (ECMP)"],
            ["L4 (Transport)", "IP + port + protocol (TCP/UDP)", "Maglev, Beamer, SilkRoad, IPVS, Katran",
             "Maglev (NSDI '16)"],
            ["L7 (Application)", "HTTP headers, URLs, cookies, gRPC", "NGINX, HAProxy, Envoy, AWS ALB",
             "Envoy (2016)"],
            ["<b>L4.5 (QUIC-aware)</b>", "<b>QUIC Connection IDs</b>",
             "<b>QUIC-LB, QUIC server migration</b>", "<b>QUIC-LB Draft (2025)</b>"],
        ],
        col_widths=[1.0*inch, 1.6*inch, 2.0*inch, 1.5*inch],
        highlight_row=5,
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<i>Note: QUIC blurs the L4/L7 boundary. Because QUIC encrypts transport headers, "
        "traditional L4 LBs cannot read ports after the handshake. QUIC-LB solves this by encoding "
        "routing info in Connection IDs. Our server migration approach goes further by moving the "
        "connection itself.</i>",
        body_italic
    ))

    # ── Dimension 2: Decision Location ──
    elements.append(Paragraph("2.2 Dimension 2: By Decision Location", h2))
    elements.append(Paragraph(
        "Where the load balancing decision is made affects latency, scalability, and failure modes.",
        body
    ))
    elements.append(make_table(
        ["Location", "Description", "Examples", "Trade-off"],
        [
            ["DNS-based", "Resolve domain name to different server IPs",
             "Route53, Cloudflare DNS, GSLB", "Simple but coarse-grained; TTL caching delays reaction"],
            ["Anycast", "Same IP advertised from multiple locations; BGP routing picks closest",
             "CDNs, Google VIPs", "No per-connection state; limited to geographic proximity"],
            ["Network / Fabric", "Switches and routers distribute across paths",
             "ECMP, CONGA, PLB", "Low latency; limited to path selection, not server selection"],
            ["Dedicated LB (HW)", "Dedicated appliance in front of backend pool",
             "F5 BIG-IP, Citrix ADC", "High throughput; expensive, single point of failure"],
            ["Dedicated LB (SW)", "Software process in front of backend pool",
             "Maglev, HAProxy, NGINX, Envoy", "Flexible; adds latency, needs scaling itself"],
            ["In-Switch LB", "LB logic programmed into switching ASICs (P4)",
             "SilkRoad, Cheetah (HW mode)", "Line-rate; limited memory for state"],
            ["<b>Server-Side (Self-Balancing)</b>",
             "<b>Server itself decides to shed load by migrating connections</b>",
             "<b>QUIC preferred_address migration</b>",
             "<b>No LB bottleneck; requires protocol support</b>"],
        ],
        col_widths=[1.2*inch, 1.7*inch, 1.5*inch, 1.7*inch],
        highlight_row=7,
    ))

    # ── Dimension 3: Statefulness ──
    elements.append(Paragraph("2.3 Dimension 3: By State Management", h2))
    elements.append(make_table(
        ["Type", "Description", "Examples", "Resilience"],
        [
            ["Stateless", "No per-connection memory in the LB; every packet routed independently",
             "ECMP, Beamer, Cheetah (stateless)", "Survives LB failures; may break conn affinity"],
            ["Stateful", "LB tracks each connection in a table",
             "Maglev, SilkRoad, iptables CONNTRACK", "Guarantees PCC; state = vulnerability (SYN floods)"],
            ["Soft-State", "State exists but can be reconstructed from hashing",
             "Consistent hashing (Maglev ring)", "Graceful degradation; small % of conn disrupted"],
            ["<b>State-Transferred</b>",
             "<b>Connection state explicitly moved between servers</b>",
             "<b>QUIC server migration (445 bytes)</b>",
             "<b>State lives on servers, not LB; LB can be stateless</b>"],
        ],
        col_widths=[1.2*inch, 2.0*inch, 1.7*inch, 1.6*inch],
        highlight_row=4,
    ))

    # ── Dimension 4: Algorithm ──
    elements.append(Paragraph("2.4 Dimension 4: By Algorithm / Policy", h2))
    elements.append(make_table(
        ["Algorithm", "How It Selects", "Best For", "Complexity"],
        [
            ["Round-Robin", "Next server in cyclic order", "Equal-capacity servers, stateless", "O(1)"],
            ["Weighted Round-Robin", "Proportional to assigned weights", "Heterogeneous server capacity", "O(1)"],
            ["Least Connections", "Server with fewest active connections", "Variable request durations", "O(log n)"],
            ["Least Response Time", "Server responding fastest", "Latency-sensitive applications", "O(n) probing"],
            ["Random", "Uniformly random selection", "Simple, zero-state", "O(1)"],
            ["Power of 2 Choices", "Pick 2 random servers, choose less loaded",
             "Near-optimal with minimal overhead", "O(1)"],
            ["Consistent Hashing", "hash(key) maps to server ring; minimal disruption on changes",
             "Caches, session affinity", "O(log n)"],
            ["Congestion-Aware", "Real-time load/congestion signals steer traffic",
             "Fabric-level path selection", "O(1) per switch"],
            ["Resource-Aware", "CPU / memory / GPU utilization metrics",
             "Heterogeneous workloads (ML, etc.)", "O(n) monitoring"],
        ],
        col_widths=[1.3*inch, 1.8*inch, 1.7*inch, 1.0*inch],
    ))

    elements.append(PageBreak())

    # ── Dimension 5: Scope ──
    elements.append(Paragraph("2.5 Dimension 5: By Scope", h2))
    elements.append(make_table(
        ["Scope", "Description", "Examples", "Typical Mechanism"],
        [
            ["Global (GSLB)", "Across data centers and geographic regions",
             "DNS-based GSLB, Anycast", "DNS, BGP"],
            ["Data Center", "Within a single data center",
             "Maglev, Beamer, fabric ECMP", "L4 LB, ECMP"],
            ["Intra-Rack", "Within a single rack",
             "Top-of-Rack switch ECMP", "Switch hashing"],
            ["Per-Service (Mesh)", "Between microservice instances",
             "Envoy, Istio, Linkerd", "Sidecar proxy, L7"],
            ["<b>Per-Connection</b>", "<b>Individual connection migrated to a different server</b>",
             "<b>QUIC server migration</b>", "<b>preferred_address + state transfer</b>"],
        ],
        col_widths=[1.2*inch, 2.0*inch, 1.7*inch, 1.6*inch],
        highlight_row=5,
    ))

    # ── Dimension 6: Timing ──
    elements.append(Paragraph("2.6 Dimension 6: By Timing", h2))
    elements.append(Paragraph(
        "This is the most important dimension for understanding why QUIC server migration is novel. "
        "Almost all existing load balancing happens <b>before</b> or <b>at</b> connection establishment. "
        "Once a connection is pinned to a backend, it stays there until it ends.",
        body
    ))
    elements.append(make_table(
        ["Timing", "When Decision Occurs", "Examples", "Can Change Server?"],
        [
            ["Pre-Connection", "Before any packets are sent (DNS resolution time)",
             "DNS-based GSLB, Anycast routing", "N/A (no connection yet)"],
            ["At Connection", "At SYN / QUIC Initial packet time",
             "All L4 LBs (Maglev, Beamer, SilkRoad, Katran)", "No (pinned after decision)"],
            ["Flowlet-Level", "During connection, at flowlet boundaries",
             "CONGA, PLB", "Changes <i>path</i>, not <i>server</i>"],
            ["<b>Mid-Connection (Reactive)</b>",
             "<b>After connection is established, server-initiated</b>",
             "<b>QUIC preferred_address migration</b>",
             "<b>Yes -- transparently moves to different server</b>"],
        ],
        col_widths=[1.2*inch, 2.0*inch, 1.8*inch, 1.5*inch],
        highlight_row=4,
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Key insight: QUIC server-side migration is the only mechanism in this taxonomy that can "
        "move an established, encrypted connection to a completely different physical server without "
        "client awareness and without any specialized load balancing infrastructure.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # SECTION 3: Key Systems
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Key Systems and Papers", h1))
    elements.append(Paragraph(
        "Below we summarize the most influential load balancing systems from top venues, "
        "organized by their approach.",
        body
    ))

    # ── 3.1 L4 Software LB ──
    elements.append(Paragraph("3.1 Layer-4 Software Load Balancers", h2))

    elements.append(Paragraph("Maglev (Google) -- NSDI 2016", h3))
    elements.append(Paragraph(
        "Google's production L4 load balancer. Uses consistent hashing with a novel \"Maglev hash\" "
        "that provides minimal disruption and uniform load distribution. Deployed on commodity Linux "
        "servers behind ECMP routers. Each Maglev machine can independently route any packet. "
        "Per-connection state via connection tracking table provides affinity.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Eisenbud et al., "Maglev: A Fast and Reliable Software Network Load Balancer," '
        'NSDI 2016. <font color="#2b6cb0">https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud</font>',
        ref_style
    ))

    elements.append(Paragraph("Beamer -- NSDI 2018", h3))
    elements.append(Paragraph(
        "Eliminates per-connection state from the LB mux entirely. When a backend pool changes, "
        "Beamer \"daisy-chains\" old backends to forward residual packets to new backends. Achieves "
        "33M pps (2x Maglev) and is immune to SYN flood state exhaustion attacks.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Olteanu et al., "Stateless Datacenter Load-balancing with Beamer," '
        'NSDI 2018. <font color="#2b6cb0">https://www.usenix.org/conference/nsdi18/presentation/olteanu</font>',
        ref_style
    ))

    elements.append(Paragraph("Katran (Meta) -- Open Source, 2018", h3))
    elements.append(Paragraph(
        "Meta's production L4 LB using XDP/eBPF for kernel-bypass packet processing. Handles "
        "QUIC connection IDs for routing. Open-source. Runs on commodity hardware at line rate.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Facebook Engineering, "Open-sourcing Katran." '
        '<font color="#2b6cb0">https://engineering.fb.com/2018/05/22/open-source/open-sourcing-katran-a-scalable-network-load-balancer/</font>',
        ref_style
    ))

    # ── 3.2 In-Switch LB ──
    elements.append(Paragraph("3.2 In-Switch / Hardware Load Balancers", h2))

    elements.append(Paragraph("SilkRoad -- SIGCOMM 2017", h3))
    elements.append(Paragraph(
        "Implements stateful L4 LB in a switching ASIC using 400 lines of P4. Supports 10M "
        "concurrent connections at line rate. Replaces hundreds of software LB servers with a "
        "single switch, reducing cost by 100x.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Miao et al., "SilkRoad: Making Stateful Layer-4 Load Balancing Fast and Cheap '
        'Using Switching ASICs," SIGCOMM 2017. <font color="#2b6cb0">https://dl.acm.org/doi/10.1145/3098822.3098824</font>',
        ref_style
    ))

    elements.append(Paragraph("Cheetah -- NSDI 2020", h3))
    elements.append(Paragraph(
        "Encodes routing info in a cookie embedded in transport headers (stateless mode) or uses "
        "hash tables (stateful mode). Implemented on both software and Tofino ASIC. Guarantees "
        "per-connection consistency with 2-3x better flow completion times.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Barbette et al., "A High-Speed Load-Balancer Design with Guaranteed Per-Connection-Consistency," '
        'NSDI 2020. <font color="#2b6cb0">https://www.usenix.org/system/files/nsdi20-paper-barbette.pdf</font>',
        ref_style
    ))

    # ── 3.3 Fabric-Level ──
    elements.append(Paragraph("3.3 Fabric-Level / Congestion-Aware", h2))

    elements.append(Paragraph("CONGA -- SIGCOMM 2014", h3))
    elements.append(Paragraph(
        "Distributed congestion-aware LB implemented in custom ASICs (Cisco). Splits flows into "
        "flowlets and routes them based on real-time congestion feedback from remote leaf switches. "
        "5x better FCT than ECMP under asymmetry.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Alizadeh et al., "CONGA: Distributed Congestion-Aware Load Balancing for Datacenters," '
        'SIGCOMM 2014. <font color="#2b6cb0">https://dl.acm.org/doi/10.1145/2740070.2626316</font>',
        ref_style
    ))

    elements.append(Paragraph("PLB (Google) -- SIGCOMM 2022", h3))
    elements.append(Paragraph(
        "Google's production path-level LB. Much simpler than CONGA: uses ECN congestion signals "
        "to reroute flowlets away from congested paths. Deployed at scale across Google's data centers. "
        "Demonstrates that simple signals suffice for production environments.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> PLB: Congestion Signals are Enough, '
        'SIGCOMM 2022. <font color="#2b6cb0">https://dl.acm.org/doi/10.1145/3544216.3544226</font>',
        ref_style
    ))

    # ── 3.4 QUIC-Specific ──
    elements.append(Paragraph("3.4 QUIC-Specific Load Balancing", h2))

    elements.append(Paragraph("QUIC-LB -- IETF Draft (Active, 2025)", h3))
    elements.append(Paragraph(
        "The IETF's standardized approach to QUIC load balancing. Servers encode their server ID "
        "into QUIC Connection IDs using a shared key with the LB. The LB decodes the CID to route "
        "packets to the correct backend -- even after client address migration. Does NOT support "
        "moving a connection to a different server; only routing to the original server.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Duke et al., "QUIC-LB: Generating Routable QUIC Connection IDs," '
        'IETF Draft v21. <font color="#2b6cb0">https://datatracker.ietf.org/doc/draft-ietf-quic-load-balancers/</font>',
        ref_style
    ))

    elements.append(Paragraph("QASM: QUIC-Aware Stateful Middleboxes -- 2025", h3))
    elements.append(Paragraph(
        "A framework for building middleboxes (including LBs) that understand QUIC's connection "
        "migration. Addresses the challenge that a single connection must remain mapped to a single "
        "server across CID changes.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> "QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes," '
        '2025. <font color="#2b6cb0">https://arxiv.org/pdf/2602.03354</font>',
        ref_style
    ))

    elements.append(Paragraph("Analysis of QUIC Connection Migration in the Wild -- 2025", h3))
    elements.append(Paragraph(
        "Empirical study of QUIC connection migration support across the Internet. Reveals that "
        "despite rapid QUIC deployment, many popular destinations do not support connection migration.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> "An Analysis of QUIC Connection Migration in the Wild," '
        'ACM SIGCOMM CCR 2025. <font color="#2b6cb0">https://dl.acm.org/doi/10.1145/3727063.3727066</font>',
        ref_style
    ))

    elements.append(Paragraph("Server-Side QUIC Migration for Edge Microservices -- 2022", h3))
    elements.append(Paragraph(
        "Proposes extending QUIC for server-side migration when containers are migrated between "
        "edge nodes. Three strategies (orchestrator-assisted, peer-to-peer, DNS-based). Evaluated "
        "against TCP+DNS and MPTCP baselines. <b>Most directly related to our work</b>, but limited "
        "to simulation -- our implementation demonstrates real cross-machine migration with Firefox.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Puliafito et al., "Server-side QUIC connection migration to support microservice '
        'deployment at the edge," Pervasive and Mobile Computing, 2022. '
        '<font color="#2b6cb0">https://www.sciencedirect.com/science/article/abs/pii/S157411922200030X</font>',
        ref_style
    ))

    elements.append(Paragraph("QUIC-Exfil: Security Implications -- ASIA CCS 2025", h3))
    elements.append(Paragraph(
        "Demonstrates that QUIC's preferred_address mechanism can be exploited for data exfiltration. "
        "Firewalls cannot distinguish malicious migrations from legitimate ones. Five ML classifiers "
        "failed to detect the attack (0-47% F1-score). Our implementation provides the first "
        "cross-machine proof of this attack's feasibility.",
        body
    ))
    elements.append(Paragraph(
        '<bullet>&bull;</bullet> Grubl et al., "QUIC-Exfil: Exploiting QUIC\'s Server Preferred Address Feature," '
        'ASIA CCS 2025. <font color="#2b6cb0">https://arxiv.org/pdf/2505.05292</font>',
        ref_style
    ))

    # ══════════════════════════════════════════
    # SECTION 4: Positioning
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. Positioning QUIC Server Migration in the Taxonomy", h1))
    elements.append(Paragraph(
        "The following table compares our QUIC server-side migration approach against the major "
        "load balancing systems across the six taxonomy dimensions.",
        body
    ))

    elements.append(make_table(
        ["System", "Layer", "Location", "State", "Timing", "Can Move Server?"],
        [
            ["Maglev", "L4", "SW LB", "Stateful", "At connection", "No"],
            ["Beamer", "L4", "SW LB", "Stateless", "At connection", "No"],
            ["SilkRoad", "L4", "In-switch", "Stateful", "At connection", "No"],
            ["Cheetah", "L4", "In-switch/SW", "Both", "At connection", "No"],
            ["CONGA", "L3", "Fabric", "Stateless", "Flowlet-level", "No (path only)"],
            ["PLB", "L3", "Fabric", "Stateless", "Flowlet-level", "No (path only)"],
            ["QUIC-LB", "L4.5", "SW LB", "Stateless", "At connection", "No (routes to original)"],
            ["Envoy/Istio", "L7", "Sidecar", "Stateful", "At request", "Per-request only"],
            ["<b>QUIC Migration</b>", "<b>L4.5</b>", "<b>Server</b>",
             "<b>State-transferred</b>", "<b>Mid-connection</b>", "<b>Yes</b>"],
        ],
        col_widths=[1.1*inch, 0.6*inch, 0.85*inch, 1.0*inch, 1.1*inch, 1.35*inch],
        highlight_row=9,
    ))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("4.1 Data Center Use Cases Enabled by Mid-Connection Migration", h2))

    use_cases = [
        ("<b>Zero-Downtime Server Drain:</b> A server scheduled for maintenance advertises "
         "preferred_address for new handshakes, migrating active connections to healthy backends. "
         "No connection drops, no client-visible errors."),
        ("<b>Reactive Load Shedding:</b> Unlike traditional LBs that pin connections at establishment, "
         "an overloaded server can shed load mid-connection. A load controller writes target addresses "
         "to Redis; servers pick up migration targets dynamically."),
        ("<b>Geographic Re-routing:</b> Anycast DNS routes the client to the nearest PoP for a fast "
         "handshake. The server then migrates the connection to a backend with the client's data "
         "(potentially in a different region)."),
        ("<b>LB Bottleneck Elimination:</b> The LB only handles initial handshakes. Post-migration, "
         "clients communicate directly with backends. This is the \"load balancer bypass\" use case "
         "described in RFC 9000 Section 9.6."),
        ("<b>Edge Container Migration:</b> When a microservice container is migrated between edge "
         "nodes (for user mobility), QUIC migration keeps the connection alive without TCP re-establishment "
         "(Puliafito et al., 2022)."),
    ]
    for uc in use_cases:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {uc}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 5: Open Problems
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("5. Open Research Questions", h1))

    questions = [
        ("<b>Migration Scheduling Policy:</b> Who decides when and where to migrate? "
         "Centralized controller (Kubernetes-style), or autonomous server decision? "
         "What metrics trigger migration (CPU, queue depth, latency percentile)?"),
        ("<b>Multi-Hop Migration:</b> RFC 9000 allows only one preferred_address per handshake. "
         "For continuous rebalancing, NEW_CONNECTION_ID + subsequent path migration would be needed. "
         "No implementation supports this yet."),
        ("<b>State Transfer Security:</b> The 445-byte migration state contains TLS secrets. "
         "Securing this transfer (mTLS, encrypted Redis, etc.) is critical. "
         "Our analysis shows Redis KV is best for security/scalability, HTTP Pull for "
         "secrets-never-leave-memory guarantees."),
        ("<b>Interaction with QUIC-LB:</b> Can QUIC-LB CID encoding coexist with preferred_address "
         "migration? The migrated server would need to generate CIDs compatible with the LB's "
         "decoding scheme."),
        ("<b>Scalability Limits:</b> How many simultaneous migrations can a data center sustain? "
         "State transfer is small (445 bytes), but PATH_CHALLENGE/RESPONSE adds 1 RTT per migration."),
        ("<b>Client Behavior Variance:</b> Different QUIC implementations handle preferred_address "
         "differently. Firefox sends multiple PATH_CHALLENGEs; other clients may not. "
         "Standardization of client migration behavior is incomplete."),
    ]
    for q in questions:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {q}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 6: References
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Complete Reference List", h1))
    elements.append(Paragraph(
        "Papers organized by venue and relevance to QUIC server-side migration.",
        body
    ))

    elements.append(Paragraph("Top Conference Papers", h2))
    refs_conf = [
        '[1] Alizadeh et al., "CONGA: Distributed Congestion-Aware Load Balancing for Datacenters," '
        '<b>SIGCOMM 2014</b>. https://dl.acm.org/doi/10.1145/2740070.2626316',

        '[2] Eisenbud et al., "Maglev: A Fast and Reliable Software Network Load Balancer," '
        '<b>NSDI 2016</b>. https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud',

        '[3] Miao et al., "SilkRoad: Making Stateful Layer-4 Load Balancing Fast and Cheap Using '
        'Switching ASICs," <b>SIGCOMM 2017</b>. https://dl.acm.org/doi/10.1145/3098822.3098824',

        '[4] Olteanu et al., "Stateless Datacenter Load-balancing with Beamer," '
        '<b>NSDI 2018</b>. https://www.usenix.org/conference/nsdi18/presentation/olteanu',

        '[5] Araujo et al., "Balancing on the Edge: Transport Affinity without Network State," '
        '<b>NSDI 2018</b>. https://www.usenix.org/system/files/conference/nsdi18/nsdi18-araujo.pdf',

        '[6] Barbette et al., "A High-Speed Load-Balancer Design with Guaranteed '
        'Per-Connection-Consistency (Cheetah)," <b>NSDI 2020</b>. https://www.usenix.org/system/files/nsdi20-paper-barbette.pdf',

        '[7] "PLB: Congestion Signals are Enough," '
        '<b>SIGCOMM 2022</b>. https://dl.acm.org/doi/10.1145/3544216.3544226',

        '[8] Grubl et al., "QUIC-Exfil: Exploiting QUIC\'s Server Preferred Address Feature," '
        '<b>ASIA CCS 2025</b>. https://arxiv.org/pdf/2505.05292',
    ]
    for r in refs_conf:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("IETF Standards and Drafts", h2))
    refs_ietf = [
        '[9] RFC 9000, "QUIC: A UDP-Based Multiplexed and Secure Transport," IETF 2021. '
        'https://www.rfc-editor.org/rfc/rfc9000.html',

        '[10] RFC 9312, "Manageability of the QUIC Transport Protocol," IETF 2022. '
        'https://www.rfc-editor.org/rfc/rfc9312.html',

        '[11] Duke et al., "QUIC-LB: Generating Routable QUIC Connection IDs," '
        'IETF Draft v21, 2025. https://datatracker.ietf.org/doc/draft-ietf-quic-load-balancers/',

        '[12] Tan et al., "QUIC Connection Migration," '
        'IETF Draft, 2024. https://datatracker.ietf.org/doc/html/draft-tan-quic-connection-migration-00',
    ]
    for r in refs_ietf:
        elements.append(Paragraph(r, ref_style))

    elements.append(Paragraph("Journal Papers and Other", h2))
    refs_other = [
        '[13] Puliafito et al., "Server-side QUIC connection migration to support microservice '
        'deployment at the edge," <b>Pervasive and Mobile Computing</b>, 2022. '
        'https://www.sciencedirect.com/science/article/abs/pii/S157411922200030X',

        '[14] "An Analysis of QUIC Connection Migration in the Wild," '
        '<b>ACM SIGCOMM CCR</b>, 2025. https://dl.acm.org/doi/10.1145/3727063.3727066',

        '[15] "QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes," '
        '2025. https://arxiv.org/pdf/2602.03354',

        '[16] "Enhancing QUIC Performance in Heterogeneous Networks: A Proactive Connection '
        'Migration Approach," <b>Int. J. Network Management</b>, 2025. '
        'https://onlinelibrary.wiley.com/doi/10.1002/nem.70022',

        '[17] Liu et al., "Traffic load balancing in data center networks: A comprehensive survey," '
        '<b>Computer Science Review</b>, 2025. '
        'https://www.sciencedirect.com/science/article/abs/pii/S1574013725000255',

        '[18] Facebook Engineering, "Open-sourcing Katran, a scalable network load balancer," 2018. '
        'https://engineering.fb.com/2018/05/22/open-source/open-sourcing-katran-a-scalable-network-load-balancer/',
    ]
    for r in refs_other:
        elements.append(Paragraph(r, ref_style))

    # Build
    doc.build(elements)
    print(f"Generated: {OUTPUT}")

if __name__ == "__main__":
    build_pdf()

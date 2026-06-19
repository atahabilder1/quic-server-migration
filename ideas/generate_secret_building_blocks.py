#!/usr/bin/env python3
"""Generate a visual, party-based diagram PDF showing how TLS secrets are built step by step."""

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

OUTPUT = "ideas/SECRET_BUILDING_BLOCKS.pdf"

# Colors
DARK_BLUE = HexColor("#1a365d")
MED_BLUE = HexColor("#2b6cb0")
LIGHT_BLUE = HexColor("#ebf4ff")
GRAY_BG = HexColor("#f7fafc")
BORDER = HexColor("#cbd5e0")
DARK_GRAY = HexColor("#2d3748")
GREEN = HexColor("#276749")
GREEN_BG = HexColor("#f0fff4")
ORANGE = HexColor("#c05621")
ORANGE_BG = HexColor("#fffaf0")
PURPLE = HexColor("#553c9a")
PURPLE_BG = HexColor("#faf5ff")
RED = HexColor("#c53030")
RED_BG = HexColor("#fff5f5")
YELLOW = HexColor("#975a16")
YELLOW_BG = HexColor("#fffff0")
TEAL = HexColor("#285e61")
TEAL_BG = HexColor("#e6fffa")
PINK = HexColor("#97266d")
PINK_BG = HexColor("#fff5f7")

# Party colors
ALICE_COLOR = MED_BLUE       # Firefox / Client
ALICE_BG = LIGHT_BLUE
BOB_COLOR = GREEN            # Primary Server
BOB_BG = GREEN_BG
CHARLIE_COLOR = PURPLE       # Preferred Server
CHARLIE_BG = PURPLE_BG
EVE_COLOR = RED              # Eavesdropper
EVE_BG = RED_BG
MIXER_COLOR = ORANGE         # HKDF (the "mixer" machine)
MIXER_BG = ORANGE_BG


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
    body_center = ParagraphStyle(
        "BodyCenter", parent=body,
        alignment=TA_CENTER,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body,
        leftIndent=20, bulletIndent=8,
        spaceBefore=2, spaceAfter=2,
    )

    def highlight_box(text, bg_color, border_color, text_color):
        return ParagraphStyle(
            "HL", parent=body,
            fontSize=10, leading=14,
            backColor=bg_color, borderColor=border_color,
            borderWidth=1, borderPadding=8,
            spaceBefore=8, spaceAfter=8,
            textColor=text_color,
            fontName="Helvetica-Bold",
        )

    highlight_style = highlight_box("", GREEN_BG, GREEN, GREEN)
    warning_style = highlight_box("", RED_BG, RED, RED)
    example_style = highlight_box("", ORANGE_BG, ORANGE, ORANGE)
    note_style = highlight_box("", PURPLE_BG, PURPLE, PURPLE)
    idea_style = highlight_box("", YELLOW_BG, YELLOW, YELLOW)
    teal_style = highlight_box("", TEAL_BG, TEAL, TEAL)

    elements = []

    def code_block(text):
        code_para = Paragraph(
            text.replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;"),
            ParagraphStyle(
                "CodeInner", parent=body,
                fontSize=8.5, leading=11,
                fontName="Courier",
                textColor=DARK_GRAY,
            )
        )
        t = Table([[code_para]], colWidths=[6.0*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        return t

    def party_box(name, description, color, bg):
        """A colored box representing a party."""
        p = Paragraph(
            f'<b>{name}</b><br/><font size="8">{description}</font>',
            ParagraphStyle("Party", parent=body, fontSize=10, textColor=color,
                           alignment=TA_CENTER, fontName="Helvetica-Bold")
        )
        t = Table([[p]], colWidths=[1.8*inch], rowHeights=[0.6*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 2, color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    def arrow_row(left, arrow_text, right, left_color=DARK_GRAY, right_color=DARK_GRAY):
        """Create [left] ---arrow---> [right] layout."""
        lp = Paragraph(left, ParagraphStyle("AL", parent=body, fontSize=9,
                        alignment=TA_CENTER, textColor=left_color, fontName="Helvetica-Bold"))
        ap = Paragraph(arrow_text, ParagraphStyle("AA", parent=body, fontSize=9,
                        alignment=TA_CENTER, textColor=ORANGE, fontName="Helvetica-Bold"))
        rp = Paragraph(right, ParagraphStyle("AR", parent=body, fontSize=9,
                        alignment=TA_CENTER, textColor=right_color, fontName="Helvetica-Bold"))
        t = Table([[lp, ap, rp]], colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), LIGHT_BLUE),
            ("BACKGROUND", (1, 0), (1, 0), ORANGE_BG),
            ("BACKGROUND", (2, 0), (2, 0), GREEN_BG),
            ("BOX", (0, 0), (0, 0), 1, MED_BLUE),
            ("BOX", (1, 0), (1, 0), 1, ORANGE),
            ("BOX", (2, 0), (2, 0), 1, GREEN),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    def step_diagram(inputs, mixer_label, output, output_color=GREEN):
        """Create a visual: [input1] + [input2] → MIXER → [output]"""
        input_parts = []
        for inp_name, inp_val, inp_color, inp_bg in inputs:
            p = Paragraph(
                f'<b>{inp_name}</b><br/><font size="7">{inp_val}</font>',
                ParagraphStyle("Inp", parent=body, fontSize=9, textColor=inp_color,
                               alignment=TA_CENTER, fontName="Helvetica-Bold")
            )
            input_parts.append(p)

        # Join inputs with "+"
        input_cells = []
        input_styles = []
        col = 0
        for i, (inp_name, inp_val, inp_color, inp_bg) in enumerate(inputs):
            p = Paragraph(
                f'<b>{inp_name}</b><br/><font size="7">{inp_val}</font>',
                ParagraphStyle("Inp", parent=body, fontSize=9, textColor=inp_color,
                               alignment=TA_CENTER, fontName="Helvetica-Bold")
            )
            input_cells.append(p)
            input_styles.append(("BACKGROUND", (col, 0), (col, 0), inp_bg))
            input_styles.append(("BOX", (col, 0), (col, 0), 1, inp_color))
            col += 1
            if i < len(inputs) - 1:
                plus = Paragraph("+", ParagraphStyle("Plus", parent=body, fontSize=14,
                                  alignment=TA_CENTER, textColor=DARK_GRAY, fontName="Helvetica-Bold"))
                input_cells.append(plus)
                col += 1

        # Arrow
        arrow = Paragraph("\u2192", ParagraphStyle("Arr", parent=body, fontSize=18,
                           alignment=TA_CENTER, textColor=ORANGE, fontName="Helvetica-Bold"))
        input_cells.append(arrow)
        col += 1

        # Mixer
        mixer = Paragraph(
            f'<b>{mixer_label}</b>',
            ParagraphStyle("Mix", parent=body, fontSize=9, textColor=ORANGE,
                           alignment=TA_CENTER, fontName="Helvetica-Bold")
        )
        input_cells.append(mixer)
        input_styles.append(("BACKGROUND", (col, 0), (col, 0), MIXER_BG))
        input_styles.append(("BOX", (col, 0), (col, 0), 2, ORANGE))
        col += 1

        # Arrow
        arrow2 = Paragraph("\u2192", ParagraphStyle("Arr2", parent=body, fontSize=18,
                            alignment=TA_CENTER, textColor=ORANGE, fontName="Helvetica-Bold"))
        input_cells.append(arrow2)
        col += 1

        # Output
        out = Paragraph(
            f'<b>{output}</b>',
            ParagraphStyle("Out", parent=body, fontSize=9, textColor=output_color,
                           alignment=TA_CENTER, fontName="Helvetica-Bold")
        )
        input_cells.append(out)
        out_bg = GREEN_BG if output_color == GREEN else PURPLE_BG if output_color == PURPLE else TEAL_BG
        input_styles.append(("BACKGROUND", (col, 0), (col, 0), out_bg))
        input_styles.append(("BOX", (col, 0), (col, 0), 2, output_color))

        # Calculate column widths
        n_inputs = len(inputs)
        n_pluses = n_inputs - 1
        total_cells = n_inputs + n_pluses + 1 + 1 + 1 + 1  # inputs + pluses + arrow + mixer + arrow + output
        input_w = 1.1*inch
        plus_w = 0.25*inch
        arrow_w = 0.3*inch
        mixer_w = 1.1*inch
        out_w = 1.2*inch

        widths = []
        for i in range(n_inputs):
            widths.append(input_w)
            if i < n_inputs - 1:
                widths.append(plus_w)
        widths.extend([arrow_w, mixer_w, arrow_w, out_w])

        t = Table([input_cells], colWidths=widths)
        base_styles = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        t.setStyle(TableStyle(base_styles + input_styles))
        return t

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
    elements.append(Paragraph("How QUIC Secrets Are Built", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("A Visual, Step-by-Step Guide", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Who Gives What, When, and How It All Mixes Together",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Reference Document &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.8*inch))

    # Cast of characters
    elements.append(Paragraph("Cast of Characters", h2))
    cast = Table([
        [party_box("Alice (Firefox)", "The client / browser", ALICE_COLOR, ALICE_BG),
         party_box("Bob (Primary)", "The primary server", BOB_COLOR, BOB_BG),
         party_box("Charlie (Preferred)", "The preferred server", CHARLIE_COLOR, CHARLIE_BG)],
    ], colWidths=[2.1*inch, 2.1*inch, 2.1*inch])
    cast.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(cast)
    elements.append(Spacer(1, 8))

    cast2 = Table([
        [party_box("HKDF (The Mixer)", "Deterministic mixing function", MIXER_COLOR, MIXER_BG),
         party_box("Eve (Eavesdropper)", "Attacker sniffing the wire", EVE_COLOR, EVE_BG),
         Paragraph("", body)],
    ], colWidths=[2.1*inch, 2.1*inch, 2.1*inch])
    cast2.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(cast2)
    elements.append(PageBreak())

    # ══════════════════════════════════════════
    # ANALOGY: PAINT MIXING
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. The Analogy: Paint Mixing", h1))
    elements.append(Paragraph(
        "Before diving into crypto, here's the intuition. Imagine secrets as paint colors:",
        body
    ))

    elements.append(code_block(
        "Alice has a SECRET paint color:  [PRIVATE BLUE]  (only she knows)\n"
        "Bob has a SECRET paint color:    [PRIVATE GREEN] (only he knows)\n"
        "\n"
        "They agree on a PUBLIC base:     [YELLOW]        (everyone knows)\n"
        "\n"
        "Step 1: Alice mixes her secret with the base:\n"
        "  [YELLOW] + [PRIVATE BLUE] = [TEAL]  \u2192 sends TEAL to Bob (public)\n"
        "\n"
        "Step 2: Bob mixes his secret with the base:\n"
        "  [YELLOW] + [PRIVATE GREEN] = [LIME]  \u2192 sends LIME to Alice (public)\n"
        "\n"
        "Step 3: Each mixes their secret with what they received:\n"
        "  Alice: [LIME] + [PRIVATE BLUE] = [DARK OLIVE]   \u2190 shared secret!\n"
        "  Bob:   [TEAL] + [PRIVATE GREEN] = [DARK OLIVE]  \u2190 same color!\n"
        "\n"
        "Eve sees: [YELLOW], [TEAL], [LIME]\n"
        "Eve CANNOT unmix paint to get [PRIVATE BLUE] or [PRIVATE GREEN]\n"
        "Eve CANNOT compute [DARK OLIVE]\n"
        "\n"
        "This is Diffie-Hellman. In QUIC, the \"paint\" is math on elliptic curves."
    ))

    elements.append(Paragraph(
        "The real QUIC version uses X25519 (an elliptic curve). \"Mixing\" is point multiplication. "
        "\"Unmixing\" would require solving the discrete logarithm problem -- computationally impossible.",
        highlight_box("", GREEN_BG, GREEN, GREEN)
    ))

    # ══════════════════════════════════════════
    # SECTION 2: MEET THE INGREDIENTS
    # ══════════════════════════════════════════
    elements.append(Paragraph("2. Meet the Ingredients (Who Provides What)", h1))

    elements.append(make_table(
        ["Ingredient", "Who Provides It", "Public?", "Example Value", "Purpose"],
        [
            ["DCID", "Alice picks randomly", "Yes (in the clear)",
             "0x8394c8f03e515708", "Seed for Initial keys only"],
            ["QUIC v1 Salt", "Nobody (hardcoded in RFC)", "Yes (public constant)",
             "0x38762cf7f559...0a", "Adds entropy to Initial key derivation"],
            ["Client Random", "Alice generates", "Yes (in ClientHello)",
             "0xa1b2c3d4... (32 bytes)", "Prevents replay; part of transcript"],
            ["Server Random", "Bob generates", "Yes (in ServerHello)",
             "0xe5f6a7b8... (32 bytes)", "Prevents replay; part of transcript"],
            ["Alice's X25519 Private", "Alice generates", "<b>NO! Secret!</b>",
             "0x[32 random bytes]", "Her secret paint color"],
            ["Alice's X25519 Public", "Alice computes from private", "Yes (in ClientHello)",
             "0x358072d636... (32 bytes)", "Her mixed paint (base + secret)"],
            ["Bob's X25519 Private", "Bob generates", "<b>NO! Secret!</b>",
             "0x[32 random bytes]", "His secret paint color"],
            ["Bob's X25519 Public", "Bob computes from private", "Yes (in ServerHello)",
             "0x9fd7ad6dcf... (32 bytes)", "His mixed paint (base + secret)"],
            ["Certificate", "Bob (from CA)", "Yes (sent in handshake)",
             "[X.509 cert chain]", "Proves Bob is who he claims"],
            ["TLS Labels", "Nobody (defined in RFC)", "Yes (public strings)",
             "\"client in\", \"quic key\"", "Domain separators for HKDF"],
        ],
        col_widths=[1.1*inch, 1.0*inch, 0.8*inch, 1.2*inch, 1.4*inch],
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Only TWO things are truly secret: Alice's private key and Bob's private key. "
        "Everything else is public. Yet from these two secrets, an unbreakable shared "
        "secret is derived that no eavesdropper can compute.",
        warning_style
    ))

    # ══════════════════════════════════════════
    # SECTION 3: STEP-BY-STEP WITH DIAGRAMS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Step-by-Step: Building the Secrets", h1))

    # ── STEP 1 ──
    elements.append(Paragraph("Step 1: Alice Creates a Random Connection ID", h2))
    elements.append(Paragraph(
        "Alice (Firefox) wants to connect. She picks a random Destination Connection ID. "
        "This will be used ONLY for the Initial packet encryption -- it provides no real security.",
        body
    ))

    elements.append(code_block(
        "Alice picks:  DCID = 0x8394c8f03e515708  (8 random bytes)\n"
        "\n"
        "Alice sends this in the clear as the first byte of her first packet.\n"
        "Eve can see it. Bob can see it. Everyone can see it."
    ))

    elements.append(Spacer(1, 4))
    elements.append(step_diagram(
        [("Alice's DCID", "0x8394c8f0...", ALICE_COLOR, ALICE_BG),
         ("QUIC v1 Salt", "0x38762cf7... (fixed)", DARK_GRAY, GRAY_BG)],
        "HKDF-Extract",
        "initial_secret",
        GREEN
    ))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Eve can also compute this! She saw the DCID on the wire, and the salt is public. "
        "That's why Initial packets are NOT truly encrypted -- they use keys anyone can derive.",
        warning_style
    ))

    # ── STEP 2 ──
    elements.append(Paragraph("Step 2: Initial Keys (For First Few Packets Only)", h2))
    elements.append(Paragraph(
        "From the initial_secret, we derive separate keys for Alice\u2192Bob and Bob\u2192Alice:",
        body
    ))

    elements.append(step_diagram(
        [("initial_secret", "(from Step 1)", GREEN, GREEN_BG),
         ("Label", "\"client in\"", DARK_GRAY, GRAY_BG)],
        "HKDF-Expand",
        "client_initial_secret",
        ALICE_COLOR
    ))
    elements.append(Spacer(1, 4))
    elements.append(step_diagram(
        [("initial_secret", "(from Step 1)", GREEN, GREEN_BG),
         ("Label", "\"server in\"", DARK_GRAY, GRAY_BG)],
        "HKDF-Expand",
        "server_initial_secret",
        BOB_COLOR
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "Same secret + different label = different keys. The label acts like a \"which door\" selector. "
        "HKDF always gives the same output for the same inputs (deterministic).",
        note_style
    ))

    elements.append(Paragraph("From each Initial secret, derive 3 actual keys:", h3))
    elements.append(code_block(
        "client_initial_secret \u2192 HKDF-Expand(\"quic key\", 16) = AES key   [16 bytes]\n"
        "                      \u2192 HKDF-Expand(\"quic iv\",  12) = IV/nonce  [12 bytes]\n"
        "                      \u2192 HKDF-Expand(\"quic hp\",  16) = HP key    [16 bytes]\n"
        "\n"
        "Example (from RFC 9001 test vectors):\n"
        "  client_initial_secret = 0xc00cf151ca5be075ed0ebfb5c80323c4...\n"
        "    \u2514\u2500 AES key = 0x1f369613dd76d5467730efcbe3b1a22d\n"
        "    \u2514\u2500 IV      = 0xfa044b2f42a3fd3b46fb255c\n"
        "    \u2514\u2500 HP key  = 0x9f50449e04a0e810283a1e9933adedd2"
    ))

    elements.append(Paragraph(
        "These keys encrypt the ClientHello and ServerHello. They contain the TLS "
        "key exchange data that will produce the REAL secrets in the next step.",
        body
    ))

    # ── STEP 3 ──
    elements.append(PageBreak())
    elements.append(Paragraph("Step 3: The Key Exchange (The Real Magic)", h2))
    elements.append(Paragraph(
        "This is the most important step. Alice and Bob each generate a fresh, random "
        "X25519 key pair. They exchange public keys and independently compute the same shared secret.",
        body
    ))

    elements.append(Paragraph("3a. Alice generates her key pair", h3))
    elements.append(code_block(
        "Alice (Firefox) generates:\n"
        "  private_key_alice = random 32 bytes = 0x49af42ba...\n"
        "      \u2514\u2500 NEVER sent anywhere. Dies when Firefox closes.\n"
        "\n"
        "  public_key_alice = X25519_basepoint_multiply(private_key_alice)\n"
        "                   = 0x358072d6365880d1aeea329adf9121383851ed21a28e3b75e965d0d2cd166254\n"
        "      \u2514\u2500 Sent in ClientHello key_share extension (visible to Eve)"
    ))

    elements.append(Paragraph("3b. Bob generates his key pair", h3))
    elements.append(code_block(
        "Bob (Primary Server) generates:\n"
        "  private_key_bob = random 32 bytes = 0x7c3e8f1a...\n"
        "      \u2514\u2500 NEVER sent anywhere. Stays in server memory.\n"
        "\n"
        "  public_key_bob = X25519_basepoint_multiply(private_key_bob)\n"
        "                 = 0x9fd7ad6dcff4298dd3f96d5b1b2af910a0535b1488d7f8fabb349a982880b615\n"
        "      \u2514\u2500 Sent in ServerHello key_share extension (visible to Eve)"
    ))

    elements.append(Paragraph("3c. Both compute the shared secret INDEPENDENTLY", h3))

    # Alice's computation
    elements.append(step_diagram(
        [("Alice's Private", "0x49af42ba... (SECRET)", ALICE_COLOR, ALICE_BG),
         ("Bob's Public", "0x9fd7ad6d... (received)", BOB_COLOR, BOB_BG)],
        "X25519",
        "shared_secret",
        TEAL
    ))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        "<i>Alice computes: X25519(her_private, Bob's_public) = 0xdf4a291baa1eb7cfd6...</i>",
        ParagraphStyle("it", parent=body, fontSize=9, alignment=TA_CENTER,
                        textColor=TEAL, fontName="Helvetica-Oblique")
    ))
    elements.append(Spacer(1, 4))

    # Bob's computation
    elements.append(step_diagram(
        [("Bob's Private", "0x7c3e8f1a... (SECRET)", BOB_COLOR, BOB_BG),
         ("Alice's Public", "0x358072d6... (received)", ALICE_COLOR, ALICE_BG)],
        "X25519",
        "shared_secret",
        TEAL
    ))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        "<i>Bob computes: X25519(his_private, Alice's_public) = 0xdf4a291baa1eb7cfd6...</i>",
        ParagraphStyle("it2", parent=body, fontSize=9, alignment=TA_CENTER,
                        textColor=TEAL, fontName="Helvetica-Oblique")
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "SAME RESULT! Both get 0xdf4a291baa1eb7cfd6... (32 bytes). This is the Diffie-Hellman "
        "miracle: X25519(a_priv, b_pub) = X25519(b_priv, a_pub). Neither side needs the other's "
        "private key.",
        highlight_box("", GREEN_BG, GREEN, GREEN)
    ))

    elements.append(Paragraph(
        "Eve sees BOTH public keys on the wire but CANNOT compute the shared secret. "
        "She would need either private key, which requires solving the Elliptic Curve "
        "Discrete Logarithm Problem -- computationally impossible.",
        warning_style
    ))

    # ── STEP 4 ──
    elements.append(PageBreak())
    elements.append(Paragraph("Step 4: From Shared Secret to Handshake Keys", h2))
    elements.append(Paragraph(
        "The shared secret goes through HKDF to produce handshake encryption keys. "
        "These encrypt the certificate exchange and handshake completion.",
        body
    ))

    elements.append(step_diagram(
        [("Zeros (no PSK)", "0x0000...00 (32 bytes)", DARK_GRAY, GRAY_BG),
         ("Label", "\"derived\"", DARK_GRAY, GRAY_BG)],
        "HKDF",
        "early_derived",
        DARK_GRAY
    ))
    elements.append(Spacer(1, 4))
    elements.append(step_diagram(
        [("early_derived", "(from above)", DARK_GRAY, GRAY_BG),
         ("shared_secret", "0xdf4a291b... (from DH)", TEAL, TEAL_BG)],
        "HKDF-Extract",
        "handshake_secret",
        PURPLE
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "Now derive separate handshake traffic secrets for each direction. "
        "The transcript hash ensures these keys are bound to THIS specific handshake "
        "(prevents replays):",
        body
    ))

    elements.append(code_block(
        "transcript_hash = SHA-256(ClientHello || ServerHello)\n"
        "  = 0x[hash of every byte exchanged so far]\n"
        "  This includes: randoms, public keys, SNI, ALPN, extensions, cipher suite\n"
        "\n"
        "client_hs_secret = HKDF-Expand-Label(\n"
        "  handshake_secret, \"c hs traffic\", transcript_hash, 32\n"
        ")\n"
        "server_hs_secret = HKDF-Expand-Label(\n"
        "  handshake_secret, \"s hs traffic\", transcript_hash, 32\n"
        ")\n"
        "\n"
        "Each \u2192 AEAD key + IV + HP key  (same 3-key derivation as Initial)"
    ))

    elements.append(Paragraph(
        "These keys encrypt: Bob's Certificate, CertificateVerify (proves he owns the cert), "
        "and both sides' Finished messages (proves no one tampered with the handshake).",
        body
    ))

    # ── STEP 5 ──
    elements.append(Paragraph("Step 5: From Handshake to Master Secret", h2))
    elements.append(step_diagram(
        [("handshake_secret", "(from Step 4)", PURPLE, PURPLE_BG),
         ("Label", "\"derived\"", DARK_GRAY, GRAY_BG)],
        "HKDF-Expand",
        "derived_secret_2",
        DARK_GRAY
    ))
    elements.append(Spacer(1, 4))
    elements.append(step_diagram(
        [("derived_secret_2", "(from above)", DARK_GRAY, GRAY_BG),
         ("Zeros (no PSK)", "0x0000...00 (32 bytes)", DARK_GRAY, GRAY_BG)],
        "HKDF-Extract",
        "master_secret",
        TEAL
    ))

    # ── STEP 6 ──
    elements.append(PageBreak())
    elements.append(Paragraph("Step 6: The Application Secrets (WHAT WE EXPORT!)", h2))
    elements.append(Paragraph(
        "This is the final derivation. The master secret + full transcript hash produce "
        "the application traffic secrets. These are the 32-byte values we export for migration.",
        body
    ))

    elements.append(code_block(
        "transcript_hash_full = SHA-256(\n"
        "  ClientHello || ServerHello || EncryptedExtensions ||\n"
        "  Certificate || CertificateVerify || Finished\n"
        ")\n"
        "= 0x[hash of the ENTIRE handshake -- every single byte]"
    ))

    elements.append(Spacer(1, 4))
    elements.append(step_diagram(
        [("master_secret", "(from Step 5)", TEAL, TEAL_BG),
         ("Label + Hash", "\"c ap traffic\" + transcript", DARK_GRAY, GRAY_BG)],
        "HKDF-Expand",
        "client_app_secret",
        ALICE_COLOR
    ))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        "<b>= 0x9e40646ce79a7f9dc05af8889bce6552875afa0b06df0087f792ebb7c17504a5</b>",
        ParagraphStyle("val", parent=body, fontSize=8.5, fontName="Courier",
                        alignment=TA_CENTER, textColor=ALICE_COLOR)
    ))
    elements.append(Spacer(1, 6))
    elements.append(step_diagram(
        [("master_secret", "(from Step 5)", TEAL, TEAL_BG),
         ("Label + Hash", "\"s ap traffic\" + transcript", DARK_GRAY, GRAY_BG)],
        "HKDF-Expand",
        "server_app_secret",
        BOB_COLOR
    ))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        "<b>= 0xa11af9f05531f856ad47116b45a950328204b4f44bfb6b3a4b4f1f3fcb631643</b>",
        ParagraphStyle("val2", parent=body, fontSize=8.5, fontName="Courier",
                        alignment=TA_CENTER, textColor=BOB_COLOR)
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "THESE two 32-byte values are what we export to Charlie (the preferred server). "
        "They contain the distilled result of the entire handshake: Alice's randomness, "
        "Bob's randomness, the DH exchange, the transcript, everything. "
        "From these 64 bytes, Charlie can derive every encryption key needed.",
        highlight_box("", GREEN_BG, GREEN, GREEN)
    ))

    # ── STEP 7 ──
    elements.append(Paragraph("Step 7: From Secrets to Actual Encryption Keys", h2))
    elements.append(Paragraph(
        "Each 32-byte secret produces 3 keys through HKDF with different labels:",
        body
    ))

    elements.append(code_block(
        "From server_app_secret (for encrypting server \u2192 client):\n"
        "\n"
        "  HKDF-Expand-Label(secret, \"quic key\", 16)\n"
        "  = 0xfd8c7da9de1b2da4d2ef9fd5188922d0       \u2190 AES-128 key\n"
        "\n"
        "  HKDF-Expand-Label(secret, \"quic iv\",  12)\n"
        "  = 0x02f6180e4f4aa456d7e8a389               \u2190 IV (nonce base)\n"
        "\n"
        "  HKDF-Expand-Label(secret, \"quic hp\",  16)\n"
        "  = 0xb7f6f021453e43b0b2c25989d0a31207       \u2190 Header Protection key"
    ))

    elements.append(Paragraph(
        "Same inputs \u2192 same outputs. ALWAYS. This is why Charlie can reconstruct "
        "identical keys from just the 32-byte secret.",
        example_style
    ))

    # ══════════════════════════════════════════
    # SECTION 4: THE HANDOFF TO CHARLIE
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. The Handoff: Bob Gives Charlie the Secrets", h1))
    elements.append(Paragraph(
        "Now the migration happens. Bob (primary server) sends Charlie (preferred server) "
        "the application traffic secrets -- and Charlie rebuilds everything.",
        body
    ))

    elements.append(Paragraph("What Bob sends to Charlie (445 bytes):", h2))

    elements.append(make_table(
        ["Component", "From Whom", "Example", "Size"],
        [
            ["<b>server_app_secret</b>", "Bob derived from handshake",
             "0xa11af9f05531f856...", "32 bytes"],
            ["<b>client_app_secret</b>", "Bob derived from handshake",
             "0x9e40646ce79a7f9d...", "32 bytes"],
            ["server_next_secret", "Bob computed for key update",
             "0x7b4f2e8c9a1d3f5e...", "32 bytes"],
            ["client_next_secret", "Bob computed for key update",
             "0x3c8b1d4e7f2a9085...", "32 bytes"],
            ["Cipher suite", "Negotiated in handshake",
             "0x1301 (AES-128-GCM)", "2 bytes"],
            ["Epoch numbers", "Bob tracks internally",
             "3 (first app data epoch)", "8 bytes"],
            ["Packet number ranges", "Bob tracks per direction",
             "write: 0..15, read: 0..3", "48 bytes"],
            ["Local CIDs (8)", "Bob issued to Alice",
             "0x7f8a3c1b9e2d4f06a5c8, ...", "162 bytes"],
            ["Remote CIDs (1)", "Alice issued to Bob",
             "0x2c5f8b1a7d3e9046c8a2", "32 bytes"],
            ["Alice's address", "From the network path",
             "141.217.168.127:50000", "7 bytes"],
            ["QUIC Version", "Negotiated",
             "0x00000001 (v1)", "4 bytes"],
        ],
        col_widths=[1.3*inch, 1.3*inch, 1.7*inch, 0.7*inch],
    ))

    elements.append(Paragraph("What Charlie does with it:", h2))

    elements.append(code_block(
        "Charlie receives 445 bytes via TCP/Redis/HTTP.\n"
        "\n"
        "Step 1: Import the raw secret bytes as NSS key objects\n"
        "  write_secret = hkdf::import_key(0xa11af9f05531f856...)\n"
        "  read_secret  = hkdf::import_key(0x9e40646ce79a7f9d...)\n"
        "\n"
        "Step 2: Re-derive AEAD and HP keys (IDENTICAL to Bob's)\n"
        "  write_aead_key = HKDF-Expand(write_secret, \"quic key\", 16)\n"
        "                 = 0xfd8c7da9de1b2da4d2ef9fd5188922d0  \u2190 same as Bob!\n"
        "  write_iv       = HKDF-Expand(write_secret, \"quic iv\", 12)\n"
        "                 = 0x02f6180e4f4aa456d7e8a389            \u2190 same as Bob!\n"
        "  write_hp       = HKDF-Expand(write_secret, \"quic hp\", 16)\n"
        "                 = 0xb7f6f021453e43b0b2c25989d0a31207    \u2190 same as Bob!\n"
        "\n"
        "  (Same for read direction)\n"
        "\n"
        "Step 3: Set up connection state\n"
        "  conn.state = Confirmed  (skip handshake)\n"
        "  conn.local_cids = [8 CIDs from Bob]\n"
        "  conn.remote_cids = [Alice's CID]\n"
        "  conn.path = Alice's IP:port \u2194 Charlie's IP:port\n"
        "\n"
        "Charlie is now a PERFECT CLONE of Bob's connection."
    ))

    elements.append(Paragraph(
        "Charlie never talked to Alice. Charlie never did Diffie-Hellman. Charlie never saw "
        "the certificate. But Charlie has byte-identical encryption keys. Alice cannot tell "
        "the difference when Charlie responds to her PATH_CHALLENGE.",
        highlight_box("", GREEN_BG, GREEN, GREEN)
    ))

    # ══════════════════════════════════════════
    # SECTION 5: WHAT EACH PARTY KNOWS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("5. Who Knows What? (Complete Picture)", h1))

    elements.append(make_table(
        ["Secret / Value", "Alice", "Bob", "Charlie", "Eve"],
        [
            ["Alice's X25519 private key", "<b>YES</b>", "No", "No", "No"],
            ["Bob's X25519 private key", "No", "<b>YES</b>", "No", "No"],
            ["Both X25519 public keys", "Yes", "Yes", "No", "<b>Yes</b> (on wire)"],
            ["ECDHE shared_secret", "<b>YES</b>", "<b>YES</b>", "No", "No"],
            ["master_secret", "YES", "YES", "No", "No"],
            ["client_app_secret (32 bytes)", "<b>YES</b>", "<b>YES</b>",
             "<b>YES</b> (from Bob)", "No"],
            ["server_app_secret (32 bytes)", "<b>YES</b>", "<b>YES</b>",
             "<b>YES</b> (from Bob)", "No"],
            ["AEAD keys / IV / HP keys", "<b>YES</b>", "<b>YES</b>",
             "<b>YES</b> (re-derived)", "No"],
            ["Can decrypt Alice's packets?", "YES", "YES",
             "<b>YES</b>", "No"],
            ["Can encrypt responses to Alice?", "N/A", "YES",
             "<b>YES</b>", "No"],
            ["Connection IDs", "YES", "YES",
             "<b>YES</b> (from Bob)", "Yes (on wire)"],
            ["Handshake transcript", "YES", "YES", "No", "Partial"],
        ],
        col_widths=[1.7*inch, 0.8*inch, 0.8*inch, 1.1*inch, 1.0*inch],
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Charlie knows LESS than Bob: he doesn't have the handshake transcript, the DH shared "
        "secret, or the master secret. He only has the final application secrets. But that's "
        "enough -- the application secrets are all you need to encrypt and decrypt app data.",
        note_style
    ))

    elements.append(Paragraph(
        "Eve knows NOTHING useful. She can see public keys and CIDs on the wire, but cannot "
        "compute any secrets. Even if she captures the 445-byte transfer between Bob and Charlie "
        "(e.g., on the LAN), she gets the secrets. That's why the transfer channel MUST be encrypted "
        "in production.",
        warning_style
    ))

    # ══════════════════════════════════════════
    # SECTION 6: THE FULL RECIPE
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. The Complete Recipe (One Page Summary)", h1))

    elements.append(code_block(
        "RECIPE: How to Build QUIC Application Secrets\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
        "\n"
        "INGREDIENTS:\n"
        "  From Alice:  private_key_a (32 bytes, random, SECRET)\n"
        "  From Bob:    private_key_b (32 bytes, random, SECRET)\n"
        "  From RFC:    QUIC v1 salt, TLS labels (public constants)\n"
        "\n"
        "STEP 1 \u2500 Key Exchange (Diffie-Hellman)\n"
        "  public_a = X25519(private_a, basepoint)     [Alice computes, sends to Bob]\n"
        "  public_b = X25519(private_b, basepoint)     [Bob computes, sends to Alice]\n"
        "  shared   = X25519(private_a, public_b)      [Both compute independently]\n"
        "           = X25519(private_b, public_a)      [Same result!]\n"
        "\n"
        "STEP 2 \u2500 Handshake Secret\n"
        "  early_secret     = HKDF-Extract(salt=0, IKM=zeros)\n"
        "  derived_1        = HKDF-Expand(early_secret, \"derived\")\n"
        "  handshake_secret = HKDF-Extract(salt=derived_1, IKM=shared)\n"
        "\n"
        "STEP 3 \u2500 Master Secret\n"
        "  derived_2        = HKDF-Expand(handshake_secret, \"derived\")\n"
        "  master_secret    = HKDF-Extract(salt=derived_2, IKM=zeros)\n"
        "\n"
        "STEP 4 \u2500 Application Secrets (what we export!)\n"
        "  transcript       = SHA-256(all handshake messages)\n"
        "  client_secret    = HKDF-Expand(master, \"c ap traffic\", transcript)\n"
        "  server_secret    = HKDF-Expand(master, \"s ap traffic\", transcript)\n"
        "\n"
        "STEP 5 \u2500 Actual Keys (derived on both Bob AND Charlie)\n"
        "  aead_key = HKDF-Expand(secret, \"quic key\", 16)    [same input = same key]\n"
        "  iv       = HKDF-Expand(secret, \"quic iv\",  12)    [same input = same iv]\n"
        "  hp_key   = HKDF-Expand(secret, \"quic hp\",  16)    [same input = same hp]\n"
        "\n"
        "EXPORT: Bob sends client_secret + server_secret (64 bytes) to Charlie\n"
        "IMPORT: Charlie runs Step 5 and gets IDENTICAL keys\n"
        "\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
        "Total exported: 64 bytes of secrets + 381 bytes of metadata = 445 bytes\n"
        "Total security: Entire connection. Cannot be forged. Cannot be reversed."
    ))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "The 32-byte application secret is the distilled essence of: "
        "Alice's randomness + Bob's randomness + their Diffie-Hellman exchange + "
        "the hash of every handshake message. All compressed into 32 bytes by HKDF. "
        "Charlie only needs these 32 bytes (per direction) to become a perfect substitute for Bob.",
        highlight_box("", GREEN_BG, GREEN, GREEN)
    ))

    # Build
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

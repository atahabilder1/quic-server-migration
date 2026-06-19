#!/usr/bin/env python3
"""Generate detailed TLS 1.3 Key Derivation in QUIC PDF with step-by-step examples."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Preformatted
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import date

OUTPUT = "ideas/TLS_KEY_DERIVATION_IN_QUIC.pdf"

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
CODE_BG = HexColor("#1a202c")
CODE_BORDER = HexColor("#4a5568")
YELLOW = HexColor("#975a16")
YELLOW_BG = HexColor("#fffff0")
RED = HexColor("#c53030")
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
    code_style = ParagraphStyle(
        "Code", parent=styles["Code"],
        fontSize=8.5, leading=11,
        fontName="Courier",
        textColor=DARK_GRAY,
        backColor=GRAY_BG,
        borderColor=BORDER,
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=6, spaceAfter=6,
        leftIndent=10,
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
        backColor=RED_BG, borderColor=RED,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=RED,
        fontName="Helvetica-Bold",
    )
    example_style = ParagraphStyle(
        "Example", parent=body,
        fontSize=10, leading=14,
        backColor=ORANGE_BG, borderColor=ORANGE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=ORANGE,
        fontName="Helvetica-Bold",
    )
    note_style = ParagraphStyle(
        "Note", parent=body,
        fontSize=10, leading=14,
        backColor=PURPLE_BG, borderColor=PURPLE,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
    )
    idea_style = ParagraphStyle(
        "Idea", parent=body,
        fontSize=10, leading=14,
        backColor=YELLOW_BG, borderColor=YELLOW,
        borderWidth=1, borderPadding=8,
        spaceBefore=8, spaceAfter=8,
        textColor=YELLOW,
        fontName="Helvetica-Bold",
    )

    elements = []

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

    def code_block(text):
        """Create a code-like block using a table with monospace font."""
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

    def arrow_box(left_text, arrow_text, right_text):
        """Create a visual: [left] --arrow--> [right]"""
        left = Paragraph(left_text, ParagraphStyle(
            "ArrowLeft", parent=body, fontSize=9, alignment=TA_CENTER, textColor=DARK_BLUE,
            fontName="Helvetica-Bold",
        ))
        arrow = Paragraph(arrow_text, ParagraphStyle(
            "Arrow", parent=body, fontSize=9, alignment=TA_CENTER, textColor=ACCENT,
            fontName="Helvetica-Bold",
        ))
        right = Paragraph(right_text, ParagraphStyle(
            "ArrowRight", parent=body, fontSize=9, alignment=TA_CENTER, textColor=GREEN,
            fontName="Helvetica-Bold",
        ))
        t = Table([[left, arrow, right]], colWidths=[2.2*inch, 1.6*inch, 2.2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), LIGHT_BLUE),
            ("BACKGROUND", (2, 0), (2, 0), GREEN_BG),
            ("BOX", (0, 0), (0, 0), 1, MED_BLUE),
            ("BOX", (2, 0), (2, 0), 1, GREEN),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    # ══════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 1.2*inch))
    elements.append(Paragraph("TLS 1.3 Key Derivation in QUIC", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("How Secrets Are Built, Step by Step", title_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="60%", thickness=2, color=MED_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "With Concrete Byte-Level Examples at Every Stage",
        subtitle_style
    ))
    elements.append(Paragraph(
        "And How We Export/Import Them for Server Migration",
        subtitle_style
    ))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Reference Document &bull; {date.today().strftime('%B %Y')}",
        ParagraphStyle("Date", parent=subtitle_style, fontSize=10, textColor=DARK_GRAY)
    ))
    elements.append(Spacer(1, 0.6*inch))

    abstract_text = (
        "This document explains exactly how QUIC derives its encryption keys from the TLS 1.3 "
        "handshake, with concrete hex examples at every step. It covers the three phases of key "
        "derivation (Initial, Handshake, Application), explains HKDF in detail, shows what our "
        "server migration exports (445 bytes), and demonstrates why the preferred server can "
        "reconstruct identical keys from just the traffic secret."
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
    # SECTION 1: THE BIG PICTURE
    # ══════════════════════════════════════════
    elements.append(Paragraph("1. The Big Picture: Three Phases of Keys", h1))
    elements.append(Paragraph(
        "A QUIC connection goes through three distinct encryption phases. Each phase uses "
        "different keys, derived from different inputs. Understanding this progression is "
        "essential to understanding what we export for migration.",
        body
    ))

    elements.append(make_table(
        ["Phase", "Epoch", "Key Source", "Security", "Who Can Decrypt?"],
        [
            ["1. Initial", "0", "Destination Connection ID (public)",
             "None (keys are public)", "Anyone who sees the DCID"],
            ["2. Handshake", "2", "TLS key exchange (ECDHE shared secret)",
             "Forward-secret", "Only client and server"],
            ["3. Application", "3+", "Derived from master secret",
             "Forward-secret + updatable", "Only client and server"],
        ],
        col_widths=[1.0*inch, 0.6*inch, 1.7*inch, 1.3*inch, 1.5*inch],
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "For server migration, we only need to export Phase 3 (Application) keys. "
        "Phase 1 and 2 are only used during the handshake, which is already complete "
        "when migration happens.",
        highlight_style
    ))

    elements.append(Paragraph(
        "The complete derivation chain looks like this:",
        body
    ))

    elements.append(code_block(
        "Phase 1: DCID (public)\n"
        "  \u2514\u2500\u2500 HKDF-Extract \u2500\u2500\u2192 initial_secret\n"
        "        \u251c\u2500\u2500 HKDF-Expand(\"client in\") \u2500\u2192 client Initial keys\n"
        "        \u2514\u2500\u2500 HKDF-Expand(\"server in\") \u2500\u2192 server Initial keys\n"
        "\n"
        "Phase 2: ECDHE shared secret (from key exchange)\n"
        "  \u2514\u2500\u2500 HKDF-Extract \u2500\u2500\u2192 handshake_secret\n"
        "        \u251c\u2500\u2500 HKDF-Expand(\"c hs traffic\") \u2500\u2192 client Handshake keys\n"
        "        \u2514\u2500\u2500 HKDF-Expand(\"s hs traffic\") \u2500\u2192 server Handshake keys\n"
        "\n"
        "Phase 3: Master secret (from handshake secret)\n"
        "  \u2514\u2500\u2500 HKDF-Extract \u2500\u2500\u2192 master_secret\n"
        "        \u251c\u2500\u2500 HKDF-Expand(\"c ap traffic\") \u2500\u2192 client App secret  \u2190 WE EXPORT THIS\n"
        "        \u2514\u2500\u2500 HKDF-Expand(\"s ap traffic\") \u2500\u2192 server App secret  \u2190 WE EXPORT THIS\n"
        "              \u251c\u2500\u2500 HKDF-Expand(\"quic key\") \u2500\u2192 AEAD key (16 bytes)\n"
        "              \u251c\u2500\u2500 HKDF-Expand(\"quic iv\")  \u2500\u2192 IV (12 bytes)\n"
        "              \u2514\u2500\u2500 HKDF-Expand(\"quic hp\")  \u2500\u2192 HP key (16 bytes)"
    ))

    # ══════════════════════════════════════════
    # SECTION 2: HKDF EXPLAINED
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("2. HKDF: The Building Block of Everything", h1))
    elements.append(Paragraph(
        "HKDF (HMAC-based Key Derivation Function, RFC 5869) is the single most important "
        "function in TLS 1.3. Every key in QUIC is derived using HKDF. It has two operations:",
        body
    ))

    elements.append(Paragraph("2.1 HKDF-Extract: Concentrate Randomness", h2))
    elements.append(Paragraph(
        "Takes potentially weak input key material (IKM) and a salt, produces a fixed-size "
        "pseudorandom key (PRK). Think of it as \"distilling\" randomness.",
        body
    ))

    elements.append(code_block(
        "HKDF-Extract(salt, IKM) \u2192 PRK\n"
        "\n"
        "Internally:  PRK = HMAC-SHA256(key=salt, data=IKM)\n"
        "\n"
        "Example (Initial keys):\n"
        "  salt = 0x38762cf7f55934b34d179ae6a4c80cadccbb7f0a  (QUIC v1 Initial salt)\n"
        "  IKM  = 0x8394c8f03e515708  (Destination Connection ID)\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "  PRK  = 0x7db5df06e7a69e432496adedb0085192\n"
        "           3595221596ae2ae9fb8115c1e9ed0a44  (32 bytes = initial_secret)"
    ))

    elements.append(Paragraph(
        "The salt is a fixed value defined by each QUIC version. For QUIC v1, it's a 20-byte "
        "constant from RFC 9001 Section 5.2. The IKM is the Destination Connection ID from "
        "the client's first packet -- which is sent in the clear!",
        body
    ))

    elements.append(Paragraph(
        "This is why Initial packets offer NO real confidentiality. Anyone who reads the "
        "DCID from the wire can compute the exact same initial_secret and decrypt everything.",
        warning_style
    ))

    elements.append(Paragraph("2.2 HKDF-Expand-Label: Derive Specific Keys", h2))
    elements.append(Paragraph(
        "Takes a PRK and a label string, produces a key of any desired length. This is how "
        "one secret becomes many different keys.",
        body
    ))

    elements.append(code_block(
        "HKDF-Expand-Label(Secret, Label, Context, Length) \u2192 Key\n"
        "\n"
        "Internally:\n"
        "  1. Build HkdfLabel struct:\n"
        "     length  = desired output length (2 bytes)\n"
        "     label   = \"tls13 \" + Label  (variable, with length prefix)\n"
        "     context = Context (variable, with length prefix, usually empty)\n"
        "  \n"
        "  2. Key = HKDF-Expand(PRK=Secret, info=HkdfLabel, L=Length)\n"
        "         = HMAC-SHA256(key=Secret, data=HkdfLabel || 0x01)  [for first block]\n"
        "\n"
        "Example (deriving client Initial secret):\n"
        "  Secret  = initial_secret (32 bytes from Extract above)\n"
        "  Label   = \"client in\"   \u2192 prefixed as \"tls13 client in\"\n"
        "  Context = \"\" (empty)\n"
        "  Length  = 32\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "  Output  = 0xc00cf151ca5be075ed0ebfb5c80323c4\n"
        "              2d6b7db67881289af4008f1f6c357aea  (client_initial_secret)"
    ))

    elements.append(Paragraph(
        "The label acts as a domain separator -- even with the same secret, different labels "
        "produce completely different keys. This is how \"quic key\", \"quic iv\", and \"quic hp\" "
        "all derive different values from the same traffic secret.",
        note_style
    ))

    # ══════════════════════════════════════════
    # SECTION 3: PHASE 1 - INITIAL KEYS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Phase 1: Initial Keys (Epoch 0)", h1))
    elements.append(Paragraph(
        "The very first QUIC packet must be encrypted, but no key exchange has happened yet. "
        "Solution: derive keys from the Destination Connection ID, which both sides know.",
        body
    ))

    elements.append(Paragraph("Step-by-Step with Real Values (RFC 9001 Appendix A)", h2))
    elements.append(Paragraph(
        "These are the exact test vectors from the RFC. You can verify them yourself.",
        body
    ))

    elements.append(Paragraph("Step 1: Client picks a random DCID", h3))
    elements.append(code_block(
        "Client's Initial packet:\n"
        "  Destination Connection ID = 0x8394c8f03e515708  (8 bytes, random)"
    ))
    elements.append(Paragraph(
        "This is in the clear -- anyone sniffing the network sees this value.",
        body
    ))

    elements.append(Paragraph("Step 2: Extract the initial secret", h3))
    elements.append(code_block(
        "initial_secret = HKDF-Extract(\n"
        "  salt = 0x38762cf7f55934b34d179ae6a4c80cadccbb7f0a,  // QUIC v1 fixed salt\n"
        "  IKM  = 0x8394c8f03e515708                            // DCID from wire\n"
        ")\n"
        "\n"
        "Result: 0x7db5df06e7a69e432496adedb00851929595221596ae2ae9fb8115c1e9ed0a44"
    ))

    elements.append(Paragraph("Step 3: Derive client and server Initial secrets", h3))
    elements.append(code_block(
        "client_initial_secret = HKDF-Expand-Label(\n"
        "  Secret = initial_secret,\n"
        "  Label  = \"client in\",    // TLS 1.3 label\n"
        "  Length = 32\n"
        ")\n"
        "= 0xc00cf151ca5be075ed0ebfb5c80323c42d6b7db67881289af4008f1f6c357aea\n"
        "\n"
        "server_initial_secret = HKDF-Expand-Label(\n"
        "  Secret = initial_secret,\n"
        "  Label  = \"server in\",\n"
        "  Length = 32\n"
        ")\n"
        "= 0x3c199828fd139efd216c155ad844cc81fb82fa8d7446fa7d78be803acdda951b"
    ))

    elements.append(Paragraph("Step 4: From each secret, derive AEAD key + IV + HP key", h3))
    elements.append(code_block(
        "From client_initial_secret:\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic key\", Length=16)\n"
        "     = 0x1f369613dd76d5467730efcbe3b1a22d          // AES-128 key (16 bytes)\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic iv\",  Length=12)\n"
        "     = 0xfa044b2f42a3fd3b46fb255c                  // IV / nonce (12 bytes)\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic hp\",  Length=16)\n"
        "     = 0x9f50449e04a0e810283a1e9933adedd2          // Header Protection (16 bytes)\n"
        "\n"
        "From server_initial_secret:\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic key\", Length=16)\n"
        "     = 0xcf3a5331653c364c88f0f379b6067e37          // AES-128 key\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic iv\",  Length=12)\n"
        "     = 0x0ac1493ca1905853b0bba03e                  // IV\n"
        "  \u2514\u2500 HKDF-Expand-Label(Label=\"quic hp\",  Length=16)\n"
        "     = 0xc206b8d9b9f0f37644430b490eeaa314          // HP key"
    ))

    elements.append(Paragraph(
        "Total: from one 8-byte DCID, we derived 6 keys (3 per direction). "
        "Each direction has an AEAD key (for encrypting/decrypting payload), an IV "
        "(combined with packet number to form the nonce), and an HP key (for obscuring "
        "the packet number in the header).",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # SECTION 4: HOW AEAD ENCRYPTION WORKS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("4. How AEAD Encryption Works in QUIC", h1))
    elements.append(Paragraph(
        "QUIC uses AEAD (Authenticated Encryption with Associated Data) -- specifically "
        "AES-128-GCM or ChaCha20-Poly1305. AEAD encrypts the payload AND authenticates "
        "both the payload and the header. Any tampering is detected.",
        body
    ))

    elements.append(Paragraph("4.1 Encryption (Sender Side)", h2))
    elements.append(code_block(
        "Inputs:\n"
        "  key   = AEAD key (16 bytes for AES-128-GCM)\n"
        "  nonce = IV XOR packet_number (12 bytes)\n"
        "  aad   = QUIC header bytes (authenticated but NOT encrypted)\n"
        "  plain = payload to encrypt\n"
        "\n"
        "Output:\n"
        "  cipher = AES-128-GCM-Encrypt(key, nonce, aad, plain)\n"
        "         = encrypted_payload (same length as plain)\n"
        "           + authentication_tag (16 bytes)\n"
        "\n"
        "Example:\n"
        "  key   = 0x1f369613dd76d5467730efcbe3b1a22d\n"
        "  IV    = 0xfa044b2f42a3fd3b46fb255c\n"
        "  PN    = 0x00000002  (packet number 2)\n"
        "  nonce = IV XOR PN = 0xfa044b2f42a3fd3b46fb255e\n"
        "                                           ^^^^ (last bytes changed by XOR)\n"
        "  aad   = [QUIC short header bytes...]\n"
        "  plain = [CRYPTO frame with ClientHello...]\n"
        "  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "  cipher = [encrypted bytes...] + [16-byte auth tag]"
    ))

    elements.append(Paragraph(
        "The nonce changes for every packet (because packet number changes). "
        "This ensures that even identical payloads produce different ciphertext. "
        "The AEAD key stays the same for the entire epoch.",
        note_style
    ))

    elements.append(Paragraph("4.2 Header Protection (HP)", h2))
    elements.append(Paragraph(
        "After AEAD encryption, the packet number in the header is still visible. "
        "QUIC applies a second layer: Header Protection. This obscures the packet number "
        "so observers can't easily track packet sequences.",
        body
    ))

    elements.append(code_block(
        "Header Protection:\n"
        "  1. Sample 16 bytes from the ciphertext (at a fixed offset)\n"
        "  2. Compute mask = AES-ECB(hp_key, sample)  [first 5 bytes used]\n"
        "  3. XOR the header flags with mask[0] (partially)\n"
        "  4. XOR the packet number bytes with mask[1..5]\n"
        "\n"
        "Result: packet number is obscured in the wire format\n"
        "Receiver reverses the process using the same HP key"
    ))

    elements.append(Paragraph("4.3 Summary: Three Keys, Three Jobs", h2))
    elements.append(make_table(
        ["Key", "Size (AES-128)", "Purpose", "Changes When?"],
        [
            ["AEAD key", "16 bytes", "Encrypt/decrypt packet payload + auth tag",
             "Only at key update (epoch change)"],
            ["IV", "12 bytes", "Combined with packet number to form unique nonce",
             "Only at key update"],
            ["HP key", "16 bytes", "Obscure packet number in header",
             "Only at key update"],
        ],
        col_widths=[1.0*inch, 1.1*inch, 2.5*inch, 1.5*inch],
    ))

    # ══════════════════════════════════════════
    # SECTION 5: PHASE 2 - HANDSHAKE KEYS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("5. Phase 2: Handshake Keys (Epoch 2)", h1))
    elements.append(Paragraph(
        "After Initial packets are exchanged, the TLS handshake happens inside them. "
        "The client and server perform an Elliptic Curve Diffie-Hellman key exchange (ECDHE). "
        "This produces a shared secret that no one else knows.",
        body
    ))

    elements.append(Paragraph("Step 1: Key Exchange (X25519)", h2))
    elements.append(code_block(
        "Client generates:\n"
        "  client_private = random 32 bytes (NEVER leaves client)\n"
        "  client_public  = X25519_basepoint(client_private)\n"
        "                 = 0x358072d6365880d1aeea329adf9121383851ed21a28e3b75e965d0d2cd166254\n"
        "\n"
        "Server generates:\n"
        "  server_private = random 32 bytes (NEVER leaves server)\n"
        "  server_public  = X25519_basepoint(server_private)\n"
        "                 = 0x9fd7ad6dcff4298dd3f96d5b1b2af910a0535b1488d7f8fabb349a982880b615\n"
        "\n"
        "Exchange: client sends client_public in ClientHello key_share\n"
        "          server sends server_public in ServerHello key_share\n"
        "\n"
        "Both compute INDEPENDENTLY:\n"
        "  shared_secret = X25519(my_private, their_public)\n"
        "\n"
        "  Client: X25519(client_private, server_public) = 0xdf4a291baa1eb7cf...\n"
        "  Server: X25519(server_private, client_public) = 0xdf4a291baa1eb7cf...\n"
        "                                                   ^^^^^^^^^^^^^^^^\n"
        "                                                   SAME VALUE! (32 bytes)"
    ))

    elements.append(Paragraph(
        "This is the magic of Diffie-Hellman: both sides compute the same shared secret "
        "without ever transmitting it. An observer who sees both public keys CANNOT compute "
        "the shared secret (this would require solving the discrete log problem on Curve25519).",
        highlight_style
    ))

    elements.append(Paragraph("Step 2: Derive Handshake Secret", h2))
    elements.append(code_block(
        "// First, derive an intermediate \"early secret\" (no PSK, so IKM = 0)\n"
        "early_secret = HKDF-Extract(salt=0, IKM=0x00...00)\n"
        "\n"
        "// Derive a salt for the next extraction\n"
        "derived_secret = HKDF-Expand-Label(early_secret, \"derived\", \"\", 32)\n"
        "\n"
        "// Extract handshake secret using the ECDHE shared secret\n"
        "handshake_secret = HKDF-Extract(\n"
        "  salt = derived_secret,\n"
        "  IKM  = shared_secret      // from Diffie-Hellman above\n"
        ")\n"
        "= 0x[32 bytes -- this is the handshake secret]"
    ))

    elements.append(Paragraph("Step 3: Derive Handshake Traffic Secrets", h2))
    elements.append(code_block(
        "// The \"Context\" here is the hash of all handshake messages so far\n"
        "// (ClientHello + ServerHello). This binds the keys to THIS specific handshake.\n"
        "\n"
        "transcript_hash = SHA-256(ClientHello || ServerHello)\n"
        "\n"
        "client_hs_secret = HKDF-Expand-Label(\n"
        "  handshake_secret, \"c hs traffic\", transcript_hash, 32\n"
        ")\n"
        "\n"
        "server_hs_secret = HKDF-Expand-Label(\n"
        "  handshake_secret, \"s hs traffic\", transcript_hash, 32\n"
        ")\n"
        "\n"
        "// From each, derive AEAD key + IV + HP key (same as Initial phase)\n"
        "// These encrypt the rest of the handshake (Certificate, Finished, etc.)"
    ))

    elements.append(Paragraph(
        "Handshake keys are only used for a few packets (server's Certificate, "
        "CertificateVerify, Finished; client's Finished). After that, both sides "
        "switch to Application keys.",
        body_italic
    ))

    # ══════════════════════════════════════════
    # SECTION 6: PHASE 3 - APPLICATION KEYS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Phase 3: Application Keys (Epoch 3) -- What We Export", h1))
    elements.append(Paragraph(
        "This is the most important phase for our migration. Application keys protect ALL "
        "data after the handshake -- every HTTP/3 request, every response, every stream. "
        "These are the keys we export to the preferred server.",
        body
    ))

    elements.append(Paragraph(
        "The application traffic secrets are what we transfer in our 445-byte migration state. "
        "Everything in this section is critical to understanding the migration.",
        warning_style
    ))

    elements.append(Paragraph("Step 1: Derive Master Secret", h2))
    elements.append(code_block(
        "// Continue the key schedule from the handshake secret\n"
        "derived_secret_2 = HKDF-Expand-Label(handshake_secret, \"derived\", \"\", 32)\n"
        "\n"
        "// Master secret -- no more DH input (IKM = 0)\n"
        "master_secret = HKDF-Extract(\n"
        "  salt = derived_secret_2,\n"
        "  IKM  = 0x00...00  (32 zero bytes)\n"
        ")\n"
        "= 0x[32 bytes]"
    ))

    elements.append(Paragraph("Step 2: Derive Application Traffic Secrets", h2))
    elements.append(code_block(
        "// Transcript now includes the FULL handshake\n"
        "transcript_hash = SHA-256(ClientHello || ... || server Finished)\n"
        "\n"
        "client_app_secret_0 = HKDF-Expand-Label(\n"
        "  master_secret,\n"
        "  \"c ap traffic\",       // \"client application traffic\"\n"
        "  transcript_hash,\n"
        "  32                     // 32 bytes for SHA-256 based ciphers\n"
        ")\n"
        "= 0x9e40646ce79a7f9dc05af8889bce6552875afa0b06df0087f792ebb7c17504a5\n"
        "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
        "    THIS IS THE CLIENT APP SECRET -- 32 bytes we export for migration\n"
        "\n"
        "server_app_secret_0 = HKDF-Expand-Label(\n"
        "  master_secret,\n"
        "  \"s ap traffic\",       // \"server application traffic\"\n"
        "  transcript_hash,\n"
        "  32\n"
        ")\n"
        "= 0xa11af9f05531f856ad47116b45a950328204b4f44bfb6b3a4b4f1f3fcb631643\n"
        "    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
        "    THIS IS THE SERVER APP SECRET -- 32 bytes we export for migration"
    ))

    elements.append(Paragraph(
        "These two 32-byte secrets are the crown jewels. With them, you can derive every "
        "key needed to decrypt and encrypt all application data for this connection. "
        "This is what makes server migration possible.",
        highlight_style
    ))

    elements.append(Paragraph("Step 3: Derive AEAD Key, IV, and HP Key", h2))
    elements.append(code_block(
        "From client_app_secret_0 (for decrypting client\u2192server packets):\n"
        "\n"
        "  client_app_key = HKDF-Expand-Label(client_app_secret_0, \"quic key\", \"\", 16)\n"
        "                 = 0xe010a295f0c2864f186b2a7e8fdc9ed7  (16-byte AES key)\n"
        "\n"
        "  client_app_iv  = HKDF-Expand-Label(client_app_secret_0, \"quic iv\",  \"\", 12)\n"
        "                 = 0x0ae7b6b932bc27d786f4bc2b  (12-byte IV)\n"
        "\n"
        "  client_app_hp  = HKDF-Expand-Label(client_app_secret_0, \"quic hp\",  \"\", 16)\n"
        "                 = 0x25a282b9e82f06f21f488917a4fc8f1b  (16-byte HP key)\n"
        "\n"
        "\n"
        "From server_app_secret_0 (for encrypting server\u2192client packets):\n"
        "\n"
        "  server_app_key = HKDF-Expand-Label(server_app_secret_0, \"quic key\", \"\", 16)\n"
        "                 = 0xfd8c7da9de1b2da4d2ef9fd5188922d0  (16-byte AES key)\n"
        "\n"
        "  server_app_iv  = HKDF-Expand-Label(server_app_secret_0, \"quic iv\",  \"\", 12)\n"
        "                 = 0x02f6180e4f4aa456d7e8a389  (12-byte IV)\n"
        "\n"
        "  server_app_hp  = HKDF-Expand-Label(server_app_secret_0, \"quic hp\",  \"\", 16)\n"
        "                 = 0xb7f6f021453e43b0b2c25989d0a31207  (16-byte HP key)"
    ))

    elements.append(Paragraph(
        "Critical insight: We do NOT export these 6 derived keys. We export the 2 traffic "
        "secrets (32 bytes each). The preferred server re-runs HKDF-Expand-Label with the "
        "same labels and gets the EXACT same keys. HKDF is deterministic -- same input always "
        "produces same output.",
        example_style
    ))

    # ══════════════════════════════════════════
    # SECTION 7: KEY UPDATE
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("7. Key Update: How Keys Evolve", h1))
    elements.append(Paragraph(
        "TLS 1.3 supports key updates: either side can request new keys at any time. "
        "This provides forward secrecy even within a single connection -- if keys from "
        "epoch N are compromised, epochs N+1, N+2... remain secure.",
        body
    ))

    elements.append(code_block(
        "Key Update derivation:\n"
        "\n"
        "  client_app_secret_1 = HKDF-Expand-Label(\n"
        "    client_app_secret_0,   // current secret\n"
        "    \"quic ku\",             // \"QUIC key update\"\n"
        "    \"\",\n"
        "    32\n"
        "  )\n"
        "  = 0x[new 32-byte secret]\n"
        "  \u2514\u2500\u2500 derive new AEAD key, IV, HP key (same process as before)\n"
        "\n"
        "  client_app_secret_2 = HKDF-Expand-Label(client_app_secret_1, \"quic ku\", \"\", 32)\n"
        "  client_app_secret_3 = HKDF-Expand-Label(client_app_secret_2, \"quic ku\", \"\", 32)\n"
        "  ... and so on\n"
        "\n"
        "Each generation:\n"
        "  - Epoch increments (3 \u2192 4 \u2192 5 \u2192 ...)\n"
        "  - Old keys are discarded\n"
        "  - Cannot go backwards (can't derive secret_0 from secret_1)"
    ))

    elements.append(Paragraph(
        "This is why we export TWO secrets per direction: the current secret (to derive "
        "current keys) and the next secret (to handle the next key update). If a key update "
        "happens right after migration, the preferred server is ready.",
        note_style
    ))

    # ══════════════════════════════════════════
    # SECTION 8: WHAT WE EXPORT
    # ══════════════════════════════════════════
    elements.append(Paragraph("8. What We Export: The 445 Bytes", h1))
    elements.append(Paragraph(
        "Now we can understand exactly what's in our migration state and why each field "
        "is necessary.",
        body
    ))

    elements.append(Paragraph("8.1 Crypto State (198 bytes)", h2))
    elements.append(make_table(
        ["Field", "Size", "Example Value", "Why Needed"],
        [
            ["Write secret (server\u2192client)", "2+32 = 34 bytes",
             "0x0020 a11af9f05531f856...  ",
             "Re-derive AEAD key + IV + HP for encrypting responses"],
            ["Write next secret", "2+32 = 34 bytes",
             "0x0020 7b4f2e8c9a1d3f5e...",
             "Handle key update after migration"],
            ["Write cipher suite", "2 bytes",
             "0x1301 (TLS_AES_128_GCM_SHA256)",
             "Which algorithm to use for key derivation"],
            ["Write direction", "1 byte",
             "0x01 (Write)",
             "Identifies this as the write direction"],
            ["Write epoch", "4 bytes",
             "0x00000003 (epoch 3 = first app data)",
             "Which key generation we're on"],
            ["Write PN range", "24 bytes",
             "start=0, end=15, min=0",
             "Continue packet numbering without gaps/replays"],
            ["Read secret (client\u2192server)", "34 bytes",
             "0x0020 9e40646ce79a7f9d...",
             "Re-derive AEAD key for decrypting client packets"],
            ["Read next secret", "34 bytes",
             "0x0020 3c8b1d4e7f2a9085...",
             "Handle key update from client side"],
            ["Read cipher + dir + epoch + PNs", "29 bytes",
             "(same structure as write)",
             "Mirror of write crypto for read direction"],
        ],
        col_widths=[1.5*inch, 0.9*inch, 1.6*inch, 2.1*inch],
    ))

    elements.append(Paragraph("8.2 Connection IDs (194 bytes)", h2))
    elements.append(code_block(
        "Local CIDs (what we issued to the client -- 8 CIDs typical):\n"
        "  Count: 0x0008\n"
        "  CID 0: seqno=0x0000000000000000 len=0x000A data=0x7f8a3c1b9e2d4f06a5c8\n"
        "  CID 1: seqno=0x0000000000000001 len=0x000A data=0x3b7e9d2f1c8a4506e7b3\n"
        "  ... (6 more)\n"
        "\n"
        "Why: The client uses these CIDs to address packets to us.\n"
        "     Preferred server must recognize them as valid.\n"
        "\n"
        "Remote CIDs (what the client issued to us -- typically 1):\n"
        "  Count: 0x0001\n"
        "  CID 0: seqno=0x0000000000000000 len=0x000A data=0x2c5f8b1a7d3e9046c8a2\n"
        "\n"
        "Why: We use this CID in our packet headers so the client\n"
        "     recognizes our packets as belonging to this connection."
    ))

    elements.append(Paragraph("8.3 Client Address (7 bytes for IPv4)", h2))
    elements.append(code_block(
        "Address type: 0x04 (IPv4)\n"
        "IP address:   0x8DD9A87F  = 141.217.168.127\n"
        "Port:         0xC350      = 50000\n"
        "\n"
        "Why: The preferred server needs to know WHERE to send packets.\n"
        "     Without this, it doesn't know the client's IP:port."
    ))

    elements.append(Paragraph("8.4 Complete Binary Layout", h2))
    elements.append(code_block(
        "Offset  Bytes  Field\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "0x000   4      Magic: \"MIGR\" (0x4D494752)\n"
        "0x004   4      QUIC Version: 0x00000001\n"
        "0x008   34     Write traffic secret\n"
        "0x02A   34     Write next secret\n"
        "0x04C   2      Write cipher suite\n"
        "0x04E   1      Write direction\n"
        "0x04F   4      Write epoch\n"
        "0x053   8      Write used_pn_start\n"
        "0x05B   8      Write used_pn_end\n"
        "0x063   8      Write min_pn\n"
        "0x06B   99     Read crypto (same structure)\n"
        "0x0CE   2      Local CID count\n"
        "0x0D0   160    Local CIDs (8 \u00d7 20 bytes each)\n"
        "0x170   2      Remote CID count\n"
        "0x172   20     Remote CIDs (1 \u00d7 20 bytes)\n"
        "0x186   1      Address type (4=IPv4)\n"
        "0x187   4      Client IP address\n"
        "0x18B   2      Client port\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "0x18D = 397 bytes  (minimum, with 8+1 CIDs, IPv4)\n"
        "\n"
        "Note: Actual size varies with CID count and IP version.\n"
        "Our typical case: ~445 bytes with 8 local + 1 remote CID on IPv4."
    ))

    # ══════════════════════════════════════════
    # SECTION 9: THE IMPORT PROCESS
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("9. Import on the Preferred Server: Reconstructing Keys", h1))
    elements.append(Paragraph(
        "The preferred server receives 445 bytes via TCP/Redis/HTTP. Here's exactly what "
        "happens to reconstruct a fully functional QUIC connection:",
        body
    ))

    elements.append(Paragraph("Step 1: Deserialize the binary state", h2))
    elements.append(code_block(
        "Parse 445 bytes:\n"
        "  \u2514\u2500 Verify magic = \"MIGR\"\n"
        "  \u2514\u2500 Read QUIC version\n"
        "  \u2514\u2500 Extract write_secret_bytes = [32 bytes]\n"
        "  \u2514\u2500 Extract write_next_secret_bytes = [32 bytes]\n"
        "  \u2514\u2500 Extract read_secret_bytes = [32 bytes]\n"
        "  \u2514\u2500 Extract read_next_secret_bytes = [32 bytes]\n"
        "  \u2514\u2500 Extract CIDs, client address, etc."
    ))

    elements.append(Paragraph("Step 2: Reconstruct NSS SymKey objects from raw bytes", h2))
    elements.append(code_block(
        "// Raw bytes \u2192 NSS internal key object\n"
        "write_secret = hkdf::import_key(TLS_VERSION_1_3, &write_secret_bytes)\n"
        "\n"
        "// What import_key does internally:\n"
        "//   1. Allocates an NSS PK11SymKey structure\n"
        "//   2. Copies the 32 raw bytes into NSS's key storage\n"
        "//   3. Tags it as an HKDF key for TLS 1.3\n"
        "//   4. Returns a SymKey handle\n"
        "\n"
        "// This SymKey is now IDENTICAL to the one the primary server had\n"
        "// Same bytes = same key = same derivation results"
    ))

    elements.append(Paragraph("Step 3: Re-derive AEAD and HP keys (deterministic!)", h2))
    elements.append(code_block(
        "// This is the critical step -- HKDF is deterministic\n"
        "\n"
        "// On the PRIMARY server during handshake:\n"
        "  HKDF-Expand-Label(secret_0xa11af9f0..., \"quic key\", 16)\n"
        "  = 0xfd8c7da9de1b2da4d2ef9fd5188922d0\n"
        "\n"
        "// On the PREFERRED server during import:\n"
        "  HKDF-Expand-Label(secret_0xa11af9f0..., \"quic key\", 16)\n"
        "  = 0xfd8c7da9de1b2da4d2ef9fd5188922d0   \u2190 IDENTICAL!\n"
        "\n"
        "// Same for IV:\n"
        "  Both: HKDF-Expand-Label(secret, \"quic iv\", 12) = 0x02f6180e4f4aa456d7e8a389\n"
        "\n"
        "// Same for HP:\n"
        "  Both: HKDF-Expand-Label(secret, \"quic hp\", 16) = 0xb7f6f021453e43b0b2c25989d0a31207\n"
        "\n"
        "// The preferred server now has byte-identical AEAD and HP keys\n"
        "// It CAN decrypt packets from the client\n"
        "// It CAN encrypt packets back to the client"
    ))

    elements.append(Paragraph(
        "This is the fundamental principle: HKDF is a deterministic function. "
        "Same secret + same label + same length = ALWAYS the same output. "
        "The preferred server never did the TLS handshake, never saw the Diffie-Hellman "
        "exchange, never verified the certificate -- but it has identical encryption keys.",
        highlight_style
    ))

    elements.append(Paragraph("Step 4: Set up the connection state", h2))
    elements.append(code_block(
        "On the preferred server:\n"
        "  conn.state = State::Confirmed     // Skip handshake entirely\n"
        "  conn.version = QUIC_V1\n"
        "  conn.write_crypto = re-derived write keys\n"
        "  conn.read_crypto = re-derived read keys\n"
        "  conn.local_cids = [8 imported CIDs]\n"
        "  conn.remote_cids = [1 imported CID]\n"
        "  conn.path = client_addr:port \u2194 local_addr:port\n"
        "  conn.next_pn = used_pn_end       // Continue packet numbering\n"
        "\n"
        "The connection object looks as if the handshake happened locally.\n"
        "The preferred server can now:\n"
        "  1. Decrypt PATH_CHALLENGE from client (using read keys)\n"
        "  2. Encrypt PATH_RESPONSE back to client (using write keys)\n"
        "  3. Handle all subsequent data exchange"
    ))

    # ══════════════════════════════════════════
    # SECTION 10: END-TO-END EXAMPLE
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("10. End-to-End Example: What Actually Happens", h1))
    elements.append(Paragraph(
        "Let's trace a complete connection from Firefox connecting to our primary server "
        "through migration to the preferred server, showing the keys at each step.",
        body
    ))

    elements.append(Paragraph("Step 1: Firefox sends Initial packet", h2))
    elements.append(code_block(
        "Firefox \u2192 Primary (141.217.168.152:4433)\n"
        "\n"
        "QUIC Long Header:\n"
        "  Version: 0x00000001 (QUIC v1)\n"
        "  DCID: 0x7f8a3c1b9e2d4f06  (random, 8 bytes)\n"
        "  SCID: 0xa5c83b7e           (Firefox's CID, 4 bytes)\n"
        "\n"
        "Encrypted with Initial keys derived from DCID:\n"
        "  initial_secret = HKDF-Extract(QUIC_v1_salt, 0x7f8a3c1b9e2d4f06)\n"
        "  client_initial_secret = HKDF-Expand-Label(initial_secret, \"client in\")\n"
        "  client_key = HKDF-Expand-Label(client_initial_secret, \"quic key\")\n"
        "\n"
        "Payload (decryptable by anyone!):\n"
        "  CRYPTO frame containing TLS ClientHello:\n"
        "    - SNI: 141.217.168.152\n"
        "    - ALPN: h3\n"
        "    - Key Share: X25519 public key (32 bytes)\n"
        "    - Supported Versions: TLS 1.3"
    ))

    elements.append(Paragraph("Step 2: Primary server responds with handshake + preferred_address", h2))
    elements.append(code_block(
        "Primary \u2192 Firefox\n"
        "\n"
        "ServerHello (in Initial packet, Initial keys):\n"
        "  - Key Share: server's X25519 public key\n"
        "  - Cipher Suite: TLS_AES_128_GCM_SHA256 (0x1301)\n"
        "\n"
        "  Both sides now compute:\n"
        "    shared_secret = X25519(my_private, their_public)\n"
        "    \u2192 handshake_secret \u2192 handshake keys\n"
        "\n"
        "EncryptedExtensions (in Handshake packet, Handshake keys):\n"
        "  QUIC Transport Parameters:\n"
        "    - preferred_address: 141.217.168.143:4433  \u2190 PREFERRED SERVER!\n"
        "    - preferred_address_cid: 0x3b7e9d2f1c...\n"
        "    - max_idle_timeout: 30000\n"
        "    - initial_max_data: 1048576\n"
        "    - (other transport params...)\n"
        "\n"
        "Certificate + CertificateVerify + Finished (Handshake keys)\n"
        "\n"
        "  After Finished exchange:\n"
        "    \u2192 master_secret\n"
        "    \u2192 client_app_secret = 0x9e40646ce79a7f9d...\n"
        "    \u2192 server_app_secret = 0xa11af9f05531f856...\n"
        "    Switch to Application keys (Epoch 3)"
    ))

    elements.append(Paragraph("Step 3: Primary exports migration state", h2))
    elements.append(code_block(
        "Primary server calls export_migration_state():\n"
        "\n"
        "  write_crypto.export_for_migration():\n"
        "    secret_bytes = self.secret.key_data()\n"
        "                 = [0xa1, 0x1a, 0xf9, 0xf0, 0x55, 0x31, ... ]  (32 bytes)\n"
        "    next_secret  = self.next_secret.key_data()\n"
        "                 = [0x7b, 0x4f, 0x2e, 0x8c, 0x9a, 0x1d, ... ]  (32 bytes)\n"
        "    cipher       = 0x1301  (TLS_AES_128_GCM_SHA256)\n"
        "    epoch        = 3\n"
        "    used_pn      = 0..15  (sent packets 0 through 14)\n"
        "\n"
        "  read_crypto.export_for_migration():\n"
        "    secret_bytes = [0x9e, 0x40, 0x64, 0x6c, 0xe7, 0x9a, ... ]  (32 bytes)\n"
        "    next_secret  = [0x3c, 0x8b, 0x1d, 0x4e, 0x7f, 0x2a, ... ]  (32 bytes)\n"
        "    used_pn      = 0..3   (received packets 0 through 2)\n"
        "\n"
        "  Serialize to 445 bytes with \"MIGR\" header"
    ))

    elements.append(Paragraph("Step 4: State transfer (TCP push to preferred server)", h2))
    elements.append(code_block(
        "Primary (141.217.168.152) \u2500\u2500TCP:9999\u2500\u2500\u2192 Preferred (141.217.168.143)\n"
        "\n"
        "  Send: [4 bytes length] [445 bytes migration state]\n"
        "\n"
        "  Time: < 1ms on LAN\n"
        "\n"
        "  The 445 bytes contain:\n"
        "    Bytes 0-7:     MIGR + version\n"
        "    Bytes 8-105:   Write crypto (secret + next + cipher + epoch + PNs)\n"
        "    Bytes 106-203: Read crypto  (same structure)\n"
        "    Bytes 204-365: Local CIDs   (8 CIDs)\n"
        "    Bytes 366-385: Remote CIDs  (1 CID)\n"
        "    Bytes 386-392: Client addr  (IPv4 + port)"
    ))

    elements.append(PageBreak())
    elements.append(Paragraph("Step 5: Preferred server imports state and rebuilds keys", h2))
    elements.append(code_block(
        "Preferred server receives 445 bytes, calls new_from_migration():\n"
        "\n"
        "  // Reconstruct write keys (for server\u2192client)\n"
        "  write_secret = hkdf::import_key(TLS_1_3, [0xa1, 0x1a, 0xf9, ...])\n"
        "  write_aead   = Aead::new(TLS_1_3, AES_128_GCM, write_secret, \"quic \")\n"
        "    internally:\n"
        "      key = HKDF-Expand-Label(write_secret, \"quic key\", 16)\n"
        "          = 0xfd8c7da9de1b2da4d2ef9fd5188922d0  \u2190 IDENTICAL to primary\n"
        "      iv  = HKDF-Expand-Label(write_secret, \"quic iv\",  12)\n"
        "          = 0x02f6180e4f4aa456d7e8a389            \u2190 IDENTICAL to primary\n"
        "  write_hp = hp::Key::extract(TLS_1_3, AES_128_GCM, write_secret, \"quic hp\")\n"
        "           = 0xb7f6f021453e43b0b2c25989d0a31207  \u2190 IDENTICAL to primary\n"
        "\n"
        "  // Reconstruct read keys (for client\u2192server)\n"
        "  read_secret = hkdf::import_key(TLS_1_3, [0x9e, 0x40, 0x64, ...])\n"
        "  read_aead   = Aead::new(...)\n"
        "  read_hp     = hp::Key::extract(...)\n"
        "  // All IDENTICAL to what the primary server had\n"
        "\n"
        "  // Set up connection\n"
        "  conn.state = Confirmed\n"
        "  conn.path  = 141.217.168.127:50000 \u2194 0.0.0.0:4433\n"
        "  conn.local_cids  = [8 CIDs from migration state]\n"
        "  conn.remote_cids = [1 CID from migration state]\n"
        "\n"
        "  // Ready to handle packets!"
    ))

    elements.append(Paragraph("Step 6: Firefox sends PATH_CHALLENGE (migration validation)", h2))
    elements.append(code_block(
        "Firefox \u2192 Preferred (141.217.168.143:4433)\n"
        "\n"
        "Firefox follows RFC 9000 Section 9.6:\n"
        "  \"When the client receives preferred_address, it SHOULD initiate\n"
        "   path validation to the preferred address.\"\n"
        "\n"
        "QUIC Short Header:\n"
        "  DCID: 0x3b7e9d2f1c8a4506e7b3  (one of our local CIDs)\n"
        "  Packet Number: 3 (encrypted with HP key)\n"
        "\n"
        "Encrypted with client_app_key + nonce(IV XOR PN=3):\n"
        "  Payload: PATH_CHALLENGE frame\n"
        "    data: 0x4a8b2c9d1e7f3a06  (random 8 bytes)\n"
        "\n"
        "Preferred server decrypts:\n"
        "  1. Remove HP: use read_hp_key to recover packet number\n"
        "  2. Compute nonce = read_iv XOR 3\n"
        "  3. AEAD-Decrypt(read_key, nonce, header, ciphertext)\n"
        "  4. Parse: PATH_CHALLENGE { data: 0x4a8b2c9d1e7f3a06 }\n"
        "  \u2713 Decryption succeeds! Keys are correct."
    ))

    elements.append(Paragraph("Step 7: Preferred server sends PATH_RESPONSE", h2))
    elements.append(code_block(
        "Preferred \u2192 Firefox (141.217.168.127:50000)\n"
        "\n"
        "QUIC Short Header:\n"
        "  DCID: 0xa5c83b7e  (Firefox's CID from remote_cids)\n"
        "  Packet Number: 15 (continuing from primary's used_pn_end)\n"
        "\n"
        "Encrypted with server_app_key + nonce(IV XOR PN=15):\n"
        "  Payload: PATH_RESPONSE frame\n"
        "    data: 0x4a8b2c9d1e7f3a06  (echo back the SAME 8 bytes)\n"
        "\n"
        "Firefox receives and decrypts:\n"
        "  1. Uses its server_app_key to decrypt\n"
        "  2. Sees PATH_RESPONSE with matching data\n"
        "  3. Path validation SUCCEEDS\n"
        "  4. Firefox switches to using 141.217.168.143:4433\n"
        "  \u2713 Migration complete! Firefox is unaware a different machine responded."
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "The entire migration is invisible to Firefox. It received a PATH_RESPONSE encrypted "
        "with keys that only the legitimate server should know. From Firefox's perspective, "
        "the server simply moved to a new address (as advertised in preferred_address). "
        "It has no way to know that a completely different physical machine generated that response.",
        highlight_style
    ))

    # ══════════════════════════════════════════
    # SECTION 11: WHY NOT EXPORT THE DERIVED KEYS DIRECTLY?
    # ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("11. Why Export the Secret, Not the Derived Keys?", h1))
    elements.append(Paragraph(
        "A natural question: why not just export the 6 derived keys (2 AEAD + 2 IV + 2 HP = "
        "88 bytes) instead of the 2 secrets (64 bytes)?",
        body
    ))

    elements.append(make_table(
        ["Approach", "Size", "Pro", "Con"],
        [
            ["Export 2 secrets", "64 bytes (+ next secrets = 128)",
             "Supports key update on preferred server",
             "Must re-derive 6 keys (fast, ~microseconds)"],
            ["Export 6 derived keys", "88 bytes",
             "No re-derivation needed",
             "Cannot do key update! No secret to derive next generation"],
        ],
        col_widths=[1.3*inch, 1.5*inch, 1.8*inch, 1.5*inch],
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "We export the secrets because the preferred server needs to support key updates. "
        "If the client requests a key update after migration, the preferred server must derive "
        "new keys from the current secret. Without the secret, it's stuck on the current keys forever.",
        body
    ))

    elements.append(Paragraph(
        "Additionally, NSS (the crypto library) constructs AEAD and HP objects from the "
        "secret during initialization. There's no API to import raw AEAD keys -- you must "
        "provide the secret and let NSS derive the keys internally.",
        note_style
    ))

    # ══════════════════════════════════════════
    # SECTION 12: SECURITY IMPLICATIONS
    # ══════════════════════════════════════════
    elements.append(Paragraph("12. Security Implications of Secret Export", h1))
    elements.append(Paragraph(
        "Exporting TLS traffic secrets has serious security implications. Understanding these "
        "is essential for evaluating the migration approach.",
        body
    ))

    sec_points = [
        "<b>The 32-byte secret IS the connection:</b> Anyone with this secret can decrypt "
        "all past and future packets (until key update). There's no additional authentication.",

        "<b>Forward secrecy is preserved up to the export point:</b> The handshake used ECDHE, "
        "so compromising the server's long-term certificate key doesn't reveal the traffic "
        "secret. But the traffic secret itself must be protected during transfer.",

        "<b>Transfer channel security is critical:</b> The TCP/Redis/HTTP channel carrying "
        "the 445 bytes must be secured. In our demo (same LAN), we use plaintext TCP. "
        "In production, this MUST be encrypted (mTLS, TLS, encrypted Redis).",

        "<b>Our 5 backends have different security profiles:</b><br/>"
        "- TCP Push: secret transits the network (encrypt the channel!)<br/>"
        "- Redis KV: secret stored temporarily in Redis (encrypt at rest!)<br/>"
        "- Redis Pub/Sub: secret transits Redis (encrypt the channel!)<br/>"
        "- HTTP Pull: secret stays in primary's memory until pulled (best security!)<br/>"
        "- File: secret written to disk (worst security!)",

        "<b>QUIC-Exfil attack:</b> This same mechanism enables data exfiltration. "
        "A malicious server can migrate connections to an attacker-controlled machine. "
        "The client can't distinguish this from legitimate migration.",
    ]
    for item in sec_points:
        elements.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

    # ══════════════════════════════════════════
    # SECTION 13: SUMMARY
    # ══════════════════════════════════════════
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("13. Summary: The Complete Key Lifecycle", h1))

    elements.append(code_block(
        "CLIENT                            PRIMARY SERVER              PREFERRED SERVER\n"
        "  |                                    |                            |\n"
        "  |--- Initial (DCID keys) ---------->|                            |\n"
        "  |<-- Initial + ServerHello ---------|                            |\n"
        "  |                                    |                            |\n"
        "  |    [ECDHE shared secret computed]  |                            |\n"
        "  |                                    |                            |\n"
        "  |--- Handshake (HS keys) ---------->|                            |\n"
        "  |<-- Handshake (cert, finished) ----|                            |\n"
        "  |                                    |                            |\n"
        "  |    [Master secret derived]         |                            |\n"
        "  |    [App traffic secrets derived]   |                            |\n"
        "  |                                    |                            |\n"
        "  |<== Application data (App keys) ==>|                            |\n"
        "  |                                    |                            |\n"
        "  |                                    |--[445 bytes via TCP]------>|\n"
        "  |                                    |  (2 secrets + CIDs + addr) |\n"
        "  |                                    |                            |\n"
        "  |                                    |            [Re-derive keys]|\n"
        "  |                                    |            [IDENTICAL keys]|\n"
        "  |                                    |                            |\n"
        "  |--- PATH_CHALLENGE (App keys) -----|----------------------------->|\n"
        "  |<-- PATH_RESPONSE (App keys) ------|-----------------------------|\n"
        "  |                                    |                            |\n"
        "  |<============ Application data (App keys) =====================>|\n"
        "  |                                                                 |\n"
        "  |    Firefox thinks it's the same server, just at a new address   |"
    ))

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "The entire security of QUIC rests on the traffic secrets derived from the TLS 1.3 "
        "handshake. By exporting just 64 bytes of secrets (+ 381 bytes of connection metadata), "
        "we transfer the complete ability to communicate with the client. The preferred server "
        "reconstructs byte-identical keys through deterministic HKDF derivation. "
        "The client cannot tell the difference.",
        highlight_style
    ))

    # Build
    doc.build(elements)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()

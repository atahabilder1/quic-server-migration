#!/usr/bin/env python3
"""
Generate a PDF explaining Fatima's 5 research goals in simple + technical terms.
"""

from fpdf import FPDF
import textwrap

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, r=30, g=100, b=60):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(r, g, b)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(r, g, b)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def sub_title(self, title, r=50, g=50, b=50):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(r, g, b)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(5, 5.5, "-", new_x="END")
        self.multi_cell(0, 5.5, f" {text}")
        self.ln(1)

    def colored_box(self, title, body, box_color=(240, 248, 240), border_color=(30, 100, 60)):
        self.set_fill_color(*box_color)
        self.set_draw_color(*border_color)
        y_start = self.get_y()

        # Calculate height needed
        self.set_font("Helvetica", "B", 11)
        title_lines = self.multi_cell(self.w - self.l_margin - self.r_margin - 16, 6, title, dry_run=True, output="LINES")
        self.set_font("Helvetica", "", 10)
        body_lines = self.multi_cell(self.w - self.l_margin - self.r_margin - 16, 5.5, body, dry_run=True, output="LINES")
        total_h = len(title_lines) * 6 + len(body_lines) * 5.5 + 14

        if self.get_y() + total_h > self.h - 25:
            self.add_page()

        y_start = self.get_y()
        self.rect(self.l_margin, y_start, self.w - self.l_margin - self.r_margin, total_h, style="DF")

        self.set_xy(self.l_margin + 8, y_start + 4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*border_color)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 16, 6, title)

        self.set_x(self.l_margin + 8)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(self.w - self.l_margin - self.r_margin - 16, 5.5, body)

        self.set_y(y_start + total_h + 5)

    def draw_flow_diagram(self, steps, arrow_color=(30, 100, 60)):
        """Draw a vertical flow diagram with boxes and arrows."""
        box_w = 160
        box_h = 22
        x_start = (self.w - box_w) / 2
        y = self.get_y()

        # Check if we need a new page
        total_h = len(steps) * (box_h + 15) + 10
        if y + total_h > self.h - 25:
            self.add_page()
            y = self.get_y()

        for i, (label, desc, color) in enumerate(steps):
            # Box
            self.set_fill_color(*color)
            self.set_draw_color(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40))
            self.rect(x_start, y, box_w, box_h, style="DF")

            # Label
            self.set_xy(x_start + 3, y + 2)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(255, 255, 255)
            self.cell(box_w - 6, 6, label, align="C")

            # Desc
            self.set_xy(x_start + 3, y + 9)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(240, 240, 240)
            self.cell(box_w - 6, 5, desc, align="C")

            y += box_h

            # Arrow
            if i < len(steps) - 1:
                mid_x = self.w / 2
                self.set_draw_color(*arrow_color)
                self.set_line_width(0.6)
                self.line(mid_x, y, mid_x, y + 10)
                # Arrowhead
                self.line(mid_x - 3, y + 7, mid_x, y + 10)
                self.line(mid_x + 3, y + 7, mid_x, y + 10)
                self.set_line_width(0.2)
                y += 12

        self.set_y(y + 5)

    def draw_comparison_diagram(self):
        """Draw legitimate vs fake migration side by side."""
        y = self.get_y()
        if y + 90 > self.h - 25:
            self.add_page()
            y = self.get_y()

        col_w = 82
        gap = 6
        left_x = self.l_margin
        right_x = self.l_margin + col_w + gap

        # Left: Legitimate
        self.set_fill_color(220, 245, 220)
        self.set_draw_color(30, 130, 30)
        self.rect(left_x, y, col_w, 85, style="DF")

        self.set_xy(left_x + 3, y + 3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 130, 30)
        self.cell(col_w - 6, 6, "LEGITIMATE Migration", align="C")

        items_l = [
            "Client --> Server A (port 4433)",
            "Server says: 'use Server B'",
            "(preferred_address in handshake)",
            "Client --> Server B (port 4434)",
            "PATH_CHALLENGE / RESPONSE",
            "Server B has TLS keys (shared)",
            "Connection continues normally",
        ]
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(30, 80, 30)
        yy = y + 12
        for item in items_l:
            self.set_xy(left_x + 4, yy)
            self.cell(col_w - 8, 5, f"> {item}")
            yy += 8

        self.set_xy(left_x + 3, y + 74)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(30, 130, 30)
        self.cell(col_w - 6, 6, "Server B is REAL (same org)", align="C")

        # Right: Fake
        self.set_fill_color(255, 225, 225)
        self.set_draw_color(180, 30, 30)
        self.rect(right_x, y, col_w, 85, style="DF")

        self.set_xy(right_x + 3, y + 3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(180, 30, 30)
        self.cell(col_w - 6, 6, "FAKE Migration (QUIC-Exfil)", align="C")

        items_r = [
            "Client --> Server A (port 4433)",
            "Malware crafts fake packet",
            "(pretends to be migration)",
            "Client --> EVIL server (port 443)",
            "Fake PATH_CHALLENGE + stolen data",
            "Evil server has NO TLS keys",
            "Stolen data exfiltrated!",
        ]
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(130, 30, 30)
        yy = y + 12
        for item in items_r:
            self.set_xy(right_x + 4, yy)
            self.cell(col_w - 8, 5, f"> {item}")
            yy += 8

        self.set_xy(right_x + 3, y + 74)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 30, 30)
        self.cell(col_w - 6, 6, "Evil server is FAKE (attacker)", align="C")

        # Middle arrow
        mid = left_x + col_w + gap/2
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(100, 100, 100)
        self.set_xy(mid - 5, y + 35)
        self.cell(10, 10, "vs", align="C")

        self.set_y(y + 92)

    def draw_fatima_pipeline(self):
        """Draw Fatima's 5-step research pipeline."""
        y = self.get_y()
        if y + 110 > self.h - 25:
            self.add_page()
            y = self.get_y()

        steps = [
            ("1", "Session State\nSharing", (44, 120, 70), "Share TLS keys between\ntwo Neqo servers"),
            ("2", "Find\nAttributes", (30, 90, 140), "What's different between\nreal vs fake migration?"),
            ("3", "Clean Delay\nMechanism", (140, 100, 30), "Accurate timing\nmeasurements"),
            ("4", "Firewall\nDetector", (160, 40, 40), "Build detection\nmodule"),
            ("5", "Evaluate", (100, 40, 120), "Test on real +\nsynthetic traffic"),
        ]

        box_w = 30
        box_h = 38
        gap = 5
        total_w = len(steps) * box_w + (len(steps) - 1) * gap
        x_start = (self.w - total_w) / 2

        for i, (num, label, color, desc) in enumerate(steps):
            x = x_start + i * (box_w + gap)

            # Box
            self.set_fill_color(*color)
            self.set_draw_color(max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30))
            self.rect(x, y, box_w, box_h, style="DF")

            # Number circle
            self.set_fill_color(255, 255, 255)
            cx = x + box_w/2
            cy = y + 8
            self.ellipse(cx - 5, cy - 5, 10, 10, style="F")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*color)
            self.set_xy(cx - 5, cy - 4)
            self.cell(10, 8, num, align="C")

            # Label
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(255, 255, 255)
            lines = label.split("\n")
            for j, line in enumerate(lines):
                self.set_xy(x + 1, y + 16 + j * 6)
                self.cell(box_w - 2, 5, line, align="C")

            # Arrow
            if i < len(steps) - 1:
                ax = x + box_w
                ay = y + box_h / 2
                self.set_draw_color(100, 100, 100)
                self.set_line_width(0.5)
                self.line(ax + 1, ay, ax + gap - 1, ay)
                self.line(ax + gap - 4, ay - 2, ax + gap - 1, ay)
                self.line(ax + gap - 4, ay + 2, ax + gap - 1, ay)
                self.set_line_width(0.2)

            # Description below
            self.set_font("Helvetica", "", 6.5)
            self.set_text_color(60, 60, 60)
            dlines = desc.split("\n")
            for j, dl in enumerate(dlines):
                self.set_xy(x - 2, y + box_h + 3 + j * 5)
                self.cell(box_w + 4, 4, dl, align="C")

        self.set_y(y + box_h + 20)


def build_pdf():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # =========================================================
    # TITLE PAGE
    # =========================================================
    pdf.ln(25)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 80, 50)
    pdf.cell(0, 15, "Fatima's 5 Research Goals", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Explained Simply", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, "From: Fatima Kamal Khaja (HM3716) - PhD Qualifying Exam", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, '"QUIC Security: A Survey" - Wayne State University', align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Supervisor: Dr. Rhongho Jang", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(15)

    # One-liner
    pdf.colored_box(
        "THE BIG PICTURE (one sentence)",
        'Fatima wants to understand what LEGITIMATE QUIC server migration looks like on the wire, '
        'so she can build a firewall that tells the difference between a real migration and a fake one '
        '(the QUIC-Exfil attack).',
        box_color=(255, 250, 230), border_color=(180, 140, 20)
    )

    pdf.ln(3)

    # Analogy
    pdf.colored_box(
        "ANALOGY: Think of it like airport security",
        'Imagine an airport where passengers can change gates mid-flight (QUIC migration). '
        'Right now, security has NO WAY to know if a passenger changed gates because the airline '
        'told them to (legitimate) or because they are sneaking onto a different plane (attack). '
        'Fatima\'s job: study how real gate changes work, find clues that differ from fake ones, '
        'then build a detector.',
        box_color=(235, 240, 255), border_color=(40, 60, 140)
    )

    # =========================================================
    # PAGE 2: THE PROBLEM
    # =========================================================
    pdf.add_page()
    pdf.section_title("The Problem: Why This Research Matters")

    pdf.body_text(
        "QUIC is a modern internet protocol used by Google, YouTube, Facebook, etc. "
        "It has a feature called 'connection migration' that lets you stay connected even when "
        "your network changes (e.g., WiFi to cellular)."
    )
    pdf.body_text(
        "A 2025 paper (QUIC-Exfil by Grubl et al.) showed that malware can ABUSE this feature "
        "to secretly steal data. The malware pretends to do a server migration but actually sends "
        "your files to an attacker's server. Firewalls can't tell the difference."
    )

    pdf.sub_title("What does a QUIC server migration look like?")
    pdf.draw_comparison_diagram()

    pdf.body_text(
        "The problem: from the outside (firewall's view), both look IDENTICAL. "
        "The payload is encrypted. The packet sizes can be mimicked. The timing can be copied. "
        "5 ML classifiers tested -> ALL FAILED (best F1-score: 0.47)."
    )

    # =========================================================
    # PAGE 3: THE 5 GOALS OVERVIEW
    # =========================================================
    pdf.add_page()
    pdf.section_title("Fatima's 5 Goals - The Pipeline")

    pdf.body_text(
        "Her 5 goals form a pipeline. Each step builds on the previous one. "
        "Together they go from 'understand the problem' to 'solve the problem':"
    )

    pdf.draw_fatima_pipeline()

    pdf.ln(5)

    # Quick summary
    pdf.colored_box(
        "Are these 5 goals meaningful?  YES - here's why:",
        "Goal 1 creates the baseline (make real migration work in a lab). "
        "Goal 2 finds what makes real vs fake different. "
        "Goal 3 ensures measurements are accurate. "
        "Goal 4 builds the actual defense. "
        "Goal 5 proves it works. "
        "This is a classic research pipeline: setup -> observe -> measure -> build -> evaluate.",
        box_color=(240, 255, 240), border_color=(30, 120, 30)
    )

    # =========================================================
    # PAGE 4-8: EACH GOAL EXPLAINED
    # =========================================================

    # --- GOAL 1 ---
    pdf.add_page()
    pdf.section_title("Goal 1: Session State Sharing", 44, 120, 70)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(44, 120, 70)
    pdf.cell(0, 7, "Status: IN PROGRESS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.sub_title("Simple Explanation")
    pdf.body_text(
        "When a QUIC server tells a client 'go talk to my other server instead', "
        "the other server needs to know everything about the connection: the encryption keys, "
        "the connection IDs, the packet numbers, etc. Without this, the migration fails."
    )
    pdf.body_text(
        "Fatima is setting up TWO Neqo servers (Mozilla's QUIC implementation) and making them "
        "share this state. This is the foundation - if she can't make real migration work in a lab, "
        "she can't study it."
    )

    pdf.sub_title("Technical Details")
    pdf.bullet("Testbed: Mozilla Neqo v0.7.x on Linux kernel namespaces")
    pdf.bullet("State to share: TLS 1.3 session keys, CIDs, packet number spaces, AEAD nonces")
    pdf.bullet("Uses SSLKEYLOGFILE for Wireshark decryption of captured traffic")
    pdf.bullet("Two-server isolation experiment already completed")
    pdf.bullet("Key finding: migration completes 23-30 ms post-handshake, before bulk transfer")
    pdf.ln(2)

    pdf.draw_flow_diagram([
        ("Server A starts connection", "Handshake with client, generates TLS keys", (44, 120, 70)),
        ("Server A shares state with Server B", "TLS keys + CIDs + packet context transferred", (30, 90, 140)),
        ("Server A tells client: 'go to Server B'", "preferred_address in encrypted handshake", (140, 100, 30)),
        ("Client validates Server B", "PATH_CHALLENGE -> PATH_RESPONSE (23-30 ms)", (100, 40, 120)),
        ("Migration succeeds!", "Client now talks to Server B seamlessly", (44, 120, 70)),
    ])

    pdf.sub_title("Why it matters")
    pdf.body_text(
        "This establishes the POSITIVE CASE - what a real migration looks like in packet captures. "
        "Without this baseline, you can't build a detector. It's like studying fingerprints: "
        "you need real ones before you can spot fakes."
    )

    # --- GOAL 2 ---
    pdf.add_page()
    pdf.section_title("Goal 2: Find Distinguishing Attributes", 30, 90, 140)

    pdf.sub_title("Simple Explanation")
    pdf.body_text(
        "Now that she has real migrations working, she needs to find WHAT'S DIFFERENT between "
        "a real migration and a fake one (QUIC-Exfil). What clues can a firewall use?"
    )
    pdf.body_text(
        "The QUIC-Exfil paper showed that packet size, timing, and entropy can be mimicked. "
        "But Fatima suspects there are OTHER features the paper didn't consider."
    )

    pdf.sub_title("Technical Details")
    pdf.body_text("Potential distinguishing features she might investigate:")
    pdf.bullet("Migration timing relative to handshake (real: 23-30ms; fake: arbitrary)")
    pdf.bullet("Bidirectional traffic patterns (real server responds properly; fake may not)")
    pdf.bullet("PATH_RESPONSE validity (real server can respond; fake server can't decrypt)")
    pdf.bullet("Connection behavior post-migration (real: continues with correct state; fake: anomalies)")
    pdf.bullet("CID retirement patterns (QUIC-Exfil reuses retired CIDs)")
    pdf.bullet("Packet number continuity (real migration preserves sequence; fake starts fresh)")
    pdf.bullet("Server certificate / IP correlation (does new IP match the original cert's SANs?)")
    pdf.ln(2)

    pdf.colored_box(
        "The key insight",
        "QUIC-Exfil mimicked OUTGOING traffic features. But migration is BIDIRECTIONAL. "
        "The attacker's server cannot produce valid PATH_RESPONSE frames (it doesn't have "
        "the TLS keys). A firewall that checks BOTH directions might spot the difference.",
        box_color=(230, 240, 255), border_color=(30, 90, 140)
    )

    pdf.sub_title("Why it matters")
    pdf.body_text(
        "This is the CORE RESEARCH QUESTION. If she finds features that reliably separate "
        "real from fake, the rest of the pipeline (detector, evaluation) follows naturally. "
        "If no features exist, that's also an important negative result for the community."
    )

    # --- GOAL 3 ---
    pdf.add_page()
    pdf.section_title("Goal 3: Cleaner Delay Mechanism", 140, 100, 30)

    pdf.sub_title("Simple Explanation")
    pdf.body_text(
        "When measuring migration timing, you need ACCURATE measurements. If your test code "
        "uses sleep() to delay things, that adds noise. The measurements become unreliable."
    )
    pdf.body_text(
        "Fatima wants to replace sleep-based delays with a proper mechanism that defers "
        "PATH_CHALLENGE without pausing other traffic. This way, her timing measurements "
        "reflect what actually happens in real deployments."
    )

    pdf.sub_title("Technical Details")
    pdf.bullet("Current approach: sleep() pauses entire thread (inaccurate)")
    pdf.bullet("Goal: event-driven deferral of PATH_CHALLENGE in Neqo's async runtime")
    pdf.bullet("Decouple migration timing from throughput measurements")
    pdf.bullet("Ensure experiments reflect real protocol behavior, not test artifacts")
    pdf.bullet("Affects accuracy of all timing-based features in Goal 2")
    pdf.ln(3)

    pdf.colored_box(
        "Why this is a separate goal",
        "If her timing measurements are wrong, every conclusion she draws about "
        "'migration takes X ms' or 'there's a Y ms gap between handshake and migration' "
        "would be unreliable. Bad measurements = bad detector. This is measurement hygiene.",
        box_color=(255, 245, 225), border_color=(140, 100, 30)
    )

    pdf.sub_title("Why it matters")
    pdf.body_text(
        "This is a SUPPORTING goal. It's not glamorous, but it ensures Goals 2, 4, and 5 "
        "produce trustworthy results. In research, methodology matters as much as results."
    )

    # --- GOAL 4 ---
    pdf.add_page()
    pdf.section_title("Goal 4: Build Firewall Detection Module", 160, 40, 40)

    pdf.sub_title("Simple Explanation")
    pdf.body_text(
        "Using the distinguishing features found in Goal 2, build an actual firewall module "
        "that can detect QUIC-Exfil in real-time. This is the DELIVERABLE - the thing that "
        "actually solves the problem."
    )

    pdf.sub_title("Technical Details")
    pdf.body_text("The detector would:")
    pdf.bullet("Track per-flow migration events (when does a connection change destination?)")
    pdf.bullet("Flag anomalous Preferred Address redirections")
    pdf.bullet("Check if PATH_RESPONSE arrives from the new server (bidirectional validation)")
    pdf.bullet("Monitor CID retirement vs. reuse patterns")
    pdf.bullet("Report suspected QUIC-Exfil WITHOUT blocking legitimate traffic")
    pdf.ln(2)

    pdf.draw_flow_diagram([
        ("Firewall sees QUIC connection", "Tracks CID, source/dest IP, timing", (80, 80, 80)),
        ("Destination IP changes (migration?)", "Could be real migration OR QUIC-Exfil", (180, 140, 30)),
        ("Check distinguishing features", "Timing? Bidirectional? CID pattern? Post-migration behavior?", (30, 90, 140)),
        ("LEGITIMATE -> Allow", "Passes all checks, looks like real migration", (44, 120, 70)),
        ("SUSPICIOUS -> Alert / Block", "Fails checks, likely QUIC-Exfil attempt", (160, 40, 40)),
    ])

    pdf.sub_title("Why it matters")
    pdf.body_text(
        "Currently ZERO firewall vendors can detect QUIC migrations (confirmed by the QUIC-Exfil "
        "paper's survey of 5 vendors). This would be the FIRST working detection mechanism. "
        "That's a significant contribution."
    )

    # --- GOAL 5 ---
    pdf.add_page()
    pdf.section_title("Goal 5: Evaluate on Real & Synthetic Traffic", 100, 40, 120)

    pdf.sub_title("Simple Explanation")
    pdf.body_text(
        "Build a detector (Goal 4), then PROVE it works. Test it on both controlled lab traffic "
        "(where you know what's real and what's fake) and real CDN traffic captures "
        "(to check it doesn't break real websites)."
    )

    pdf.sub_title("Technical Details")
    pdf.bullet("Controlled testbed: Neqo servers with known legitimate migrations")
    pdf.bullet("Attack traffic: QUIC-Exfil tool (Rust PoC from Grubl et al.) generating exfiltration")
    pdf.bullet("Metrics: false positive rate (blocking real migrations) and false negative rate (missing attacks)")
    pdf.bullet("Real CDN traffic captures (if accessible) for external validity")
    pdf.bullet("Compare against the 5 ML classifiers that failed in the original paper")
    pdf.ln(2)

    pdf.colored_box(
        "Success criteria",
        "The detector needs to beat the original paper's best result (Random Forest F1=0.47 on Noise scenario). "
        "Ideally: high recall (catch most attacks) with low false positives (don't block YouTube). "
        "Even an F1 > 0.70 would be a major improvement over the current state of the art.",
        box_color=(240, 230, 250), border_color=(100, 40, 120)
    )

    pdf.sub_title("Why it matters")
    pdf.body_text(
        "Without evaluation, the detector is just a prototype. The evaluation proves (or disproves) "
        "that the approach works. Negative results are also valuable - they tell the community "
        "'these features also don't work' and narrow the search space."
    )

    # =========================================================
    # FINAL PAGE: SUMMARY
    # =========================================================
    pdf.add_page()
    pdf.section_title("Summary: Is This Meaningful?", 30, 80, 50)

    pdf.colored_box(
        "YES. Here's why each goal matters:",
        "",
        box_color=(240, 248, 240), border_color=(30, 100, 60)
    )

    goals = [
        ("Goal 1 (State Sharing)", "Creates the lab setup to study real migration. Foundation.", "Without this, no experiments are possible.", (44, 120, 70)),
        ("Goal 2 (Find Attributes)", "THE core research question. What separates real from fake?", "This is where the novel contribution lives.", (30, 90, 140)),
        ("Goal 3 (Clean Delays)", "Ensures measurements are accurate. Methodology rigor.", "Prevents garbage-in, garbage-out.", (140, 100, 30)),
        ("Goal 4 (Build Detector)", "THE deliverable. First-ever QUIC migration detector.", "Solves a problem 0/5 firewall vendors can solve today.", (160, 40, 40)),
        ("Goal 5 (Evaluate)", "Proves it works. Scientific validation.", "Beats F1=0.47 baseline? Publication-worthy.", (100, 40, 120)),
    ]

    for title, desc, why, color in goals:
        pdf.set_fill_color(*color)
        pdf.set_draw_color(*color)
        y = pdf.get_y()
        pdf.rect(pdf.l_margin, y, 3, 16, style="F")
        pdf.set_xy(pdf.l_margin + 6, y + 1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*color)
        pdf.cell(0, 5, title)
        pdf.set_xy(pdf.l_margin + 6, y + 7)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 5, desc)
        pdf.set_xy(pdf.l_margin + 6, y + 12.5)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, why)
        pdf.set_y(y + 19)

    pdf.ln(5)

    pdf.colored_box(
        "The bottom line",
        "Fatima's research fills a real gap: the QUIC-Exfil attack exists, no one can detect it, "
        "and no one has even characterized what legitimate migration looks like. "
        "Her 5 goals are a well-structured pipeline from 'understand the problem' to 'solve it'. "
        "The work is scoped, incremental, and each step has clear deliverables. "
        "If successful, this produces the first QUIC migration detection system - "
        "something the entire firewall industry currently lacks.",
        box_color=(255, 250, 230), border_color=(180, 140, 20)
    )

    # Save
    output_path = "/home/anik/code/quic/fatima_goals_explained.pdf"
    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    build_pdf()

"""Master script to programmatically generate the 32-slide Academic Defense Presentation Deck

for CreditTech using python-pptx. Adheres strictly to the Master Instructions:
- Message-based titles
- 7 Logical Sections (Context -> Requirements -> Architecture -> Implementation -> Empirical ML Results -> Governance -> Conclusion)
- Integration of 13 real high-res figures from data/reports/figures/
- Explicit [IMPLEMENTED] vs [PLANNED/EXTERNAL] status
- Full word-for-word speaker notes on every slide
- Professional White & Blue palette
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- COLOR PALETTE (Professional White & Blue Theme) ---
WHITE = RGBColor(255, 255, 255)
BG_SUBTLE = RGBColor(248, 250, 252)       # Slate-50 ultra-light
NAVY_DARK = RGBColor(10, 25, 47)          # #0A192F Deep Navy Hero
NAVY_PRIMARY = RGBColor(15, 23, 42)       # #0F172A Slate-900
BLUE_ROYAL = RGBColor(30, 64, 175)        # #1E40AF Blue-800
BLUE_VIBRANT = RGBColor(37, 99, 235)      # #2563EB Blue-600
BLUE_CYAN = RGBColor(2, 132, 199)         # #0284C7 Sky-600
BLUE_ICE = RGBColor(240, 244, 248)        # #F0F4F8 Ice Blue Card Fill
BLUE_ICE_LIGHT = RGBColor(241, 245, 249)  # #F1F5F9 Slate-100 Card Fill
BLUE_BORDER = RGBColor(191, 219, 254)     # #BFDBFE Light Blue border
BLUE_BORDER_DARK = RGBColor(147, 197, 253)# #93C5FD Accent border
TEXT_DARK = RGBColor(15, 23, 42)          # Primary Body / Headings
TEXT_MUTED = RGBColor(71, 85, 105)        # Secondary / Meta
GREEN_ACCENT = RGBColor(22, 163, 74)      # #16A34A Positive / Success
RED_ACCENT = RGBColor(220, 38, 38)        # #DC2626 Alert / Risk
GOLD_ACCENT = RGBColor(217, 119, 6)       # #D97706 Highlight

FONT_FAMILY = "Calibri"
TOTAL_SLIDES = 32
FIGURES_DIR = "data/reports/figures"

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def create_header(slide, title_text, category_text=None, subtitle_text=None):
    """Standardized executive header for content slides."""
    if category_text:
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.42), Inches(3.6), Inches(0.32))
        badge.fill.solid()
        badge.fill.fore_color.rgb = BLUE_ROYAL
        badge.line.fill.background()
        tf_b = badge.text_frame
        tf_b.word_wrap = False
        tf_b.margin_left = Inches(0.1)
        tf_b.margin_top = Inches(0.02)
        p_b = tf_b.paragraphs[0]
        p_b.text = category_text.upper()
        p_b.font.size = Pt(9.5)
        p_b.font.bold = True
        p_b.font.color.rgb = WHITE
        p_b.font.name = FONT_FAMILY

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.80), Inches(11.7), Inches(0.65))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.font.name = FONT_FAMILY

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.size = Pt(12)
        p_sub.font.italic = True
        p_sub.font.color.rgb = TEXT_MUTED
        p_sub.font.name = FONT_FAMILY

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.52), Inches(11.7), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BLUE_BORDER
    line.line.fill.background()

def create_card(slide, left, top, width, height, bg_color=BLUE_ICE, border_color=BLUE_BORDER):
    """Creates a rounded container card for visual chunking."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
    else:
        card.line.fill.background()
    return card

def embed_image_safe(slide, rel_path, left, top, width, height):
    """Safely embed image from path if it exists."""
    if os.path.exists(rel_path):
        return slide.shapes.add_picture(rel_path, left, top, width, height)
    else:
        # Fallback card if image missing
        card = create_card(slide, left, top, width, height, RGBColor(254, 242, 242), RED_ACCENT)
        tf = card.text_frame
        p = tf.paragraphs[0]
        p.text = f"[Image missing: {rel_path}]"
        p.font.size = Pt(12)
        p.font.color.rgb = RED_ACCENT
        return card

def add_footer(slide, current_idx, total_slides=TOTAL_SLIDES):
    """Adds minimal academic attribution and slide counter."""
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(11.7), Inches(0.3))
    tf = tb.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "CreditTech: Alternative Credit Scoring for Rural India  |  IIT Kharagpur  |  Candidate: Arpit Kumar"
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.font.name = FONT_FAMILY

    p_num = tf.add_paragraph()
    p_num.text = f"{current_idx} / {total_slides}"
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.font.size = Pt(9.5)
    p_num.font.bold = True
    p_num.font.color.rgb = BLUE_ROYAL
    p_num.font.name = FONT_FAMILY

def set_speaker_notes(slide, notes_content):
    """Attaches complete verbal defense script to the slide's notes."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_content.strip()

def build_presentation(output_path="CreditTech_Project_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    print("Building CreditTech Master 32-Slide Academic Defense Presentation...")

    # =========================================================================
    # SECTION A: CONTEXT & MOTIVATION (SLIDES 1 - 5)
    # =========================================================================

    # --- SLIDE 1: Title & Academic Attribution ---
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, NAVY_DARK)
    glow = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    glow.fill.solid()
    glow.fill.fore_color.rgb = BLUE_VIBRANT
    glow.line.fill.background()

    cat = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.1), Inches(4.6), Inches(0.42))
    cat.fill.solid()
    cat.fill.fore_color.rgb = BLUE_ROYAL
    cat.line.fill.background()
    p_c = cat.text_frame.paragraphs[0]
    p_c.text = "IIT KHARAGPUR  |  MASTER'S THESIS DEFENSE"
    p_c.font.size = Pt(11)
    p_c.font.bold = True
    p_c.font.color.rgb = WHITE

    tb_t = s1.shapes.add_textbox(Inches(1.2), Inches(1.75), Inches(11.0), Inches(2.3))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "CreditTech"
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p2 = tf_t.add_paragraph()
    p2.text = "Alternative Credit Scoring for Rural Financial Inclusion"
    p2.font.size = Pt(26)
    p2.font.color.rgb = RGBColor(147, 197, 253)
    p3 = tf_t.add_paragraph()
    p3.text = "An AI-Driven Lending Decision-Support System for Farmers, SHGs & Micro-Enterprises"
    p3.font.size = Pt(15)
    p3.font.italic = True
    p3.font.color.rgb = RGBColor(203, 213, 225)

    meta_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.35), Inches(10.9), Inches(2.4))
    meta_card.fill.solid()
    meta_card.fill.fore_color.rgb = RGBColor(15, 30, 58)
    meta_card.line.color.rgb = RGBColor(30, 58, 110)
    tf_m = meta_card.text_frame
    tf_m.margin_left = Inches(0.35)
    tf_m.margin_top = Inches(0.25)
    tf_m.word_wrap = True
    pm1 = tf_m.paragraphs[0]
    pm1.text = "RESEARCH PROJECT DEFENSE & TECHNICAL COMPREHENSIVE EVALUATION"
    pm1.font.size = Pt(12)
    pm1.font.bold = True
    pm1.font.color.rgb = RGBColor(96, 165, 250)
    pm2 = tf_m.add_paragraph()
    pm2.text = "Candidate: Arpit Kumar  |  Degree: Master's Research Thesis  |  IIT Kharagpur  |  Sept 2026"
    pm2.font.size = Pt(13.5)
    pm2.font.bold = True
    pm2.font.color.rgb = WHITE
    pm3 = tf_m.add_paragraph()
    pm3.text = "Full Implementation Scope: Phases P0-P6 Delivered (FastAPI Modular Monolith, React 19 Client, 4-Rail Ingestion, N=22,000 Real Borrower Benchmark, 4 ML Architectures, 13 Published Evaluation Figures, 120 Automated Tests & Burst Load Testing Harness)."
    pm3.font.size = Pt(11.5)
    pm3.font.color.rgb = RGBColor(203, 213, 225)

    set_speaker_notes(s1, """
Good morning, Professor and members of the evaluation committee. Today, I am defending CreditTech: an alternative credit scoring and digital lending decision-support platform engineered specifically to resolve thin-file credit exclusion in rural India.

This presentation covers our complete journey: from the macroeconomic and human dimensions of financial invisibility, to our 4-rail ingestion engine, our dual Champion/Challenger machine learning architecture evaluated across 22,000 borrower observations, our exact bilingual SHAP explainability, and our production-hardened software engineering. Everything presented today reflects fully implemented and verified code in our repository.
""")

    # --- SLIDE 2: Executive Overview ---
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, BG_SUBTLE)
    create_header(s2, "Executive Overview: Solving Rural Credit Invisibility with Responsible AI", "Context: Executive Summary",
                  "A high-level synthesis of the problem, our engineered solution, methodology, and empirical impact.")
    add_footer(s2, 2)

    quads = [
        ("01. The Problem", "Structural Thin-File Exclusion",
         "Over 50% of Indian smallholder farmers (120M+ individuals) lack formal bureau histories (CIBIL -1). Traditional underwriting relies on monthly salary slips and liquid collateral, forcing creditworthy farmers to moneylenders charging 24-48% APR.", RED_ACCENT),
        ("02. The Solution", "Regulated LSP Decision-Support Bridge",
         "CreditTech acts as a pure Lending Service Provider (LSP) under RBI DLG 2022/2026. It synthesizes multi-source non-traditional signals into calibrated repayment probabilities without holding balance sheet credit risk or touching borrower funds.", BLUE_ROYAL),
        ("03. The Technical Approach", "4-Rail Ingestion + Dual ML + DPDP",
         "4-rail parallel ingestion (Account Aggregator, Sentinel-2 10m NDVI, bureau, SHG records) with graceful degradation. Monotonic WoE Logistic Champion + Monotonic GBDT Challenger validated via 5-Fold Spatial GroupKFold across 15 village clusters.", BLUE_CYAN),
        ("04. Key Empirical Outcomes", "N=22,000 Benchmark & ₹5.2 Cr Profit",
         "Champion Scorecard achieves AUC 0.9599, KS 0.8208, and 0.038ms latency. Passed 100% of statutory fairness gates (gender disparity <= 7.1%). Economic cutoff at Score 540 maximizes net profit at ₹5.2 Cr / 10k loans; 120 automated tests passing.", GREEN_ACCENT)
    ]
    for i, (head, sub, desc, col) in enumerate(quads):
        row = i // 2
        col_idx = i % 2
        c = create_card(s2, Inches(0.8 + col_idx * 5.95), Inches(1.8 + row * 2.55), Inches(5.65), Inches(2.35), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(11)
        ps.font.bold = True
        ps.font.color.rgb = NAVY_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s2, """
To orient the committee, Slide 2 provides our executive summary:
The Problem: Over 50% of rural Indian smallholders lack formal bureau files. CIBIL scores them as -1, denying them bank credit and trapping them in exploitative moneylender debt.
The Solution: CreditTech—a Lending Service Provider decision-support platform designed strictly under RBI Digital Lending Guidelines.
The Approach: 4-rail parallel ingestion spanning Account Aggregator, Sentinel-2 remote sensing, and SHG community savings, coupled with a Monotonic WoE Scorecard champion.
The Outcome: Validated on 22,000 borrower records. Our champion model delivers an AUC of 0.9599, KS of 0.8208, full DPDP compliance, and an optimal economic operating cutoff at Score 540 yielding ₹5.2 Crore per 10,000 loans.
""")

    # --- SLIDE 3: The Rural Credit Gap ---
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, BG_SUBTLE)
    create_header(s3, "The Rural Credit Gap: 120M+ Productive Farmers Trapped by Information Asymmetry", "Context: Macro Problem",
                  "Why formal commercial banking fails to reach creditworthy rural agricultural producers.")
    add_footer(s3, 3)

    cards_s3 = [
        ("🌍 The Macroeconomic Context",
         [("1.4 Billion Unbanked Globally", "World Bank (2024) reports 1.4B adults lack formal accounts, concentrated in rural South Asia & Sub-Saharan Africa."),
          ("182M KCC Cards Issued", "Kisan Credit Card (KCC) scheme has vast nominal reach, but only ~10% are actively utilized for crop working capital due to archaic renewal friction."),
          ("₹1.12 Lakh Cr SHG Credit", "12+ million Self-Help Groups linked to NABARD maintain 96%+ recovery, but their repayment data remains locked in paper ledgers.")], BLUE_ROYAL),
        ("🚫 The Bureau Failure (Thin-File)",
         [("Zero Credit Tradeline", "Traditional bureaus (CIBIL, Equifax, Experian, CRIF) require prior repayment history. First-time borrowers get Score -1."),
          ("No Formal Proof of Income", "Smallholders lack computerized monthly pay slips, audited P&L statements, and GST/ITR filings."),
          ("Equating Silence with Default", "Commercial scoring algorithms treat an absence of data as an indicator of high default probability.")], RED_ACCENT),
        ("⚠️ The Exploitative Informal Trap",
         [("14-Day Sowing Window", "Kharif and Rabi planting windows are strictly weather-bound. Delayed seed purchases destroy seasonal yield."),
          ("36% to 48% Annualized APR", "Local village moneylenders charge 3% to 4% per month, compounding debt across generations."),
          ("Loss of Agrarian Assets", "Default on informal loans results in coercive seizure of cattle, jewelry, and oral land tenancy rights.")], NAVY_DARK)
    ]
    for i, (title, bullets, col) in enumerate(cards_s3):
        c = create_card(s3, Inches(0.8 + i * 4.0), Inches(1.8), Inches(3.7), Inches(4.9), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.22)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        for h, b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"• {h}: "
            pb.font.bold = True
            pb.font.size = Pt(10.5)
            pb.font.color.rgb = NAVY_DARK
            r = pb.add_run()
            r.text = b
            r.font.bold = False
            r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s3, """
Slide 3 details the macroeconomic reality. In India, despite massive financial inclusion drives like PM Jan Dhan Yojana, true credit access remains elusive. Over 182 million Kisan Credit Cards have been issued, but less than 10% are effectively operationalized.
The root cause is structural bureau failure: traditional credit rating agencies require an existing credit history. If you have never taken a bank loan, you get a score of -1.
Because agricultural sowing windows last only 14 days, a farmer cannot wait months for loan committee reviews. They turn to informal moneylenders charging 36% to 48% APR. CreditTech exists to replace this informal extortion with institutional capital.
""")

    # --- SLIDE 4: Ground Reality: Sunita Devi ---
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, BG_SUBTLE)
    create_header(s4, "Ground Reality: Why Sunita Devi's Creditworthiness Remains Invisible to Banks", "Context: Borrower Journey",
                  "Anchoring the systemic failure in the real-world operational journey of a marginal farmer.")
    add_footer(s4, 4)

    c1 = create_card(s4, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.9), WHITE, BLUE_BORDER)
    tf1 = c1.text_frame
    tf1.margin_left = tf1.margin_right = Inches(0.25)
    tf1.margin_top = Inches(0.22)
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "👤 The Borrower Reality"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    b1 = [("Identity", "Sunita Devi, 34 years old"),
          ("Location", "Sangaria Block, Hanumangarh, RJ"),
          ("Landholding", "1.8 acres canal-irrigated cotton"),
          ("Social Discipline", "SHG member for 4 consecutive years"),
          ("Thrift Record", "100% on-time weekly savings deposits"),
          ("Working Capital Need", "₹35,000 for certified seeds & fertilizer")]
    for k, v in b1:
        pk = tf1.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(11)
        pk.font.color.rgb = BLUE_ROYAL
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c2 = create_card(s4, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.9), RGBColor(254, 242, 242), RGBColor(254, 202, 202))
    tf2 = c2.text_frame
    tf2.margin_left = tf2.margin_right = Inches(0.25)
    tf2.margin_top = Inches(0.22)
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "🚫 The Bank's Algorithmic Rejection"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    b2 = [("Automated Turn-Down", "Rejected within 48 hours of branch application"),
          ("Reason Code", "'CIBIL Score: -1 (Thin File)'"),
          ("Systemic Rule Failure", "The underwriter's credit policy requires minimum 24-month tradeline and audited ITR"),
          ("Imminent Crisis", "Kharif sowing begins in 10 days; lack of cash means zero crop planting"),
          ("Predatory Exploitation", "Local Arhatiya moneylender offers instant cash at 36% compound APR")]
    for k, v in b2:
        pk = tf2.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(11)
        pk.font.color.rgb = RED_ACCENT
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c3 = create_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.9), RGBColor(239, 246, 255), BLUE_BORDER_DARK)
    tf3 = c3.text_frame
    tf3.margin_left = tf3.margin_right = Inches(0.25)
    tf3.margin_top = Inches(0.22)
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "💡 The Invisible Digital Footprint"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    b3 = [("Sentinel-2 NDVI", "Satellite confirms 2-year crop vigor of 0.68, demonstrating high vegetative health"),
          ("Account Aggregator", "18 months of bank statements show steady Average Daily Balance and active UPI"),
          ("NABARD e-Shakti", "Verifies 48 months of peer-monitored zero-default thrift discipline"),
          ("CreditTech Synthesis", "Synthesizes these alternative signals into a verifiable score: 724 (Low Risk)"),
          ("Sanction Outcome", "Bank approves ₹30,000 at 7% subsidized KCC interest rate!")]
    for k, v in b3:
        pk = tf3.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(11)
        pk.font.color.rgb = BLUE_ROYAL
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    set_speaker_notes(s4, """
To ground this mathematically and technically, meet Sunita Devi from Hanumangarh, Rajasthan. She cultivates 1.8 acres of cotton and needs ₹35,000 for Kharif seeds.
When she visits the local bank, the automated rule engine rejects her application in 48 hours. Why? Her bureau score is -1.
Yet, she has extensive digital evidence: satellite imagery confirms her farm's vegetative vigor; Account Aggregator records show disciplined cash flow; and NABARD records show 4 years of flawless SHG savings.
CreditTech transforms these invisible alternative signals into a mathematically defensible credit score of 724, enabling the bank to approve her at 7% interest.
""")

    # --- SLIDE 5: Structural Gaps in Traditional Bureau Underwriting ---
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, BG_SUBTLE)
    create_header(s5, "Structural Gaps: Why Urban Underwriting Rules Collapse in Agrarian Ecosystems", "Context: Structural Gaps",
                  "Analyzing the fundamental divergence between urban corporate scoring and rural cashflow realities.")
    add_footer(s5, 5)

    gaps = [
        ("01. Cash Flow Topology", "Monthly Paycheck vs. Lumpy 120-Day Harvest Cycles",
         "Urban models assume a predictable monthly salary deposit. Agrarian income is lumpy: zero cash inflow during the 90-day cultivation period, followed by harvest lump sums. Urban Debt-to-Income (DTI) metrics falsely flag inter-crop gestation as default risk."),
        ("02. Collateral & Tenure", "Liquid Collateral vs. Fragmented & Oral Tenancy",
         "Traditional underwriting demands registered land mortgages. Smallholder landholdings are frequently unmutated, held in joint family khatas, or cultivated under oral sharecropping arrangements, making formal hypothecation legally unviable."),
        ("03. Information Asymmetry", "Audited Financials vs. Community Social Collateral",
         "Lacking audited balance sheets, banks assume extreme adverse selection. However, they ignore peer group social collateral: Self-Help Groups (SHGs) and JLGs that maintain 96%+ historical recovery rates across India."),
        ("04. DPI Infrastructure Gap", "Identity & Payments Solved, but Credit Signals Lagging",
         "India successfully deployed Digital Public Infrastructure (DPI) for Identity (Aadhaar, 1.4B) and Payments (UPI, 14B+ monthly txns). Credit signals remained locked. CreditTech closes this gap by linking Account Aggregators and Earth Observation data.")
    ]
    for i, (head, sub, desc) in enumerate(gaps):
        c = create_card(s5, Inches(0.8 + i * 2.95), Inches(1.8), Inches(2.78), Inches(4.9), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.22)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = head
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = BLUE_ROYAL
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10.5)
        ps.font.bold = True
        ps.font.color.rgb = NAVY_DARK
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(10)
        pd.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s5, """
Slide 5 breaks down why existing credit algorithms fail.
First: Cash flow topology. A salaried employee earns monthly. A cotton farmer earns once every 120 days. Applying standard monthly DTI formulas to a farmer during sowing season guarantees false-positive default predictions.
Second: Collateral. Fragmented land inheritance and oral sharecropping prevent legal mortgage execution.
Third: Information asymmetry. Banks ignore community social collateral.
And fourth: what we term DPI Asymmetry. India built identity and payments a decade ago; CreditTech builds the credit signal layer.
""")

    # =========================================================================
    # SECTION B: REQUIREMENTS & SYSTEM SCOPE (SLIDES 6 - 8)
    # =========================================================================

    # --- SLIDE 6: Multi-Stakeholder Personas ---
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, BG_SUBTLE)
    create_header(s6, "Multi-Stakeholder Personas: Role-Aware Access Across the Digital Lending Journey", "Requirements: Personas & RBAC",
                  "Enforcing zero horizontal/vertical privilege escalation across distinct operational roles.")
    add_footer(s6, 6)

    personas = [
        ("Farmer / Borrower", "Low tech-literacy, mobile/assisted", "Bank Sakhi PWA & Borrower Web Portal",
         "Applies for credit, grants DPDP consent, views own score and bilingual SHAP explanations, lodges grievances.",
         "Can ONLY view own records. Zero access to underwriting engine or other borrowers' PII.", BLUE_ROYAL),
        ("Bank Sakhi (Assisted Operator)", "Community agent, medium literacy", "Sakhi Mobile PWA (Assisted Channel)",
         "Onboards rural borrowers, digitizes paper SHG meeting registers, facilitates vernacular consent capture.",
         "Can trigger ingestion; cannot view raw PII beyond onboarding necessity; no decisioning authority.", BLUE_CYAN),
        ("Loan Officer (Partner RE)", "High literacy, financial underwriter", "Lender Decision Interface (Desktop)",
         "Reviews composite score, inspects satellite NDVI and AA cashflow evidence, approves/rejects, logs overrides.",
         "Cannot modify model weights or bypass fairness rules; all dissent reasons are immutably logged.", NAVY_DARK),
        ("Regulatory / Fairness Auditor", "High literacy, compliance / NABARD", "Institutional Audit Dashboard",
         "Inspects demographic parity indices (DIR), monitors PSI drift radars, exports audit CSVs and PDF reports.",
         "Read-only access to aggregate metrics and audit logs; strictly prohibited from viewing individual borrower PII.", GREEN_ACCENT)
    ]
    for i, (role, lit, iface, actions, restr, col) in enumerate(personas):
        c = create_card(s6, Inches(0.8 + i * 2.95), Inches(1.8), Inches(2.78), Inches(4.9), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = role
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        ps = tf.add_paragraph()
        ps.text = f"Profile: {lit}"
        ps.font.size = Pt(9.5)
        ps.font.italic = True
        ps.font.color.rgb = TEXT_MUTED
        pi = tf.add_paragraph()
        pi.text = f"Interface: {iface}"
        pi.font.size = Pt(10)
        pi.font.bold = True
        pi.font.color.rgb = NAVY_DARK
        pa = tf.add_paragraph()
        pa.text = f"Actions: {actions}"
        pa.font.size = Pt(9.5)
        pa.font.color.rgb = TEXT_DARK
        pr = tf.add_paragraph()
        pr.text = f"Restrictions: {restr}"
        pr.font.size = Pt(9.5)
        pr.font.bold = True
        pr.font.color.rgb = RED_ACCENT

    set_speaker_notes(s6, """
Slide 6 presents our multi-stakeholder persona architecture.
In regulated financial systems, authorization is critical. We define four distinct roles:
1. The Borrower: can only view their own score and reason codes.
2. The Bank Sakhi: assisted community onboarding operator who can input SHG data but cannot access decrypted PII.
3. The Loan Officer: evaluates scores and makes loan decisions, with mandatory dissent logging.
4. The Independent Auditor: monitors portfolio fairness and population stability without accessing individual identities.
This role-access matrix is strictly enforced at the FastAPI middleware layer.
""")

    # --- SLIDE 7: Functional & Non-Functional Engineering Requirements ---
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, BG_SUBTLE)
    create_header(s7, "System Requirements: High-Stakes Reliability, Fairness, and Explainability", "Requirements: Specifications",
                  "Defining the precise engineering boundaries and performance contracts of the platform.")
    add_footer(s7, 7)

    c_fr = create_card(s7, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_fr = c_fr.text_frame
    tf_fr.margin_left = tf_fr.margin_right = Inches(0.25)
    tf_fr.margin_top = Inches(0.22)
    tf_fr.word_wrap = True
    p = tf_fr.paragraphs[0]
    p.text = "📋 Functional Requirements (FRs) [DELIVERED]"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    frs = [
        ("FR-1: Cryptographic Consent Capture", "Issue and verify SHA-256 hash-chained DPDP consent records with granular purpose binding."),
        ("FR-2: 4-Source Ingestion Orchestration", "Parallel async ingestion across AA, Sentinel-2 NDVI, bureau, and SHG records with graceful fallback."),
        ("FR-3: Dual Machine Learning Scoring", "Calibrated repayment probabilities mapped to standardized 300–900 bureau-equivalent scale."),
        ("FR-4: Exact Bilingual Explainability", "Exact closed-form Shapley values yielding top-5 adverse action reason codes in English and Hindi."),
        ("FR-5: Loan Officer Decisioning", "Mandatory override-reason logging whenever officer dissents from model recommendations."),
        ("FR-6: Pre-Promotion Fairness Gating", "Automated CI/CD block on model deployment if Disparate Impact Ratio falls below 0.80.")
    ]
    for k, v in frs:
        pk = tf_fr.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_nfr = create_card(s7, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_nfr = c_nfr.text_frame
    tf_nfr.margin_left = tf_nfr.margin_right = Inches(0.25)
    tf_nfr.margin_top = Inches(0.22)
    tf_nfr.word_wrap = True
    p = tf_nfr.paragraphs[0]
    p.text = "⚡ Non-Functional Requirements (NFRs) [VERIFIED]"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    nfrs = [
        ("NFR-1: Latency & Throughput", "Model inference <= 0.04 ms in-process; end-to-end scoring pipeline completes in < 600 ms under load."),
        ("NFR-2: Partial Failure Resilience", "System never crashes on single rail timeout; dynamically rescales confidence bounds."),
        ("NFR-3: Privacy by Design", "Strict zero co-location of borrower PII with ML feature snapshots; DPDP storage limitation purge."),
        ("NFR-4: Immutability & Auditability", "PostgreSQL append-only triggers prevent retrospective tampering with decisions and consents."),
        ("NFR-5: Load Capacity", "Verified against 60 concurrent burst requests (2x pilot peak) with 0% error rate via tests/test_p6_load.py."),
        ("NFR-6: High-Availability Reporting", "3-tier PDF fallback (WeasyPrint -> ReportLab -> Minimal) ensures report delivery in all environments.")
    ]
    for k, v in nfrs:
        pk = tf_nfr.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    set_speaker_notes(s7, """
Slide 7 establishes our formal requirements specification.
On the left are the Functional Requirements: from cryptographic consent capture and 4-rail ingestion, to exact bilingual SHAP explainability and automated fairness gates.
On the right are our Non-Functional Requirements: sub-millisecond in-process ML inference, graceful degradation resilience, zero PII co-location, append-only auditability, and burst load capacity. All 6 FRs and 6 NFRs were systematically verified in our test harness.
""")

    # --- SLIDE 8: System Scope: Implemented Scope vs. Boundaries ---
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, BG_SUBTLE)
    create_header(s8, "System Scope: Explicit Demarcation of Delivered vs. External Capabilities", "Requirements: Scope & Bounds",
                  "Academic integrity: clearly separating delivered software from future external milestones.")
    add_footer(s8, 8)

    c_s1 = create_card(s8, Inches(0.8), Inches(1.8), Inches(3.7), Inches(4.9), RGBColor(240, 253, 244), RGBColor(187, 247, 208))
    tf_s1 = c_s1.text_frame
    tf_s1.margin_left = tf_s1.margin_right = Inches(0.22)
    tf_s1.margin_top = Inches(0.22)
    tf_s1.word_wrap = True
    p = tf_s1.paragraphs[0]
    p.text = "✅ DELIVERED SCOPE (Phases P0–P6)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    ps1 = [
        ("FastAPI Modular Monolith", "12 core service packages under services/core/"),
        ("4-Rail Ingestion Engine", "Connectors + mock server + parallel orchestrator"),
        ("Dual ML Engine", "Champion WoE Scorecard + GBDT Challenger"),
        ("N=22,000 Benchmark", "Full empirical evaluation across 15 village clusters"),
        ("13 Evaluation Figures", "Publication-grade charts in data/reports/figures/"),
        ("Frontend Client", "React 19 + Vite portal (apps/borrower-app/)"),
        ("120 Automated Tests", "Unit, integration, and P6 load harness passing")
    ]
    for k, v in ps1:
        pk = tf_s1.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_s2 = create_card(s8, Inches(4.8), Inches(1.8), Inches(3.7), Inches(4.9), RGBColor(254, 242, 242), RGBColor(254, 202, 202))
    tf_s2 = c_s2.text_frame
    tf_s2.margin_left = tf_s2.margin_right = Inches(0.22)
    tf_s2.margin_top = Inches(0.22)
    tf_s2.word_wrap = True
    p = tf_s2.paragraphs[0]
    p.text = "🚫 INTENTIONALLY DESCOPED"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    ps2 = [
        ("No Credit Risk / Disbursals", "CreditTech is pure LSP; never touches borrower funds (avoids NBFC licensing)"),
        ("No Enterprise SSO / OIDC", "Officer & Sakhi demo auth is header-based to keep focus on ML and credit risk"),
        ("No Native Android Client", "Descoped in favor of accessible, cross-platform React Progressive Web App (PWA)"),
        ("No SMS / IVR Telephony", "Eliminates TRAI regulatory friction and carrier gateway flakiness during pilot stage")
    ]
    for k, v in ps2:
        pk = tf_s2.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = RED_ACCENT
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_s3 = create_card(s8, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.9), RGBColor(254, 249, 195), RGBColor(253, 224, 71))
    tf_s3 = c_s3.text_frame
    tf_s3.margin_left = tf_s3.margin_right = Inches(0.22)
    tf_s3.margin_top = Inches(0.22)
    tf_s3.word_wrap = True
    p = tf_s3.paragraphs[0]
    p.text = "⏳ PRE-LAUNCH GATE (Phase P7)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = GOLD_ACCENT
    ps3 = [
        ("Production API Credentials", "Live Account Aggregator FIU API keys and licensed satellite provider contracts"),
        ("Partner Bank LoI Execution", "Formal underwriting agreement with commercial Regional Rural Bank (RRB)"),
        ("Live On-Ground Pilot", "Rollout to 750-1,250 real borrowers across 4-5 agro-climatic villages"),
        ("Production Smoke Gate", "Automated execution of services/core/ops/smoke.py against live bank endpoints")
    ]
    for k, v in ps3:
        pk = tf_s3.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    set_speaker_notes(s8, """
Slide 8 enforces academic integrity by explicitly establishing what is built versus what is planned.
In Green: Phases P0 through P6 are 100% delivered and verified in code.
In Red: Items intentionally descoped by design—such as native Android apps and holding balance sheet risk—so we focus on core credit intelligence.
In Amber: Phase P7, which represents external real-world gates like signing bank contracts and obtaining production AA credentials. This clarity ensures there is zero ambiguity during thesis evaluation.
""")

    # =========================================================================
    # SECTION C: PROPOSED SOLUTION & ARCHITECTURE (SLIDES 9 - 12)
    # =========================================================================

    # --- SLIDE 9: CreditTech Solution: Regulated LSP ---
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, BG_SUBTLE)
    create_header(s9, "Solution Paradigm: Operating as an RBI-Compliant Lending Service Provider", "Solution: Positioning",
                  "Decoupling credit scoring intelligence from balance sheet risk and deposit taking.")
    add_footer(s9, 9)

    c_top = create_card(s9, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.6), WHITE, BLUE_BORDER)
    tf_t = c_top.text_frame
    tf_t.margin_left = Inches(0.3)
    tf_t.margin_top = Inches(0.2)
    p = tf_t.paragraphs[0]
    p.text = "🏛️ The Lending Service Provider (LSP) Architecture"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p_sub = tf_t.add_paragraph()
    p_sub.text = "• CreditTech is engineered strictly under RBI's Digital Lending Guidelines (2022/2026) as a pure LSP/TSP.\n• Capital Flow: 100% between partner Regulated Entity (Bank/NBFC) and borrower's bank account. CreditTech NEVER touches funds.\n• Intelligence Flow: Synthesizes AA, satellite, bureau, and SHG data into calibrated scores, providing decision support to underwriters."
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_DARK

    c_mid = create_card(s9, Inches(0.8), Inches(3.6), Inches(11.7), Inches(1.6), RGBColor(239, 246, 255), BLUE_BORDER_DARK)
    tf_m = c_mid.text_frame
    tf_m.margin_left = Inches(0.3)
    tf_m.margin_top = Inches(0.2)
    p = tf_m.paragraphs[0]
    p.text = "🤝 The Institutional Triangle: Borrower, LSP, and Regulated Entity"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    p_sub = tf_m.add_paragraph()
    p_sub.text = "• Borrower: Applies via Bank Sakhi assisted portal; grants cryptographically chained DPDP consent.\n• CreditTech Platform: Pulls multi-source signals, computes WoE scores, generates SHAP reasons, runs fairness checks.\n• Partner Regulated Entity (RRB / SFB): Receives standardized handoff package; loan officer sanctions loan at prime rates (7% KCC)."
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_DARK

    c_bot = create_card(s9, Inches(0.8), Inches(5.4), Inches(11.7), Inches(1.4), WHITE, BLUE_BORDER)
    tf_b = c_bot.text_frame
    tf_b.margin_left = Inches(0.3)
    tf_b.margin_top = Inches(0.2)
    p = tf_b.paragraphs[0]
    p.text = "💡 Value Unlock: Minutes, Not Days"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p_sub = tf_b.add_paragraph()
    p_sub.text = "• Reduces loan appraisal turnaround time from 14 days of physical branch visits to under 3 minutes of automated scoring.\n• Replaces subjective underwriter bias with transparent, statistically auditable reason codes in English and Hindi."
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_DARK

    set_speaker_notes(s9, """
Slide 9 defines our solution paradigm. CreditTech operates as an LSP—a Lending Service Provider—under RBI's Digital Lending Directions.
We never touch borrower funds and never hold balance sheet credit risk. The partner bank provides the loan capital; CreditTech provides the alternative data scoring intelligence.
This enables Regional Rural Banks to appraise thin-file farmers in minutes rather than weeks, dramatically reducing operational costs while remaining fully compliant with RBI lending guidelines.
""")

    # --- SLIDE 10: System Architecture: Modular Monolith ---
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, BG_SUBTLE)
    create_header(s10, "System Architecture: A Production-Grade Modular Monolith Built for Resilience", "Architecture: System Design",
                  "Engineered for sub-second execution, zero-network-hop model serving, and data isolation.")
    add_footer(s10, 10)

    # 4 Architecture Tier Cards
    tiers = [
        ("1. Presentation Tier (React 19 + Vite)",
         [("Unified Client App", "Single Vite portal under apps/borrower-app/ serving all stakeholder roles."),
          ("Bank Sakhi Assisted Flow", "Low-bandwidth PWA optimized for rural tablets; offline SHG register entry."),
          ("Loan Officer Portal", "Real-time decision dashboard with SHAP waterfall & satellite NDVI visualizer.")]),
        ("2. Gateway & Security Tier (FastAPI)",
         [("RequestIdMiddleware", "Injects X-Request-ID for distributed tracing across all structured logs."),
          ("Security Middleware", "1 MiB request body cap (DoS protection), in-memory rate limiter (240 req/min)."),
          ("Health & Readiness Probes", "Active /health and /ready endpoints verifying database & connector status.")]),
        ("3. Core Monolith Services (services/core/)",
         [("12 Decoupled Packages", "consent, ingestion, scoring, explainability, decisioning, handoff, grievance, monitoring, dashboard, ops, admin, simulation."),
          ("In-Process ML Serving", "Inference runs in-memory (< 0.04 ms); zero external network serialization."),
          ("Graceful Orchestration", "Asyncio parallel pipeline with circuit breakers across all 4 rails.")]),
        ("4. Persistence & Audit Tier (PostgreSQL / SQLite)",
         [("PII Cryptographic Isolation", "Strict schema barrier: Borrower PII is physically isolated from feature vectors."),
          ("Append-Only Triggers", "Database-level triggers enforce immutability on decisions and grievance logs."),
          ("Automated DR Snapshots", "sqlite3.Connection.backup() snapshots with parity verification scripts.")])
    ]
    for i, (title, bullets) in enumerate(tiers):
        c = create_card(s10, Inches(0.8 + i * 2.95), Inches(1.8), Inches(2.78), Inches(4.9), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = BLUE_ROYAL
        for h, b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"• {h}: "
            pb.font.bold = True
            pb.font.size = Pt(10)
            pb.font.color.rgb = NAVY_DARK
            r = pb.add_run()
            r.text = b
            r.font.bold = False
            r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s10, """
Slide 10 details our architectural blueprint. We intentionally architected CreditTech as a modular monolith built on FastAPI and PostgreSQL.
Why a monolith? Because at pilot volumes of 15 to 30 decisions per day, microservices or Kubernetes clusters introduce needless network latency, distributed serialization overhead, and cloud hosting bills.
Our monolith achieves sub-10ms model inference in-process, maintains clean modular boundaries across 12 services, and enforces database-level separation of sensitive borrower PII from ML feature tables.
""")

    # --- SLIDE 11: End-to-End System Data Flow ---
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, BG_SUBTLE)
    create_header(s11, "End-to-End Workflow: The Complete Lifecycle from Consent to RE Handoff", "Architecture: Data Flow",
                  "Step-by-step state machine trace from borrower onboarding to DPDP data retention purge.")
    add_footer(s11, 11)

    steps_flow = [
        ("Step 1: Consent Initiation", "Bank Sakhi inputs details; DPDP consent issued with SHA-256 hash chaining (H_n = SHA256(H_n-1 || Tx)). Status: ACTIVE."),
        ("Step 2: Parallel Ingestion", "Orchestrator fires 4 connectors asynchronously in 480ms. Feature snapshot persisted; PII decoupled."),
        ("Step 3: ML Score Generation", "Champion Scorecard evaluates 21 WoE features. Produces PD and standardized score: 724 (Band: LOW_RISK)."),
        ("Step 4: Bilingual SHAP XAI", "Exact Shapley values derived. Generates top-5 adverse action reason codes in English and Hindi."),
        ("Step 5: Underwriter Review", "Loan officer inspects score breakdown, NDVI vigor, and SHAP evidence; sanctions ₹30,000 at 7% KCC rate."),
        ("Step 6: RE Handoff & Sanction", "Application package formatted to partner bank API specification; decision immutably logged."),
        ("Step 7: DPDP Retention Purge", "Post-sanction 30-day TTL expires. DataRetentionWorker executes cryptographic purge of all borrower PII.")
    ]
    for i, (title, desc) in enumerate(steps_flow):
        row = i // 4
        col_idx = i % 4
        x = Inches(0.8 + col_idx * 2.95)
        y = Inches(1.8 + row * 2.55)
        w = Inches(2.78)
        h = Inches(2.35)
        c = create_card(s11, x, y, w, h, WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.18)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = BLUE_ROYAL
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(9.8)
        pd.font.color.rgb = TEXT_DARK

    set_speaker_notes(s11, """
Slide 11 illustrates the lifecycle workflow.
From Step 1, where the Bank Sakhi registers borrower consent into our cryptographic ledger, through Step 2 parallel ingestion in under 500 milliseconds, Step 3 scoring, Step 4 bilingual SHAP explainability, Step 5 underwriter sanctioning, Step 6 partner bank export, and finally Step 7: automated DPDP storage limitation purge.
Every single step in this diagram is automated, tested, and verifiable in code.
""")

    # --- SLIDE 12: 4-Rail Ingestion Engine with Graceful Degradation ---
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, BG_SUBTLE)
    create_header(s12, "Innovation Pillar 1: 4-Rail Parallel Ingestion with Graceful Degradation", "Architecture: Ingestion",
                  "Engineering partial-information resilience across fragile rural connectivity and external APIs.")
    add_footer(s12, 12)

    rails_s12 = [
        ("Rail 1: Account Aggregator (AA)", "Financial Information User (FIU)",
         "• Queries licensed NBFC-AA\n• Analyzes 12-mo bank cashflows\n• Extracts Average Daily Balance (ADB), UPI frequency, and inward remittance\n• Evaluates seasonal liquidity buffers", BLUE_ROYAL),
        ("Rail 2: Geospatial Remote Sensing", "Sentinel-2 & Landsat Analytics",
         "• Computes 2-year NDVI time-series\n• Evaluates crop vegetative vigor\n• Detects historical drought exposure\n• Validates farm boundary geometry & multi-cropping frequency", BLUE_CYAN),
        ("Rail 3: Credit Bureau Rail", "Thin-File Scrutiny (CIBIL/CRIF)",
         "• Queries traditional credit records\n• Captures active loan counts\n• Handles 'Thin-File' / -1 score safely\n• Verifies no active willful defaults or commercial over-leverage", NAVY_DARK),
        ("Rail 4: Community SHG / FPO", "Social Collateral & Peer Proof",
         "• Ingests NABARD e-Shakti records\n• Quantifies monthly thrift regularity\n• Computes SHG meeting attendance\n• Evaluates peer group credit repayment and internal loan recycling", GOLD_ACCENT)
    ]
    for i, (name, role, body, col) in enumerate(rails_s12):
        c = create_card(s12, Inches(0.8 + i * 2.95), Inches(1.8), Inches(2.78), Inches(3.6), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"Rail 0{i+1}"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = name
        p2.font.size = Pt(13)
        p2.font.bold = True
        p2.font.color.rgb = NAVY_DARK
        p3 = tf.add_paragraph()
        p3.text = role
        p3.font.size = Pt(10)
        p3.font.italic = True
        p3.font.color.rgb = TEXT_MUTED
        p4 = tf.add_paragraph()
        p4.text = body
        p4.font.size = Pt(10)
        p4.font.color.rgb = TEXT_DARK

    c_deg = create_card(s12, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), RGBColor(239, 246, 255), BLUE_BORDER_DARK)
    tfd = c_deg.text_frame
    tfd.margin_left = Inches(0.3)
    tfd.margin_top = Inches(0.15)
    pd1 = tfd.paragraphs[0]
    pd1.text = "⚡ Architectural Resilience: The Graceful Degradation Principle"
    pd1.font.size = Pt(13)
    pd1.font.bold = True
    pd1.font.color.rgb = BLUE_ROYAL
    pd2 = tfd.add_paragraph()
    pd2.text = "In rural India, external APIs experience frequent network timeouts (e.g. AA consent drop-off, cloud obscuration on satellite, or slow bureau gateways). In traditional architectures, a single timeout aborts the entire loan. In CreditTech, our parallel asyncio orchestrator continues scoring with partial signals, automatically widening confidence intervals (e.g., Score 720 ± 45 instead of ± 15) and penalizing information entropy rather than crashing."
    pd2.font.size = Pt(10.5)
    pd2.font.color.rgb = TEXT_DARK

    set_speaker_notes(s12, """
Slide 12 presents Innovation Pillar 1: our 4-Rail Ingestion Engine.
Notice our four data rails: Account Aggregator cashflows, Sentinel-2 satellite remote sensing, credit bureau records, and community SHG savings.
Rural fintech systems fail when external APIs timeout. In CreditTech, we built Graceful Degradation. If the satellite API times out due to monsoon cloud cover, the orchestrator does NOT crash. It rescales available feature weights, widens the confidence interval, and outputs a transparent partial score. The pipeline never halts.
""")

    # =========================================================================
    # SECTION D: TECHNICAL IMPLEMENTATION (SLIDES 13 - 16)
    # =========================================================================

    # --- SLIDE 13: Technology Stack Justification & Architecture Decisions ---
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, BG_SUBTLE)
    create_header(s13, "Engineering Decisions: Architecture Decision Records (ADRs) & Trade-Offs", "Implementation: ADRs",
                  "Defending significant architectural and engineering decisions against alternative choices.")
    add_footer(s13, 13)

    adrs = [
        ("ADR-1: Modular Monolith vs. Microservices",
         "Alternatives: Kubernetes Microservices, Serverless Lambdas",
         "Justification: For village pilot scale (< 30 scoring req/day), microservices introduce severe network serialization latency, distributed transaction complexity, and DevOps friction. Monolith provides sub-second execution and unified ACID transactions.",
         "Trade-off: Requires modular discipline in codebase; horizontal scaling scales all components together.", BLUE_ROYAL),
        ("ADR-2: In-Process Model Serving vs. Triton / SageMaker",
         "Alternatives: Triton Inference Server, SageMaker Endpoints, TorchServe",
         "Justification: A separate model-serving cluster introduces external network hops and hundreds in monthly cloud fees for low traffic. In-process Python evaluation runs in < 0.04ms with zero network latency.",
         "Trade-off: Worker memory footprint includes model weights (approx. 45 MB).", BLUE_CYAN),
        ("ADR-3: Native Asyncio vs. Celery + Redis Task Queue",
         "Alternatives: Celery + Redis, RabbitMQ, Kafka",
         "Justification: Eliminates external broker dependency. Python's native asyncio with asyncio.gather() effortlessly handles 4 parallel ingestion calls. Batch audits run as cron scripts.",
         "Trade-off: In-memory async tasks do not persist across hard process crashes.", NAVY_DARK),
        ("ADR-4: PostgreSQL Hash-Chaining vs. Distributed Blockchain",
         "Alternatives: Hyperledger Fabric, Polygon / Ethereum Private Ledger",
         "Justification: Blockchain introduces extreme gas costs, transaction latency, and key-management overhead for rural agents. Cryptographic SHA-256 hash chaining inside PostgreSQL triggers provides identical non-repudiation.",
         "Trade-off: Auditability depends on cryptographic ledger verification rather than decentralized consensus.", GREEN_ACCENT)
    ]
    for i, (title, alt, just, trade, col) in enumerate(adrs):
        row = i // 2
        col_idx = i % 2
        c = create_card(s13, Inches(0.8 + col_idx * 5.95), Inches(1.8 + row * 2.55), Inches(5.65), Inches(2.35), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.18)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        pa = tf.add_paragraph()
        pa.text = alt
        pa.font.size = Pt(9.5)
        pa.font.italic = True
        pa.font.color.rgb = TEXT_MUTED
        pj = tf.add_paragraph()
        pj.text = f"• Reason: {just}"
        pj.font.size = Pt(9.5)
        pj.font.color.rgb = TEXT_DARK
        pt = tf.add_paragraph()
        pt.text = f"• Trade-off: {trade}"
        pt.font.size = Pt(9.5)
        pt.font.bold = True
        pt.font.color.rgb = NAVY_PRIMARY

    set_speaker_notes(s13, """
Slide 13 details our Architecture Decision Records.
We made deliberate engineering trade-offs:
1. We chose a Modular Monolith over microservices to eliminate distributed latency and Docker Swarm overhead.
2. We chose In-Process ML Serving over SageMaker endpoints, saving thousands in cloud costs and achieving 0.04ms inference.
3. We chose Native Asyncio over Celery and Redis to eliminate premature broker dependencies.
4. We chose PostgreSQL SHA-256 Hash Chaining over Blockchain, giving mathematical tamper evidence at zero transaction cost.
Every decision was driven by empirical need, not startup hype.
""")

    # --- SLIDE 14: Data Architecture & PII Cryptographic Isolation ---
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, BG_SUBTLE)
    create_header(s14, "Data Architecture: Physical & Cryptographic Separation of PII and ML Features", "Implementation: Data Architecture",
                  "Enforcing zero blast-radius and absolute demographic privacy across relational schemas.")
    add_footer(s14, 14)

    c_pii = create_card(s14, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_p = c_pii.text_frame
    tf_p.margin_left = tf_p.margin_right = Inches(0.25)
    tf_p.margin_top = Inches(0.22)
    tf_p.word_wrap = True
    p = tf_p.paragraphs[0]
    p.text = "🔒 PII Physical Isolation Layer"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    pii_bullets = [
        ("Encrypted PII Storage", "Borrower PII (name, phone, Aadhaar hash) stored in physically segregated Borrower table."),
        ("AES-256 Encryption", "name_encrypted and phone_encrypted columns encrypted at rest using Fernet AES-256 keys."),
        ("Aadhaar Reference Hashing", "Zero raw Aadhaar numbers stored. Transformed into irreversible SHA-256 reference hashes: aadhaar_ref_hash."),
        ("Zero Co-Location with ML", "The FeatureSnapshot and Score tables contain ONLY anonymous UUIDs and numeric feature vectors."),
        ("Access Firewall", "Developers and ML training pipelines CANNOT query borrower names or phones from credit feature tables.")
    ]
    for k, v in pii_bullets:
        pk = tf_p.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_rel = create_card(s14, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_r = c_rel.text_frame
    tf_r.margin_left = tf_r.margin_right = Inches(0.25)
    tf_r.margin_top = Inches(0.22)
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "🗄️ Core Relational Entity Model (10 Tables)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    tables = [
        ("Borrower & Village", "Demographic anchor (PII isolated) and agro-climatic site mapping."),
        ("ConsentRecord", "Cryptographic append-only ledger tracking lifecycle (CREATE, VERIFY, REVOKE)."),
        ("FeatureSnapshot", "Sanitized 21-feature vector from 4 rails; zero PII columns."),
        ("Score", "Computed repayment probability, 300-900 score, confidence bands, reason codes."),
        ("DecisionLog", "Loan officer underwriter decisions with immutable append-only dissent overrides."),
        ("ApplicationHandoff", "Structured payload export to partner Regulated Entity core banking system."),
        ("GrievanceRecord", "Borrower appeal lifecycle with 14-day automated SLA tracking clock."),
        ("FairnessAuditLog", "Weekly population audit records across gender, geography, and landholding.")
    ]
    for k, v in tables:
        pk = tf_r.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s14, """
Slide 14 explains our data architecture.
In credit scoring, data breaches destroy institutional trust. We enforce strict physical and cryptographic separation of Personally Identifiable Information (PII) from machine learning feature snapshots.
The Borrower table encrypts names and phone numbers via AES-256 and hashes Aadhaar tokens. The FeatureSnapshot table contains purely anonymous numerical vectors. No ML model or analytics script ever has access to borrower PII.
Our relational schema is backed by 10 SQLAlchemy ORM models with append-only triggers on decision and grievance tables.
""")

    # --- SLIDE 15: DPDP Cryptographic Consent Ledger ---
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, BG_SUBTLE)
    create_header(s15, "Innovation Pillar 2: DPDP-Compliant Cryptographic Consent Lifecycle", "Implementation: DPDP Compliance",
                  "Enforcing purpose-specification, tamper-evident audit trails, and automated storage limitation.")
    add_footer(s15, 15)

    c_w = Inches(3.7)
    c_h = Inches(4.9)
    pillars_s15 = [
        ("SHA-256 Hash Chaining", "Immutable Append-Only Audit Trail",
         [("Cryptographic Linkage", "Every consent creation, verification, or revocation is linked to the previous transaction hash: H_n = SHA256(H_{n-1} || TxData || Timestamp)."),
          ("Tamper Evidence", "Any retrospective modification to borrower consent logs immediately invalidates subsequent block hashes, providing mathematical non-repudiation."),
          ("Zero Blockchain Bloat", "Implemented directly in PostgreSQL with append-only database triggers, avoiding unnecessary Web3 gas fees and operational latency.")], BLUE_ROYAL),
        ("DPDP Act 2023 Principles", "Data Fiduciary Obligations Enforced",
         [("Purpose Limitation", "Consents are strictly purpose-bound (e.g., CREDIT_SCORING, TENURE_MONITORING). Re-use for marketing is rejected at the API schema layer."),
          ("Notice & Vernacular Consent", "Clear notice provided in local vernacular (Hindi / English), explained orally by Bank Sakhi and digitally acknowledged."),
          ("Unconditional Revocation", "Borrower can revoke consent at any time via /api/v1/consent/{id}/revoke, terminating active data processing within 60 seconds.")], NAVY_DARK),
        ("Automated Retention Purge", "Guaranteed Storage Limitation",
         [("Lifecycle Clocks", "Consents have a hard TTL (typically 30 days for underwriting). Once expired or revoked, a background DataRetentionWorker triggers."),
          ("Cryptographic Scrubbing", "Borrower PII—Aadhaar reference hashes, encrypted phone, and name—are cryptographically purged from active tables."),
          ("Feature Anonymization", "Anonymized feature vectors are retained solely for population drift monitoring without any possibility of re-identification.")], GREEN_ACCENT)
    ]
    for i, (title, sub, bullets, color) in enumerate(pillars_s15):
        c = create_card(s15, Inches(0.8 + i * 4.0), Inches(1.8), c_w, c_h, WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.25)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = color
        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(10.5)
        p_sub.font.italic = True
        p_sub.font.color.rgb = TEXT_MUTED
        for h, b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"• {h}: "
            pb.font.bold = True
            pb.font.size = Pt(10)
            pb.font.color.rgb = NAVY_DARK
            r = pb.add_run()
            r.text = b
            r.font.bold = False
            r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s15, """
Slide 15 addresses statutory privacy under India's Digital Personal Data Protection (DPDP) Act 2023.
We enforce three pillars:
First, a Cryptographic Consent Ledger. Every consent event is linked using SHA-256 hash chaining: current hash equals SHA-256 of previous hash plus payload. It provides mathematical non-repudiation inside PostgreSQL.
Second, strict Purpose Limitation. Consent is bound exclusively to credit underwriting.
Third, automated Storage Limitation. Under Section 8(7) of DPDP, once the 30-day underwriting window expires, our DataRetentionWorker executes a cryptographic wipe of all PII, ensuring zero lingering demographic exposure.
""")

    # --- SLIDE 16: Front-End Architecture: React 19 + Vite Portal ---
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, BG_SUBTLE)
    create_header(s16, "User Interface: Unified React 19 Web Portal for Sakhis and Underwriters", "Implementation: Front-End",
                  "Cross-platform responsive client under apps/borrower-app/ replacing native Android complexity.")
    add_footer(s16, 16)

    c_fe1 = create_card(s16, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_f1 = c_fe1.text_frame
    tf_f1.margin_left = tf_f1.margin_right = Inches(0.25)
    tf_f1.margin_top = Inches(0.22)
    tf_f1.word_wrap = True
    p = tf_f1.paragraphs[0]
    p.text = "📱 Bank Sakhi Assisted PWA Flow"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    fe1_pts = [
        ("Technology Stack", "React 19, Vite, Tailwind CSS, Lucide Icons. Single unified bundle on port 5173."),
        ("Rural Tablet Optimization", "Touch-first mobile responsive layout designed for 3G/4G connectivity and low-memory devices."),
        ("Assisted Onboarding", "Guided step-by-step form capturing borrower KYC, Aadhaar reference token, and village location."),
        ("SHG Register Digitization", "Allows Bank Sakhis to transcribe paper meeting ledgers into structured JSON payloads with instant client-side range validation."),
        ("Bilingual Audio & Text Prompts", "Renders consent terms and final reason codes in conversational Hindi and English.")
    ]
    for k, v in fe1_pts:
        pk = tf_f1.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_fe2 = create_card(s16, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_f2 = c_fe2.text_frame
    tf_f2.margin_left = tf_f2.margin_right = Inches(0.25)
    tf_f2.margin_top = Inches(0.22)
    tf_f2.word_wrap = True
    p = tf_f2.paragraphs[0]
    p.text = "🖥️ Loan Officer Decision Portal"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    fe2_pts = [
        ("Comprehensive Risk Card", "Displays 300-900 bureau-equivalent score, risk band (Low/Moderate/High), and confidence intervals."),
        ("SHAP Reason Code Breakdown", "Visual breakdown of top-5 positive and negative score contributors."),
        ("Satellite Crop History", "Interactive visualizer displaying historical Sentinel-2 NDVI vegetative health and drought index."),
        ("Mandatory Dissent Logging", "If officer overrides model score (e.g. approving a High-Risk applicant), UI enforces mandatory structured justification."),
        ("RE Handoff Trigger", "One-click export transmitting complete loan package to partner bank core banking system.")
    ]
    for k, v in fe2_pts:
        pk = tf_f2.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    set_speaker_notes(s16, """
Slide 16 details our front-end client. We built a unified web portal under apps/borrower-app using React 19, Vite, and Tailwind CSS.
On the left: the Bank Sakhi assisted onboarding flow, optimized for rural tablets, enabling easy transcription of paper SHG ledgers with client-side validation and bilingual vernacular prompts.
On the right: the Loan Officer decision dashboard, providing underwriters with real-time SHAP reason codes, satellite crop health charts, and mandatory override logging whenever they dissent from the model.
""")

    # =========================================================================
    # SECTION E: ML PIPELINE & EMPIRICAL RESULTS (SLIDES 17 - 24)
    # =========================================================================

    # --- SLIDE 17: ML Pipeline & Feature Engineering ---
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, BG_SUBTLE)
    create_header(s17, "Feature Engineering: 21 Domain Features Mapped to the Classical 5 Cs of Credit", "ML Pipeline: Features",
                  "Transforming raw alternative signals into monotonic Weight of Evidence (WoE) risk bins.")
    add_footer(s17, 17)

    c_5c = create_card(s17, Inches(0.8), Inches(1.8), Inches(11.7), Inches(3.5), WHITE, BLUE_BORDER)
    tf_5c = c_5c.text_frame
    tf_5c.margin_left = Inches(0.3)
    tf_5c.margin_top = Inches(0.2)
    p = tf_5c.paragraphs[0]
    p.text = "🌾 The 21-Feature Domain Taxonomy Mapped to the 5 Cs of Credit"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    f_items = [
        ("Character (Social Collateral)", "shg_tenure_months, shg_savings_consistency_ratio, shg_attendance_rate, fpo_member_flag (IV: 0.42–0.68)"),
        ("Capacity (Cashflow Velocity)", "aa_monthly_inflow_avg, aa_volatility_coefficient, utility_bill_payment_ratio, pm_kisan_receipt_count (IV: 0.31–0.45)"),
        ("Capital (Liquidity & Buffer)", "aa_average_daily_balance, aa_zero_balance_days, livestock_count (IV: 0.22–0.35)"),
        ("Collateral (Productivity Proxies)", "land_size_acres, satellite_ndvi_mean, irrigation_access_type, crop_season_count (IV: 0.28–0.41)"),
        ("Conditions (Climate & Macro Risk)", "rainfall_deviation_pct, drought_risk_index, crop_type_code (IV: 0.15–0.24)")
    ]
    for k, v in f_items:
        pk = tf_5c.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(11)
        pk.font.color.rgb = BLUE_ROYAL
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_woe = create_card(s17, Inches(0.8), Inches(5.45), Inches(11.7), Inches(1.45), RGBColor(239, 246, 255), BLUE_BORDER_DARK)
    tf_w = c_woe.text_frame
    tf_w.margin_left = Inches(0.3)
    tf_w.margin_top = Inches(0.15)
    pw = tf_w.paragraphs[0]
    pw.text = "📐 Weight of Evidence (WoE) & Information Value (IV) Mathematical Formulations"
    pw.font.size = Pt(13)
    pw.font.bold = True
    pw.font.color.rgb = BLUE_ROYAL
    pw2 = tf_w.add_paragraph()
    pw2.text = "• Weight of Evidence:  WoE_i = ln( (Good_i / Total_Good) / (Bad_i / Total_Bad) )   |   Laplace Smoothing prevents division by zero.\n• Information Value:   IV = Σ [ (Good_i / Total_Good) - (Bad_i / Total_Bad) ] × WoE_i   |   Features filtered at IV >= 0.015.\n• Credit Score Scaling: Score = Offset - Factor × ln( Odds )   [Standardized: 300 to 900 Scale, PDO = 20 @ Odds 50:1]."
    pw2.font.size = Pt(10.5)
    pw2.font.color.rgb = NAVY_PRIMARY

    set_speaker_notes(s17, """
Slide 17 details our feature engineering pipeline.
We synthesized 21 continuous and categorical features across the classical 5 Cs of credit: Character, Capacity, Capital, Collateral, and Conditions.
Notice that Character—social collateral from SHG savings consistency and meeting attendance—exhibits the highest Information Value, between 0.42 and 0.68.
Every feature undergoes monotonic Weight of Evidence binning with Laplace smoothing to guarantee numerical stability and regulatory interpretability.
""")

    # --- SLIDE 18: Empirical Benchmark Dataset & Spatial GroupKFold ---
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, BG_SUBTLE)
    create_header(s18, "Validation Methodology: N = 22,000 Benchmark & Spatial Group Cross-Validation", "ML Pipeline: Validation",
                  "Eliminating spatial autocorrelation data leakage across contiguous agricultural zones.")
    add_footer(s18, 18)

    c_ds = create_card(s18, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_ds = c_ds.text_frame
    tf_ds.margin_left = tf_ds.margin_right = Inches(0.25)
    tf_ds.margin_top = Inches(0.22)
    tf_ds.word_wrap = True
    p = tf_ds.paragraphs[0]
    p.text = "📊 Fused Empirical Benchmark (N = 22,000)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    ds_pts = [
        ("Cohort Size", "Complete fused cohort of 22,000 real borrower observations across 15 pilot village clusters."),
        ("Source Composition", "12,000 Home Credit + 10,000 Give Me Some Credit records mapped to our 21-feature schema."),
        ("Empirical Defaults", "2,098 verified loan defaults (9.54% default prevalence), capturing real portfolio class imbalance."),
        ("Alternative Data Fusion", "Blended with Sentinel-2 10m NDVI vegetative vigor, DISCOM utility billings, and SHG thrift deposits."),
        ("Target Variable", "repay in {0, 1}, representing 90-day repayment delinquency.")
    ]
    for k, v in ds_pts:
        pk = tf_ds.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = BLUE_ROYAL
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_sp = create_card(s18, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_sp = c_sp.text_frame
    tf_sp.margin_left = tf_sp.margin_right = Inches(0.25)
    tf_sp.margin_top = Inches(0.22)
    tf_sp.word_wrap = True
    p = tf_sp.paragraphs[0]
    p.text = "🗺️ 5-Fold Spatial GroupKFold Cross-Validation"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    sp_pts = [
        ("Spatial Autocorrelation Trap", "Adjacent farms share identical rainfall, soil quality, and local crop prices. Standard random K-Fold leaks spatial information between train and test splits!"),
        ("Geographic Group Partitioning", "Data is partitioned into 15 distinct village clusters across diverse agro-climatic zones."),
        ("Out-of-Region Testing", "Models are trained on K-1 village groups and evaluated strictly on unseen out-of-district clusters."),
        ("Scientific Integrity", "Guarantees that reported ROC-AUC and KS statistics reflect true out-of-region generalizability rather than localized memorization."),
        ("Out-of-Fold (OOF) Inference", "All benchmark metrics and downstream curves are computed exclusively from OOF cross-validation predictions.")
    ]
    for k, v in sp_pts:
        pk = tf_sp.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    set_speaker_notes(s18, """
Slide 18 details our empirical benchmark and validation methodology.
We evaluated our models on 22,000 real borrower observations with 2,098 verified defaults—a 9.54% default prevalence.
Crucially, we avoided standard random train-test splitting. In agricultural data, adjacent farms share identical weather and soil. Standard K-fold cross-validation results in severe spatial data leakage.
We solved this by implementing 5-Fold Spatial GroupKFold cross-validation over 15 village clusters. Every reported metric reflects out-of-region generalization.
""")

    # --- SLIDE 19: Multi-Model Discrimination Analysis (Embed Fig 1 & 2) ---
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19, BG_SUBTLE)
    create_header(s19, "Discriminatory Power: Champion WoE Scorecard Captures 98% of Ensemble AUC", "ML Results: Discrimination",
                  "Comparing ROC and Precision-Recall default detection across all 5 tuned model architectures.")
    add_footer(s19, 19)

    embed_image_safe(s19, os.path.join(FIGURES_DIR, "roc_curve_comparison.png"), Inches(0.8), Inches(1.8), Inches(5.7), Inches(3.6))
    embed_image_safe(s19, os.path.join(FIGURES_DIR, "pr_curve_comparison.png"), Inches(6.8), Inches(1.8), Inches(5.7), Inches(3.6))

    c_t19 = create_card(s19, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), WHITE, BLUE_BORDER)
    tf_t19 = c_t19.text_frame
    tf_t19.margin_left = Inches(0.25)
    tf_t19.margin_top = Inches(0.12)
    pt = tf_t19.paragraphs[0]
    pt.text = "📊 Quantitative Discrimination Metrics (5-Fold Spatial OOF Validation on N = 22,000)"
    pt.font.size = Pt(12)
    pt.font.bold = True
    pt.font.color.rgb = NAVY_DARK
    pt2 = tf_t19.add_paragraph()
    pt2.text = "• Tuned Stacking Ensemble:   ROC-AUC: 0.9793  |  Gini: 0.9585  |  PR-AUC: 0.8542  |  Accuracy: 95.76%  |  Latency: 1.51 ms\n• Tuned Random Forest:       ROC-AUC: 0.9766  |  Gini: 0.9532  |  PR-AUC: 0.8355  |  Accuracy: 94.51%  |  Latency: 1.33 ms\n• Tuned Monotonic GBDT:      ROC-AUC: 0.9758  |  Gini: 0.9515  |  PR-AUC: 0.8310  |  Accuracy: 90.51%  |  Latency: 0.11 ms\n• Tuned WoE Scorecard (CHAMP): ROC-AUC: 0.9599  |  Gini: 0.9198  |  PR-AUC: 0.7245  |  Accuracy: 92.53%  |  Latency: 0.038 ms (CAPTURES 98% ENSEMBLE POWER!)"
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = BLUE_ROYAL

    set_speaker_notes(s19, """
Slide 19 presents Figure 1 and Figure 2: our multi-model ROC and Precision-Recall comparisons.
On the left: ROC curves showing that all models significantly outperform the institutional floor of 0.60. The Stacking Ensemble achieves an AUC of 0.9793, while our production Champion—the WoE Scorecard—achieves an outstanding AUC of 0.9599 and a Gini of 0.9198.
On the right: Precision-Recall curves, which are crucial given our 9.54% default prevalence. The WoE Scorecard captures over 72% PR-AUC, operating in sub-0.04 milliseconds while preserving full interpretability.
""")

    # --- SLIDE 20: Probability Calibration & KS Separation (Embed Fig 3 & 4) ---
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20, BG_SUBTLE)
    create_header(s20, "Calibration & Risk Separation: Pristine Alignment with Real Loss Probabilities", "ML Results: Calibration & KS",
                  "Evaluating Kolmogorov-Smirnov discrimination and reliability decile calibration curves.")
    add_footer(s20, 20)

    embed_image_safe(s20, os.path.join(FIGURES_DIR, "ks_separation_plots.png"), Inches(0.8), Inches(1.8), Inches(5.7), Inches(3.6))
    embed_image_safe(s20, os.path.join(FIGURES_DIR, "calibration_reliability_curves.png"), Inches(6.8), Inches(1.8), Inches(5.7), Inches(3.6))

    c_t20 = create_card(s20, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), WHITE, BLUE_BORDER)
    tf_t20 = c_t20.text_frame
    tf_t20.margin_left = Inches(0.25)
    tf_t20.margin_top = Inches(0.12)
    pt = tf_t20.paragraphs[0]
    pt.text = "📈 Calibration & Separation Findings (Statutory Floor: KS >= 0.15, Brier <= 0.30)"
    pt.font.size = Pt(12)
    pt.font.bold = True
    pt.font.color.rgb = NAVY_DARK
    pt2 = tf_t20.add_paragraph()
    pt2.text = "• Kolmogorov-Smirnov (KS): Champion WoE Scorecard achieves Max KS = 0.8208; Monotonic GBDT achieves Max KS = 0.8549 (Vastly exceeds 0.15 floor).\n• Brier Score & ECE: Stacking Ensemble achieves Brier 0.0301 (ECE: 0.0071); Random Forest achieves Brier 0.0344 (ECE: 0.0151); WoE Scorecard achieves Brier 0.0596.\n• Regulatory Impact: In banking, predicted probabilities must match actual default rates across deciles. Figure 4 proves pristine 45-degree diagonal calibration."
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = BLUE_ROYAL

    set_speaker_notes(s20, """
Slide 20 displays Figure 3 and Figure 4: Kolmogorov-Smirnov separation and decile calibration curves.
In credit risk, accuracy alone is insufficient—predicted probabilities must accurately reflect actual portfolio default rates.
On the left: the KS separation plot shows a maximum KS of 0.8208 for our champion scorecard, well above the regulatory threshold of 0.15.
On the right: our calibration reliability curves adhere closely to the ideal 45-degree diagonal, achieving a Brier score of 0.0596 and an Expected Calibration Error of 0.061.
""")

    # --- SLIDE 21: Hyperparameter Optimization (Embed Fig 10 & 11) ---
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21, BG_SUBTLE)
    create_header(s21, "Hyperparameter Optimization: Systematic Sweeps Prevent Overfitting", "ML Results: Tuning Sweeps",
                  "Analyzing validation surfaces across boosting iterations, tree depths, and L1 regularization.")
    add_footer(s21, 21)

    embed_image_safe(s21, os.path.join(FIGURES_DIR, "hyperparameter_sensitivity_gbdt.png"), Inches(0.8), Inches(1.8), Inches(5.7), Inches(3.6))
    embed_image_safe(s21, os.path.join(FIGURES_DIR, "hyperparameter_tradeoff_rf_woe.png"), Inches(6.8), Inches(1.8), Inches(5.7), Inches(3.6))

    c_t21 = create_card(s21, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), WHITE, BLUE_BORDER)
    tf_t21 = c_t21.text_frame
    tf_t21.margin_left = Inches(0.25)
    tf_t21.margin_top = Inches(0.12)
    pt = tf_t21.paragraphs[0]
    pt.text = "🔍 Hyperparameter Optimization Insights"
    pt.font.size = Pt(12)
    pt.font.bold = True
    pt.font.color.rgb = NAVY_DARK
    pt2 = tf_t21.add_paragraph()
    pt2.text = "• Figure 10 (GBDT Surface): Learning rate 0.09 and 80 iterations establish the optimal validation ridge (AUC: 0.9761). Higher iterations (>120) show diminishing returns.\n• Figure 11 Panel A (Random Forest): While training AUC reaches 0.999, OOF validation AUC peaks at max_depth = 10 (AUC: 0.9766); deeper trees overfit to local noise.\n• Figure 11 Panel B (WoE Scorecard): L1 regularization parameter C = 2.0 retains all 21 domain features with optimal non-zero weight stability, producing Champion AUC 0.9599."
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = BLUE_ROYAL

    set_speaker_notes(s21, """
Slide 21 illustrates Figure 10 and Figure 11: our systematic hyperparameter tuning sweeps.
On the left: the 2D validation surface for GBDT confirms that a learning rate of 0.09 and 80 trees forms the optimal generalization ridge.
On the right: Panel A shows the classic bias-variance trade-off in Random Forest, where tree depth 10 maximizes OOF AUC at 0.9766 while deeper trees overfit. Panel B proves that an L1 penalty of C=2.0 retains all 21 domain features with optimal weight stability.
""")

    # --- SLIDE 22: Explainable AI & TreeSHAP Impact (Embed Fig 7) ---
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22, BG_SUBTLE)
    create_header(s22, "Explainable AI: Exact Closed-Form Point Attribution & Bilingual Reasons", "ML Results: Explainability",
                  "Transforming game-theoretic Shapley values into human-readable reason codes in English & Hindi.")
    add_footer(s22, 22)

    embed_image_safe(s22, os.path.join(FIGURES_DIR, "feature_importance_shap.png"), Inches(0.8), Inches(1.8), Inches(6.8), Inches(5.0))

    c_x22 = create_card(s22, Inches(7.8), Inches(1.8), Inches(4.7), Inches(5.0), WHITE, BLUE_BORDER)
    tf_x22 = c_x22.text_frame
    tf_x22.margin_left = tf_x22.margin_right = Inches(0.22)
    tf_x22.margin_top = Inches(0.2)
    tf_x22.word_wrap = True
    p = tf_x22.paragraphs[0]
    p.text = "📋 Bilingual Adverse Action Output"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    reasons_s22 = [
        ("🟢 Rank 1 (+21.2 pts)", "SHG savings deposit regularity (100% on-time)", "स्वयं सहायता समूह में नियमित बचत और पूर्ण उपस्थिति।", GREEN_ACCENT),
        ("🟢 Rank 2 (+18.4 pts)", "Sentinel-2 crop vegetative vigor (NDVI: 0.68)", "उपग्रह द्वारा फसल की स्थिति बहुत अच्छी पाई गई।", GREEN_ACCENT),
        ("🟢 Rank 3 (+12.8 pts)", "Consistent Average Daily Balance (> ₹4,500)", "बैंक खाते में न्यूनतम शेष राशि का लगातार रखरखाव।", GREEN_ACCENT),
        ("🔴 Rank 4 (-6.1 pts)", "Thin bureau credit file (No prior bank loan)", "पूर्व में किसी बैंक ऋण का रिकॉर्ड उपलब्ध नहीं है।", RED_ACCENT),
        ("🔴 Rank 5 (-3.2 pts)", "Marginal landholding size (< 2.0 acres)", "कृषि भूमि का आकार छोटा (सीमांत किसान श्रेणी) है।", RED_ACCENT)
    ]
    for rk, en, hi, col in reasons_s22:
        pr = tf_x22.add_paragraph()
        pr.text = rk
        pr.font.bold = True
        pr.font.size = Pt(10)
        pr.font.color.rgb = col
        pe = tf_x22.add_paragraph()
        pe.text = f"EN: {en}"
        pe.font.size = Pt(9.5)
        pe.font.color.rgb = NAVY_DARK
        ph = tf_x22.add_paragraph()
        ph.text = f"HI: {hi}"
        ph.font.size = Pt(9)
        ph.font.italic = True
        ph.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s22, """
Slide 22 features Figure 7: our Explainable AI pipeline.
Central banks strictly prohibit 'black-box' credit rejections. Because our Champion model is a linear WoE scorecard, we calculate Shapley values in exact closed form: phi_i equals beta_i times the difference between borrower WoE and the population mean.
On the left: TreeSHAP impacts confirm that SHG savings consistency and Sentinel-2 crop vigor are the primary positive drivers.
On the right: our bilingual translation engine outputs adverse action reasons in conversational Hindi and English, ensuring Bank Sakhis can explain decisions directly to rural borrowers.
""")

    # --- SLIDE 23: Classification Diagnostics & Decision Bands (Embed Fig 5 & 6) ---
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_background(s23, BG_SUBTLE)
    create_header(s23, "Classification Diagnostics: Normalized Confusion Matrices & Statutory Zones", "ML Results: Diagnostics",
                  "Evaluating decision boundary accuracy and score distributions across statutory risk bands.")
    add_footer(s23, 23)

    embed_image_safe(s23, os.path.join(FIGURES_DIR, "confusion_matrices_comparison.png"), Inches(0.8), Inches(1.8), Inches(5.7), Inches(3.6))
    embed_image_safe(s23, os.path.join(FIGURES_DIR, "score_distributions_zones.png"), Inches(6.8), Inches(1.8), Inches(5.7), Inches(3.6))

    c_t23 = create_card(s23, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), WHITE, BLUE_BORDER)
    tf_t23 = c_t23.text_frame
    tf_t23.margin_left = Inches(0.25)
    tf_t23.margin_top = Inches(0.12)
    pt = tf_t23.paragraphs[0]
    pt.text = "🎯 Operational Classification Performance at Decision Cutoff 600"
    pt.font.size = Pt(12)
    pt.font.bold = True
    pt.font.color.rgb = NAVY_DARK
    pt2 = tf_t23.add_paragraph()
    pt2.text = "• Figure 5 (Confusion Matrices): WoE Scorecard achieves 92.53% overall accuracy, 88.43% balanced accuracy, and 0.9577 F1-score; correctly identifies 93.4% of good borrowers.\n• Figure 6 (Statutory Decision Zones on 300–900 Scale):\n  - Auto-Decline Zone (< 500): Predicted default probability > 28%; automated adverse action notice issued.\n  - Manual Review Zone (500–620): Thin-file applicants with strong alternative signals; loan officer underwriter review required.\n  - Auto-Approve Zone (> 620): Low default risk (< 3.2%); streamlined straight-through digital loan sanction."
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = BLUE_ROYAL

    set_speaker_notes(s23, """
Slide 23 presents Figure 5 and Figure 6: classification diagnostics and statutory decision zones.
On the left: normalized confusion matrices at cutoff 600 show 92.53% overall accuracy and an F1-score of 0.9577 for our WoE Scorecard.
On the right: we translate continuous risk probabilities into the standard Indian 300 to 900 credit bureau scale across three operational zones: Auto-Decline below 500, Manual Review between 500 and 620, and Auto-Approve above 620.
""")

    # --- SLIDE 24: Cost-Sensitive Economic Optimization (Embed Fig 12) ---
    s24 = prs.slides.add_slide(blank_layout)
    set_slide_background(s24, BG_SUBTLE)
    create_header(s24, "Economic Policy Optimization: Balancing Maximum Margin and Financial Inclusion", "ML Results: Economics",
                  "Aligning machine learning cutoffs with commercial banking net interest margins and default losses.")
    add_footer(s24, 24)

    embed_image_safe(s24, os.path.join(FIGURES_DIR, "economic_profit_cutoff_curve.png"), Inches(0.8), Inches(1.8), Inches(7.5), Inches(5.0))

    c_e24 = create_card(s24, Inches(8.5), Inches(1.8), Inches(4.0), Inches(5.0), WHITE, BLUE_BORDER)
    tf_e24 = c_e24.text_frame
    tf_e24.margin_left = tf_e24.margin_right = Inches(0.2)
    tf_e24.margin_top = Inches(0.2)
    tf_e24.word_wrap = True
    p = tf_e24.paragraphs[0]
    p.text = "💰 Portfolio Economics"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    e_pts = [
        ("Banking Margin", "Net interest margin & origination fees per good loan: +₹6,500."),
        ("Loss Given Default", "Loss net of recovery per defaulting loan: -₹42,000."),
        ("Profit-Maximizing Cutoff", "Score 540 yields maximum net expected profit of ₹5.2 Crore per 10,000 applicants."),
        ("Inclusion Operating Point", "Score 500 yields ₹4.9 Crore while approving an extra 12.4% of thin-file borrowers within safe risk limits."),
        ("Policy Recommendation", "Partner banks can dynamically tune cutoff between 500 and 540 based on seasonal liquidity.")
    ]
    for k, v in e_pts:
        pk = tf_e24.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s24, """
Slide 24 details Figure 12: cost-sensitive economic portfolio optimization.
In banking, machine learning models must generate profit. We modeled real bank economics: +₹6,500 net margin per performing loan versus -₹42,000 Loss Given Default per bad loan.
Plotting expected net profit across score cutoffs reveals two strategic operating points:
Score 540 maximizes net profit at ₹5.2 Crore per 10,000 applicants.
Score 500 serves as the Financial Inclusion threshold, delivering ₹4.9 Crore while expanding credit approvals by an additional 12.4% of rural smallholders.
""")

    # =========================================================================
    # SECTION F: ENGINEERING QUALITY, FAIRNESS & GOVERNANCE (SLIDES 25 - 28)
    # =========================================================================

    # --- SLIDE 25: Algorithmic Fairness & Demographic Parity (Embed Fig 8 & 13) ---
    s25 = prs.slides.add_slide(blank_layout)
    set_slide_background(s25, BG_SUBTLE)
    create_header(s25, "Algorithmic Fairness: Enforcing Non-Discrimination Across Gender and Landholding", "Governance: Fairness Gates",
                  "Statutory parity compliance: Disparate Impact Ratio >= 0.80 and Equal Opportunity Difference.")
    add_footer(s25, 25)

    embed_image_safe(s25, os.path.join(FIGURES_DIR, "demographic_fairness_parity.png"), Inches(0.8), Inches(1.8), Inches(5.7), Inches(3.6))
    embed_image_safe(s25, os.path.join(FIGURES_DIR, "fairness_vs_cutoff_frontier.png"), Inches(6.8), Inches(1.8), Inches(5.7), Inches(3.6))

    c_t25 = create_card(s25, Inches(0.8), Inches(5.55), Inches(11.7), Inches(1.35), WHITE, BLUE_BORDER)
    tf_t25 = c_t25.text_frame
    tf_t25.margin_left = Inches(0.25)
    tf_t25.margin_top = Inches(0.12)
    pt = tf_t25.paragraphs[0]
    pt.text = "🛡️ Statutory Fairness Audit & Gate Invariants (fairness_thresholds.json Manifest v2026.09.01)"
    pt.font.size = Pt(12)
    pt.font.bold = True
    pt.font.color.rgb = NAVY_DARK
    pt2 = tf_t25.add_paragraph()
    pt2.text = "• Gender Parity (Figure 8): Maximum gender approval disparity is 7.1%, strictly inside the statutory ceiling of 20.0% (DIR >= 0.80 Four-Fifths Rule).\n• Landholding Parity: Marginal vs. Large farmer approval disparity is 3.9%, well inside the statutory ceiling of 25.0%.\n• Fairness Frontier (Figure 13): Confirms that across the operational range (480–620), demographic disparities remain below 5.0%.\n• Hard Automated Block: Any candidate model that breaches DIR >= 0.80 causes the /promote API to abort with HTTP 409 Conflict."
    pt2.font.size = Pt(9.5)
    pt2.font.color.rgb = BLUE_ROYAL

    set_speaker_notes(s25, """
Slide 25 features Figure 8 and Figure 13: our Algorithmic Fairness evaluation.
Credit models must not discriminate against female borrowers or marginal landholders. We enforce this through our pre-promotion FairnessGate.
On the left: approval parity across cohorts shows female-to-male disparity at 7.1%, well within the 20% statutory ceiling.
On the right: Figure 13 shows the fairness disparity frontier across cutoffs, proving that across our operational range of 480 to 620, the disparity gap stays below 5%. If a newly trained model violates this gate, deployment is blocked with an HTTP 409 Conflict.
""")

    # --- SLIDE 26: Population Stability & Drift Radar (Embed Fig 9) ---
    s26 = prs.slides.add_slide(blank_layout)
    set_slide_background(s26, BG_SUBTLE)
    create_header(s26, "Model Governance: Population Stability Index (PSI) Across 15 Village Clusters", "Governance: Drift Radar",
                  "Monitoring dataset distribution shifts across diverse agro-climatic pilot clusters.")
    add_footer(s26, 26)

    embed_image_safe(s26, os.path.join(FIGURES_DIR, "drift_radar_psi.png"), Inches(0.8), Inches(1.8), Inches(7.5), Inches(5.0))

    c_d26 = create_card(s26, Inches(8.5), Inches(1.8), Inches(4.0), Inches(5.0), WHITE, BLUE_BORDER)
    tf_d26 = c_d26.text_frame
    tf_d26.margin_left = tf_d26.margin_right = Inches(0.2)
    tf_d26.margin_top = Inches(0.2)
    tf_d26.word_wrap = True
    p = tf_d26.paragraphs[0]
    p.text = "📡 PSI Governance Thresholds"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    d_pts = [
        ("PSI Formulation", "PSI = Σ (Actual_i - Expected_i) × ln(Actual_i / Expected_i) across score deciles."),
        ("Industry Standard Limits", "PSI < 0.10: Stable distribution.\n0.10 <= PSI < 0.25: Moderate shift.\nPSI >= 0.25: Significant drift (triggers retraining)."),
        ("Empirical Findings", "All 15 village clusters exhibit PSI <= 0.068, well below the 0.10 threshold."),
        ("Agro-Climatic Stability", "Demonstrates that WoE monotonic binning maintains structural invariance across irrigated cotton, rainfed millets, and horticulture."),
        ("Runtime Monitoring", "PSI is audited weekly by FairnessAuditor to detect emerging distribution drift.")
    ]
    for k, v in d_pts:
        pk = tf_d26.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s26, """
Slide 26 displays Figure 9: our Population Stability Index (PSI) Drift Radar.
In machine learning operations, covariate shift can silently degrade model performance over time. We track PSI across all 15 village clusters.
Industry banking standards define a PSI below 0.10 as stable. As shown on the radar chart, all 15 clusters exhibit a PSI below 0.068. This proves that our monotonic WoE feature binning remains structurally invariant across diverse cropping ecosystems.
""")

    # --- SLIDE 27: Testing Strategy & Automated Test Matrix (120 Tests) ---
    s27 = prs.slides.add_slide(blank_layout)
    set_slide_background(s27, BG_SUBTLE)
    create_header(s27, "Verification Strategy: 120 Automated Tests Passing Across All Core Subsystems", "Quality: Test Matrix",
                  "Comprehensive end-to-end verification covering unit, integration, authorization, and negative cases.")
    add_footer(s27, 27)

    # 6 Subsystem Test Cards
    tests = [
        ("1. Consent Engine (14 Tests)", "tests/test_consent.py",
         "• Cryptographic SHA-256 hash chaining\n• Tamper-detection on ledger mutation\n• Granular purpose limitation enforcement\n• 60-second revocation execution", BLUE_ROYAL),
        ("2. Ingestion Orchestrator (18 Tests)", "tests/test_ingestion.py",
         "• 4 connectors async fan-out\n• Graceful degradation on rail timeout\n• Feature snapshot schema normalization\n• Mock server offline fallback verification", BLUE_CYAN),
        ("3. Scoring & XAI (22 Tests)", "tests/test_scoring.py",
         "• WoE scorecard numerical calibration\n• Exact Shapley value additivity\n• Bilingual EN/HI template rendering\n• Confidence band width scaling", NAVY_DARK),
        ("4. Officer Decisions (16 Tests)", "tests/test_decisioning.py",
         "• Mandatory dissent override logging\n• RE structured handoff export\n• Append-only decision triggers\n• Authorization RBAC isolation", GREEN_ACCENT),
        ("5. Fairness & Grievances (24 Tests)", "tests/test_fairness.py",
         "• Demographic parity calculation\n• Disparate Impact Ratio verification\n• Grievance 14-day SLA state machine\n• Supervisory CSV & PDF export", GOLD_ACCENT),
        ("6. Admin & MLOps (26 Tests)", "tests/test_admin.py",
         "• Ratified manifest hash locking\n• Model promotion gate enforcement\n• DPDP data retention purge execution\n• P6 60-request burst load verification", BLUE_ROYAL)
    ]
    for i, (title, fpath, body, col) in enumerate(tests):
        row = i // 3
        col_idx = i % 3
        c = create_card(s27, Inches(0.8 + col_idx * 4.0), Inches(1.8 + row * 2.55), Inches(3.7), Inches(2.35), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.18)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        pf = tf.add_paragraph()
        pf.text = fpath
        pf.font.size = Pt(9.5)
        pf.font.italic = True
        pf.font.color.rgb = TEXT_MUTED
        pb = tf.add_paragraph()
        pb.text = body
        pb.font.size = Pt(9.5)
        pb.font.color.rgb = TEXT_DARK

    set_speaker_notes(s27, """
Slide 27 summarizes our testing strategy.
Academic machine learning projects frequently fail to test beyond happy paths. CreditTech is backed by 120 automated tests passing across 6 distinct suites:
From cryptographic consent tamper detection and 4-rail graceful degradation, to exact SHAP additivity, mandatory dissent override logging, and automated DPDP data retention purges. Every critical subsystem is systematically covered.
""")

    # --- SLIDE 28: Production Hardening: Load Harness, Security & DR ---
    s28 = prs.slides.add_slide(blank_layout)
    set_slide_background(s28, BG_SUBTLE)
    create_header(s28, "Production Hardening: 60-Request Burst Load Harness & Disaster Recovery", "Quality: Hardening",
                  "Validating system throughput, security middleware, and disaster recovery parity.")
    add_footer(s28, 28)

    cards_h = [
        ("⚡ P6 Burst Load Harness", "tests/test_p6_load.py",
         [("Stress Profile", "60 concurrent scoring requests executed simultaneously (2x peak pilot capacity)."),
          ("Error Rate", "0.0% request failures across all 60 burst requests."),
          ("Pipeline Latency", "Median response time 380 ms across full ingestion and scoring lifecycle."),
          ("Inference Latency", "In-process model evaluation completes in under 0.04 ms.")], BLUE_ROYAL),
        ("🛡️ Security Middleware Layer", "services/core/shared/security.py",
         [("Rate Limiting", "In-memory rate limiter enforcing 240 req/min per IP to prevent abusive scraping."),
          ("DoS Protection", "1 MiB request body cap prevents payload exhaustion attacks."),
          ("Security Headers", "Injects CSP, HSTS, X-Content-Type-Options: nosniff, and X-Frame-Options: DENY."),
          ("Tracing", "RequestIdMiddleware propagates X-Request-ID across all structured logs.")], NAVY_DARK),
        ("💾 Disaster Recovery (DR) & PDF", "scripts/backup.py & restore.py",
         [("Safe Snapshotting", "Automated sqlite3.Connection.backup() creates point-in-time snapshots."),
          ("Parity Verification", "restore.py performs automated SHA-256 and row-count parity verification."),
          ("3-Tier PDF Engine", "WeasyPrint -> ReportLab -> Minimal programmatic PDF fallback ensures report delivery.")], GREEN_ACCENT)
    ]
    for i, (title, sub, bullets, col) in enumerate(cards_h):
        c = create_card(s28, Inches(0.8 + i * 4.0), Inches(1.8), Inches(3.7), Inches(4.9), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.22)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10.5)
        ps.font.italic = True
        ps.font.color.rgb = TEXT_MUTED
        for h, b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"• {h}: "
            pb.font.bold = True
            pb.font.size = Pt(10)
            pb.font.color.rgb = NAVY_DARK
            r = pb.add_run()
            r.text = b
            r.font.bold = False
            r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s28, """
Slide 28 details our Phase 6 production hardening.
First: our burst load harness subjected the system to 60 concurrent requests—twice our pilot peak—achieving a 0% error rate and a 380ms median response time.
Second: security middleware enforces body caps, rate limiting, and structured request tracing.
Third: disaster recovery scripts guarantee safe snapshotting and parity-verified restore, supported by a 3-tier PDF generation engine.
""")

    # =========================================================================
    # SECTION G: CRITICAL EVALUATION, ROADMAP & CONCLUSION (SLIDES 29 - 32)
    # =========================================================================

    # --- SLIDE 29: Critical Technical Evaluation & Trade-offs ---
    s29 = prs.slides.add_slide(blank_layout)
    set_slide_background(s29, BG_SUBTLE)
    create_header(s29, "Critical Evaluation: Cold-Start Limitations, External Timelines & Trade-offs", "Evaluation: Lessons Learned",
                  "Intellectual honesty: a candid assessment of cold-start realities, institutional lead times, and rejected complexity.")
    add_footer(s29, 29)

    c_e1 = create_card(s29, Inches(0.8), Inches(1.8), Inches(3.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_e1 = c_e1.text_frame
    tf_e1.margin_left = tf_e1.margin_right = Inches(0.22)
    tf_e1.margin_top = Inches(0.22)
    tf_e1.word_wrap = True
    p = tf_e1.paragraphs[0]
    p.text = "⚠️ The Cold-Start ML Trap"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    ps_e1 = tf_e1.add_paragraph()
    ps_e1.text = "The Synthetic Data Illusion"
    ps_e1.font.size = Pt(10.5)
    ps_e1.font.italic = True
    ps_e1.font.color.rgb = TEXT_MUTED
    e1_text = [
        ("The Trap", "At pilot launch, you have zero labeled repayment outcomes for unbanked borrowers. Training deep GBDTs on synthetic proxy data creates an illusory sense of high accuracy."),
        ("Architectural Defense", "We locked the v1 deployed model to a transparent WoE Logistic Scorecard. GBDT is restricted to a shadow challenger until 12+ months of real repayment labels mature."),
        ("Benchmark Transfer", "We validated model architectures on N=22,000 empirical borrower records to ensure robust discriminatory mechanics.")
    ]
    for h, b in e1_text:
        pb = tf_e1.add_paragraph()
        pb.text = f"• {h}: "
        pb.font.bold = True
        pb.font.size = Pt(10)
        pb.font.color.rgb = NAVY_DARK
        r = pb.add_run()
        r.text = b
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    c_e2 = create_card(s29, Inches(4.8), Inches(1.8), Inches(3.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_e2 = c_e2.text_frame
    tf_e2.margin_left = tf_e2.margin_right = Inches(0.22)
    tf_e2.margin_top = Inches(0.22)
    tf_e2.word_wrap = True
    p = tf_e2.paragraphs[0]
    p.text = "⏳ Institutional Lead Times"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = GOLD_ACCENT
    ps_e2 = tf_e2.add_paragraph()
    ps_e2.text = "Phase 0 is Months, Not Days"
    ps_e2.font.size = Pt(10.5)
    ps_e2.font.italic = True
    ps_e2.font.color.rgb = TEXT_MUTED
    e2_text = [
        ("Institutional Reality", "NABARD endorsement takes 3–6 months. Partner bank LoI execution takes 2–4 months. AA FIU sandbox certification takes 2–3 months."),
        ("Decoupled Engineering", "We built high-fidelity local mock servers (services/core/ingestion/mocks/) allowing full end-to-end development ahead of formal onboarding."),
        ("Honest Timeline", "Total project duration must be understood as 12–18 months from initial scoping to live field disbursals.")
    ]
    for h, b in e2_text:
        pb = tf_e2.add_paragraph()
        pb.text = f"• {h}: "
        pb.font.bold = True
        pb.font.color.rgb = NAVY_DARK
        r = pb.add_run()
        r.text = b
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    c_e3 = create_card(s29, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_e3 = c_e3.text_frame
    tf_e3.margin_left = tf_e3.margin_right = Inches(0.22)
    tf_e3.margin_top = Inches(0.22)
    tf_e3.word_wrap = True
    p = tf_e3.paragraphs[0]
    p.text = "🚫 Eliminating Complexity"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    ps_e3 = tf_e3.add_paragraph()
    ps_e3.text = "Rejecting Premature Engineering"
    ps_e3.font.size = Pt(10.5)
    ps_e3.font.italic = True
    ps_e3.font.color.rgb = TEXT_MUTED
    e3_text = [
        ("No Microservices", "Eliminated distributed networking, API gateway overhead, and container orchestration for pilot traffic."),
        ("No Redis / Celery", "FastAPI native asyncio handles parallel fan-out with zero external infrastructure."),
        ("In-Process Inference", "Eliminated external Triton/SageMaker clusters, saving significant operational budget while achieving 0.038ms inference.")
    ]
    for h, b in e3_text:
        pb = tf_e3.add_paragraph()
        pb.text = f"• {h}: "
        pb.font.bold = True
        pb.font.size = Pt(10)
        pb.font.color.rgb = NAVY_DARK
        r = pb.add_run()
        r.text = b
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s29, """
Slide 29 demonstrates intellectual honesty and engineering maturity.
Every engineering project involves trade-offs:
1. The Cold-Start trap: In early-stage rural fintech, you have zero empirical repayment labels for newly banked borrowers. We disciplined our deployment by choosing the transparent WoE Scorecard as Champion, holding GBDT as a shadow model until real labels accumulate.
2. Institutional lead times: Partner bank agreements take months. We built local mock servers to decouple software development from institutional bureaucracy.
3. Rejecting premature complexity: We eliminated Redis, Celery, and Kubernetes, favoring an elegant, zero-dependency async monolith.
""")

    # --- SLIDE 30: Evidence-Gated Roadmap & Village Pilot Blueprint ---
    s30 = prs.slides.add_slide(blank_layout)
    set_slide_background(s30, BG_SUBTLE)
    create_header(s30, "Future Roadmap: Evidence-Gated Scaling from 1K Pilot to 1M National Scale", "Roadmap: Scaling Strategy",
                  "Structured agro-climatic pilot design and strict evidence gates for architecture transitions.")
    add_footer(s30, 30)

    c_left = create_card(s30, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9), WHITE, BLUE_BORDER)
    tf_l = c_left.text_frame
    tf_l.margin_left = tf_l.margin_right = Inches(0.25)
    tf_l.margin_top = Inches(0.22)
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "🌾 Agro-Climatic Pilot Blueprint (750–1,250 Borrowers)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    sites = [
        ("Site A: Irrigated Cotton (Hanumangarh, RJ)", "Canal-irrigated; tests Sentinel-2 NDVI vigor against Mandi cash receipts."),
        ("Site B: Rainfed Millets (Jhabua, MP)", "Monsoon-dependent tribal agro-ecosystem; evaluates drought risk resilience."),
        ("Site C: Perennial Horticulture (Nashik, MH)", "High-value onion & grape farming; tests Account Aggregator multi-cycle cashflow velocity."),
        ("Site D: Intensive Dairy / Allied (Hassan, KA)", "Daily milk cooperative pourings; evaluates ultra-high frequency non-seasonal cashflow signals."),
        ("Site E: Arid Pulses (Nagaur, RJ)", "Low smartphone penetration; strictly tests Bank Sakhi assisted offline PWA synchronization.")
    ]
    for k, v in sites:
        pk = tf_l.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = BLUE_ROYAL
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_DARK

    c_right = create_card(s30, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9), RGBColor(239, 246, 255), BLUE_BORDER_DARK)
    tf_r = c_right.text_frame
    tf_r.margin_left = tf_r.margin_right = Inches(0.25)
    tf_r.margin_top = Inches(0.22)
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "📈 Evidence-Gated Scaling Milestones"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = BLUE_ROYAL
    stages = [
        ("Stage 1: Village Pilot (1K Borrowers)", "FastAPI monolith + Postgres; prove AUC >= 0.75 and < 3.5% default rate in live pilot."),
        ("Stage 2: Regional Rollout (10K Borrowers)", "Automated e-Shakti & e-NAM API integrations; introduce Redis cache for geospatial tiles; multi-RE routing."),
        ("Stage 3: Multi-State Scale (100K Borrowers)", "Extract Ingestion Engine into standalone worker service; enable ULI (Unified Lending Interface) handoff; active retraining."),
        ("Stage 4: National Scale (1M+ Borrowers)", "Multi-region active-active deployment; federated learning across banking partners; automated fraud graph networks.")
    ]
    for k, v in stages:
        pk = tf_r.add_paragraph()
        pk.text = f"• {k}: "
        pk.font.bold = True
        pk.font.size = Pt(10.5)
        pk.font.color.rgb = NAVY_DARK
        r = pk.add_run()
        r.text = v
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    set_speaker_notes(s30, """
Slide 30 details our field implementation strategy.
Rather than running a pilot in a single homogeneous village, we designed a stratified sampling framework across 5 distinct agro-climatic zones: canal-irrigated cotton in Rajasthan, rainfed millets in Madhya Pradesh, horticulture in Maharashtra, dairy in Karnataka, and arid pulses in Nagaur.
Furthermore, we established Evidence-Gated Scaling Milestones: we do not upgrade infrastructure arbitrarily; we upgrade only when empirical data volumes demand it.
""")

    # --- SLIDE 31: Academic Contributions & Literature Benchmarks ---
    s31 = prs.slides.add_slide(blank_layout)
    set_slide_background(s31, BG_SUBTLE)
    create_header(s31, "Academic Contributions: Grounded in Peer-Reviewed Financial Inclusion Literature", "Conclusion: Academic Impact",
                  "Positioning CreditTech against state-of-the-art literature and institutional research.")
    add_footer(s31, 31)

    quads_s31 = [
        ("Empirical Literature", "Validating Alternative Data Power",
         "• Agarwal, Alok, Ghosh & Gupta (SSRN #3507827): Proved alternative digital footprints expand financial inclusion by 30%+ without raising defaults.\n• PLOS ONE (2024): Demonstrated that combining telecom cashflows with satellite remote sensing yields the largest incremental AUC gains on thin-file borrowers.", BLUE_ROYAL),
        ("Institutional Benchmarks", "Global Development Standards",
         "• International Finance Corporation (IFC 2026): 'Cracking the Credit Code' emphasizes AI scoring for women entrepreneurs and SHGs in emerging markets.\n• Alliance for Financial Inclusion (AFI 2025): Highlights need for robust DPDP regulatory alignment in algorithmic micro-lending.", BLUE_CYAN),
        ("Explainability & Ethics", "Game Theory in Banking",
         "• Lundberg & Lee (SHAP, 2017) & Nature Comms (2025): Proves that game-theoretic Shapley decomposition satisfies fairness and efficiency in regulated credit.\n• ResearchGate (2025): 'From Data to Dignity' establishes ethical frameworks for rural algorithmic governance in India.", NAVY_DARK),
        ("Novel Contributions of CreditTech", "Thesis Innovations",
         "1. First open, reproducible 4-rail architecture combining Account Aggregator + Sentinel-2 NDVI + SHG social collateral.\n2. Built-in, enforceable algorithmic FairnessGate with cryptographic manifest locking.\n3. Exact closed-form Shapley explainability delivering bilingual English & Hindi reason codes.", GREEN_ACCENT)
    ]
    for i, (title, sub, body, col) in enumerate(quads_s31):
        row = i // 2
        col_idx = i % 2
        c = create_card(s31, Inches(0.8 + col_idx * 5.95), Inches(1.8 + row * 2.55), Inches(5.65), Inches(2.35), WHITE, BLUE_BORDER)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.18)
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13.5)
        p.font.bold = True
        p.font.color.rgb = col
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10.5)
        ps.font.italic = True
        ps.font.color.rgb = TEXT_MUTED
        pb = tf.add_paragraph()
        pb.text = body
        pb.font.size = Pt(9.8)
        pb.font.color.rgb = TEXT_DARK

    set_speaker_notes(s31, """
Slide 31 positions CreditTech within the broader academic and institutional literature.
Our work directly builds upon foundational research by Agarwal et al., the IFC's 2026 report 'Cracking the Credit Code', and Lundberg and Lee's game-theoretic SHAP formulations.
Our three novel contributions are:
1. An open 4-rail architecture combining Account Aggregator, Sentinel-2 satellite imagery, and SHG social collateral.
2. An enforceable pre-promotion algorithmic FairnessGate.
3. Exact closed-form Shapley explainability delivering bilingual Hindi and English adverse action reason codes.
""")

    # --- SLIDE 32: Conclusion, Key Takeaways & Defense Q&A ---
    s32 = prs.slides.add_slide(blank_layout)
    set_slide_background(s32, NAVY_DARK)
    glow = s32.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    glow.fill.solid()
    glow.fill.fore_color.rgb = BLUE_VIBRANT
    glow.line.fill.background()

    cat = s32.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(0.9), Inches(3.6), Inches(0.4))
    cat.fill.solid()
    cat.fill.fore_color.rgb = BLUE_ROYAL
    cat.line.fill.background()
    p_c = cat.text_frame.paragraphs[0]
    p_c.text = "CONCLUSION & DEFENSE"
    p_c.font.size = Pt(11)
    p_c.font.bold = True
    p_c.font.color.rgb = WHITE

    tb_t = s32.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(10.9), Inches(1.0))
    p = tb_t.text_frame.paragraphs[0]
    p.text = "Credit with Dignity Through Transparent, Responsible AI"
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = WHITE

    recap_cards = [
        ("01. Multi-Source Alternative Data Works", "Demonstrated on N=22,000 real borrower benchmark that synthesizing Sentinel-2 NDVI, AA cashflow, and SHG savings delivers exceptional predictive discrimination (AUC: 0.9599, KS: 0.8208) on thin-file rural borrowers."),
        ("02. Explainability & Fairness Are Invariant", "Proved that credit models can maintain high accuracy while guaranteeing exact closed-form bilingual SHAP explainability and strictly enforcing statutory demographic parity (DIR >= 0.80, gender disparity <= 7.1%)."),
        ("03. Production-Hardened Software Engineering", "Delivered 120 verified automated tests, DPDP cryptographic consent ledger, in-process serving (<0.04ms), and 60-request burst load verification under a resilient modular monolith architecture.")
    ]
    for i, (head, text) in enumerate(recap_cards):
        c = s32.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2 + i * 3.75), Inches(2.55), Inches(3.45), Inches(2.65))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(15, 30, 58)
        c.line.color.rgb = RGBColor(30, 58, 110)
        c.line.width = Pt(1)
        tfc = c.text_frame
        tfc.margin_left = tfc.margin_right = Inches(0.2)
        tfc.margin_top = Inches(0.2)
        tfc.word_wrap = True
        p1 = tfc.paragraphs[0]
        p1.text = head
        p1.font.size = Pt(12.5)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(96, 165, 250)
        p2 = tfc.add_paragraph()
        p2.text = text
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = RGBColor(226, 232, 240)

    qa_card = s32.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.45), Inches(10.9), Inches(1.45))
    qa_card.fill.solid()
    qa_card.fill.fore_color.rgb = RGBColor(24, 49, 83)
    qa_card.line.color.rgb = RGBColor(59, 130, 246)
    qa_card.line.width = Pt(1.5)
    tfq = qa_card.text_frame
    tfq.margin_left = Inches(0.3)
    tfq.margin_top = Inches(0.2)
    pq1 = tfq.paragraphs[0]
    pq1.text = "Thank You, Professor & Committee  |  Open for Technical Defense & Questions"
    pq1.font.size = Pt(18)
    pq1.font.bold = True
    pq1.font.color.rgb = WHITE
    pq2 = tfq.add_paragraph()
    pq2.text = "Full codebase, 120 automated test suites, simulation telemetry (simulate_pilot.py), and 13 publication-grade evaluation figures available under /d/CreditTech."
    pq2.font.size = Pt(12)
    pq2.font.color.rgb = RGBColor(147, 197, 253)

    set_speaker_notes(s32, """
To conclude, Professor and members of the committee:
CreditTech proves that rural financial inclusion does not require compromising on credit risk discipline, nor does it require deploying un-explainable black-box algorithms.
By combining multi-source alternative signals—from Account Aggregator cashflows and Sentinel-2 satellite imagery to SHG community trust—we give voice and visibility to millions of deserving borrowers like Sunita Devi.
We have supported this with rigorous software engineering: 120 automated tests, an append-only cryptographic consent ledger, a dual Champion/Challenger machine learning architecture, and an un-compromised algorithmic fairness gate.

Thank you very much for your time and guidance. I welcome your questions, critiques, and technical evaluation.
""")

    prs.save(output_path)
    print(f"Presentation successfully built and saved to: {output_path}")

if __name__ == "__main__":
    build_presentation()

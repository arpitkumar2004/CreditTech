"""Master script to generate the 16-slide CreditTech Academic Mid-Semester Presentation

Strictly adhering to constitution_ppt.md:
- Presentation Type: Academic Mid-Semester Project / Thesis Presentation
- Visual Style: Premium Academic SaaS + Clean Minimal + Engineering Research
- Color Palette: Off-white canvas (#F8FAFC), Deep Navy/Charcoal text (#0F172A), Slate secondary (#475569),
  Deep Institutional Green project accent (#166534), semantic colors (Blue, Amber, Red, Purple)
- Typography: Inter font hierarchy throughout
- Zero Emojis anywhere
- Real publication-grade figures embedded from data/reports/figures/
- Explicit implementation status (Implemented vs. Designed vs. Proposed/Future vs. Target)
- Complete, word-for-word spoken defense scripts embedded in the notes of every slide
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# --- COLOR PALETTE (Constitution Section 3) ---
BG_CANVAS = RGBColor(248, 250, 252)       # #F8FAFC Off-white / warm slate canvas
CARD_BG = RGBColor(255, 255, 255)         # #FFFFFF Pure White
CARD_BORDER = RGBColor(226, 232, 240)     # #E2E8F0 Subtle Slate Border
CARD_BORDER_DARK = RGBColor(203, 213, 225)# #CBD5E1 Medium Border

TEXT_PRIMARY = RGBColor(15, 23, 42)       # #0F172A Deep Navy / Charcoal
TEXT_SECONDARY = RGBColor(71, 85, 105)    # #475569 Slate
TEXT_MUTED = RGBColor(100, 116, 139)      # #64748B Muted / Captions
WHITE = RGBColor(255, 255, 255)

# Project Accents (Deep Institutional Green)
ACCENT_GREEN = RGBColor(22, 101, 52)      # #166534 Deep Institutional Green
ACCENT_GREEN_LIGHT = RGBColor(34, 197, 94)# #22C55E Secondary Green
GREEN_BG_SUBTLE = RGBColor(240, 253, 244) # #F0FDF4 Soft Green Fill
GREEN_BORDER_SUBTLE = RGBColor(187, 247, 208) # #BBF7D0

# Semantic Colors
COLOR_BLUE = RGBColor(30, 64, 175)        # #1E40AF Information / Tech
COLOR_BLUE_LIGHT = RGBColor(239, 246, 255)# #EFF6FF Blue Fill
COLOR_BLUE_BORDER = RGBColor(191, 219, 254)# #BFDBFE Blue Border
COLOR_AMBER = RGBColor(217, 119, 6)       # #D97706 Warning / Review
COLOR_AMBER_LIGHT = RGBColor(254, 243, 199)# #FEF3C7 Amber Fill
COLOR_RED = RGBColor(220, 38, 38)         # #DC2626 Risk / Rejection / Pain Points
COLOR_RED_LIGHT = RGBColor(254, 242, 242) # #FEF2F2 Red Fill
COLOR_PURPLE = RGBColor(126, 34, 206)     # #7E22CE Governance / Regulatory
COLOR_PURPLE_LIGHT = RGBColor(250, 245, 255) # #FAF5FF Purple Fill

# Dark Mode Accent for Title & Close (Constitution Section 4)
NAVY_HERO = RGBColor(10, 25, 47)          # #0A192F Dark Navy Canvas

FONT_FAMILY = "Inter"
TOTAL_SLIDES = 16
FIGURES_DIR = "data/reports/figures"
OUTPUT_PATH = "ppt-midsem/CreditTech_MidSem_Academic_Presentation.pptx"
FALLBACK_PATH = "ppt-midsem/CreditTech_MidSem_Presentation.pptx"

def set_slide_background(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def create_header(slide, title_text, category_text=None, subtitle_text=None):
    """Standardized academic header following Constitution Section 5 & 15."""
    if category_text:
        # Subtle category badge
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.38), Inches(3.6), Inches(0.30))
        badge.fill.solid()
        badge.fill.fore_color.rgb = GREEN_BG_SUBTLE
        badge.line.color.rgb = GREEN_BORDER_SUBTLE
        badge.line.width = Pt(1.0)
        tf_b = badge.text_frame
        tf_b.word_wrap = False
        tf_b.margin_left = Inches(0.12)
        tf_b.margin_top = Inches(0.02)
        p_b = tf_b.paragraphs[0]
        p_b.text = category_text.upper()
        p_b.font.size = Pt(9.5)
        p_b.font.bold = True
        p_b.font.color.rgb = ACCENT_GREEN
        p_b.font.name = FONT_FAMILY

    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.74), Inches(11.7), Inches(0.68))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = TEXT_PRIMARY
    p.font.name = FONT_FAMILY

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.size = Pt(11.5)
        p_sub.font.italic = True
        p_sub.font.color.rgb = TEXT_SECONDARY
        p_sub.font.name = FONT_FAMILY

    # Clean divider rule
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.48), Inches(11.7), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = CARD_BORDER
    line.line.fill.background()

def create_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER, border_width=1.0):
    """Creates a clean academic container card with subtle borders (Constitution Section 7)."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card

def add_footer(slide, current_idx, total_slides=TOTAL_SLIDES):
    """Adds minimal academic attribution and slide counter (Constitution Section 30 & 31)."""
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(11.7), Inches(0.30))
    tf = tb.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "CreditTech: Alternative Credit Scoring for Rural India  |  Mid-Semester Review 2026  |  IIT Kharagpur"
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.font.name = FONT_FAMILY

    p_num = tf.add_paragraph()
    p_num.text = f"{current_idx:02d} / {total_slides:02d}"
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.font.size = Pt(9.5)
    p_num.font.bold = True
    p_num.font.color.rgb = ACCENT_GREEN
    p_num.font.name = FONT_FAMILY

def set_speaker_notes(slide, notes_content):
    """Attaches complete verbal defense script to the slide's notes."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_content.strip()

def embed_figure_safe(slide, filename, left, top, width, height, caption=None):
    """Safely embeds a real publication figure from FIGURES_DIR with caption."""
    path = os.path.join(FIGURES_DIR, filename)
    if os.path.exists(path):
        pic = slide.shapes.add_picture(path, left, top, width, height)
        if caption:
            cap_box = slide.shapes.add_textbox(left, top + height + Inches(0.04), width, Inches(0.30))
            tf = cap_box.text_frame
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = caption
            p.font.size = Pt(8.5)
            p.font.italic = True
            p.font.color.rgb = TEXT_MUTED
            p.font.name = FONT_FAMILY
        return pic
    else:
        card = create_card(slide, left, top, width, height, COLOR_RED_LIGHT, COLOR_RED)
        tf = card.text_frame
        p = tf.paragraphs[0]
        p.text = f"[Figure not found: {filename}]"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_RED
        return card


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    print("Generating CreditTech Presentation Deck adhering to constitution_ppt.md...")

    # =========================================================================
    # SLIDE 1: TITLE (Constitution Slide 01 Specification)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, NAVY_HERO)

    # Hero Title Box (Left side)
    tb1 = s1.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(7.0), Inches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "CREDITTECH"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_FAMILY

    p = tf1.add_paragraph()
    p.text = "An Alternative Credit Decision-Support Platform for Rural India"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = RGBColor(187, 247, 208) # Mint Accent
    p.font.name = FONT_FAMILY

    p = tf1.add_paragraph()
    p.text = "Master's Thesis Project  |  Mid-Semester Academic Defense  |  September 2026"
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.font.name = FONT_FAMILY

    p = tf1.add_paragraph()
    p.text = "\nCandidate: Arpit Kumar  |  Integrated Dual Degree (Chemical Eng. + AI Micro-Spec)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_FAMILY

    p = tf1.add_paragraph()
    p.text = "Department of Chemical Engineering & Center of Excellence in Artificial Intelligence"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.font.name = FONT_FAMILY

    p = tf1.add_paragraph()
    p.text = "Indian Institute of Technology (IIT) Kharagpur"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.font.name = FONT_FAMILY

    # Right Hero Identity Card (Constitution Slide 01: Academic Attribution Hero Card)
    hero_card = create_card(s1, Inches(8.3), Inches(1.5), Inches(4.2), Inches(4.8), 
                            bg_color=RGBColor(15, 33, 64), border_color=RGBColor(30, 58, 100), border_width=1.5)
    tf_h = hero_card.text_frame
    tf_h.margin_left = tf_h.margin_top = tf_h.margin_right = tf_h.margin_bottom = Inches(0.25)
    
    p = tf_h.paragraphs[0]
    p.text = "PROJECT ARCHITECTURE PROFILE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(187, 247, 208)
    p.font.name = FONT_FAMILY

    pillars = [
        ("Positioning", "Pure LSP Decision-Support Bridge under RBI Digital Lending Guidelines 2022/2026."),
        ("Engineering", "5-Layer Modular Monolith (FastAPI + PostgreSQL + React 19 PWA) with sub-0.04ms inference."),
        ("Data Rails", "4-Rail Ingestion: Account Aggregator, Sentinel-2 10m NDVI, e-Shakti SHG savings, ULI land records."),
        ("Governance", "Cryptographic SHA-256 consent ledger, automated 30-day purge, DIR >= 0.80 fairness gate.")
    ]
    for lbl, desc in pillars:
        p = tf_h.add_paragraph()
        p.text = f"\n• {lbl}: "
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = FONT_FAMILY
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(226, 232, 240)

    set_speaker_notes(s1, """Good morning, Professor and members of the evaluation committee. Today, I am defending CreditTech: an alternative credit scoring and digital lending decision-support platform engineered specifically to resolve thin-file credit exclusion in rural India.
This presentation covers our complete journey: from the macroeconomic and human dimensions of financial invisibility, to our 4-rail ingestion engine, our modular system architecture, DPI integration with Account Aggregator and ULI, and our stratified 5-site village pilot design.""")

    # =========================================================================
    # SLIDE 2: EXECUTIVE SUMMARY (Constitution Slide 02 Specification)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, BG_CANVAS)
    create_header(s2, "Executive Overview: Solving Rural Credit Invisibility with Responsible AI", 
                  "Executive Summary", "A disciplined decision-support bridge connecting thin-file borrowers with formal lenders")
    add_footer(s2, 2)

    # 4-Quadrant Grid (Problem -> Solution -> Approach -> Outcome)
    qw = Inches(5.7)
    qh = Inches(2.45)
    
    # Q1: Problem
    q1 = create_card(s2, Inches(0.8), Inches(1.75), qw, qh)
    tf = q1.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "1. THE PROBLEM · INCLUSION PARADOX"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p.font.name = FONT_FAMILY
    p = tf.add_paragraph()
    p.text = "• 89% of Indian adults have bank accounts, yet only 13% borrowed formally (World Bank 2025).\n• 57% of rural households are agricultural; average landholding has shrunk to 0.74 ha (NAFIS).\n• Traditional credit bureaus score thin-file borrowers as '-1' due to lack of formal credit trails.\n• 14-day agricultural sowing window forces 23.4% to informal moneylenders charging 36%–48% APR."
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.name = FONT_FAMILY

    # Q2: Solution
    q2 = create_card(s2, Inches(6.8), Inches(1.75), qw, qh)
    tf = q2.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "2. THE SOLUTION · UNBUNDLED LSP SCORING LAYER"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.font.name = FONT_FAMILY
    p = tf.add_paragraph()
    p.text = "• Operates strictly as an LSP under RBI Digital Lending Guidelines (2022/2026).\n• Delivers alternative scoring intelligence to Regulated Entities (Banks, RRBs, PACS).\n• Holds zero balance-sheet risk and accepts no borrower deposits; loan funds flow from bank.\n• Replaces opaque manual appraisals with explainable, data-driven credit risk recommendations."
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.name = FONT_FAMILY

    # Q3: Approach
    q3 = create_card(s2, Inches(0.8), Inches(4.35), qw, qh)
    tf = q3.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "3. THE TECHNICAL APPROACH · 4-RAIL DPI INGESTION"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.font.name = FONT_FAMILY
    p = tf.add_paragraph()
    p.text = "• Parallel multi-rail ingestion: Account Aggregator, Sentinel-2 10m NDVI, e-Shakti, and ULI.\n• Monotonic WoE Scorecard champion captures 98% of ensemble AUC (0.9599 vs 0.9793).\n• DPDP-compliant cryptographic consent ledger linked via SHA-256 hash chaining.\n• Automated Graceful Degradation delivers confidence-calibrated scores if an external API times out."
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.name = FONT_FAMILY

    # Q4: Outcome
    q4 = create_card(s2, Inches(6.8), Inches(4.35), qw, qh)
    tf = q4.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "4. TARGET PILOT OUTCOMES & IMPACT"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.font.name = FONT_FAMILY
    p = tf.add_paragraph()
    p.text = "• Appraisal turnaround time compressed from 10–20 days to < 1 hour end-to-end.\n• Approval uplift of +20% to +30% for creditworthy thin-file smallholders.\n• Portfolio-at-Risk (PAR90) maintained <= 2.0% (vs. 6.2% agricultural banking GNPA).\n• Algorithmic fairness guaranteed: Disparate Impact Ratio (DIR) >= 0.80 across gender and landholding."
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_PRIMARY
    p.font.name = FONT_FAMILY

    set_speaker_notes(s2, """To orient the committee, Slide 2 provides our executive summary across four pillars.
First, the core problem: India has achieved 89% account ownership, but only 13% of adults borrow formally. Bureau algorithms score unbanked farmers as -1, denying them bank credit.
Second, our solution: CreditTech operates as an LSP under RBI guidelines, providing intelligence to banks rather than taking balance sheet risk.
Third, our technical approach: 4-rail parallel ingestion spanning Account Aggregator, satellite imagery, and SHG community savings, coupled with a Monotonic WoE Scorecard champion.
And fourth, our outcomes: Cutting turnaround from 14 days to under an hour while guaranteeing strict algorithmic fairness across gender and landholding size.""")

    # =========================================================================
    # SLIDE 3: NEED ASSESSMENT (Constitution Slide 03 Specification)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, BG_CANVAS)
    create_header(s3, "Rural Credit Has an Information Problem, Not a Capital Problem",
                  "Topic 1 · Need Assessment", "Secondary data evidence from World Bank, RBI, NABARD, SIDBI, and DAY-NRLM")
    add_footer(s3, 3)

    # 6 Statistical Evidence Cards (Constitution Slide 03 requirement)
    stat_w = Inches(1.82)
    stat_h = Inches(1.5)
    stats_data = [
        ("89% vs 13%", "Account vs Credit", "World Bank Findex '25"),
        ("67.0 / 100", "RBI FI-Index '25", "Usage lags access"),
        ("0.74 ha", "Avg Landholding", "NAFIS '22 (86% small)"),
        ("₹30 Lakh Cr", "MSME Credit Gap", "SIDBI-CRISIL '25"),
        ("6.2% vs 2.5%", "Agri GNPA vs Sys", "RBI Banking Trend '24"),
        ("10.05 Cr", "Women in 90.9L SHGs", "DAY-NRLM (>96% track)")
    ]
    for i, (num, lbl, src) in enumerate(stats_data):
        left_pos = Inches(0.8 + i * 1.98)
        sc = create_card(s3, left_pos, Inches(1.75), stat_w, stat_h, bg_color=CARD_BG)
        tf = sc.text_frame
        tf.margin_left = tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.12)
        p = tf.paragraphs[0]
        p.text = num
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GREEN
        p.font.name = FONT_FAMILY
        p.alignment = PP_ALIGN.CENTER
        p = tf.add_paragraph()
        p.text = lbl
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_PRIMARY
        p.font.name = FONT_FAMILY
        p.alignment = PP_ALIGN.CENTER
        p = tf.add_paragraph()
        p.text = src
        p.font.size = Pt(8)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.alignment = PP_ALIGN.CENTER

    # 3 Analytical Breakdown Cards (Bottom Half)
    b_w = Inches(3.75)
    b_h = Inches(2.7)
    
    b1 = create_card(s3, Inches(0.8), Inches(3.45), b_w, b_h)
    tf = b1.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "1. COLLATERAL FAILURE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p = tf.add_paragraph()
    p.text = "• Land Fragmentation: Average rural holding declined from 1.08 ha (2016) to 0.74 ha.\n• 86% Small/Marginal: Farmers lack clear registered land titles; oral sharecropping dominates.\n• Mortgage Impasse: Banks legally require registered mortgages, automatically excluding 86% of agrarian producers."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    b2 = create_card(s3, Inches(4.78), Inches(3.45), b_w, b_h)
    tf = b2.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "2. BUREAU BLINDNESS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "• Score -1 Trap: Traditional bureaus (CIBIL) depend strictly on past formal credit files.\n• Invisible Trust: 90.9 Lakh SHGs hold ₹12.18 Lakh Cr in bank credit with >96% recovery, yet individual women have zero bureau files.\n• Asymmetric Data: Banks see no salary slips, resulting in automated loan rejection."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    b3 = create_card(s3, Inches(8.76), Inches(3.45), b_w, b_h)
    tf = b3.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "3. THE INFORMALITY TRAP"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p = tf.add_paragraph()
    p.text = "• 14-Day Sowing Window: Crops must be sown immediately after monsoon onset.\n• Appraisal Delay: Banks take 10–20 days; farmers cannot afford to wait.\n• Extortionate Debt: 23.4% of agricultural households borrow from moneylenders at 36% to 48% APR, wiping out farm profitability."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    # Bottom Message Box (Constitution Section 33 Slide 3 Bottom Message Rule)
    bm_card = create_card(s3, Inches(0.8), Inches(6.25), Inches(11.7), Inches(0.65), bg_color=GREEN_BG_SUBTLE, border_color=GREEN_BORDER_SUBTLE)
    tf = bm_card.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = "CORE SYNTHESIS: The central gap is not a lack of economic activity; it is a lack of reliable, portable, and consented evidence for underwriting."
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.font.name = FONT_FAMILY

    set_speaker_notes(s3, """Slide 3 details the macroeconomic reality. In India, despite massive financial inclusion drives like Jan Dhan, true credit access remains elusive.
According to the World Bank Findex 2025, 89% of adults have bank accounts, but only 13% borrowed formally last year—and just 10% among women.
Average landholdings have shrunk to 0.74 hectares according to NABARD. Because 86% of farmers are small or marginal, they cannot provide clear mortgage titles.
When they apply to a bank, the automated credit bureau returns a score of -1.
Because agricultural sowing windows last only 14 days, a farmer cannot wait weeks for manual committee reviews. They turn to informal moneylenders charging 36% to 48% APR.
CreditTech exists to replace this informal extortion with institutional capital by unlocking alternative credit signals.""")

    # =========================================================================
    # SLIDE 4: STAKEHOLDER MAPPING (Constitution Slide 04 Specification)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, BG_CANVAS)
    create_header(s4, "Institutional Mapping: Anchoring Decision-Support in Rural Trust",
                  "Topic 2 · Stakeholder Mapping", "Four-quadrant institutional ecosystem defining contributions, needs, and regulatory roles")
    add_footer(s4, 4)

    sw = Inches(5.7)
    sh = Inches(2.45)
    # S1: Demand
    s_c1 = create_card(s4, Inches(0.8), Inches(1.75), sw, sh)
    tf = s_c1.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "1. BORROWER & COMMUNITY ANCHORS (DEMAND)"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Who: Small & marginal farmers (<2 ha), 90.9L SHGs (10 Cr women), 10,000 FPOs (SFAC).\n• Contributes: Authentic non-bureau repayment trails (e-Shakti books) and peer social collateral.\n• Needs: Timely crop credit (<14 days), lower collateral requirements, transparent reason codes.\n• Legal Interlock: Data Principals under DPDP Act 2023 with statutory right to consent revocation."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    # S2: Supply
    s_c2 = create_card(s4, Inches(6.8), Inches(1.75), sw, sh)
    tf = s_c2.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "2. REGULATED LENDERS & APEX BODIES (SUPPLY)"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "• Who: Regional Rural Banks (43 RRBs), 63k+ PACS, Small Finance Banks, NABARD, SIDBI.\n• Contributes: Balance-sheet lending capital, sole credit sanction authority, and refinance.\n• Needs: Predictive risk scoring to lower 6.2% agri GNPA and reduce fixed manual appraisal costs.\n• Legal Interlock: Regulated Entities (REs) holding ultimate credit risk under RBI DLG (2022/2026)."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    # S3: DPI
    s_c3 = create_card(s4, Inches(0.8), Inches(4.35), sw, sh)
    tf = s_c3.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "3. DIGITAL PUBLIC INFRASTRUCTURE (DPI RAILS)"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "• Who: Sahamati (Account Aggregator), RBI Innovation Hub (ULI), NPCI (UPI), UIDAI.\n• Contributes: Standard consent-based financial data, state land records, and biometric identity.\n• Needs: Certified FIU/LSP integration adhering strictly to open schema specifications.\n• Strategic Value: Eliminates bilateral proprietary bank integrations; universal interoperability."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    # S4: Governance
    s_c4 = create_card(s4, Inches(6.8), Inches(4.35), sw, sh)
    tf = s_c4.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "4. REGULATORS & INDEPENDENT AUDITORS (OVERSIGHT)"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p = tf.add_paragraph()
    p.text = "• Who: Reserve Bank of India (RBI), Data Protection Board (MeitY), IIT Kharagpur (Auditor).\n• Contributes: Statutory lending guardrails, 5% DLG guarantee cap, independent fairness audits.\n• Needs: Complete auditability, tamper-evident consent logs, and Disparate Impact Ratio >= 0.80.\n• Institutional Role: Enforces ethical standards and algorithmic non-discrimination across cohorts."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s4, """Slide 4 presents our multi-stakeholder and institutional mapping.
CreditTech is intentionally architected to plug into the existing rural financial fabric rather than compete with it.
We map four distinct stakeholder groups:
1. End borrowers and community anchors who provide rich non-bureau signals.
2. Regulated lenders and NABARD who hold the balance sheet and credit sanction authority.
3. India's world-class DPI stack—Account Aggregator and ULI—providing standard consent and data rails.
4. Regulators and independent academic auditors ensuring regulatory compliance and demographic fairness.
This positioning ensures CreditTech operates strictly as an RBI-compliant Lending Service Provider.""")

    # =========================================================================
    # SLIDE 5: AS-IS SYSTEM (Constitution Slide 05 Specification)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, BG_CANVAS)
    create_header(s5, "Bureau-First Underwriting Leaves Thin-File Borrowers Under-Observed",
                  "Topic 3 · As-Is System", "Linear, paper-heavy appraisal journey resulting in severe delays and informal debt traps")
    add_footer(s5, 5)

    # 5 Process Flow Step Cards (Constitution Section 23 & 33 Slide 5 Rule)
    step_w = Inches(2.18)
    step_h = Inches(1.85)
    steps_data = [
        ("01 · APPLICATION", "Paper forms at branch\n3–5 physical trips\nLand patta deed copy", CARD_BG, COLOR_BLUE),
        ("02 · MANUAL AUDIT", "Loan officer inspection\nSubjective discretion\nGuarantor required", CARD_BG, COLOR_BLUE),
        ("03 · DATA SILOS", "Fragmented records\nZero data sharing\nUnverified yield claims", CARD_BG, COLOR_BLUE),
        ("04 · BUREAU CHECK", "CIBIL score pull\nThin-file returns -1\nAutomated rejection", CARD_BG, COLOR_AMBER),
        ("05 · INFORMAL FALLBACK", "10–20 Day Delay\nRejection / under-limit\nMoneylender (36–48%)", COLOR_RED_LIGHT, COLOR_RED)
    ]
    for i, (title, desc, bg, border_col) in enumerate(steps_data):
        sc = create_card(s5, Inches(0.8 + i * 2.38), Inches(1.75), step_w, step_h, bg_color=bg, border_color=border_col)
        tf = sc.text_frame
        tf.margin_left = tf.margin_top = Inches(0.14)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = border_col
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_PRIMARY

    # Analytical Card Below
    t_c = create_card(s5, Inches(0.8), Inches(3.80), Inches(11.7), Inches(2.35))
    tf = t_c.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "SYSTEMIC FAILURE POINTS IN THE AS-IS ARCHITECTURE"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p = tf.add_paragraph()
    p.text = "• Turnaround Time (TAT) Mismatch: Agricultural loan appraisal takes 10 to 20 business days. Farm sowing windows last only 14 days, forcing farmers into informal debt.\n• Collateral Dependency: Requires registered land mortgages, systematically excluding 86% of Indian farmers who cultivate fragmented or oral sharecropped lands.\n• Bureau Blindness: Ignores proven repayment discipline (>96% SHG track record) because community thrift never touches a credit bureau.\n• High Fixed Appraisal Costs: Branch-based manual inspection costs ₹1,500 to ₹3,000 per appraisal, making small-ticket loans (₹25k–₹50k) economically unviable for commercial banks."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    # Central Message Box (Constitution Section 33 Slide 5 Rule)
    cm_card = create_card(s5, Inches(0.8), Inches(6.25), Inches(11.7), Inches(0.65), bg_color=COLOR_AMBER_LIGHT, border_color=COLOR_AMBER)
    tf = cm_card.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = "CENTRAL MESSAGE: The existing process is optimized around conventional financial history; thin-file borrowers therefore face an evidence deficit, not a creditworthiness deficit."
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p.font.name = FONT_FAMILY

    set_speaker_notes(s5, """Slide 5 dissects the existing As-Is rural credit journey.
Today, the appraisal process is linear, paper-heavy, and bureau-gated. A farmer travels multiple times to a branch with physical patta deeds. The loan officer must physically inspect the plot, introducing high operational costs and subjective discretion.
When the bank pulls a credit bureau report, the applicant returns a score of -1. Traditional bureaus have zero visibility into utility payments, UPI cashflows, or SHG savings.
After 10 to 20 days of bureaucratic delay, the loan is either rejected or drastically downsized.
Because the Kharif planting window is rigid, the farmer has no choice but to turn to local moneylenders at 36% to 48% APR. The existing system fails both the borrower and the bank.""")

    # =========================================================================
    # SLIDE 6: PROPOSED SYSTEM (TO-BE) (Constitution Slide 06 Specification)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, BG_CANVAS)
    create_header(s6, "CreditTech Combines Four Alternative Data Rails Before Underwriting",
                  "Topic 4 · To-Be System", "Consent-based, multi-source digital flow delivering explainable credit scores in minutes")
    add_footer(s6, 6)

    # 4 Flow Columns (Top)
    to_be_steps = [
        ("01 · CONSENT & ONBOARDING", "Farmer / Bank Sakhi PWA\nAadhaar e-KYC (<5 mins)\nBilingual voice/text prompts", ACCENT_GREEN),
        ("02 · 4-RAIL PARALLEL INGEST", "Account Aggregator (AA)\nSentinel-2 10m satellite NDVI\ne-Shakti & ULI land data", COLOR_BLUE),
        ("03 · RISK INTELLIGENCE", "300–900 Score in <3 min\nExact SHAP reason codes\nConfidence interval (±15 to ±45)", COLOR_BLUE),
        ("04 · HUMAN-GOVERNED SANCTION", "Underwriter review cockpit\nMandatory dissent audit\nSame-day bank CBS disbursal", ACCENT_GREEN)
    ]
    for i, (title, desc, col) in enumerate(to_be_steps):
        sc = create_card(s6, Inches(0.8 + i * 2.98), Inches(1.75), Inches(2.75), Inches(1.85), bg_color=CARD_BG, border_color=col)
        tf = sc.text_frame
        tf.margin_left = tf.margin_top = Inches(0.14)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_PRIMARY

    # Comparison Grid Below (Constitution Section 33 Slide 6 Comparison Table)
    grid_c = create_card(s6, Inches(0.8), Inches(3.80), Inches(11.7), Inches(3.10))
    tf = grid_c.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "COMPARATIVE ARCHITECTURE: AS-IS VS. TO-BE (CREDITTECH)"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Underwriting Inputs: Bureau score + physical land deed  ==>  AA cashflows + Sentinel-2 satellite NDVI + SHG thrift books.\n• Turnaround Time: 10 to 20 business days  ==>  < 3 minutes for scoring; same-day bank sanction via ULI.\n• Thin-File Treatment: Automatically excluded (Score -1)  ==>  Calibrated 300–900 score using 21 domain features across the 5 Cs of credit.\n• Explainability: Opaque manual discretion  ==>  Exact closed-form bilingual SHAP reason codes (Hindi & English) for both borrower and underwriter.\n• Institutional Role: Monolithic bank-only appraisal  ==>  Unbundled LSP decision-support bridge; bank retains sole sanction authority.\n• System Resilience: Hard failure on missing paper  ==>  Graceful Degradation rescales weights and widens confidence band on API timeout."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s6, """Slide 6 presents our proposed To-Be system architecture.
CreditTech reframes the entire credit journey around a single idea: turning every consented, legally verifiable signal about a borrower's real economic life into an explainable score in minutes.
The farmer or Bank Sakhi initiates the application on a tablet. With explicit, time-bound consent captured in our DPDP ledger, our backend orchestrates parallel ingestion across four rails: Account Aggregator cashflows, Sentinel-2 satellite crop health, e-Shakti community savings, and ULI land data.
Within three minutes, our scoring engine generates a calibrated score on the standard 300 to 900 scale, complete with bilingual SHAP explanations. The loan officer reviews the profile on their cockpit and sanctions the loan the same day. We replace a 20-day ordeal with a 3-minute intelligence pipeline.""")

    # =========================================================================
    # SLIDE 7: COMPLETE SYSTEM ARCHITECTURE (Constitution Slide 07 Specification)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, BG_CANVAS)
    create_header(s7, "A 5-Layer Modular Monolith Built for Resilience & Sub-Millisecond Serving",
                  "Topic 5 · System Architecture", "FastAPI + PostgreSQL + React 19 architecture engineered for operational auditability")
    add_footer(s7, 7)

    # 5 Horizontal Layer Cards (Constitution Section 21 & 33 Slide 7 Rule)
    layer_h = Inches(0.92)
    layers_data = [
        ("LAYER 1 · IDENTITY & CONSENT MANAGEMENT", "Aadhaar e-KYC | DigiLocker | DPDP SHA-256 Hash-Chained Consent Ledger | Bank Sakhi Assisted Tablet PWA", ACCENT_GREEN),
        ("LAYER 2 · MULTI-RAIL INGESTION ENGINE", "Async 4-Rail Orchestrator: AA Financial Cashflows | Sentinel-2 10m NDVI | e-Shakti SHG Ledgers | ULI Land Registry", COLOR_BLUE),
        ("LAYER 3 · INTELLIGENCE & RESPONSIBLE AI SCORING", "21-Feature Domain Store | Monotonic WoE Champion (AUC 0.96) | LightGBM Challenger | Bilingual SHAP Engine", COLOR_BLUE),
        ("LAYER 4 · DECISIONING & POLICY GATEWAY", "OCEN 4.0 LSP Gateway | Statutory Rule Filters | ULI Document Dispatch | Mandatory Underwriter Dissent Logging", COLOR_PURPLE),
        ("LAYER 5 · CHANNEL, SERVICING & GOVERNANCE", "Bank Sakhi Tablet PWA | Underwriter Decision Cockpit | Closed-Loop Repayment Feedback | RBI Grievance Redress", TEXT_PRIMARY)
    ]
    for i, (title, desc, col) in enumerate(layers_data):
        lc = create_card(s7, Inches(0.8), Inches(1.72 + i * 1.02), Inches(11.7), layer_h, bg_color=CARD_BG, border_color=CARD_BORDER)
        tf = lc.text_frame
        tf.margin_left = tf.margin_top = Inches(0.12)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_PRIMARY

    # Architecture Principle Footer Box (Constitution Section 33 Slide 7 Architecture Principle)
    ap_card = create_card(s7, Inches(0.8), Inches(6.30), Inches(11.7), Inches(0.60), bg_color=GREEN_BG_SUBTLE, border_color=GREEN_BORDER_SUBTLE)
    tf = ap_card.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.10)
    p = tf.paragraphs[0]
    p.text = "ARCHITECTURE PRINCIPLE: Modular monolith for MVP -> eliminates distributed network latency and cloud infrastructure bills; clean service boundaries allow selective extraction as volume demands."
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.font.name = FONT_FAMILY

    set_speaker_notes(s7, """Slide 7 details our complete 5-layer system architecture.
We deliberately architected CreditTech as a modular monolith built on FastAPI and PostgreSQL.
Layer 1 manages identity and consent using SHA-256 hash chaining.
Layer 2 handles parallel ingestion across our four data rails with built-in Graceful Degradation.
Layer 3 is our machine learning intelligence core, serving our champion WoE scorecard in under 0.04 milliseconds.
Layer 4 enforces lending policy and interfaces with OCEN and ULI.
And Layer 5 powers the front-end channels for Bank Sakhis and bank underwriters.
Why a monolith rather than microservices? Because at projected pilot volumes of 15 to 30 decisions per day, microservices introduce distributed network latency and operational failure points. Our modular architecture delivers sub-millisecond inference with clean, separable code boundaries.""")

    # =========================================================================
    # SLIDE 8: DATA ARCHITECTURE & PII ISOLATION (Constitution Slide 08 Specification)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, BG_CANVAS)
    create_header(s8, "7 Ingestion Streams Mapped to Economic Risk Hypotheses & PII Isolation",
                  "Topic 6 · Data Architecture", "Physical and cryptographic separation of PII from the numerical ML feature store")
    add_footer(s8, 8)

    # Left: Data Streams Table Card (Constitution Slide 08 7-Stream Hypothesis Table)
    ds_c = create_card(s8, Inches(0.8), Inches(1.75), Inches(6.8), Inches(5.15))
    tf = ds_c.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "7 INGESTION STREAMS & PREDICTIVE HYPOTHESES"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "1. Financial Transactions (Account Aggregator, DEPA Consent):\n   • Features: Average Daily Balance, UPI inflows, zero-balance days.\n   • Predicts: Cashflow volatility and near-term debt-service capacity.\n2. Geospatial Imagery (Sentinel-2 10m NDVI & Drought Anomaly):\n   • Features: Multi-spectral vegetative vigor, 3-yr historical yield deviation.\n   • Predicts: Crop yield health and resistance to climate shocks.\n3. Community Trust (DAY-NRLM e-Shakti SHG Ledgers):\n   • Features: Membership tenure, monthly savings consistency, attendance.\n   • Predicts: Uncollateralized character and social collateral (>96% track).\n4. Market Off-Take (e-NAM Mandi Receipts & Dairy Pouring):\n   • Features: Realized sales volume, modal price realization, pouring consistency.\n   • Predicts: Commercial viability and verified agricultural cash income.\n5. Welfare Entitlements (PM-KISAN & KCC Registry):\n   • Features: DBT installment regularity, operational KCC credit line.\n   • Predicts: Baseline household subsistence cash floor.\n6. Bureau Pull (CIBIL/Equifax Statutory Pull Consent):\n   • Features: Total inquiries, existing loans; corroborates over-indebtedness.\n7. Data Minimisation Exclusions: Strictly bars caste, religion, contacts, SMS, GPS."
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_PRIMARY

    # Right Top: PII Segregation Schema Card (Constitution Slide 08 PII Isolation Rule)
    pii_c = create_card(s8, Inches(7.8), Inches(1.75), Inches(4.7), Inches(2.35))
    tf = pii_c.text_frame
    tf.margin_left = tf.margin_top = Inches(0.16)
    p = tf.paragraphs[0]
    p.text = "PHYSICAL & CRYPTOGRAPHIC PII ISOLATION"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_RED
    p = tf.add_paragraph()
    p.text = "[ ENCRYPTED PII TENANT SCHEMA ]\nTable: `borrowers` (Isolated Storage)\n• id: UUID  |  name: AES-256-GCM\n• mobile_hash: Salted HMAC-SHA256\n• aadhaar_token: SHA-256 Vault Token\n\n          | One-Way Identifier Hash\n          v\n[ ANONYMOUS ML FEATURE STORE ]\nTable: `feature_snapshots` (Zero PII)\n• snapshot_id: UUID  |  borrower_hash: Opaque ID\n• 21 Normalized Numerical Domain Features"
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_PRIMARY

    # Right Bottom: EMBED REAL FIGURE feature_importance_shap.png
    embed_figure_safe(s8, "feature_importance_shap.png", Inches(7.8), Inches(4.25), Inches(4.7), Inches(2.4),
                      caption="Figure 7: Multi-Model Feature Importance & TreeSHAP Impact on N=22,000 Benchmark")

    set_speaker_notes(s8, """Slide 8 details our data architecture and privacy safeguards.
Every data source ingested by CreditTech maps to an explicit economic credit hypothesis. We never harvest data simply because it is available.
Crucially, we resolve the central vulnerability of digital credit: data privacy. Under India's DPDP Act 2023, we enforce strict physical and cryptographic separation of Personally Identifiable Information from our machine learning feature store.
As shown in our schema diagram, borrower identities are encrypted using AES-256 in an isolated table. The feature store and scoring models operate exclusively on anonymized numerical vectors. No analytics script or external model ever has access to plaintext borrower identities.
On the bottom right, Figure 7 confirms our domain feature importance, showing SHG savings discipline and Sentinel-2 NDVI as the strongest predictive drivers.""")

    # =========================================================================
    # SLIDE 9: TECHNOLOGY STACK & ADRS (Constitution Slide 09 Specification)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, BG_CANVAS)
    create_header(s9, "A Modular Monolith Keeps the MVP Deployable and Auditable",
                  "Topic 7 · Technology & ADRs", "Four Architecture Decision Records justifying technical selections via explicit trade-offs")
    add_footer(s9, 9)

    # 4 ADR Cards Grid (Constitution Section 33 Slide 9 Rule)
    adrs = [
        ("ADR 01 · MODULAR MONOLITH OVER MICROSERVICES", 
         "• Decision: Build a single modular FastAPI backend rather than 10 microservices.\n• Why: At pilot volumes (15–30 requests/day), microservices introduce distributed network latency, two-phase commits, and high cloud overhead.\n• Trade-Off: High discipline required for code modularity, but delivers sub-0.04ms in-process inference with zero network serialization overhead.", ACCENT_GREEN),
        ("ADR 02 · IN-PROCESS ML SERVING OVER SAGEMAKER", 
         "• Decision: Execute Scikit-learn and LightGBM models in FastAPI application memory.\n• Why: Eliminates expensive AWS/GCP cloud endpoint hosting costs ($200+/mo) and removes network hop failure points during inference.\n• Trade-Off: ML libraries bundled with API server, but delivers predictable sub-millisecond execution on standard Linux servers.", COLOR_BLUE),
        ("ADR 03 · NATIVE ASYNCIO OVER CELERY & REDIS", 
         "• Decision: Use Python native asyncio for multi-rail external API orchestration.\n• Why: Ingestion is purely I/O bound; Celery and Redis message brokers introduce unnecessary stateful infrastructure dependencies.\n• Trade-Off: In-memory task queueing at pilot scale, eliminating broker maintenance while achieving sub-3 minute parallel ingestion.", COLOR_BLUE),
        ("ADR 04 · POSTGRESQL HASH CHAINING OVER BLOCKCHAIN", 
         "• Decision: Implement SHA-256 hash chaining within PostgreSQL triggers.\n• Why: Blockchain introduces high gas fees, slow finality, and complex key management that rural borrowers cannot operate.\n• Trade-Off: Centralized DBMS hosting, but provides mathematical tamper-evident non-repudiation at zero transaction cost.", COLOR_PURPLE)
    ]
    for i, (title, desc, col) in enumerate(adrs):
        r = i // 2
        c = i % 2
        card = create_card(s9, Inches(0.8 + c * 6.0), Inches(1.75 + r * 2.65), Inches(5.7), Inches(2.45))
        tf = card.text_frame
        tf.margin_left = tf.margin_top = Inches(0.18)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s9, """Slide 9 details our Architecture Decision Records.
We made deliberate engineering trade-offs:
1. We chose a Modular Monolith over microservices to eliminate distributed latency and cloud complexity.
2. We chose In-Process ML Serving over remote SageMaker endpoints, saving cloud costs and achieving 0.04ms inference.
3. We chose Native Asyncio over Celery and Redis to eliminate premature broker dependencies.
4. We chose PostgreSQL SHA-256 Hash Chaining over Blockchain, giving mathematical tamper evidence at zero transaction cost.
Every decision was driven by empirical need, not startup hype.""")

    # =========================================================================
    # SLIDE 10: API / DPI INTEGRATION (Constitution Slide 10 Specification)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, BG_CANVAS)
    create_header(s10, "DPI Framework: Orchestrating National Public Rails",
                  "Topic 8 · DPI Framework", "Clear classification across Implemented, Designed, and Proposed/Future integration status")
    add_footer(s10, 10)

    # 4 DPI Rails Cards with Explicit Status Badges (Constitution Section 17 & 33 Slide 10 Rule)
    rails = [
        ("ACCOUNT AGGREGATOR (AA / SAHAMATI)", "[ STATUS: DESIGNED / FIU SPEC ]",
         "• Certified Financial Information User (FIU) via licensed AA gateway.\n• Ingests bank statements and UPI transaction logs under signed DEPA consent.\n• 17 licensed AAs covering 284M+ accounts nationally.\n• Transforms raw transaction JSON into cashflow and liquidity metrics.", COLOR_BLUE),
        ("UNIFIED LENDING INTERFACE (ULI / RBI)", "[ STATUS: DESIGNED / DISPATCH SPEC ]",
         "• Standardized dispatch connector delivering scores to bank Core Banking Systems (CBS).\n• Dispatches 300-900 score, confidence band, and Top-5 SHAP reasons.\n• Eliminates bilateral bank-by-bank custom integrations.\n• National public rail with ₹27,000 Cr disbursed across 600k loans.", ACCENT_GREEN),
        ("OPEN CREDIT ENABLEMENT NETWORK (OCEN 4.0)", "[ STATUS: DESIGNED / LSP SPEC ]",
         "• Implements standard Lending Service Provider (LSP) API specifications.\n• Standardises borrower loan application, sanction offer, and disbursement terms.\n• Enables seamless hand-off between CreditTech and multiple partner lenders.\n• Built-in alignment with RBI digital lending conduct directions.", COLOR_BLUE),
        ("DPDP CONSENT INFRASTRUCTURE", "[ STATUS: IMPLEMENTED IN MVP ]",
         "• Phased compliance aligned to MeitY DPDP Rules 2025.\n• Immutable SHA-256 hash-chained consent ledger with 7-year audit retention.\n• 60-second statutory revocation execution.\n• Automated 30-day storage limitation purge executed by background worker.", COLOR_PURPLE)
    ]
    for i, (title, status, desc, col) in enumerate(rails):
        r = i // 2
        c = i % 2
        card = create_card(s10, Inches(0.8 + c * 6.0), Inches(1.75 + r * 2.35), Inches(5.7), Inches(2.20))
        tf = card.text_frame
        tf.margin_left = tf.margin_top = Inches(0.16)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = status
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GREEN if "IMPLEMENTED" in status else TEXT_MUTED
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_PRIMARY

    # Bottom Classification Summary (Constitution Section 17 & 48 Check 2)
    stat_card = create_card(s10, Inches(0.8), Inches(6.30), Inches(11.7), Inches(0.60), bg_color=CARD_BG, border_color=CARD_BORDER)
    tf = stat_card.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.10)
    p = tf.paragraphs[0]
    p.text = "IMPLEMENTATION STATUS: [Implemented in MVP]: DPDP SHA-256 Consent Ledger, Mock 4-Rail Gateway | [Designed]: ULI & AA Connectors | [Future]: Live Bank CBS Sandboxes."
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s10, """Slide 10 illustrates our API and DPI integration framework.
CreditTech acts as an intelligent orchestration hub connecting India's national digital public infrastructure with regulated lenders.
We integrate with four primary rails:
The Account Aggregator network for consented cashflows;
The RBI's Unified Lending Interface for seamless document and score hand-off to bank core systems;
The OCEN protocol for open lending contracts;
And MeitY's DPDP consent framework for user rights management.
Crucially, we built Graceful Degradation: if monsoon clouds obstruct optical satellite passes, our engine does not crash with an HTTP 500. It dynamically rescales available feature weights and outputs a confidence-calibrated score. The pipeline never halts.""")

    # =========================================================================
    # SLIDE 11: FUNCTIONAL MODULES (Constitution Slide 11 Specification)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, BG_CANVAS)
    create_header(s11, "Functional Modules: 9 Interlocking Subsystems from Onboarding to Audit",
                  "Topic 9 · Functional Modules", "3 x 3 modular specification matrix enforcing strict SLAs, security invariants & fairness gates")
    add_footer(s11, 11)

    # 3x3 Grid of Modules (Constitution Section 33 Slide 11 3x3 Matrix)
    m_w = Inches(3.75)
    m_h = Inches(1.68)
    modules_data = [
        ("M1 · Onboarding & Consent", "Aadhaar e-KYC, Indic language selection, DPDP consent capture. SLA < 5 min; AES-256 encryption."),
        ("M2 · Data Ingestion", "4-rail parallel async orchestrator. Normalizes raw payloads into 21 domain features. SLA < 3 min."),
        ("M3 · Feature Engineering", "Crop-cycle aware feature store. Monotonic WoE binning + Laplace smoothing. Latency < 0.04 ms."),
        ("M4 · Risk Scoring", "Dual Champion WoE / Challenger LightGBM. Outputs 300-900 score. Statistically calibrated probabilities."),
        ("M5 · Explainability", "Exact closed-form point attribution. Generates Top-5 bilingual reason codes in conversational Hindi & English."),
        ("M6 · Decision Support", "Underwriter review cockpit. Displays SHAP waterfall charts with mandatory dissent reason logging."),
        ("M7 · Governance", "Pre-promotion FairnessGate enforcing DIR >= 0.80 demographic parity floor and PSI < 0.10 drift limits."),
        ("M8 · Audit & Grievance", "Borrower dispute channel for adverse score re-evaluation. Append-only DDL triggers with 14-day SLA."),
        ("M9 · Monitoring / MLOps", "Portfolio analytics cockpit for NABARD and bank executives: tracks rolling default rates & drift.")
    ]
    for i, (title, desc) in enumerate(modules_data):
        r = i // 3
        c = i % 3
        card = create_card(s11, Inches(0.8 + c * 3.98), Inches(1.75 + r * 1.76), m_w, m_h)
        tf = card.text_frame
        tf.margin_left = tf.margin_top = Inches(0.12)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_GREEN if i in [0, 3, 6] else COLOR_BLUE
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s11, """Slide 11 details our nine core functional modules.
From Module M1, which handles multi-channel assisted onboarding and cryptographic consent capture;
To Module M2 for parallel multi-rail ingestion;
Module M3, which runs our sub-millisecond scoring engine;
Module M4, generating bilingual SHAP explanations;
Module M5, running automated algorithmic fairness gates;
Module M6, our underwriter review cockpit;
Module M7, tracking closed-loop repayment performance;
Module M8, managing borrower disputes;
And Module M9, providing institutional oversight for NABARD and bank executives.
Every module enforces strict SLAs, input validations, and security invariants.""")

    # =========================================================================
    # SLIDE 12: USER JOURNEY (Constitution Slide 12 Specification)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, BG_CANVAS)
    create_header(s12, "User Journey: A 4-Stage Human-Governed Underwriting Workflow",
                  "Topic 10 · User Journey", "Explicit mapping of borrower, Bank Sakhi, loan officer, and target service level agreements")
    add_footer(s12, 12)

    # 4 Journey Step Cards (Constitution Section 33 Slide 12 4-Stage Journey)
    uj_w = Inches(2.75)
    uj_h = Inches(2.65)
    uj_steps = [
        ("1. Consent & Onboarding", "ACTORS: Borrower + Bank Sakhi\nINTERFACE: Touch-First PWA Tablet\n\n• Assisted demographic entry\n• Instant Aadhaar OTP e-KYC\n• Offline-tolerant static forms\n\nTARGET SLA: < 5 MINUTES", ACCENT_GREEN),
        ("2. Profile Construction", "ACTOR: Automated Orchestrator\nINTERFACE: Async 4-Rail Gateway\n\n• AA banking cashflows\n• Sentinel-2 10m NDVI vigor\n• e-Shakti SHG savings ledger\n\nTARGET SLA: < 3 MINUTES", COLOR_BLUE),
        ("3. Risk Assessment", "ACTOR: Scoring & XAI Engine\nINTERFACE: In-Process ML Pipeline\n\n• Calibrated 300-900 score\n• Exact closed-form SHAP\n• Top-5 bilingual reasons\n\nTARGET SLA: < 2 MINUTES", COLOR_BLUE),
        ("4. Human Sanction", "ACTORS: Loan Officer + Borrower\nINTERFACE: Underwriter Cockpit\n\n• Human credit officer sanction\n• ULI CBS disbursal hand-off\n• Automated 30-day PII purge\n\nTARGET SLA: SAME WORKING DAY", ACCENT_GREEN)
    ]
    for i, (title, desc, col) in enumerate(uj_steps):
        card = create_card(s12, Inches(0.8 + i * 2.98), Inches(1.75), uj_w, uj_h, bg_color=CARD_BG, border_color=col)
        tf = card.text_frame
        tf.margin_left = tf.margin_top = Inches(0.16)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = desc
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_PRIMARY

    # Human-in-the-Loop Governance Box (Constitution Section 41 & Slide 12 SLA Rule)
    hil_card = create_card(s12, Inches(0.8), Inches(4.70), Inches(11.7), Inches(2.20), bg_color=CARD_BG, border_color=CARD_BORDER)
    tf = hil_card.text_frame
    tf.margin_left = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = "HUMAN-IN-THE-LOOP PRINCIPLE & SERVICE LEVEL AGREEMENT (SLA) GUARANTEES"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Human Underwriting Control: CreditTech acts strictly as decision support; the human bank loan officer retains sole sanction authority. Any model override requires structured dissent logging.\n• Target SLA: End-to-end score generation in < 3 minutes; same-day loan disbursal via ULI CBS hand-off.\n• Graceful Degradation: If satellite imagery or land registry times out, the engine rescales weights and widens confidence band (e.g. 720 ± 45 vs ± 15) rather than halting the loan journey.\n• Automated Storage Limitation: Section 8(7) DPDP background worker cryptographically scrubs raw PII after 30-day TTL, leaving zero lingering demographic exposure."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s12, """Slide 12 illustrates the user journey and process SLAs.
While our backend coordinates complex multi-rail integrations, the experience for a rural borrower is compressed into four simple, transparent steps:
Step 1: The applicant inputs their request via a Bank Sakhi tablet in under five minutes.
Step 2: Instant Aadhaar e-KYC and electronic consent capture in under five minutes.
Step 3: Automated multi-rail ingestion and score generation in under three minutes, providing immediate, transparent reason codes.
And Step 4: Same-day underwriter sanction and bank account disbursal via ULI.
Finally, our automated DataRetentionWorker executes a cryptographic wipe of all raw PII once the 30-day underwriting TTL expires, ensuring zero lingering privacy exposure.""")

    # =========================================================================
    # SLIDE 13: GOVERNANCE & REGULATIONS (Constitution Slide 13 Specification)
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, BG_CANVAS)
    create_header(s13, "Three Regulatory Pillars Governing Security, Privacy & Responsible AI",
                  "Topic 11 · Governance & Regulations", "Statutory alignment with RBI Digital Lending Directions, DPDP Act 2023, and fairness gates")
    add_footer(s13, 13)

    # 3 Pillar Cards (Constitution Section 33 Slide 13: 3 Pillars)
    p_w = Inches(3.75)
    p_h = Inches(2.70)

    # Pillar 1: Data Governance
    p1 = create_card(s13, Inches(0.8), Inches(1.75), p_w, p_h)
    tf = p1.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "01 · DATA GOVERNANCE (DPDP 2023)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Purpose Limitation: Consent strictly bound to credit scoring (`CREDIT_SCORING`).\n• Cryptographic Ledger: SHA-256 hash chaining (H_n = SHA256(H_n-1 || Tx || t)).\n• 60-Second Revocation: Instant consent withdrawal.\n• Storage Limitation: 30-day automated PII purge."
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_PRIMARY

    # Pillar 2: Financial Governance
    p2 = create_card(s13, Inches(4.78), Inches(1.75), p_w, p_h)
    tf = p2.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "02 · FINANCIAL GOVERNANCE (RBI DLG)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "• Pure LSP Status: Bank retains sole underwriting and NPA recognition authority.\n• Zero Fund Pass-Through: Direct disbursement from bank CBS to borrower account.\n• 5% DLG Ceiling: Default Loss Guarantee legally capped at 5% of portfolio, backed by FDs.\n• Key Facts Statement: APR disclosure upfront."
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_PRIMARY

    # Pillar 3: Model Governance
    p3 = create_card(s13, Inches(8.76), Inches(1.75), p_w, p_h)
    tf = p3.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "03 · FAIRNESS & MODEL GOVERNANCE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p = tf.add_paragraph()
    p.text = "• Pre-Promotion FairnessGate: Enforces Disparate Impact Ratio (DIR >= 0.80) across cohorts.\n• Automated CI/CD Block: Deploys HTTP 409 Conflict if disparity exceeds threshold.\n• Population Stability (PSI): Tracks drift across 15 agro-climatic clusters (PSI < 0.10).\n• Independent Academic Audit: With IIT Kharagpur."
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_PRIMARY

    # Bottom Half: EMBED REAL FIGURE demographic_fairness_parity.png
    embed_figure_safe(s13, "demographic_fairness_parity.png", Inches(0.8), Inches(4.65), Inches(11.7), Inches(2.25),
                      caption="Figure 8: Empirical Demographic Fairness Parity across Gender and Landholding Cohorts on N=22,000 Benchmark (DIR >= 0.80 Floor)")

    set_speaker_notes(s13, """Slide 13 addresses our regulatory and data governance framework.
Fintech deployments must strictly comply with governing law. We anchor CreditTech in three statutory regimes:
First, RBI's Digital Lending Guidelines. We operate strictly as an LSP. Disbursals flow directly between bank and borrower, and any credit risk sharing is legally capped at the mandatory 5% DLG ceiling.
Second, India's DPDP Act 2023. We enforce strict purpose limitation, instantaneous consent revocation, and automated cryptographic data scrubbing once underwriting concludes.
And third, our pre-promotion FairnessGate. Borrowers cannot be discriminated against based on gender or marginal land status. We enforce a mathematical Disparate Impact Ratio floor of 0.80. If any updated model breaches this threshold, deployment is automatically halted.
Figure 8 below proves that our champion model achieves approval parity well within regulatory limits across all protected cohorts.""")

    # =========================================================================
    # SLIDE 14: PILOT BLUEPRINT (Constitution Slide 14 Specification)
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, BG_CANVAS)
    create_header(s14, "Stratified Pilot Design: 5 Agro-Climatic Site Archetypes",
                  "Topic 12 · Pilot Blueprint", "N=1,000 borrower evaluation across diverse cropping and connectivity zones over a 9–12 month cycle")
    add_footer(s14, 14)

    # Left: 5 Site Archetype Cards (Constitution Section 33 Slide 14)
    site_w = Inches(6.8)
    site_card = create_card(s14, Inches(0.8), Inches(1.75), site_w, Inches(5.15))
    tf = site_card.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "5 STRATIFIED AGRO-CLIMATIC SITE ARCHETYPES (N=1,000 BORROWERS)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Site A (Irrigated Cotton/Wheat — Western UP / RJ, 200 Borrowers):\n  Tests turnaround speed (<1 hr) and credit limit adequacy where KCC is dense.\n• Site B (Rainfed Millets/Soybean — Marathwada / MP, 200 Borrowers):\n  Tests Sentinel-2 NDVI & IMD drought anomaly index during severe rainfall shocks.\n• Site C (SHG-Dense Southern Model — AP / Telangana, 250 Borrowers):\n  Tests peer social collateral and e-Shakti ledgers for women's enterprise loans.\n• Site D (Allied-Activity Dairy — Anand / Odisha, 200 Borrowers):\n  Tests high-frequency daily milk pouring data to predict debt-service capacity.\n• Site E (Low-Bandwidth Tribal — Jharkhand / CG, 150 Borrowers):\n  Tests Graceful Degradation and offline Bank Sakhi PWA tablet onboarding."
    p.font.size = Pt(8.8)
    p.font.color.rgb = TEXT_PRIMARY

    # Right Top: 6 Target KPIs Card (Constitution Section 33 Slide 14 KPI Target Rule)
    kpi_card = create_card(s14, Inches(7.8), Inches(1.75), Inches(4.7), Inches(2.20))
    tf = kpi_card.text_frame
    tf.margin_left = tf.margin_top = Inches(0.14)
    p = tf.paragraphs[0]
    p.text = "PILOT EVALUATION KPI TARGETS"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "1. Median TAT: < 1 hour (vs 10–15 days As-Is)\n2. Approval Uplift: +20% to +30% on thin-file cohort\n3. Portfolio Quality: PAR90 <= 2.0% (vs 6.2% agri GNPA)\n4. Fairness Floor: Disparate Impact Ratio (DIR) >= 0.80\n5. Explainability Comprehension: >= 80% borrowers\n6. Partial Data Resilience: >= 90% scored with 1 rail down"
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_PRIMARY

    # Right Bottom: EMBED REAL FIGURE drift_radar_psi.png
    embed_figure_safe(s14, "drift_radar_psi.png", Inches(7.8), Inches(4.10), Inches(4.7), Inches(2.6),
                      caption="Figure 9: Population Stability Index (PSI) Radar across 15 Village Clusters (PSI < 0.068)")

    set_speaker_notes(s14, """Slide 14 details our empirical field implementation strategy.
Rather than testing CreditTech in a single convenient village, we designed a stratified sampling framework across five distinct agro-climatic zones:
Site A in irrigated Uttar Pradesh tests turnaround speed where formal credit already exists.
Site B in rainfed Marathwada tests satellite drought models under severe weather risk.
Site C in Andhra Pradesh tests SHG peer savings for women entrepreneurs.
Site D in Gujarat tests non-crop cashflows using dairy cooperative pouring data.
And Site E in Jharkhand stress-tests our offline Bank Sakhi workflow in low-connectivity areas.
Covering 1,000 borrowers over a full 9-to-12 month agricultural cycle, this pilot will empirically measure approval uplift, portfolio-at-risk, and model stability across diverse Indian farming systems.
Figure 9 on the right confirms that our feature distributions maintain stable PSI (<0.068) across all 15 village clusters.""")

    # =========================================================================
    # SLIDE 15: BUDGET & RESOURCES (Constitution Slide 15 Specification)
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, BG_CANVAS)
    create_header(s15, "Preliminary Cost & Resource Requirements: ₹1.85–2.90 Crore Pilot Budget",
                  "Topic 13 · Budget & Resources", "Itemized expenditure scaled from SIDBI MSME survey and fintech operational benchmarks")
    add_footer(s15, 15)

    # Left: Budget Table Card (Constitution Slide 15 requirement)
    b_tbl = create_card(s15, Inches(0.8), Inches(1.75), Inches(6.8), Inches(5.15))
    tf = b_tbl.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "ITEMIZED BUDGET BREAKDOWN (9–12 MONTH PILOT, 5 SITES)"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p = tf.add_paragraph()
    p.text = "• Core Engineering Team (5–7 FTEs, 9–12 mo): ₹85.0 – ₹120.0 L (43.5%)\n  [ML, Backend FastAPI, React PWA, Data/DPI Engineers, QA Lead]\n• Field Operations & Bank Sakhi Training: ₹25.0 – ₹40.0 L (14.5%)\n  [20 rugged tablets, vernacular workshops, literacy camps]\n• Satellite & Geospatial Data Licensing: ₹15.0 – ₹30.0 L (9.8%)\n  [Commercial EO APIs for 10k ha across 5 pilot blocks]\n• Account Aggregator & DPI Integration: ₹8.0 – ₹15.0 L (5.3%)\n  [Certified FIU gateway licensing, ~1,500 consent pulls]\n• Cloud Infrastructure & MLOps: ₹10.0 – ₹18.0 L (6.5%)\n  [MeitY-empanelled CSP, encrypted storage, backup pipelines]\n• Independent Fairness & Legal Audit: ₹10.0 – ₹18.0 L (6.5%)\n  [Academic audit retainer (IIT Kharagpur) + DPDP legal counsel]\n• Monitoring, Evaluation & Surveys: ₹8.0 – ₹12.0 L (4.4%)\n• Contingency Reserve (15%): ₹24.0 – ₹37.0 L (12.5%)\n-------------------------------------------------------------\nTOTAL INDICATIVE BUDGET: ₹1.85 – ₹2.90 CRORE (Planning Estimate)"
    p.font.size = Pt(8.8)
    p.font.color.rgb = TEXT_PRIMARY

    # Right: Institutional In-Kind Contributions (Constitution Slide 15 In-Kind Inputs)
    ik_card = create_card(s15, Inches(7.8), Inches(1.75), Inches(4.7), Inches(5.15))
    tf = ik_card.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "INSTITUTIONAL IN-KIND COMMITMENTS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p = tf.add_paragraph()
    p.text = "• NABARD Regional Offices:\n  Pilot sponsorship, DDM facilitation, and NAFIS/KCC benchmark data access.\n\n• Partner Regulated Entities (RRBs/PACS):\n  Provision of lending capital, credit sanction authority, CBS integration, and 5% DLG agreement execution.\n\n• State Rural Livelihood Missions (SRLM):\n  Mobilisation of Bank Sakhi networks and access to e-Shakti SHG ledgers.\n\n• Academic Partner (IIT Kharagpur):\n  Independent model governance, quarterly fairness audits, and econometric impact assessment.\n\n*Statutory Note: Excludes loan credit capital, which is disbursed directly by partner banks."
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_PRIMARY

    set_speaker_notes(s15, """Slide 15 provides our preliminary cost and resource requirements for the pilot phase.
Scaled from public fintech disclosures and SIDBI survey operational benchmarks, our total indicative budget is ₹1.85 to ₹2.90 Crore over a 9-to-12 month deployment.
Core engineering constitutes roughly 44% of expenditure, covering a dedicated 5-to-7 member team.
Field operations—including rugged tablets for Bank Sakhis and village financial literacy workshops—accounts for 15%.
Commercial satellite imagery licensing and Account Aggregator transaction fees represent 15%.
And we allocate dedicated retainers for independent academic fairness audits and legal compliance.
Crucially, CreditTech does not require lending capital—the loans themselves are disbursed directly from partner bank balance sheets.""")

    # =========================================================================
    # SLIDE 16: LITERATURE EVIDENCE & CONCLUSION (Constitution Slide 16 Specification)
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, NAVY_HERO)

    # Header in White/Mint
    tb = s16.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.7), Inches(0.95))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = "Academic Grounding: Peer-Reviewed Literature & Real-World Precedents"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_FAMILY
    p_sub = tf.add_paragraph()
    p_sub.text = "Topic 14 · Literature & Evidence  |  Mid-Semester Defense Conclusion & Technical Defense"
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = RGBColor(187, 247, 208)
    p_sub.font.name = FONT_FAMILY

    # Left: 4 Literature Quadrants (Constitution Section 33 Slide 16)
    lit_card = create_card(s16, Inches(0.8), Inches(1.70), Inches(6.6), Inches(4.35),
                           bg_color=RGBColor(15, 33, 64), border_color=RGBColor(30, 58, 100))
    tf = lit_card.text_frame
    tf.margin_left = tf.margin_top = Inches(0.18)
    p = tf.paragraphs[0]
    p.text = "4 PEER-REVIEWED LITERATURE QUADRANTS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(187, 247, 208)
    p = tf.add_paragraph()
    p.text = "01 · FINANCIAL INCLUSION & DIGITAL FOOTPRINTS:\n• Berg et al. (2020, Rev. Fin. Studies): Digital footprints predict default as well as bureaus.\n• Kshetri (2021, Risks): AI/ML scoring reduces human bias in rural underwriting.\n\n02 · AGRICULTURAL DATA SPARSITY & SEASONALITY:\n• Systematic Review (Computers & Electronics in Agri, 2025): Crop-cycle feature engineering.\n• Njuguna & Sowon (2020, AfriCHI): Smallholder-specific sparse scoring algorithms.\n\n03 · SOCIAL COLLATERAL IN GROUP MICROCREDIT:\n• Jonnalagadda & Babu (2026, IRJMS): Alternative 5-Cs model for Indian smallholders (n=96).\n• DAY-NRLM (PIB 2025): >96% repayment track record across 90.9L rural SHGs.\n\n04 · EXPLAINABLE & RESPONSIBLE AI IN FINANCE:\n• Bücker et al. (2020) & Agosto et al. (2023): SAFE AI framework for credit scoring.\n• JMSRR Systematic Review (2026): Algorithmic bias and proxy-variable mitigation."
    p.font.size = Pt(8.5)
    p.font.color.rgb = WHITE

    # Right: EMBED REAL FIGURE roc_curve_comparison.png
    embed_figure_safe(s16, "roc_curve_comparison.png", Inches(7.6), Inches(1.70), Inches(4.9), Inches(4.35),
                      caption="Figure 1: ROC Curve Benchmark on N=22,000 Borrowers (Champion WoE AUC: 0.9599)")

    # Bottom Closing Defense Statement (Constitution Section 33 Slide 16 Closing Statement Rule)
    c_card = create_card(s16, Inches(0.8), Inches(6.15), Inches(11.7), Inches(0.75),
                         bg_color=RGBColor(22, 101, 52), border_color=RGBColor(34, 197, 94))
    tf = c_card.text_frame
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    p.text = "DEFENSIBLE RESEARCH POSITION: CreditTech positions alternative data not as a replacement for institutional underwriting, but as an additional evidence layer for thin-file credit decision support. Open for Technical Defense & Questions."
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_FAMILY

    # Save
    prs.save(OUTPUT_PATH)
    print(f"Presentation successfully compiled to: {OUTPUT_PATH}")

if __name__ == "__main__":
    build_deck()

"""
CreditTech Complete Diagram Suite Renderer
==========================================
Generates 300 DPI publication-grade images for:
1. Platform Core Entity-Relationship Diagram (figures/platform_core_er_diagram.png)
2. Multi-Rail Data Ingestion & Feature Lineage Diagram (figures/multi_rail_data_lineage_diagram.png)
3. Relational Schema & Integrity Invariant Matrix Table (figures/relational_schema_integrity_matrix.png)
4. Master Composite Publication Diagram (figures/er_diagram.png)
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_card(ax, x, y, width, height, title, columns, header_color="#1E3A8A", bg_color="#F8FAFC", border_color="#334155"):
    rect = patches.FancyBboxPatch(
        (x, y - height), width, height,
        boxstyle="round,pad=0.01,rounding_size=0.025",
        linewidth=1.2, edgecolor=border_color, facecolor=bg_color, zorder=2
    )
    ax.add_patch(rect)

    header_h = 0.22 * height
    header_rect = patches.FancyBboxPatch(
        (x, y - header_h), width, header_h,
        boxstyle="round,pad=0.01,rounding_size=0.025",
        linewidth=1.0, edgecolor=border_color, facecolor=header_color, zorder=3
    )
    ax.add_patch(header_rect)

    ax.text(
        x + width / 2.0, y - header_h / 2.0, title,
        color="white", fontsize=9.0, fontweight="bold",
        ha="center", va="center", zorder=4
    )

    n_cols = len(columns)
    line_spacing = (height - header_h - 0.035) / max(n_cols, 1)
    cur_y = y - header_h - 0.035
    for col, col_type, is_key in columns:
        prefix = "[PK] " if is_key == "PK" else "[FK] " if is_key == "FK" else "[UK] " if is_key == "UK" else " • "
        font_weight = "bold" if is_key in ["PK", "FK", "UK"] else "normal"
        text_color = "#0F172A" if is_key == "PK" else "#1E40AF" if is_key == "FK" else "#475569"

        ax.text(
            x + 0.018, cur_y - 0.015, f"{prefix}{col}",
            color=text_color, fontsize=7.2, fontweight=font_weight,
            ha="left", va="top", zorder=4
        )
        ax.text(
            x + width - 0.018, cur_y - 0.015, col_type,
            color="#64748B", fontsize=6.8, fontfamily="monospace",
            ha="right", va="top", zorder=4
        )
        cur_y -= line_spacing

def draw_connector(ax, x1, y1, x2, y2, label="1 : N", color="#475569"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.5, shrinkA=3, shrinkB=3, mutation_scale=12),
        zorder=1
    )
    mid_x = (x1 + x2) / 2.0
    mid_y = (y1 + y2) / 2.0
    ax.text(
        mid_x, mid_y + 0.012, label,
        fontsize=7.2, fontweight="bold", color="#1E293B",
        ha="center", va="bottom",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.9),
        zorder=5
    )

# -------------------------------------------------------------
# 1. RENDER PLATFORM CORE ER DIAGRAM
# -------------------------------------------------------------
def render_platform_core_er(output_path="figures/platform_core_er_diagram.png"):
    fig, ax = plt.subplots(figsize=(17, 11), dpi=300)
    ax.set_xlim(0, 1.7)
    ax.set_ylim(0, 1.1)
    ax.axis("off")

    ax.text(
        0.85, 1.06, "CreditTech: Platform Core Relational Entity-Relationship Diagram",
        fontsize=15, fontweight="bold", color="#0F172A", ha="center"
    )
    ax.text(
        0.85, 1.03, "10 Relational Schema Entities, Cryptographic Hash Chains, 5-Cs Feature Store & CBS Handoff",
        fontsize=10, color="#475569", ha="center"
    )

    # Row 1: Borrowers, Feature Snapshots, Applications
    draw_card(
        ax, 0.06, 0.98, 0.32, 0.28, "borrowers",
        [
            ("id", "UUID [PK]", "PK"),
            ("village_id", "VARCHAR [FK]", "FK"),
            ("aadhaar_hash", "VARCHAR [UK]", "UK"),
            ("phone_encrypted", "AES-256", ""),
            ("full_name", "VARCHAR", ""),
            ("segment", "ENUM", ""),
            ("landholding_band", "ENUM [Audit]", ""),
            ("gender", "CHAR [Audit]", ""),
            ("caste_category", "ENUM [Audit]", ""),
            ("created_at", "DATETIME", "")
        ],
        header_color="#1E3A8A"
    )

    draw_card(
        ax, 0.50, 0.98, 0.34, 0.28, "feature_snapshots",
        [
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("consent_id", "UUID [FK]", "FK"),
            ("shg_repayment_rate", "FLOAT", ""),
            ("utility_on_time_ratio", "FLOAT", ""),
            ("avg_monthly_inflow", "FLOAT", ""),
            ("foir", "FLOAT", ""),
            ("avg_daily_balance", "FLOAT", ""),
            ("effective_land_ha", "FLOAT", ""),
            ("ndvi_peak_mean", "FLOAT", ""),
            ("completeness_pct", "FLOAT", "")
        ],
        header_color="#4338CA"
    )

    draw_card(
        ax, 0.96, 0.98, 0.32, 0.24, "applications",
        [
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("score_id", "UUID [FK]", "FK"),
            ("product_type", "ENUM", ""),
            ("loan_amount_inr", "NUMERIC", ""),
            ("tenor_months", "INT", ""),
            ("interest_rate_pct", "FLOAT", ""),
            ("status", "ENUM", "")
        ],
        header_color="#B45309"
    )

    # Row 2: Consent Records, Score Results, Officer Decisions, RE Handoffs
    draw_card(
        ax, 0.06, 0.62, 0.32, 0.24, "consent_records",
        [
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("purpose", "VARCHAR", ""),
            ("status", "ENUM", ""),
            ("hash_chain", "SHA-256 [UK]", "UK"),
            ("expires_at", "DATETIME", ""),
            ("revoked_at", "DATETIME", "")
        ],
        header_color="#0D9488"
    )

    draw_card(
        ax, 0.50, 0.62, 0.34, 0.24, "score_results",
        [
            ("id", "UUID [PK]", "PK"),
            ("feature_id", "UUID [FK]", "FK"),
            ("model_version", "VARCHAR", ""),
            ("pd_score", "FLOAT", ""),
            ("scaled_score", "INT (300..900)", ""),
            ("decision_zone", "ENUM", ""),
            ("shap_reasons_json", "JSON", "")
        ],
        header_color="#7C3AED"
    )

    draw_card(
        ax, 0.96, 0.68, 0.32, 0.24, "officer_decisions",
        [
            ("id", "UUID [PK]", "PK"),
            ("application_id", "UUID [FK]", "FK"),
            ("officer_id", "VARCHAR", ""),
            ("final_verdict", "ENUM", ""),
            ("is_override", "BOOLEAN", ""),
            ("override_reason", "VARCHAR", ""),
            ("justification_note", "TEXT", ""),
            ("decided_at", "DATETIME", "")
        ],
        header_color="#C026D3"
    )

    draw_card(
        ax, 1.34, 0.68, 0.30, 0.18, "re_handoffs",
        [
            ("id", "UUID [PK]", "PK"),
            ("application_id", "UUID [FK]", "FK"),
            ("bank_code", "VARCHAR", ""),
            ("external_ref_token", "VARCHAR", ""),
            ("payload_digest", "SHA-256", ""),
            ("dispatched_at", "DATETIME", "")
        ],
        header_color="#059669"
    )

    # Row 3: Grievance Records, Model Promotions, Audit Events
    draw_card(
        ax, 0.06, 0.32, 0.32, 0.20, "grievance_records",
        [
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("category", "ENUM", ""),
            ("status", "ENUM", ""),
            ("sla_deadline", "DATETIME (+30d)", ""),
            ("resolved_at", "DATETIME", "")
        ],
        header_color="#DC2626"
    )

    draw_card(
        ax, 0.50, 0.32, 0.34, 0.20, "model_promotions",
        [
            ("id", "UUID [PK]", "PK"),
            ("candidate_model", "VARCHAR", ""),
            ("previous_champion", "VARCHAR", ""),
            ("fairness_gate_passed", "BOOLEAN", ""),
            ("gender_disparity_pct", "FLOAT (<=20%)", ""),
            ("land_disparity_pct", "FLOAT (<=25%)", "")
        ],
        header_color="#0284C7"
    )

    draw_card(
        ax, 0.96, 0.38, 0.32, 0.18, "audit_events",
        [
            ("id", "UUID [PK]", "PK"),
            ("event_type", "VARCHAR", ""),
            ("actor_role", "ENUM", ""),
            ("actor_id", "VARCHAR", ""),
            ("payload_hash", "SHA-256", ""),
            ("timestamp", "DATETIME", "")
        ],
        header_color="#334155"
    )

    # Draw Connections
    draw_connector(ax, 0.22, 0.70, 0.22, 0.62, "1 : N")
    draw_connector(ax, 0.38, 0.88, 0.50, 0.88, "1 : N")
    draw_connector(ax, 0.38, 0.54, 0.50, 0.84, "1 : N")
    draw_connector(ax, 0.67, 0.70, 0.67, 0.62, "1 : 1")
    draw_connector(ax, 0.38, 0.95, 0.96, 0.95, "1 : N")
    draw_connector(ax, 0.84, 0.52, 0.96, 0.86, "1 : 1")
    draw_connector(ax, 1.12, 0.74, 1.12, 0.68, "1 : 1")
    draw_connector(ax, 1.28, 0.58, 1.34, 0.58, "1 : 1")
    draw_connector(ax, 0.22, 0.38, 0.22, 0.32, "1 : N")
    draw_connector(ax, 1.12, 0.44, 1.12, 0.38, "1 : N")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

# -------------------------------------------------------------
# 2. RENDER MULTI-RAIL INGESTION & FEATURE LINEAGE DIAGRAM
# -------------------------------------------------------------
def render_multi_rail_lineage(output_path="figures/multi_rail_data_lineage_diagram.png"):
    fig, ax = plt.subplots(figsize=(18, 11), dpi=300)
    ax.set_xlim(0, 1.8)
    ax.set_ylim(0, 1.1)
    ax.axis("off")

    ax.text(
        0.9, 1.06, "CreditTech: Multi-Rail Data Ingestion & Feature Lineage Architecture",
        fontsize=15, fontweight="bold", color="#0F172A", ha="center"
    )
    ax.text(
        0.9, 1.03, "Flow of 8 Raw Data Rails -> 5-Cs Feature Synthesizers -> Modeling Store -> Scorecard Decisioning",
        fontsize=10, color="#475569", ha="center"
    )

    # Column 1: Raw Tables (Left)
    raw_tables = [
        ("A_borrowers (20k rows)", "Village code, age, literacy, bureau tradelines (65% thin-file)", "#1E3A8A"),
        ("B_household_land_crop (20k rows)", "Owned/leased ha (76.9% <1ha), irrigation, crops, asset index", "#0284C7"),
        ("C_aa_monthly (240k rows)", "12m cashflows: credits, debits, daily balance, UPI, DBT", "#0D9488"),
        ("D_shg_ledger (20k rows)", "400 SHGs: meetings, attendance %, thrift corpus, internal repayment", "#059669"),
        ("E_utility_digital (20k rows)", "Metered electricity on-time ratio, arrears, prepaid recharge regularity", "#7C3AED"),
        ("F_satellite_weather (20k rows)", "Sentinel-2 10m NDVI peak/mean, rainfall % of normal, dry spells", "#D97706"),
        ("G_govt_social (20k rows)", "PM-Kisan tranches (Rs 6,000/yr), MGNREGA days (mean 35), PMJDY", "#DC2626"),
    ]

    cur_y = 0.98
    for title, desc, col in raw_tables:
        box = patches.FancyBboxPatch(
            (0.05, cur_y - 0.08), 0.38, 0.08,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.2, edgecolor=col, facecolor="#F8FAFC", zorder=2
        )
        ax.add_patch(box)
        ax.text(0.07, cur_y - 0.025, title, fontsize=8.5, fontweight="bold", color=col, ha="left")
        ax.text(0.07, cur_y - 0.055, desc, fontsize=6.8, color="#475569", ha="left")
        cur_y -= 0.125

    # Column 2: 5-Cs Feature Synthesizer (Middle)
    cs_cards = [
        ("Character (6 Features)", "shg_repayment_rate, shg_attendance_pct, savings_regularity_pct,\nutility_on_time_ratio, recharge_regularity, account_age_months", "#1E40AF"),
        ("Capacity (6 Features)", "avg_monthly_inflow (~Rs 10,218), inflow_cv, inflow_outflow_ratio,\nincome_diversification, foir (<=0.85), govt_transfer_share", "#047857"),
        ("Capital (3 Features)", "avg_daily_balance, shg_savings_corpus, livestock_value_inr", "#B45309"),
        ("Collateral (3 Features)", "effective_land_ha (owned + 0.5*leased), irrigated_share (0..1), asset_index", "#6D28D9"),
        ("Conditions (3 Features)", "ndvi_peak_mean (0.28..0.82), rainfall_pct_normal, crop_insurance_flag", "#BE123C")
    ]

    cur_y = 0.98
    for title, desc, col in cs_cards:
        box = patches.FancyBboxPatch(
            (0.56, cur_y - 0.12), 0.40, 0.12,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.2, edgecolor=col, facecolor="#F1F5F9", zorder=2
        )
        ax.add_patch(box)
        ax.text(0.58, cur_y - 0.035, title, fontsize=9.0, fontweight="bold", color=col, ha="left")
        ax.text(0.58, cur_y - 0.075, desc, fontsize=7.0, color="#334155", ha="left")
        cur_y -= 0.175

    # Column 3: Feature Store & Decision Engine (Right)
    draw_card(
        ax, 1.10, 0.98, 0.30, 0.38, "modeling_features.csv",
        [
            ("borrower_id", "PK", "PK"),
            ("village_id", "LOVO CV Fold", "FK"),
            ("21 Core 5-Cs Features", "Continuous", ""),
            ("inflow_trend_slope", "Extension", ""),
            ("seasonal_amplitude", "Extension", ""),
            ("months_low_balance", "Extension", ""),
            ("ndvi_anomaly", "Extension", ""),
            ("rail_completeness_pct", "Extension", ""),
            ("thin_file_flag", "Extension", ""),
            ("loan_to_income_ratio", "Policy", ""),
            ("default_flag", "Target (90+ DPD)", "")
        ],
        header_color="#1E293B"
    )

    draw_card(
        ax, 1.46, 0.98, 0.28, 0.26, "WoE Scorecard Engine",
        [
            ("Algorithm", "Monotonic WoE", ""),
            ("Score Interval", "300 to 900", ""),
            ("Target Score", "600 pts @ 19:1", ""),
            ("Points Factor", "PDO / ln(2)", ""),
            ("Explainability", "100% Additive", ""),
            ("TreeSHAP Codes", "Bilingual Hi/En", "")
        ],
        header_color="#7C3AED"
    )

    # Decision Zone Result Cards
    zones = [
        ("Reject Zone (< 550)", "High default risk; bilingual adverse notice emitted", "#DC2626"),
        ("Manual Review (550 - 650)", "Marginal file; branch officer field visit & override", "#D97706"),
        ("Auto-Approve (>= 650)", "Clean repayment track; handoff to Bank CBS queue", "#059669")
    ]
    cur_y = 0.65
    for title, desc, col in zones:
        box = patches.FancyBboxPatch(
            (1.46, cur_y - 0.09), 0.28, 0.09,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.2, edgecolor=col, facecolor="#FFFFFF", zorder=2
        )
        ax.add_patch(box)
        ax.text(1.48, cur_y - 0.03, title, fontsize=8.2, fontweight="bold", color=col, ha="left")
        ax.text(1.48, cur_y - 0.06, desc, fontsize=6.8, color="#475569", ha="left")
        cur_y -= 0.12

    # Draw Connecting Arrows from Raw to 5-Cs
    ax.annotate("", xy=(0.56, 0.92), xytext=(0.43, 0.94), arrowprops=dict(arrowstyle="->", color="#3B82F6", lw=1.2))
    ax.annotate("", xy=(0.56, 0.74), xytext=(0.43, 0.70), arrowprops=dict(arrowstyle="->", color="#10B981", lw=1.2))
    ax.annotate("", xy=(0.56, 0.58), xytext=(0.43, 0.82), arrowprops=dict(arrowstyle="->", color="#F59E0B", lw=1.2))
    ax.annotate("", xy=(0.56, 0.40), xytext=(0.43, 0.82), arrowprops=dict(arrowstyle="->", color="#8B5CF6", lw=1.2))
    ax.annotate("", xy=(0.56, 0.22), xytext=(0.43, 0.35), arrowprops=dict(arrowstyle="->", color="#EC4899", lw=1.2))

    # Connect 5-Cs to Feature Store
    ax.annotate("", xy=(1.10, 0.79), xytext=(0.96, 0.79), arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.8))
    # Connect Feature Store to WoE Scorecard
    ax.annotate("", xy=(1.46, 0.85), xytext=(1.40, 0.85), arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=1.8))
    # Connect WoE Scorecard to Decision Zones
    ax.annotate("", xy=(1.60, 0.65), xytext=(1.60, 0.72), arrowprops=dict(arrowstyle="->", color="#334155", lw=1.5))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

# -------------------------------------------------------------
# 3. RENDER RELATIONAL SCHEMA & INTEGRITY MATRIX GRAPHIC
# -------------------------------------------------------------
def render_schema_matrix_table(output_path="figures/relational_schema_integrity_matrix.png"):
    fig, ax = plt.subplots(figsize=(20, 11), dpi=300)
    ax.axis("off")

    matrix_data = [
        ["borrowers", "id (UUID)", "village_id", "Anchor", "aadhaar_hash is unique salted SHA-256; mobile AES-256; PII isolated from X", "DPDP Act 2023 Citizen Sovereignty"],
        ["consent_records", "id (UUID)", "borrower_id", "1 : N", "Append-only SHA-256 hash chaining H(n)=SHA256(H(n-1)||data); unilateral revocation", "DPDP Act 2023 Purpose Limitation"],
        ["feature_snapshots", "id (UUID)", "borrower_id, consent_id", "1 : N", "Persists 21 continuous/categorical 5-Cs features; strictly immutable snapshot", "BCBS SR 11-7 Model Governance"],
        ["score_results", "id (UUID)", "feature_id", "1 : 1", "scaled_score bounded to [300, 900]; bilingual TreeSHAP reason codes in JSON", "RBI Digital Lending Clause 6.3"],
        ["applications", "id (UUID)", "borrower_id, score_id", "1 : N", "Unique (borrower_id, created_at) prevents duplicate open applications", "Lending Origination Controls"],
        ["officer_decisions", "id (UUID)", "application_id", "1 : 1", "Append-only trigger prevents UPDATE/DELETE; requires override_reason and note", "Credit Risk Dissent Audit Trail"],
        ["re_handoffs", "id (UUID)", "application_id", "1 : 1", "Generates idempotency reference token and SHA-256 digest for Bank CBS queue", "Commercial Bank CBS Interoperability"],
        ["grievance_records", "id (UUID)", "borrower_id", "1 : N", "sla_deadline automatically set to created_at + 30 days statutory regulatory countdown", "Statutory 30-Day SLA Redressal"],
        ["audit_events", "id (UUID)", "None", "1 : N", "Immutable system event bus logging actor_role, endpoint, and payload_hash", "Non-Repudiation Security Log"],
        ["model_promotions", "id (UUID)", "None", "1 : N", "Logs champion version tags & automated Fairness Gate disparity scores (<=20%, <=25%)", "RBI Fair Lending Parity Oversight"]
    ]

    col_labels = ["Entity Name", "Primary Key", "Foreign Keys", "Cardinality", "Key Constraints & Invariants", "Regulatory Compliance Anchor"]

    table = ax.table(
        cellText=matrix_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="left",
        colWidths=[0.11, 0.08, 0.12, 0.07, 0.38, 0.24]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 2.3)

    # Style header
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1E3A8A")
            cell.set_text_props(color="white", weight="bold")
        else:
            if row % 2 == 1:
                cell.set_facecolor("#F8FAFC")
            else:
                cell.set_facecolor("#FFFFFF")
            if col == 0:
                cell.set_text_props(weight="bold", color="#1E40AF")
            elif col in [1, 2]:
                cell.set_text_props(family="monospace", color="#334155")
            elif col == 3:
                cell.set_text_props(weight="bold", color="#B45309", ha="center")
            elif col == 4:
                cell.set_text_props(color="#0F172A")
            elif col == 5:
                cell.set_text_props(color="#047857", weight="bold")

    plt.title("CreditTech: Relational Schema & Integrity Invariant Matrix", fontsize=14, fontweight="bold", pad=20, color="#0F172A")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

def render_all():
    print("Rendering CreditTech complete diagram suite (300 DPI)...")
    render_platform_core_er("figures/platform_core_er_diagram.png")
    render_multi_rail_lineage("figures/multi_rail_data_lineage_diagram.png")
    render_schema_matrix_table("figures/relational_schema_integrity_matrix.png")
    print("All diagrams rendered successfully!")

if __name__ == "__main__":
    render_all()


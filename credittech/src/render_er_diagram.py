"""
CreditTech Publication ER Diagram Renderer
==========================================
Generates a crisp, publication-grade 300 DPI Entity-Relationship diagram
visualizing both the 10 core institutional entities and the 4-rail multi-table schema.
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_table_card(ax, x, y, width, height, title, columns, header_color="#1E3A8A", bg_color="#F8FAFC", border_color="#334155"):
    # Card outer shadow & box
    rect = patches.FancyBboxPatch(
        (x, y - height), width, height,
        boxstyle="round,pad=0.01,rounding_size=0.03",
        linewidth=1.2,
        edgecolor=border_color,
        facecolor=bg_color,
        zorder=2
    )
    ax.add_patch(rect)

    # Header box
    header_h = 0.22 * height
    header_rect = patches.FancyBboxPatch(
        (x, y - header_h), width, header_h,
        boxstyle="round,pad=0.01,rounding_size=0.03",
        linewidth=1.0,
        edgecolor=border_color,
        facecolor=header_color,
        zorder=3
    )
    ax.add_patch(header_rect)

    # Header text
    ax.text(
        x + width / 2.0, y - header_h / 2.0, title,
        color="white", fontsize=9.5, fontweight="bold",
        ha="center", va="center", zorder=4
    )

    # Column lines
    n_cols = len(columns)
    line_spacing = (height - header_h - 0.04) / max(n_cols, 1)
    cur_y = y - header_h - 0.04
    for col, col_type, is_key in columns:
        prefix = "[PK] " if is_key == "PK" else "[FK] " if is_key == "FK" else "[UK] " if is_key == "UK" else " • "
        font_weight = "bold" if is_key in ["PK", "FK", "UK"] else "normal"
        text_color = "#0F172A" if is_key == "PK" else "#1E40AF" if is_key == "FK" else "#475569"
        
        ax.text(
            x + 0.02, cur_y - 0.02, f"{prefix}{col}",
            color=text_color, fontsize=7.5, fontweight=font_weight,
            ha="left", va="top", zorder=4
        )
        ax.text(
            x + width - 0.02, cur_y - 0.02, col_type,
            color="#64748B", fontsize=7.0, fontfamily="monospace",
            ha="right", va="top", zorder=4
        )
        cur_y -= line_spacing

def draw_arrow(ax, x1, y1, x2, y2, label="1 : N", color="#475569"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.5, shrinkA=4, shrinkB=4, mutation_scale=12),
        zorder=1
    )
    mid_x = (x1 + x2) / 2.0
    mid_y = (y1 + y2) / 2.0
    ax.text(
        mid_x, mid_y + 0.015, label,
        fontsize=7.5, fontweight="bold", color="#1E293B",
        ha="center", va="bottom",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="#CBD5E1", alpha=0.9),
        zorder=5
    )

def render_er_diagram(output_path="figures/er_diagram.png"):
    fig, ax = plt.subplots(figsize=(18, 12), dpi=300)
    ax.set_xlim(0, 1.8)
    ax.set_ylim(0, 1.2)
    ax.axis("off")

    # Title & Subtitle
    ax.text(
        0.9, 1.16, "CreditTech: Relational Entity-Relationship (ER) Architecture",
        fontsize=16, fontweight="bold", color="#0F172A", ha="center"
    )
    ax.text(
        0.9, 1.13, "DPDP Act 2023 Consent Chaining, 4-Rail Feature Store, Scorecard Decisioning & Core Banking CBS Handoff",
        fontsize=10.5, color="#475569", ha="center"
    )

    # 1. Borrowers (Anchor Entity)
    draw_table_card(
        ax, x=0.08, y=1.05, width=0.30, height=0.28,
        title="borrowers (A_borrowers)",
        columns=[
            ("id / borrower_id", "UUID [PK]", "PK"),
            ("village_id", "VARCHAR [FK]", "FK"),
            ("aadhaar_hash", "VARCHAR [UK]", "UK"),
            ("full_name", "VARCHAR", ""),
            ("phone_encrypted", "AES-256", ""),
            ("segment", "ENUM", ""),
            ("landholding_band", "ENUM [Audit]", ""),
            ("gender", "CHAR [Audit]", ""),
            ("caste_category", "ENUM [Audit]", ""),
            ("bureau_tradelines", "INT", "")
        ],
        header_color="#1E3A8A"
    )

    # 2. Consent Records (DPDP Immutable Ledger)
    draw_table_card(
        ax, x=0.08, y=0.68, width=0.30, height=0.22,
        title="consent_records",
        columns=[
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

    # 3. Multi-Rail Feature Snapshots
    draw_table_card(
        ax, x=0.52, y=1.05, width=0.34, height=0.28,
        title="feature_snapshots (modeling_features)",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("consent_id", "UUID [FK]", "FK"),
            ("shg_repayment_rate", "FLOAT (Char)", ""),
            ("utility_on_time_ratio", "FLOAT (Char)", ""),
            ("avg_monthly_inflow", "FLOAT (Cap)", ""),
            ("foir", "FLOAT (Cap)", ""),
            ("avg_daily_balance", "FLOAT (Cap)", ""),
            ("effective_land_ha", "FLOAT (Coll)", ""),
            ("ndvi_peak_mean", "FLOAT (Cond)", ""),
            ("completeness_pct", "FLOAT", "")
        ],
        header_color="#4338CA"
    )

    # 4. Score Results (300-900 Scorecard)
    draw_table_card(
        ax, x=0.52, y=0.68, width=0.34, height=0.22,
        title="score_results",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("feature_id", "UUID [FK]", "FK"),
            ("model_version", "VARCHAR", ""),
            ("pd_score", "FLOAT (0..1)", ""),
            ("scaled_score", "INT (300..900)", ""),
            ("decision_zone", "ENUM", ""),
            ("shap_reasons_json", "JSON (Hi/En)", "")
        ],
        header_color="#7C3AED"
    )

    # 5. Loan Applications
    draw_table_card(
        ax, x=0.98, y=1.05, width=0.32, height=0.24,
        title="applications (H_loans)",
        columns=[
            ("id / loan_id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("score_id", "UUID [FK]", "FK"),
            ("product_type", "ENUM", ""),
            ("loan_amount_inr", "NUMERIC", ""),
            ("tenor_months", "INT", ""),
            ("interest_rate_pct", "FLOAT", ""),
            ("repayment_mode", "ENUM", ""),
            ("status", "ENUM", "")
        ],
        header_color="#B45309"
    )

    # 6. Officer Underwriting Decisions & Overrides
    draw_table_card(
        ax, x=0.98, y=0.72, width=0.32, height=0.22,
        title="officer_decisions",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("application_id", "UUID [FK]", "FK"),
            ("officer_id", "VARCHAR", ""),
            ("final_verdict", "ENUM", ""),
            ("is_override", "BOOLEAN", ""),
            ("override_reason_code", "VARCHAR", ""),
            ("justification_note", "TEXT", ""),
            ("decided_at", "DATETIME", "")
        ],
        header_color="#C026D3"
    )

    # 7. Regulated Bank CBS Handoff
    draw_table_card(
        ax, x=1.40, y=0.72, width=0.32, height=0.18,
        title="re_handoffs",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("application_id", "UUID [FK]", "FK"),
            ("bank_code", "VARCHAR (RRB)", ""),
            ("external_ref_token", "VARCHAR", ""),
            ("payload_digest", "SHA-256", ""),
            ("dispatched_at", "DATETIME", "")
        ],
        header_color="#059669"
    )

    # 8. Grievance Records (30-day statutory SLA)
    draw_table_card(
        ax, x=0.08, y=0.38, width=0.30, height=0.20,
        title="grievance_records",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("borrower_id", "UUID [FK]", "FK"),
            ("category", "ENUM", ""),
            ("status", "ENUM", ""),
            ("sla_deadline", "DATETIME (+30d)", ""),
            ("resolved_at", "DATETIME", "")
        ],
        header_color="#DC2626"
    )

    # 9. Audit Events (Append-Only Event Bus)
    draw_table_card(
        ax, x=0.98, y=0.42, width=0.32, height=0.18,
        title="audit_events",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("event_type", "VARCHAR", ""),
            ("actor_role", "ENUM", ""),
            ("actor_id", "VARCHAR", ""),
            ("payload_hash", "SHA-256", ""),
            ("timestamp", "DATETIME", "")
        ],
        header_color="#334155"
    )

    # 10. Model Promotions & Governance
    draw_table_card(
        ax, x=0.52, y=0.38, width=0.34, height=0.20,
        title="model_promotions",
        columns=[
            ("id", "UUID [PK]", "PK"),
            ("candidate_model_id", "VARCHAR", ""),
            ("previous_champion_id", "VARCHAR", ""),
            ("fairness_gate_passed", "BOOLEAN", ""),
            ("gender_disparity_pct", "FLOAT (<=20%)", ""),
            ("land_disparity_pct", "FLOAT (<=25%)", ""),
            ("promoted_by", "VARCHAR", "")
        ],
        header_color="#0284C7"
    )

    # 11. 4-Rail Raw Input Micro-Tables Panel (Bottom Banner)
    raw_panel = patches.FancyBboxPatch(
        (0.08, 0.04), 1.64, 0.10,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1.0, edgecolor="#94A3B8", facecolor="#F1F5F9", zorder=1
    )
    ax.add_patch(raw_panel)
    ax.text(
        0.9, 0.115, "MULTI-RAIL SOURCE TABLES (Join key: borrower_id)",
        fontsize=9.0, fontweight="bold", color="#334155", ha="center"
    )
    rails_text = (
        "C_aa_monthly (Account Aggregator, 12m cashflows)  |  "
        "D_shg_ledger (Peer Thrift & Meetings)  |  "
        "E_utility_digital (Electricity & Mobile Recharges)\n"
        "F_satellite_weather (Sentinel-2 NDVI & Rain)  |  "
        "B_household_land_crop (Land & Livestock)  |  "
        "G_govt_social (PM-Kisan & MGNREGA)  |  "
        "ground_truth_latent (Audit Only)"
    )
    ax.text(0.9, 0.065, rails_text, fontsize=8.0, color="#475569", ha="center")

    # Connective Relationship Lines & Arrows
    # 1. Borrowers -> Consent Records (1 : N)
    draw_arrow(ax, 0.23, 0.77, 0.23, 0.68, "1 : N")
    # 2. Borrowers -> Feature Snapshots (1 : N)
    draw_arrow(ax, 0.38, 0.95, 0.52, 0.95, "1 : N")
    # 3. Consent Records -> Feature Snapshots (1 : N)
    draw_arrow(ax, 0.38, 0.60, 0.52, 0.91, "1 : N")
    # 4. Feature Snapshots -> Score Results (1 : 1)
    draw_arrow(ax, 0.69, 0.77, 0.69, 0.68, "1 : 1")
    # 5. Borrowers -> Applications (1 : N)
    draw_arrow(ax, 0.38, 1.02, 0.98, 1.02, "1 : N")
    # 6. Score Results -> Applications (1 : 1)
    draw_arrow(ax, 0.86, 0.60, 0.98, 0.93, "1 : 1")
    # 7. Applications -> Officer Decisions (1 : 1)
    draw_arrow(ax, 1.14, 0.81, 1.14, 0.72, "1 : 1")
    # 8. Officer Decisions -> RE Handoffs (1 : 1)
    draw_arrow(ax, 1.30, 0.61, 1.40, 0.61, "1 : 1")
    # 9. Borrowers -> Grievance Records (1 : N)
    draw_arrow(ax, 0.23, 0.46, 0.23, 0.38, "1 : N")
    # 10. Officer Decisions -> Audit Events (1 : N)
    draw_arrow(ax, 1.14, 0.50, 1.14, 0.42, "1 : N")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Publication-grade ER diagram saved to: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "figures/er_diagram.png"
    render_er_diagram(out)

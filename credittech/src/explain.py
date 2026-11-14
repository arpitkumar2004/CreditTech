"""
CreditTech Explainability, Fairness & Credit Policy Engine
=========================================================
Implements regulatory-grade explainability and fair lending compliance:
1. Closed-form WoE Scorecard Point Attribution & Adverse Reason Codes
   in English and Hindi (Devanagari) per RBI Digital Lending Guidelines (Clause 6.3).
2. Counterfactual "What-If" Prescriptive Guidance for borderline applicants.
3. Demographic Fairness & Disparate Impact Audit across protected groups
   (Gender, Caste Category, Age Bands, Landholding Bands).
4. Economic Expected Profit Optimization & Policy Cutoff Frontier.
5. Personalized Safe Debt-Service Loan Sizing Recommender.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression

# -------------------------------------------------------------
# 1. BILINGUAL REGULATORY REASON CODES DICTIONARY (RBI CLAUSE 6.3)
# -------------------------------------------------------------
REASON_CODES_CATALOG = {
    "foir": {
        "en": "High debt obligation relative to monthly cash inflow (FOIR > 40%).",
        "hi": "मासिक नकदी प्रवाह की तुलना में ऋण देनदारियों का उच्च अनुपात (FOIR > 40%)।",
        "direction": "lower_is_better"
    },
    "utility_on_time_ratio": {
        "en": "History of electricity utility payment delays or overdue arrears.",
        "hi": "बिजली बिल भुगतान में देरी या पिछले बकाए का रिकॉर्ड।",
        "direction": "higher_is_better"
    },
    "shg_repayment_rate": {
        "en": "Sub-optimal internal loan repayment rate in Self-Help Group (SHG).",
        "hi": "स्वयं सहायता समूह (SHG) के आंतरिक ऋण पुनर्भुगतान दर में कमी।",
        "direction": "higher_is_better"
    },
    "savings_regularity_pct": {
        "en": "Irregularity in monthly SHG thrift savings contributions.",
        "hi": "स्वयं सहायता समूह (SHG) में मासिक बचत योगदान में अनियमितता।",
        "direction": "higher_is_better"
    },
    "avg_daily_balance": {
        "en": "Low average daily bank balance and frequent near-zero dips.",
        "hi": "बैंक खाते में कम औसत दैनिक शेषराशि और बार-बार न्यूनतम राशि।",
        "direction": "higher_is_better"
    },
    "inflow_cv": {
        "en": "High volatility and unpredictability in monthly cash inflows.",
        "hi": "मासिक नकद आय प्रवाह में अत्यधिक उतार-चढ़ाव और अनिश्चितता।",
        "direction": "lower_is_better"
    },
    "inflow_outflow_ratio": {
        "en": "Total debits closely match or exceed total banking inflows.",
        "hi": "कुल बैंकिंग निकासी कुल आवक के बराबर या उससे अधिक है।",
        "direction": "higher_is_better"
    },
    "recharge_regularity": {
        "en": "Irregular mobile phone prepaid top-up pattern.",
        "hi": "मोबाइल फोन प्रीपेड रिचार्ज चक्र में अनियमितता।",
        "direction": "higher_is_better"
    },
    "account_age_months": {
        "en": "Limited operating tenure of primary bank account (< 24 months).",
        "hi": "मुख्य बैंक खाते का सीमित परिचालन इतिहास (< 24 महीने)।",
        "direction": "higher_is_better"
    },
    "effective_land_ha": {
        "en": "Limited operational agricultural landholding buffer.",
        "hi": "परिचालन योग्य कृषि भूमि का सीमित सुरक्षा दायरा।",
        "direction": "higher_is_better"
    },
    "livestock_value": {
        "en": "Low liquid livestock and productive biological asset base.",
        "hi": "दुधारू पशुधन और उत्पादक जैविक परिसंपत्तियों का अभाव।",
        "direction": "higher_is_better"
    },
    "asset_index": {
        "en": "Low composite physical asset ownership score.",
        "hi": "भौतिक संपत्ति और कृषि उपकरणों का निम्न समग्र सूचकांक।",
        "direction": "higher_is_better"
    },
    "ndvi_peak_mean": {
        "en": "Satellite telemetry indicates vegetation stress or depressed crop biomass.",
        "hi": "उपग्रह चित्रों में फसलों की स्थिति और बायोमास में कमजोरी दर्ज।",
        "direction": "higher_is_better"
    },
    "rainfall_pct_normal": {
        "en": "Village agro-climatic zone experienced severe rainfall deficit.",
        "hi": "ग्राम कृषि-जलवायु क्षेत्र में सामान्य से काफी कम वर्षा दर्ज।",
        "direction": "higher_is_better"
    },
    "crop_insurance_flag": {
        "en": "Absence of PMFBY crop insurance cover against yield shocks.",
        "hi": "फसल नुकसान के खिलाफ प्रधानमंत्री फसल बीमा (PMFBY) का अभाव।",
        "direction": "higher_is_better"
    }
}

# -------------------------------------------------------------
# 2. WOE SCORECARD ATTRIBUTION & BILINGUAL ADVERSE REASON GENERATOR
# -------------------------------------------------------------
class ScorecardExplainer:
    """
    Computes closed-form point contributions, bilingual adverse reason codes,
    and counterfactual prescriptions for individual rural applicants.
    """
    def __init__(self, target_score=600, target_odds=19.0, pdo=40, n_bins=5):
        self.target_score = target_score
        self.target_odds = target_odds
        self.pdo = pdo
        self.n_bins = n_bins
        self.factor_ = pdo / np.log(2.0)
        self.offset_ = target_score - self.factor_ * np.log(target_odds)
        self.bin_edges_ = {}
        self.woe_maps_ = {}
        self.feature_names_ = []
        self.lr_model_ = LogisticRegression(C=1.5, max_iter=1000, random_state=42)

    def fit(self, X_df, y):
        self.feature_names_ = list(X_df.columns)
        X_woe = np.zeros_like(X_df.values, dtype=float)
        y_arr = np.array(y)

        total_goods = np.sum(y_arr == 0)
        total_bads = np.sum(y_arr == 1)

        for col_idx, col in enumerate(self.feature_names_):
            col_vals = X_df[col].values
            try:
                _, edges = pd.qcut(col_vals, q=self.n_bins, retbins=True, duplicates="drop")
            except Exception:
                _, edges = pd.cut(col_vals, bins=self.n_bins, retbins=True)
            edges[0] = -np.inf
            edges[-1] = np.inf
            self.bin_edges_[col] = edges

            bin_idx = np.digitize(col_vals, edges) - 1
            woe_map = {}
            for b in np.unique(bin_idx):
                mask = bin_idx == b
                goods = np.sum((y_arr == 0) & mask) + 0.5
                bads = np.sum((y_arr == 1) & mask) + 0.5
                woe = np.log((goods / total_goods) / (bads / total_bads))
                woe_map[b] = woe
                X_woe[mask, col_idx] = woe
            self.woe_maps_[col] = woe_map

        self.lr_model_.fit(X_woe, y_arr)
        # Compute base points and feature point lookup tables
        self.intercept_ = float(self.lr_model_.intercept_[0])
        self.coefs_ = self.lr_model_.coef_[0]
        self.base_points_ = int(round(self.offset_ - self.factor_ * self.intercept_))

    def score_applicant(self, applicant_row):
        """Scores a single applicant and provides closed-form feature points."""
        feat_points = {}
        total_score = self.base_points_

        for col_idx, col in enumerate(self.feature_names_):
            val = applicant_row[col]
            edges = self.bin_edges_[col]
            woe_map = self.woe_maps_[col]
            b_idx = int(np.digitize([val], edges)[0] - 1)
            default_woe = float(np.mean(list(woe_map.values())))
            woe = woe_map.get(b_idx, default_woe)
            beta = self.coefs_[col_idx]
            # Contribution to scaled score: points = - (beta * woe) * factor
            pts = int(round(- beta * woe * self.factor_))
            feat_points[col] = pts
            total_score += pts

        scaled_score = int(np.clip(total_score, 300, 900))
        # Derive decision zone
        if scaled_score >= 650:
            zone = "AUTO_APPROVE"
        elif scaled_score >= 550:
            zone = "MANUAL_REVIEW"
        else:
            zone = "REJECT"

        return scaled_score, zone, feat_points

    def generate_adverse_reasons(self, applicant_row, top_n=3):
        """Generates top-N adverse reason codes in English & Hindi per RBI Clause 6.3."""
        score, zone, feat_points = self.score_applicant(applicant_row)
        # Sort features by lowest points (greatest drag on credit score)
        sorted_feats = sorted(feat_points.items(), key=lambda item: item[1])

        adverse_reasons = []
        for feat, pts in sorted_feats:
            if feat in REASON_CODES_CATALOG:
                adverse_reasons.append({
                    "feature": feat,
                    "point_impact": pts,
                    "reason_en": REASON_CODES_CATALOG[feat]["en"],
                    "reason_hi": REASON_CODES_CATALOG[feat]["hi"]
                })
            if len(adverse_reasons) >= top_n:
                break

        return score, zone, adverse_reasons

    def generate_counterfactual_hint(self, applicant_row):
        """Generates smallest realistic behavioral adjustment to reach next credit tier."""
        score, zone, feat_points = self.score_applicant(applicant_row)
        if zone == "AUTO_APPROVE":
            return {
                "current_zone": zone,
                "current_score": score,
                "target_zone": zone,
                "target_score": score,
                "prescription_en": "Profile qualified for prime automated sanction. No corrective action required.",
                "prescription_hi": "प्रोफाइल स्वचालित स्वीकृति के लिए योग्य है। किसी सुधारात्मक कार्रवाई की आवश्यकता नहीं।"
            }

        target_score = 650 if zone == "MANUAL_REVIEW" else 550
        gap = target_score - score

        # Identify top actionable levers: utility_on_time_ratio, savings_regularity_pct, avg_daily_balance, shg_repayment_rate
        actionable_levers = ["utility_on_time_ratio", "savings_regularity_pct", "avg_daily_balance", "shg_repayment_rate"]
        best_lever = None
        min_loss = float("inf")

        for lev in actionable_levers:
            if lev in self.feature_names_:
                current_val = applicant_row[lev]
                # Simulate optimal improvement
                sim_row = applicant_row.copy()
                if lev == "utility_on_time_ratio":
                    sim_row[lev] = 1.0
                    action_en = "Paying all electricity utility bills strictly on time for the next 6 months"
                    action_hi = "अगले 6 महीनों तक सभी बिजली बिलों का समय पर पूर्ण भुगतान करना"
                elif lev == "savings_regularity_pct":
                    sim_row[lev] = min(100.0, current_val + 25.0)
                    action_en = f"Increasing SHG monthly thrift attendance and savings regularity to {sim_row[lev]:.0f}%"
                    action_hi = f"स्वयं सहायता समूह में मासिक बचत नियमितता को बढ़ाकर {sim_row[lev]:.0f}% करना"
                elif lev == "avg_daily_balance":
                    sim_row[lev] = current_val + 1500.0
                    action_en = "Maintaining an additional Rs 1,500 average minimum balance in bank account"
                    action_hi = "बैंक खाते में ₹1,500 की अतिरिक्त औसत न्यूनतम शेष राशि बनाए रखना"
                elif lev == "shg_repayment_rate":
                    sim_row[lev] = 1.0
                    action_en = "Clearing pending internal SHG group loan dues on schedule"
                    action_hi = "समूह के आंतरिक ऋण बकाया का समय पर पूर्ण भुगतान करना"

                new_score, new_zone, _ = self.score_applicant(sim_row)
                gain = new_score - score
                if gain > 0 and (gap - gain) < min_loss:
                    min_loss = max(0, gap - gain)
                    best_lever = {
                        "lever": lev,
                        "simulated_score": new_score,
                        "point_gain": gain,
                        "action_en": action_en,
                        "action_hi": action_hi
                    }

        if best_lever is not None:
            presc_en = f"{best_lever['action_en']} will lift score by +{best_lever['point_gain']} pts to reach {best_lever['simulated_score']}."
            presc_hi = f"{best_lever['action_hi']} क्रेडिट स्कोर को +{best_lever['point_gain']} अंक बढ़ाकर {best_lever['simulated_score']} तक पहुंचा देगा।"
        else:
            presc_en = "Maintain continuous timely debt service and regular banking transactions for 6 months."
            presc_hi = "6 महीनों तक नियमित बैंकिंग लेनदेन और समय पर ऋण भुगतान बनाए रखें।"

        return {
            "current_zone": zone,
            "current_score": score,
            "target_zone": "MANUAL_REVIEW" if zone == "REJECT" else "AUTO_APPROVE",
            "target_score": target_score,
            "prescription_en": presc_en,
            "prescription_hi": presc_hi
        }

# -------------------------------------------------------------
# 3. DEMOGRAPHIC FAIRNESS & PARITY AUDIT
# -------------------------------------------------------------
def run_demographic_fairness_audit(df_features, scores, cutoffs=(550, 650)):
    """
    Executes algorithmic fairness evaluation across protected demographic groups.
    Computes Approval Rate, Disparate Impact Ratio (DIR), False Positive Rate (FPR),
    and False Negative Rate (FNR) per group.
    """
    df_eval = df_features.copy()
    scores_arr = np.array(scores)
    df_eval["score"] = scores_arr
    df_eval["approved"] = (scores_arr >= cutoffs[0]).astype(int) # At least manual review or auto approve

    protected_attributes = ["gender", "caste_category", "age_band", "landholding_band"]
    fairness_records = []

    for attr in protected_attributes:
        groups = df_eval[attr].unique()
        # Baseline group with highest approval rate for Disparate Impact Ratio
        group_rates = df_eval.groupby(attr)["approved"].mean()
        ref_group = group_rates.idxmax()
        ref_rate = max(group_rates.max(), 1e-4)

        for grp in groups:
            sub = df_eval[df_eval[attr] == grp]
            n_tot = len(sub)
            n_app = sub["approved"].sum()
            app_rate = n_app / n_tot
            dir_ratio = app_rate / ref_rate

            # Error rates (False Positive = Predicted Good but Defaulted; False Negative = Predicted Bad but Non-Default)
            y_true = sub["default_flag"].values
            y_pred_bad = (sub["score"] < cutoffs[0]).astype(int)

            actual_goods = np.sum(y_true == 0)
            actual_bads = np.sum(y_true == 1)

            fnr = float(np.sum((y_pred_bad == 1) & (y_true == 0)) / max(actual_goods, 1)) # False Rejection Rate
            fpr = float(np.sum((y_pred_bad == 0) & (y_true == 1)) / max(actual_bads, 1))  # False Acceptance Rate

            fairness_records.append({
                "attribute": attr,
                "group": grp,
                "n_borrowers": n_tot,
                "avg_score": round(float(sub["score"].mean()), 1),
                "approval_rate_pct": round(app_rate * 100.0, 1),
                "disparate_impact_ratio": round(dir_ratio, 3),
                "dir_passed_80pct_rule": bool(dir_ratio >= 0.80),
                "false_rejection_rate_fnr": round(fnr * 100.0, 1),
                "false_acceptance_rate_fpr": round(fpr * 100.0, 1)
            })

    return pd.DataFrame(fairness_records)

# -------------------------------------------------------------
# 4. ECONOMIC EXPECTED PROFIT OPTIMIZATION
# -------------------------------------------------------------
def compute_economic_profit_curve(y_true, scores, loan_amount=50000.0, net_margin=0.13, lgd=0.70):
    """
    Computes institutional net expected profit curve across score cutoffs (300 to 900).
    Reward per Good Loan = loan_amount * net_margin (e.g. Rs 6,500)
    Loss per Bad Loan = loan_amount * lgd (e.g. Rs 35,000 to 42,000 with recovery cost)
    """
    reward_good = loan_amount * net_margin
    cost_bad = loan_amount * lgd + 7000.0 # Rs 42,000 total loss given default

    cutoffs = np.arange(350, 850, 10)
    profit_curve = []

    for s_cut in cutoffs:
        approved_mask = scores >= s_cut
        n_approved = int(np.sum(approved_mask))
        if n_approved == 0:
            profit_curve.append({
                "score_cutoff": s_cut,
                "approval_rate_pct": 0.0,
                "default_rate_pct": 0.0,
                "expected_profit_inr": 0.0
            })
            continue

        goods = int(np.sum((y_true == 0) & approved_mask))
        bads = int(np.sum((y_true == 1) & approved_mask))
        tot_profit = goods * reward_good - bads * cost_bad
        app_rate = (n_approved / len(y_true)) * 100.0
        def_rate = (bads / n_approved) * 100.0

        profit_curve.append({
            "score_cutoff": s_cut,
            "approval_rate_pct": round(app_rate, 1),
            "default_rate_pct": round(def_rate, 2),
            "expected_profit_inr": round(tot_profit, 0)
        })

    df_profit = pd.DataFrame(profit_curve)
    best_row = df_profit.loc[df_profit["expected_profit_inr"].idxmax()]
    breakeven_candidates = df_profit[df_profit["expected_profit_inr"] >= 0]
    breakeven_cutoff = int(breakeven_candidates["score_cutoff"].min()) if len(breakeven_candidates) > 0 else 500

    return df_profit, int(best_row["score_cutoff"]), breakeven_cutoff

# -------------------------------------------------------------
# 5. PERSONALIZED SAFE DEBT-SERVICE LOAN SIZING RECOMMENDER
# -------------------------------------------------------------
def recommend_safe_loan_amount(monthly_inflow, foir, asset_index, product="Crop input (KCC-type)", tenor_months=12):
    """
    Personalized loan sizing based on statutory 40% debt-service ceiling and asset cushion.
    """
    caps = {
        "Crop input (KCC-type)": 100000.0,
        "SHG-BLP group loan": 80000.0,
        "Dairy / livestock": 120000.0,
        "Micro-enterprise working capital": 200000.0
    }
    cap = caps.get(product, 100000.0)

    # Maximum allowed debt capacity per month (40% minus existing obligations)
    max_emi_avail = max(1000.0, monthly_inflow * max(0.10, 0.40 - foir))
    # Cumulative capacity over repayment window with safety haircut based on asset index
    asset_multiplier = 0.80 + 0.35 * (asset_index / 100.0)
    raw_amount = max_emi_avail * tenor_months * asset_multiplier

    recommended_amount = int(np.clip(round(raw_amount / 5000.0) * 5000, 20000.0, cap))
    return recommended_amount

# -------------------------------------------------------------
# 6. MASTER EXECUTION & PIPELINE INTEGRATION
# -------------------------------------------------------------
def run_explainability_and_policy(data_dir="data"):
    print("=" * 80)
    print(" CREDITTECH EXPLAINABILITY, FAIRNESS & POLICY ENGINE (20,000 BORROWERS) ")
    print("=" * 80)

    feat_path = os.path.join(data_dir, "processed", "modeling_features.csv")
    df_feat = pd.read_csv(feat_path)

    core_21 = [
        "shg_repayment_rate", "shg_attendance_pct", "savings_regularity_pct",
        "utility_on_time_ratio", "recharge_regularity", "account_age_months",
        "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio",
        "income_diversification", "foir", "govt_transfer_share",
        "avg_daily_balance", "shg_savings_corpus", "livestock_value",
        "effective_land_ha", "irrigated_share", "asset_index",
        "ndvi_peak_mean", "rainfall_pct_normal", "crop_insurance_flag"
    ]

    explainer = ScorecardExplainer(target_score=600, target_odds=19.0, pdo=40, n_bins=5)
    explainer.fit(df_feat[core_21], df_feat["default_flag"])

    # Score all 20,000 borrowers
    print("\nScoring all 20,000 borrowers on 300-900 WoE Scorecard...")
    scores = []
    zones = []
    for idx in range(len(df_feat)):
        row = df_feat.iloc[idx]
        sc, zn, _ = explainer.score_applicant(row)
        scores.append(sc)
        zones.append(zn)

    df_feat["credit_score"] = scores
    df_feat["decision_zone"] = zones

    zone_counts = df_feat["decision_zone"].value_counts()
    print("\nDecision Zone Distribution across 20,000 Borrowers:")
    for zn, cnt in zone_counts.items():
        pct = (cnt / len(df_feat)) * 100.0
        print(f"  {zn:<15}: {cnt:>6} borrowers ({pct:>5.1f}%)")

    # Sample Bilingual Adverse Reasons for 3 Borderline / Rejected Applicants
    print("\n--- SAMPLE BILINGUAL ADVERSE REASON CODES (RBI CLAUSE 6.3) ---")
    sample_rejections = df_feat[df_feat["decision_zone"] == "REJECT"].head(2)
    sample_reviews = df_feat[df_feat["decision_zone"] == "MANUAL_REVIEW"].head(1)
    samples = pd.concat([sample_rejections, sample_reviews])

    for i, (_, row) in enumerate(samples.iterrows(), 1):
        b_id = row["borrower_id"]
        sc = row["credit_score"]
        zn = row["decision_zone"]
        print(f"\n[Case #{i}] Borrower {b_id} | Segment: {row['segment']} | Score: {sc} | Zone: {zn}")
        _, _, reasons = explainer.generate_adverse_reasons(row, top_n=3)
        for r_idx, r in enumerate(reasons, 1):
            print(f"  Reason {r_idx} (Impact: {r['point_impact']:+d} pts | Feature: {r['feature']}):")
            print(f"    [EN] {r['reason_en']}")
            print(f"    [HI] {r['reason_hi']}")

        hint = explainer.generate_counterfactual_hint(row)
        print(f"  Actionable Counterfactual Prescription (Target: {hint['target_score']} pts):")
        print(f"    [EN] {hint['prescription_en']}")
        print(f"    [HI] {hint['prescription_hi']}")

    # Demographic Fairness Audit
    print("\n" + "=" * 80)
    print(" DEMOGRAPHIC FAIRNESS & PARITY AUDIT (4 PROTECTED ATTRIBUTES) ")
    print("=" * 80)
    df_fairness = run_demographic_fairness_audit(df_feat, scores)
    print(df_fairness.to_string(index=False))

    fairness_out = os.path.join(data_dir, "processed", "demographic_fairness_audit.csv")
    df_fairness.to_csv(fairness_out, index=False)
    print(f"\nSaved fairness audit results to: {fairness_out}")

    # Economic Profit Optimization
    print("\n" + "=" * 80)
    print(" ECONOMIC EXPECTED PROFIT & POLICY CUTOFF OPTIMIZATION ")
    print("=" * 80)
    df_profit, best_cutoff, breakeven_cutoff = compute_economic_profit_curve(df_feat["default_flag"].values, np.array(scores))
    print(f"Profit-Maximizing Score Cutoff     : {best_cutoff} Points (Peak Net Profit: Rs {df_profit.loc[df_profit['score_cutoff']==best_cutoff, 'expected_profit_inr'].values[0]:,.0f})")
    print(f"Financial Inclusion Break-Even Cutoff: {breakeven_cutoff} Points (Zero Institutional Loss Threshold)")
    print(f"Regulatory Operational Recommended Cutoff: 550 Points (Manual Review Band: 550 to 650 Points)")

    profit_out = os.path.join(data_dir, "processed", "economic_profit_curve.csv")
    df_profit.to_csv(profit_out, index=False)
    print(f"Saved profit curve table to: {profit_out}")

    print("\n" + "=" * 80)
    print(" EXPLAINABILITY, FAIRNESS & POLICY ENGINE COMPLETED SUCCESSFULLY! ")
    print("=" * 80)
    return explainer, df_fairness, df_profit

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "data"
    run_explainability_and_policy(d)

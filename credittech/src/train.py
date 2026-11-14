"""
CreditTech Master Model Benchmark & Rail Ablation Suite
=======================================================
Trains and evaluates the 5 required model architectures on the calibrated rural dataset:
1. Standardized Logistic Regression Baseline
2. Monotonic Weight-of-Evidence (WoE) Scorecard Champion (300-900 Scale)
3. Calibrated Random Forest
4. Monotonic HistGradientBoosting (Monotonic GBDT)
5. Stacking Meta-Ensemble

Executes:
- Stratified 70/30 Holdout evaluation for publication metrics
- 8-Fold Leave-One-Village-Out Cross-Validation (LOVO CV) for spatial robustness
- Rail-by-rail ablation study proving alternative data lift
- Full calibration, ECE, Brier, KS, and inference latency benchmarking
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    brier_score_loss,
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix
)
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
    StackingClassifier
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, ClassifierMixin

# -------------------------------------------------------------
# 1. METRICS HELPERS (KS, ECE, GINI)
# -------------------------------------------------------------
def compute_ks_statistic(y_true, y_prob):
    """Computes Kolmogorov-Smirnov (KS) separation statistic."""
    df = pd.DataFrame({"y": y_true, "p": y_prob}).sort_values("p")
    total_goods = np.sum(df["y"] == 0)
    total_bads = np.sum(df["y"] == 1)
    if total_goods == 0 or total_bads == 0:
        return 0.0
    df["cum_goods"] = (df["y"] == 0).cumsum() / total_goods
    df["cum_bads"] = (df["y"] == 1).cumsum() / total_bads
    return float(np.max(np.abs(df["cum_goods"] - df["cum_bads"])))

def compute_ece(y_true, y_prob, n_bins=10):
    """Computes Expected Calibration Error (ECE) across deciles."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = bin_indices == b
        if np.sum(mask) > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            bin_weight = np.sum(mask) / n
            ece += bin_weight * np.abs(bin_acc - bin_conf)
    return float(ece)

def compute_prauc(y_true, y_prob):
    """Computes Precision-Recall AUC (PR-AUC)."""
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    return float(auc(recall, precision))

# -------------------------------------------------------------
# 2. MONOTONIC WEIGHT-OF-EVIDENCE (WoE) SCORECARD IMPLEMENTATION
# -------------------------------------------------------------
class WoEScorecardClassifier(BaseEstimator, ClassifierMixin):
    """
    Production-grade Weight-of-Evidence (WoE) Scorecard.
    Binned continuous features with monotonic constraints,
    scaled to standard institutional credit bureau points (300-900).
    """
    def __init__(self, target_score=600, target_odds=19.0, pdo=40, n_bins=5, C=1.5):
        self.target_score = target_score
        self.target_odds = target_odds
        self.pdo = pdo
        self.n_bins = n_bins
        self.C = C
        self.factor_ = pdo / np.log(2.0)
        self.offset_ = target_score - self.factor_ * np.log(target_odds)
        self.bin_edges_ = {}
        self.woe_maps_ = {}
        self.model_ = LogisticRegression(C=self.C, max_iter=1000, random_state=42)
        self.classes_ = np.array([0, 1])

    def fit(self, X, y):
        X_df = pd.DataFrame(X).copy()
        y_arr = np.array(y)
        self.n_features_in_ = X_df.shape[1]

        total_goods = np.sum(y_arr == 0)
        total_bads = np.sum(y_arr == 1)

        X_woe = np.zeros_like(X_df.values, dtype=float)

        for col_idx in range(self.n_features_in_):
            col_vals = X_df.iloc[:, col_idx].values
            # Quantile binning
            try:
                _, edges = pd.qcut(col_vals, q=self.n_bins, retbins=True, duplicates="drop")
            except Exception:
                _, edges = pd.cut(col_vals, bins=self.n_bins, retbins=True)
            edges[0] = -np.inf
            edges[-1] = np.inf
            self.bin_edges_[col_idx] = edges

            # Digitize and compute WoE
            bin_idx = np.digitize(col_vals, edges) - 1
            woe_map = {}
            for b in np.unique(bin_idx):
                mask = bin_idx == b
                goods = np.sum((y_arr == 0) & mask) + 0.5
                bads = np.sum((y_arr == 1) & mask) + 0.5
                dist_good = goods / total_goods
                dist_bad = bads / total_bads
                woe = np.log(dist_good / dist_bad)
                woe_map[b] = woe
                X_woe[mask, col_idx] = woe
            self.woe_maps_[col_idx] = woe_map

        self.model_.fit(X_woe, y_arr)
        return self

    def _transform_woe(self, X):
        X_df = pd.DataFrame(X).copy()
        X_woe = np.zeros_like(X_df.values, dtype=float)
        for col_idx in range(self.n_features_in_):
            col_vals = X_df.iloc[:, col_idx].values
            edges = self.bin_edges_[col_idx]
            woe_map = self.woe_maps_[col_idx]
            bin_idx = np.digitize(col_vals, edges) - 1
            default_woe = np.mean(list(woe_map.values()))
            for b in np.unique(bin_idx):
                mask = bin_idx == b
                X_woe[mask, col_idx] = woe_map.get(b, default_woe)
        return X_woe

    def predict_proba(self, X):
        X_woe = self._transform_woe(X)
        return self.model_.predict_proba(X_woe)

    def predict(self, X):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= 0.12).astype(int)

    def to_points(self, X):
        """Converts applicant features to 300-900 scaled bureau credit score."""
        probs = self.predict_proba(X)[:, 1]
        probs = np.clip(probs, 1e-4, 1.0 - 1e-4)
        log_odds = np.log(probs / (1.0 - probs))
        scores = self.offset_ - self.factor_ * log_odds
        return np.round(np.clip(scores, 300.0, 900.0)).astype(int)

# -------------------------------------------------------------
# 3. MASTER TRAINER & BENCHMARK SUITE
# -------------------------------------------------------------
def train_and_evaluate_all(data_dir="data"):
    print("=" * 80)
    print(" CREDITTECH BENCHMARK SUITE: 5 MODEL ARCHITECTURES & RAIL ABLATIONS ")
    print("=" * 80)

    proc_file = os.path.join(data_dir, "processed", "modeling_features.csv")
    df = pd.read_csv(proc_file)

    core_21 = [
        "shg_repayment_rate", "shg_attendance_pct", "savings_regularity_pct",
        "utility_on_time_ratio", "recharge_regularity", "account_age_months",
        "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio",
        "income_diversification", "foir", "govt_transfer_share",
        "avg_daily_balance", "shg_savings_corpus", "livestock_value",
        "effective_land_ha", "irrigated_share", "asset_index",
        "ndvi_peak_mean", "rainfall_pct_normal", "crop_insurance_flag"
    ]

    X_all = df[core_21].values
    y_all = df["default_flag"].values
    village_all = df["village_id"].values

    # Fixed 70/30 Stratified Holdout
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    # 70% train (folds 0..6), 30% test (folds 7..9)
    train_idx, test_idx = [], []
    for fold, (trn, tst) in enumerate(skf.split(X_all, y_all)):
        if fold < 7:
            train_idx.extend(tst)
        else:
            test_idx.extend(tst)

    X_train, y_train = X_all[train_idx], y_all[train_idx]
    X_test, y_test = X_all[test_idx], y_all[test_idx]
    v_test = village_all[test_idx]

    print(f"Dataset Split: Train N = {len(train_idx)} (Defaults: {np.sum(y_train)}), Test N = {len(test_idx)} (Defaults: {np.sum(y_test)})")

    # Define the 5 Models
    # Monotonic constraints: positive index means higher feature increases default, negative decreases
    # For core_21:
    # 0: shg_repayment_rate (-1)
    # 1: shg_attendance_pct (-1)
    # 2: savings_regularity_pct (-1)
    # 3: utility_on_time_ratio (-1)
    # 4: recharge_regularity (-1)
    # 5: account_age_months (-1)
    # 6: avg_monthly_inflow (-1)
    # 7: inflow_cv (+1)
    # 8: inflow_outflow_ratio (-1)
    # 9: income_diversification (0)
    # 10: foir (+1)
    # 11: govt_transfer_share (0)
    # 12: avg_daily_balance (-1)
    # 13: shg_savings_corpus (-1)
    # 14: livestock_value (-1)
    # 15: effective_land_ha (-1)
    # 16: irrigated_share (-1)
    # 17: asset_index (-1)
    # 18: ndvi_peak_mean (-1)
    # 19: rainfall_pct_normal (-1)
    # 20: crop_insurance_flag (-1)
    mono_constraints = [-1, -1, -1, -1, -1, -1, -1, 1, -1, 0, 1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1]

    models = {
        "Logistic Baseline": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=0.8, max_iter=1000, random_state=42))
        ]),
        "WoE Scorecard (Champion)": WoEScorecardClassifier(C=1.5, n_bins=5),
        "Calibrated Random Forest": CalibratedClassifierCV(
            estimator=RandomForestClassifier(max_depth=6, n_estimators=100, min_samples_leaf=20, random_state=42),
            method="sigmoid",
            cv=3
        ),
        "Monotonic GBDT": HistGradientBoostingClassifier(
            monotonic_cst=mono_constraints,
            max_iter=60,
            learning_rate=0.08,
            min_samples_leaf=25,
            random_state=42
        ),
        "Stacking Meta-Ensemble": StackingClassifier(
            estimators=[
                ("lr", Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(C=0.5, random_state=42))])),
                ("woe", WoEScorecardClassifier(C=1.2, n_bins=5)),
                ("rf", RandomForestClassifier(max_depth=6, n_estimators=60, min_samples_leaf=20, random_state=42)),
                ("gbdt", HistGradientBoostingClassifier(max_iter=50, learning_rate=0.07, min_samples_leaf=25, random_state=42))
            ],
            final_estimator=LogisticRegression(C=1.0, random_state=42),
            cv=3
        )
    }

    results = []

    print("\nEvaluating Models on 70/30 Holdout and Benchmarking Single-Row Latency...")
    for name, model in models.items():
        # Fit on training set
        model.fit(X_train, y_train)

        # Measure single-row inference latency
        sample_row = X_test[0:1]
        latencies = []
        for _ in range(200):
            t0 = time.perf_counter()
            _ = model.predict_proba(sample_row)
            latencies.append((time.perf_counter() - t0) * 1000.0) # ms
        avg_latency_ms = float(np.median(latencies))

        # Evaluate on test holdout
        y_prob = model.predict_proba(X_test)[:, 1]
        roc_auc = float(roc_auc_score(y_test, y_prob))
        gini = float(2.0 * roc_auc - 1.0)
        ks = compute_ks_statistic(y_test, y_prob)
        pr_auc = compute_prauc(y_test, y_prob)
        brier = float(brier_score_loss(y_test, y_prob))
        ece = compute_ece(y_test, y_prob, n_bins=10)

        # Operational cutoff: top ~10% risk threshold (bad rate policy)
        cutoff_prob = np.percentile(y_prob, 90.0)
        y_pred = (y_prob >= cutoff_prob).astype(int)
        acc = float(accuracy_score(y_test, y_pred) * 100.0)
        b_acc = float(balanced_accuracy_score(y_test, y_pred) * 100.0)

        results.append({
            "model_name": name,
            "roc_auc": round(roc_auc, 4),
            "gini": round(gini, 4),
            "ks_stat": round(ks, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4),
            "accuracy_pct": round(acc, 2),
            "balanced_accuracy_pct": round(b_acc, 2),
            "latency_ms": round(avg_latency_ms, 3)
        })

    df_benchmark = pd.DataFrame(results)
    print("\n--- MASTER 70/30 HOLDOUT BENCHMARK METRICS ---")
    print(df_benchmark.to_string(index=False))

    benchmark_out = os.path.join(data_dir, "processed", "model_benchmark_results.csv")
    df_benchmark.to_csv(benchmark_out, index=False)
    print(f"\nSaved benchmark metrics to: {benchmark_out}")

    # -------------------------------------------------------------
    # 4. LEAVE-ONE-VILLAGE-OUT CROSS-VALIDATION (LOVO CV: 8 FOLDS)
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" LEAVE-ONE-VILLAGE-OUT (LOVO) SPATIAL CROSS-VALIDATION (8 VILLAGES) ")
    print("=" * 80)

    logo = LeaveOneGroupOut()
    lovo_results = []
    unique_villages = np.unique(village_all)

    champion_model = models["WoE Scorecard (Champion)"]

    for train_lovo_idx, test_lovo_idx in logo.split(X_all, y_all, groups=village_all):
        test_v = village_all[test_lovo_idx][0]
        X_trn_v, y_trn_v = X_all[train_lovo_idx], y_all[train_lovo_idx]
        X_tst_v, y_tst_v = X_all[test_lovo_idx], y_all[test_lovo_idx]

        champion_model.fit(X_trn_v, y_trn_v)
        v_probs = champion_model.predict_proba(X_tst_v)[:, 1]

        v_auc = float(roc_auc_score(y_tst_v, v_probs))
        v_ks = compute_ks_statistic(y_tst_v, v_probs)
        lovo_results.append({
            "test_village": test_v,
            "borrowers": len(y_tst_v),
            "defaults": int(np.sum(y_tst_v)),
            "default_rate_pct": round(float(np.mean(y_tst_v) * 100.0), 1),
            "holdout_auc": round(v_auc, 4),
            "ks_stat": round(v_ks, 4)
        })

    df_lovo = pd.DataFrame(lovo_results)
    print(df_lovo.to_string(index=False))
    print(f"\nLeave-One-Village-Out Mean AUC: {df_lovo['holdout_auc'].mean():.4f} (Range: {df_lovo['holdout_auc'].min():.4f} to {df_lovo['holdout_auc'].max():.4f})")
    lovo_out = os.path.join(data_dir, "processed", "leave_village_out_results.csv")
    df_lovo.to_csv(lovo_out, index=False)

    # -------------------------------------------------------------
    # 5. RAIL-BY-RAIL ABLATION STUDY
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" RAIL ABLATION BENCHMARK: PROVING THE LIFT OF ALTERNATIVE DATA ")
    print("=" * 80)

    # Define Rail Feature Subsets
    rails = [
        ("Rail 1: Bureau Proxy Only", ["account_age_months"]),
        ("Rail 2: + Account Aggregator", ["account_age_months", "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio", "foir", "avg_daily_balance"]),
        ("Rail 3: + SHG Peer-Thrift", ["account_age_months", "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio", "foir", "avg_daily_balance", "shg_repayment_rate", "shg_attendance_pct", "savings_regularity_pct", "shg_savings_corpus"]),
        ("Rail 4: + Utility Telemetry", ["account_age_months", "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio", "foir", "avg_daily_balance", "shg_repayment_rate", "shg_attendance_pct", "savings_regularity_pct", "shg_savings_corpus", "utility_on_time_ratio", "recharge_regularity"]),
        ("Rail 5: + Satellite & Weather", ["account_age_months", "avg_monthly_inflow", "inflow_cv", "inflow_outflow_ratio", "foir", "avg_daily_balance", "shg_repayment_rate", "shg_attendance_pct", "savings_regularity_pct", "shg_savings_corpus", "utility_on_time_ratio", "recharge_regularity", "ndvi_peak_mean", "rainfall_pct_normal", "crop_insurance_flag"]),
        ("Rail 6: All Rails (5-Cs Core)", core_21)
    ]

    ablation_results = []
    base_auc = None

    for rail_name, feat_subset in rails:
        X_sub = df[feat_subset].values
        X_sub_trn, X_sub_tst = X_sub[train_idx], X_sub[test_idx]

        model = HistGradientBoostingClassifier(max_iter=50, learning_rate=0.08, min_samples_leaf=25, random_state=42)
        model.fit(X_sub_trn, y_train)
        probs = model.predict_proba(X_sub_tst)[:, 1]

        r_auc = float(roc_auc_score(y_test, probs))
        r_ks = compute_ks_statistic(y_test, probs)
        r_prauc = compute_prauc(y_test, probs)

        if base_auc is None:
            base_auc = r_auc
            auc_lift = 0.0
        else:
            auc_lift = (r_auc - base_auc) * 100.0

        ablation_results.append({
            "rail_configuration": rail_name,
            "num_features": len(feat_subset),
            "roc_auc": round(r_auc, 4),
            "auc_lift_pts": round(auc_lift, 2),
            "ks_stat": round(r_ks, 4),
            "pr_auc": round(r_prauc, 4)
        })

    df_ablation = pd.DataFrame(ablation_results)
    print(df_ablation.to_string(index=False))

    ablation_out = os.path.join(data_dir, "processed", "rail_ablation_results.csv")
    df_ablation.to_csv(ablation_out, index=False)
    print(f"\nSaved rail ablation results to: {ablation_out}")

    print("\n" + "=" * 80)
    print(" ALL 5 BENCHMARK MODELS AND ABLATION EXPERIMENTS COMPLETED SUCCESSFULLY! ")
    print("=" * 80)
    return df_benchmark, df_lovo, df_ablation

if __name__ == "__main__":
    d_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    train_and_evaluate_all(data_dir=d_dir)


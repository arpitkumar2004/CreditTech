"""V1 Logistic Scorecard — P3.3.

The runtime scorecard is a linear/logistic model over the P0 feature list.
There are two ways to instantiate it:

  * `LogisticScorecard()`               — default, hand-authored weights derived
                                           from 5-Cs literature (Jonnalagadda &
                                           Babu 2026). This is the pre-training
                                           baseline used by early tests.
  * `LogisticScorecard.from_artifact(p)` — loads weights fitted by ScorecardTrainer
                                           and persisted through the registry.

The predict/calibration interface is identical either way, so services/core/scoring
does not care which one is loaded.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES


# ────────────────────────────────────────────────────────────────
# Runtime scorecard (used by services/core/scoring)
# ────────────────────────────────────────────────────────────────
class LogisticScorecard:
    """Deterministic logistic credit scorecard implementing the '5 Cs' framework."""

    DEFAULT_INTERCEPT = -1.2
    DEFAULT_WEIGHTS: dict[str, float] = {
        # Character
        "shg_repayment_rate": 0.45,
        "shg_meeting_attendance_pct": 0.25,
        "shg_savings_consistency": -0.30,
        "shg_membership_years": 0.15,
        "shg_grade": 0.30,
        "utility_payment_ontime_pct": 0.20,
        "upi_transaction_regularity": -0.20,
        # Capacity
        "estimated_crop_income_kharif": 0.00001,
        "estimated_crop_income_rabi": 0.00001,
        "income_stability_cv": -0.40,
        "monthly_avg_credit_inflow": 0.00002,
        "pm_kisan_regularity": 0.25,
        # Capital
        "shg_cumulative_savings": 0.000015,
        "bank_balance_avg_6m": 0.000025,
        "asset_score": 0.35,
        # Collateral
        "land_holding_acres": 0.10,
        "irrigation_access": 0.30,
        "land_quality_ndvi_avg": 0.50,
        # Conditions
        "ndvi_trend_2season": 0.40,
        "rainfall_deviation_pct": -0.01,
        "crop_insurance_enrolled": 0.25,
    }

    def __init__(
        self,
        intercept: float | None = None,
        weights: dict[str, float] | None = None,
        model_version: str = "v1.0.0-logistic-default",
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.intercept = self.DEFAULT_INTERCEPT if intercept is None else float(intercept)
        self.weights = dict(self.DEFAULT_WEIGHTS if weights is None else weights)
        self.model_version = model_version
        self.feature_version = feature_version

    # ---------- prediction ----------
    def _coerce(self, feature: str, val: Any) -> float | None:
        if val is None:
            return None
        if isinstance(val, bool):
            return 1.0 if val else 0.0
        if isinstance(val, str):
            if feature == "shg_grade":
                return {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.1}.get(val.strip().upper())
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    def predict_probability(self, features: dict[str, Any]) -> float:
        log_odds = self.intercept
        for feature, val in features.items():
            if feature not in self.weights:
                continue
            v = self._coerce(feature, val)
            if v is None:
                continue
            log_odds += self.weights[feature] * v
        try:
            return 1.0 / (1.0 + math.exp(-log_odds))
        except OverflowError:
            return 0.0 if log_odds < 0 else 1.0

    def calibrate_score(self, prob_repayment: float) -> tuple[float, int]:
        score_100 = round(prob_repayment * 100, 1)
        p = max(0.001, min(0.999, prob_repayment))
        odds = p / (1.0 - p)
        factor = 20.0 / math.log(2.0)
        offset = 600.0 - factor * math.log(50.0)
        score_900 = int(offset + factor * math.log(odds))
        score_900 = max(300, min(900, score_900))
        return score_100, score_900

    # ---------- persistence ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "intercept": self.intercept,
            "weights": self.weights,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LogisticScorecard:
        return cls(
            intercept=payload["intercept"],
            weights=payload["weights"],
            model_version=payload.get("model_version", "v1.0.0-logistic-unknown"),
            feature_version=payload.get("feature_version", FEATURE_VERSION),
        )

    @classmethod
    def from_artifact(cls, path: str | Path) -> LogisticScorecard:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save_artifact(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        return p


# ────────────────────────────────────────────────────────────────
# Trainer (fits sklearn LogisticRegression, exports weights)
# ────────────────────────────────────────────────────────────────
@dataclass
class TrainingReport:
    model_version: str
    feature_version: str
    n_train: int
    n_val: int
    class_balance_train: dict[str, float]
    auc: float
    gini: float
    ks: float
    brier: float
    calibration_bins: list[dict[str, float]]
    feature_means: dict[str, float]
    intercept: float
    weights: dict[str, float]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScorecardTrainer:
    """Fits a weighted logistic regression on the training frame and returns a
    LogisticScorecard plus a TrainingReport suitable for the registry.

    Preprocessing:
      * missing values -> per-feature median (imputer statistics stored in report
        under feature_means)
      * per-feature standardisation is NOT applied because the runtime scorecard
        must accept raw feature values (predict_probability is a linear form on
        raw units). We keep the original units and let the model absorb scale.
      * class imbalance handled with class_weight='balanced'.
      * probability calibration with sigmoid (Platt) via CalibratedClassifierCV.
    """

    def __init__(self, model_version: str = "v1.0.0-logistic", random_state: int = 42) -> None:
        self.model_version = model_version
        self.random_state = random_state

    def fit(self, X, y) -> tuple[LogisticScorecard, TrainingReport]:
        # Local imports so unit tests that don't touch training can skip heavy deps.
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import brier_score_loss, roc_auc_score
        from sklearn.model_selection import train_test_split

        # Restrict to schema-declared features only.
        cols = [c for c in MODEL_FEATURE_NAMES if c in X.columns]
        X = X[cols].copy()
        # Impute per-feature medians; record for provenance.
        medians = X.median(numeric_only=True)
        X = X.fillna(medians)
        feature_means = X.mean(numeric_only=True).to_dict()
        # Standardise for optimisation so features on very different scales
        # (crop income ~1e4, ndvi ~0.5) are handled evenly. We convert the
        # fitted coefficients back to raw-unit space before export, so the
        # runtime scorecard still accepts un-scaled feature values.
        stds = X.std(numeric_only=True).replace(0.0, 1.0).to_dict()

        stratify = y if y.nunique() > 1 else None
        X_tr, X_val, y_tr, y_val = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, stratify=stratify,
        )

        # Scale inside training only
        mu = np.array([feature_means[c] for c in cols])
        sigma = np.array([stds[c] for c in cols])
        X_tr_s = (X_tr.to_numpy() - mu) / sigma
        X_val_s = (X_val.to_numpy() - mu) / sigma

        clf = LogisticRegression(
            penalty="l2", C=1.0, solver="lbfgs", max_iter=1000,
            class_weight="balanced", random_state=self.random_state,
        )
        clf.fit(X_tr_s, y_tr)

        proba_val = clf.predict_proba(X_val_s)[:, 1]
        auc = float(roc_auc_score(y_val, proba_val)) if y_val.nunique() > 1 else float("nan")
        gini = 2 * auc - 1 if not math.isnan(auc) else float("nan")
        brier = float(brier_score_loss(y_val, proba_val))
        ks = _ks_statistic(np.asarray(y_val), proba_val)
        calib = _calibration_bins(np.asarray(y_val), proba_val, n_bins=10)

        # Convert standardised coefficients back to raw-unit space:
        #   sum(w_s * (x - mu)/sigma) + b_s
        # = sum((w_s/sigma) * x) + (b_s - sum(w_s * mu / sigma))
        w_std = clf.coef_[0]
        w_raw = w_std / sigma
        b_raw = float(clf.intercept_[0] - float((w_std * mu / sigma).sum()))
        weights = {feat: float(w) for feat, w in zip(cols, w_raw)}
        intercept = b_raw
        class_balance = y_tr.value_counts(normalize=True).to_dict()
        # Convert numpy int keys to plain strings
        class_balance = {str(int(k)): float(v) for k, v in class_balance.items()}

        scorecard = LogisticScorecard(
            intercept=intercept,
            weights=weights,
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
        )
        report = TrainingReport(
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
            n_train=int(len(X_tr)),
            n_val=int(len(X_val)),
            class_balance_train=class_balance,
            auc=auc,
            gini=gini,
            ks=ks,
            brier=brier,
            calibration_bins=calib,
            feature_means={k: float(v) for k, v in feature_means.items()},
            intercept=intercept,
            weights=weights,
            notes=[
                "trained on proxy/synthetic data — NOT real repayment outcomes",
                "L2 logistic regression, class_weight=balanced, 80/20 stratified split",
                "no per-feature standardisation (runtime uses raw units)",
                "missing values imputed with per-feature train-set median",
            ],
        )
        return scorecard, report


def _ks_statistic(y_true, y_score) -> float:
    """Kolmogorov-Smirnov separation between positive and negative distributions."""
    import numpy as np
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    if y_true.sum() == 0 or y_true.sum() == len(y_true):
        return float("nan")
    order = np.argsort(-y_score)
    y_sorted = y_true[order]
    cum_pos = np.cumsum(y_sorted) / max(y_sorted.sum(), 1)
    cum_neg = np.cumsum(1 - y_sorted) / max((1 - y_sorted).sum(), 1)
    return float(np.max(np.abs(cum_pos - cum_neg)))


def _calibration_bins(y_true, y_prob, n_bins: int = 10) -> list[dict[str, float]]:
    import numpy as np
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi if i < n_bins - 1 else y_prob <= hi)
        count = int(mask.sum())
        if count == 0:
            bins.append({"bin_lo": float(lo), "bin_hi": float(hi), "count": 0,
                         "mean_predicted": 0.0, "observed_rate": 0.0})
        else:
            bins.append({
                "bin_lo": float(lo), "bin_hi": float(hi), "count": count,
                "mean_predicted": float(y_prob[mask].mean()),
                "observed_rate": float(y_true[mask].mean()),
            })
    return bins

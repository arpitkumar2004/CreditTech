"""Challenger Model: Monotonic-Constrained Gradient Boosted Trees (GBDT).

Captures non-linear feature interactions and threshold effects while enforcing
mathematical monotonic constraints (e.g. higher repayment rate or savings
can strictly NEVER lower an applicant's score). Calibrated via Isotonic Regression.
"""

from __future__ import annotations

import math
import pickle
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES
from ml.training.validation import ValidationMetrics, evaluate_predictions


@dataclass
class GBMTrainingReport:
    model_version: str
    feature_version: str
    n_train: int
    n_val: int
    auc: float
    gini: float
    ks: float
    brier: float
    pr_auc: float
    features: list[str]
    monotonic_constraints: dict[str, int]
    calibration_bins: list[dict[str, float]]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MonotonicGBMScorecard:
    """Runtime Monotonic Gradient Boosted Tree Scorecard."""

    # Explicit directional monotonic constraints
    # +1: higher value -> higher P(repay)
    # -1: higher value -> lower P(repay) (riskier)
    #  0: non-monotonic / neutral
    MONOTONIC_MAP: dict[str, int] = {
        "shg_repayment_rate": 1,
        "shg_meeting_attendance_pct": 1,
        "shg_savings_consistency": 1,
        "shg_membership_years": 1,
        "shg_grade": 1,
        "utility_payment_ontime_pct": 1,
        "pm_kisan_regularity": 1,
        "land_quality_ndvi_avg": 1,
        "ndvi_trend_2season": 1,
        "irrigation_access": 1,
        "crop_insurance_enrolled": 1,
        "asset_score": 1,
        "income_stability_cv": -1,  # higher volatility -> riskier
        "rainfall_deviation_pct": -1, # negative deviation -> drought risk
    }

    def __init__(
        self,
        classifier: HistGradientBoostingClassifier,
        features: list[str],
        calibrator_x: list[float] | None = None,
        calibrator_y: list[float] | None = None,
        model_version: str = "v1.1.0-gbm-challenger",
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.classifier = classifier
        self.features = features
        self.model_version = model_version
        self.feature_version = feature_version

        # TreeSHAP explainer
        try:
            self._explainer: shap.TreeExplainer | None = shap.TreeExplainer(self.classifier)
        except Exception:
            self._explainer = None

        # Isotonic probability calibrator
        self.calibrator_x = calibrator_x or []
        self.calibrator_y = calibrator_y or []
        self._iso: IsotonicRegression | None = None
        if len(self.calibrator_x) >= 5:
            self._iso = IsotonicRegression(out_of_bounds="clip")
            self._iso.fit(self.calibrator_x, self.calibrator_y)

    def _features_to_df(self, features: dict[str, Any]) -> pd.DataFrame:
        row = {}
        for col in self.features:
            val = features.get(col)
            if val is None or pd.isna(val):
                row[col] = np.nan
            else:
                try:
                    row[col] = float(val)
                except (TypeError, ValueError):
                    row[col] = np.nan
        return pd.DataFrame([row], columns=self.features)

    def predict_raw_probability(self, features: dict[str, Any]) -> float:
        """Computes raw uncalibrated probability from the tree ensemble."""
        X_df = self._features_to_df(features)
        proba = self.classifier.predict_proba(X_df)[0, 1]
        return float(proba)

    def predict_probability(self, features: dict[str, Any]) -> float:
        """Returns empirical, isotonic-calibrated probability of repayment."""
        raw_p = self.predict_raw_probability(features)
        if self._iso is not None:
            cal_p = float(self._iso.predict([raw_p])[0])
            return max(0.01, min(0.99, cal_p))
        return raw_p

    def predict_probability_array(self, X: pd.DataFrame) -> np.ndarray:
        """Vectorized prediction for a DataFrame of borrowers."""
        X_aligned = X[self.features].astype(float)
        raw_p = self.classifier.predict_proba(X_aligned)[:, 1]
        if self._iso is not None:
            cal_p = self._iso.predict(raw_p)
            return np.clip(cal_p, 0.01, 0.99)
        return raw_p

    def calibrate_score(self, prob_repayment: float) -> tuple[float, int]:
        """Maps probability to (score_100, score_900) on the 300-900 scale."""
        score_100 = round(prob_repayment * 100, 1)
        p = max(0.001, min(0.999, prob_repayment))
        odds = p / (1.0 - p)
        factor = 20.0 / math.log(2.0)
        offset = 600.0 - factor * math.log(50.0)
        score_900 = int(offset + factor * math.log(odds))
        score_900 = max(300, min(900, score_900))
        return score_100, score_900

    def compute_shap_values(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Computes TreeSHAP feature contributions for the applicant."""
        X_df = self._features_to_df(features)
        contributions = []

        if self._explainer is not None:
            try:
                shap_vals = self._explainer.shap_values(X_df)
                # TreeExplainer for binary classification may return array of shape (1, n_features)
                # or list of two classes [negative_class, positive_class]
                if isinstance(shap_vals, list) and len(shap_vals) == 2:
                    raw_shap = shap_vals[1][0]
                else:
                    raw_shap = np.array(shap_vals).squeeze()

                for feat, s_val in zip(self.features, raw_shap):
                    val = features.get(feat)
                    contributions.append({
                        "feature": feat,
                        "value": float(val) if val is not None and not pd.isna(val) else 0.0,
                        "shap_value": float(s_val),
                    })
            except Exception:
                pass

        if not contributions:
            # Fallback if TreeSHAP calculation fails on single instance
            for feat in self.features:
                contributions.append({
                    "feature": feat,
                    "value": float(features.get(feat, 0.0)),
                    "shap_value": 0.0,
                })

        contributions.sort(key=lambda x: (-abs(x["shap_value"]), x["feature"]))
        return contributions

    # ---------- Persistence ----------
    def save_artifact(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self, f)
        return p

    @classmethod
    def from_artifact(cls, path: str | Path) -> MonotonicGBMScorecard:
        with open(path, "rb") as f:
            return pickle.load(f)


class GBMScorecardTrainer:
    """Trains the Challenger Monotonic Gradient Boosted Tree Model with Isotonic Calibration."""

    def __init__(
        self,
        model_version: str = "v1.1.0-gbm-challenger",
        max_iter: int = 120,
        learning_rate: float = 0.05,
        min_samples_leaf: int = 25,
        random_state: int = 42,
    ) -> None:
        self.model_version = model_version
        self.max_iter = max_iter
        self.learning_rate = learning_rate
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        groups: pd.Series | None = None,
    ) -> tuple[MonotonicGBMScorecard, GBMTrainingReport]:
        n_samples = len(X)
        split_point = int(n_samples * 0.8)

        X_train, X_val = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_val = y.iloc[:split_point], y.iloc[split_point:]

        features = list(X.columns)
        # Build monotonic constraints vector in column order
        monotonic_cst = [MonotonicGBMScorecard.MONOTONIC_MAP.get(feat, 0) for feat in features]

        # 1. Fit monotonic HistGradientBoostingClassifier
        clf = HistGradientBoostingClassifier(
            monotonic_cst=monotonic_cst,
            max_iter=self.max_iter,
            learning_rate=self.learning_rate,
            min_samples_leaf=self.min_samples_leaf,
            class_weight="balanced",
            random_state=self.random_state,
        )
        clf.fit(X_train[features], y_train)

        # 2. Out-of-fold probability calibration
        raw_val_p = clf.predict_proba(X_val[features])[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(raw_val_p, y_val)

        # Calibrated validation predictions
        cal_val_p = np.clip(iso.predict(raw_val_p), 0.01, 0.99)
        metrics = evaluate_predictions(y_val, cal_val_p)

        # 3. Assemble Scorecard
        scorecard = MonotonicGBMScorecard(
            classifier=clf,
            features=features,
            calibrator_x=raw_val_p.tolist(),
            calibrator_y=y_val.tolist(),
            model_version=self.model_version,
        )

        constraints_dict = {f: c for f, c in zip(features, monotonic_cst) if c != 0}
        report = GBMTrainingReport(
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
            n_train=len(X_train),
            n_val=len(X_val),
            auc=metrics.auc,
            gini=metrics.gini,
            ks=metrics.ks,
            brier=metrics.brier,
            pr_auc=metrics.pr_auc,
            features=features,
            monotonic_constraints=constraints_dict,
            calibration_bins=metrics.calibration_bins,
            notes=[
                f"Monotonic GBDT fitted on {len(X_train)} samples with {len(constraints_dict)} constrained features",
                "TreeSHAP explainability engine wired",
                "Isotonic probability calibration applied",
            ],
        )

        return scorecard, report

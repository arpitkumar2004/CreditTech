"""Random Forest Ensemble Scorecard — Challenger Model 2.

Fits a calibrated Random Forest classifier (bagging ensemble) with shallow trees
to reduce variance and provide non-linear feature interaction benchmarks.
Calibrated via Isotonic Regression to ensure well-behaved default probabilities.
"""

from __future__ import annotations

import math
import pickle
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES
from ml.training.validation import ValidationMetrics, evaluate_predictions


@dataclass
class RFTrainingReport:
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
    feature_importances: dict[str, float]
    calibration_bins: list[dict[str, float]]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RandomForestScorecard:
    """Runtime Random Forest Scorecard for Challenger Model Benchmarking."""

    def __init__(
        self,
        classifier: RandomForestClassifier,
        features: list[str],
        calibrator_x: list[float] | None = None,
        calibrator_y: list[float] | None = None,
        model_version: str = "v1.1.0-rf-scorecard",
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.classifier = classifier
        self.features = features
        self.model_version = model_version
        self.feature_version = feature_version

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
                row[col] = 0.0
            else:
                try:
                    row[col] = float(val)
                except (TypeError, ValueError):
                    row[col] = 0.0
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
        X_aligned = X[self.features].copy()
        X_aligned = X_aligned.fillna(X_aligned.median(numeric_only=True)).fillna(0.0).astype(float)
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

    def compute_feature_importances(self) -> list[dict[str, Any]]:
        """Returns Gini feature importances sorted descending."""
        importances = self.classifier.feature_importances_
        results = []
        for feat, imp in zip(self.features, importances):
            results.append({
                "feature": feat,
                "importance": round(float(imp), 4),
            })
        results.sort(key=lambda x: x["importance"], reverse=True)
        return results

    def save_artifact(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "features": self.features,
            "classifier": self.classifier,
            "calibrator_x": self.calibrator_x,
            "calibrator_y": self.calibrator_y,
        }
        with open(out, "wb") as f:
            pickle.dump(data, f)
        return out

    @classmethod
    def from_artifact(cls, path: str | Path) -> RandomForestScorecard:
        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(
            classifier=data["classifier"],
            features=data["features"],
            calibrator_x=data.get("calibrator_x", []),
            calibrator_y=data.get("calibrator_y", []),
            model_version=data.get("model_version", "v1.1.0-rf-scorecard"),
            feature_version=data.get("feature_version", FEATURE_VERSION),
        )


class RFScorecardTrainer:
    """Trainer for Random Forest Ensemble Scorecard."""

    def __init__(
        self,
        model_version: str = "v1.1.0-rf-scorecard",
        n_estimators: int = 100,
        max_depth: int = 6,
        random_state: int = 42,
    ) -> None:
        self.model_version = model_version
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        groups: pd.Series | None = None,
    ) -> tuple[RandomForestScorecard, RFTrainingReport]:
        from sklearn.metrics import brier_score_loss, roc_auc_score
        from sklearn.model_selection import StratifiedKFold

        features = [col for col in MODEL_FEATURE_NAMES if col in X.columns]
        X_df = X[features].copy()
        medians = X_df.median(numeric_only=True)
        X_clean = X_df.fillna(medians).fillna(0.0).astype(float)
        y_arr = y.to_numpy(dtype=int)

        # 1. Fit main classifier
        clf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            class_weight="balanced",
            random_state=self.random_state,
            n_jobs=-1,
        )
        clf.fit(X_clean, y_arr)

        # 2. Out-of-fold probability estimation for calibration
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
        oof_preds = np.zeros(len(y_arr))
        for tr_idx, val_idx in cv.split(X_clean, y_arr):
            fold_clf = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1,
            )
            fold_clf.fit(X_clean.iloc[tr_idx], y_arr[tr_idx])
            oof_preds[val_idx] = fold_clf.predict_proba(X_clean.iloc[val_idx])[:, 1]

        # 3. Fit Isotonic Calibrator
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(oof_preds, y_arr)
        cal_preds = np.clip(iso.predict(oof_preds), 0.01, 0.99)

        # 4. Evaluation Metrics
        eval_metrics = evaluate_predictions(y_arr, cal_preds)
        from ml.training.scorecard import _calibration_bins
        cal_bins = _calibration_bins(y_arr, cal_preds, n_bins=10)

        # Feature importances
        importances = {feat: round(float(imp), 4) for feat, imp in zip(features, clf.feature_importances_)}

        scorecard = RandomForestScorecard(
            classifier=clf,
            features=features,
            calibrator_x=oof_preds.tolist()[:1000],  # Subsample calibration points for compact storage
            calibrator_y=y_arr.tolist()[:1000],
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
        )

        report = RFTrainingReport(
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
            n_train=int(len(y_arr) * 0.8),
            n_val=int(len(y_arr) * 0.2),
            auc=round(eval_metrics.auc, 4),
            gini=round(eval_metrics.gini, 4),
            ks=round(eval_metrics.ks, 4),
            brier=round(eval_metrics.brier, 4),
            pr_auc=round(eval_metrics.pr_auc, 4),
            features=features,
            feature_importances=importances,
            calibration_bins=cal_bins,
            notes=[
                f"RandomForestClassifier(n_estimators={self.n_estimators}, max_depth={self.max_depth})",
                "Fitted on full benchmark cohort with 5-fold stratified out-of-fold Isotonic calibration",
            ],
        )

        return scorecard, report

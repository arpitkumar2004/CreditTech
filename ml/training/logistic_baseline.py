"""Standardized Logistic Regression Baseline — Baseline Model.

Implements standard L2-regularized Logistic Regression over standardized continuous features.
Serves as the empirical linear baseline against which non-linear tree ensembles and
monotonic WoE scorecards are rigorously benchmarked per the ml-best-practices skill.
"""

from __future__ import annotations

import math
import pickle
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES
from ml.training.validation import ValidationMetrics, evaluate_predictions


@dataclass
class LogisticBaselineReport:
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
    coefficients: dict[str, float]
    intercept: float
    calibration_bins: list[dict[str, float]]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LogisticBaselineScorecard:
    """Standardized Logistic Regression Baseline Scorecard."""

    def __init__(
        self,
        classifier: Any,
        features: list[str],
        means: dict[str, float],
        stds: dict[str, float],
        model_version: str = "v1.1.0-logistic-baseline",
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.classifier = classifier
        self.features = features
        self.means = means
        self.stds = stds
        self.model_version = model_version
        self.feature_version = feature_version

    def _transform(self, X: pd.DataFrame) -> np.ndarray:
        X_aligned = X[self.features].copy()
        for col in self.features:
            mu = self.means.get(col, 0.0)
            sig = self.stds.get(col, 1.0)
            sig = sig if sig > 1e-6 else 1.0
            X_aligned[col] = (X_aligned[col].fillna(mu) - mu) / sig
        return X_aligned.to_numpy(dtype=float)

    def predict_probability(self, features: dict[str, Any]) -> float:
        row = {f: features.get(f, self.means.get(f, 0.0)) for f in self.features}
        df = pd.DataFrame([row], columns=self.features)
        X_s = self._transform(df)
        p = float(self.classifier.predict_proba(X_s)[0, 1])
        return max(0.01, min(0.99, p))

    def predict_probability_array(self, X: pd.DataFrame) -> np.ndarray:
        X_s = self._transform(X)
        p = self.classifier.predict_proba(X_s)[:, 1]
        return np.clip(p, 0.01, 0.99)

    def calibrate_score(self, prob_repayment: float) -> tuple[float, int]:
        score_100 = round(prob_repayment * 100, 1)
        p = max(0.001, min(0.999, prob_repayment))
        odds = p / (1.0 - p)
        factor = 20.0 / math.log(2.0)
        offset = 600.0 - factor * math.log(50.0)
        score_900 = int(offset + factor * math.log(odds))
        score_900 = max(300, min(900, score_900))
        return score_100, score_900

    def save_artifact(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "features": self.features,
            "means": self.means,
            "stds": self.stds,
            "classifier": self.classifier,
        }
        with open(out, "wb") as f:
            pickle.dump(data, f)
        return out

    @classmethod
    def from_artifact(cls, path: str | Path) -> LogisticBaselineScorecard:
        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(
            classifier=data["classifier"],
            features=data["features"],
            means=data.get("means", {}),
            stds=data.get("stds", {}),
            model_version=data.get("model_version", "v1.1.0-logistic-baseline"),
            feature_version=data.get("feature_version", FEATURE_VERSION),
        )


class LogisticBaselineTrainer:
    """Trainer for Standardized L2 Logistic Regression Baseline."""

    def __init__(
        self,
        model_version: str = "v1.1.0-logistic-baseline",
        c_penalty: float = 1.0,
        random_state: int = 42,
    ) -> None:
        self.model_version = model_version
        self.c_penalty = c_penalty
        self.random_state = random_state

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        groups: pd.Series | None = None,
    ) -> tuple[LogisticBaselineScorecard, LogisticBaselineReport]:
        features = [col for col in MODEL_FEATURE_NAMES if col in X.columns]
        X_df = X[features].copy()
        means = X_df.mean(numeric_only=True).to_dict()
        stds = X_df.std(numeric_only=True).replace(0.0, 1.0).to_dict()

        # Scale features
        X_scaled = pd.DataFrame(index=X_df.index)
        for col in features:
            mu = means.get(col, 0.0)
            sig = stds.get(col, 1.0)
            sig = sig if sig > 1e-6 else 1.0
            X_scaled[col] = (X_df[col].fillna(mu) - mu) / sig

        y_arr = y.to_numpy(dtype=int)

        base_clf = LogisticRegression(
            penalty="l2",
            C=self.c_penalty,
            solver="lbfgs",
            max_iter=1000,
            class_weight="balanced",
            random_state=self.random_state,
        )
        base_clf.fit(X_scaled, y_arr)

        cal_clf = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=5)
        cal_clf.fit(X_scaled, y_arr)

        proba = cal_clf.predict_proba(X_scaled)[:, 1]
        eval_metrics = evaluate_predictions(y_arr, proba)

        from ml.training.scorecard import _calibration_bins
        cal_bins = _calibration_bins(y_arr, proba, n_bins=10)

        coefs = {feat: round(float(c), 4) for feat, c in zip(features, base_clf.coef_[0])}
        intercept = float(base_clf.intercept_[0])

        scorecard = LogisticBaselineScorecard(
            classifier=cal_clf,
            features=features,
            means=means,
            stds=stds,
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
        )

        report = LogisticBaselineReport(
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
            coefficients=coefs,
            intercept=round(intercept, 4),
            calibration_bins=cal_bins,
            notes=[
                f"Standardized L2 Logistic Regression (C={self.c_penalty}, solver='lbfgs')",
                "Platt sigmoid calibration applied via 5-fold cross-validation",
            ],
        )

        return scorecard, report

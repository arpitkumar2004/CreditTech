"""Champion Model: Basel-Compliant Weight of Evidence (WoE) Credit Scorecard.

Features are binned into monotonic risk-linear categories with missing values isolated.
Log-odds are converted into an exact points scorecard (e.g. 600 points at 50:1 odds, PDO=20),
and empirical probabilities are calibrated via Isotonic Regression.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES
from ml.features.woe import WoETransformer
from ml.training.validation import ValidationMetrics, evaluate_predictions


@dataclass
class WoETrainingReport:
    model_version: str
    feature_version: str
    n_train: int
    n_val: int
    auc: float
    gini: float
    ks: float
    brier: float
    pr_auc: float
    selected_features: list[str]
    iv_summary: list[dict[str, Any]]
    calibration_bins: list[dict[str, float]]
    intercept: float
    weights: dict[str, float]
    points_offset: float
    points_factor: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WoEScorecard:
    """Runtime Basel-style Weight of Evidence Credit Scorecard."""

    DEFAULT_BASE_SCORE = 600.0
    DEFAULT_BASE_ODDS = 50.0  # 50:1 repayment odds
    DEFAULT_PDO = 20.0        # Points to Double the Odds

    def __init__(
        self,
        woe_transformer: WoETransformer,
        intercept: float,
        weights: dict[str, float],
        calibrator_x: list[float] | None = None,
        calibrator_y: list[float] | None = None,
        base_score: float = DEFAULT_BASE_SCORE,
        base_odds: float = DEFAULT_BASE_ODDS,
        pdo: float = DEFAULT_PDO,
        model_version: str = "v1.1.0-woe-scorecard",
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.woe_transformer = woe_transformer
        self.intercept = float(intercept)
        self.weights = {k: float(v) for k, v in weights.items()}
        self.model_version = model_version
        self.feature_version = feature_version

        # Points scaling constants
        self.factor = pdo / math.log(2.0)
        self.offset = base_score - self.factor * math.log(base_odds)

        # Build Points Table per feature bin
        # Total Score = Offset - Factor * (intercept + sum(w_i * woe_i))
        # Distributed: Base points per feature = Offset / m - Factor * (intercept / m + w_i * woe_i)
        self.points_table: dict[str, dict[str, int]] = {}
        m = max(1, len(self.weights))
        for feat, w in self.weights.items():
            if feat not in self.woe_transformer.feature_rules:
                continue
            rule = self.woe_transformer.feature_rules[feat]
            self.points_table[feat] = {}
            for b in rule.bins:
                # Bin points
                bin_pts = round((self.offset / m) - self.factor * ((self.intercept / m) + w * b.woe))
                self.points_table[feat][b.label] = bin_pts

        # Isotonic probability calibrator mapping
        self.calibrator_x = calibrator_x or []
        self.calibrator_y = calibrator_y or []
        self._iso: IsotonicRegression | None = None
        if len(self.calibrator_x) >= 5:
            self._iso = IsotonicRegression(out_of_bounds="clip")
            self._iso.fit(self.calibrator_x, self.calibrator_y)

    def predict_raw_probability(self, features: dict[str, Any]) -> float:
        """Computes raw uncalibrated probability from WoE log-odds."""
        log_odds = self.intercept
        for feat, w in self.weights.items():
            val = features.get(feat)
            woe_val = self.woe_transformer.transform_value(feat, val)
            log_odds += w * woe_val
        try:
            return 1.0 / (1.0 + math.exp(-log_odds))
        except OverflowError:
            return 0.0 if log_odds < 0 else 1.0

    def predict_probability(self, features: dict[str, Any]) -> float:
        """Returns empirical, well-calibrated probability of repayment."""
        raw_p = self.predict_raw_probability(features)
        if self._iso is not None:
            cal_p = float(self._iso.predict([raw_p])[0])
            return max(0.01, min(0.99, cal_p))
        return raw_p

    def predict_probability_array(self, X: pd.DataFrame) -> np.ndarray:
        """Vectorized prediction for a DataFrame of borrowers."""
        woe_df = self.woe_transformer.transform(X)
        log_odds = np.full(len(X), self.intercept, dtype=float)
        for feat, w in self.weights.items():
            if feat in woe_df.columns:
                log_odds += w * woe_df[feat].to_numpy()
        raw_p = 1.0 / (1.0 + np.exp(-log_odds))
        if self._iso is not None:
            cal_p = self._iso.predict(raw_p)
            return np.clip(cal_p, 0.01, 0.99)
        return raw_p

    def compute_points(self, features: dict[str, Any]) -> int:
        """Sums points across all features using the exact points scorecard."""
        total_pts = 0
        for feat in self.weights:
            val = features.get(feat)
            rule = self.woe_transformer.feature_rules.get(feat)
            if not rule:
                continue
            # Find matching bin
            matched_bin_label = "Missing"
            if val is not None and not pd.isna(val):
                for b in rule.bins:
                    if b.label != "Missing" and b.matches(val):
                        matched_bin_label = b.label
                        break
            pts = self.points_table.get(feat, {}).get(matched_bin_label, 0)
            total_pts += pts
        return max(300, min(900, int(total_pts)))

    def calibrate_score(self, prob_repayment: float) -> tuple[float, int]:
        """Maps probability to (score_100, score_900) adhering to CreditTech standard."""
        score_100 = round(prob_repayment * 100, 1)
        p = max(0.001, min(0.999, prob_repayment))
        odds = p / (1.0 - p)
        score_900 = int(self.offset + self.factor * math.log(odds))
        score_900 = max(300, min(900, score_900))
        return score_100, score_900

    def compute_shap_values(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        """Computes exact closed-form Shapley values in WoE space."""
        contributions = []
        for feat, w in self.weights.items():
            val = features.get(feat)
            woe_val = self.woe_transformer.transform_value(feat, val)
            # Reference mean WoE in a balanced population is 0.0
            shap_val = float(w * woe_val)
            try:
                numeric_val = float(val) if val is not None and not pd.isna(val) else 0.0
            except (TypeError, ValueError):
                grade_map = {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.1}
                numeric_val = grade_map.get(str(val).strip().upper(), 0.0)
            contributions.append({
                "feature": feat,
                "value": numeric_val,
                "shap_value": shap_val,
            })
        contributions.sort(key=lambda x: (-abs(x["shap_value"]), x["feature"]))
        return contributions

    # ---------- Persistence ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "intercept": self.intercept,
            "weights": self.weights,
            "points_table": self.points_table,
            "offset": self.offset,
            "factor": self.factor,
            "calibrator_x": self.calibrator_x,
            "calibrator_y": self.calibrator_y,
            "woe_transformer": self.woe_transformer.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WoEScorecard:
        woe = WoETransformer.from_dict(data["woe_transformer"])
        scorecard = cls(
            woe_transformer=woe,
            intercept=data["intercept"],
            weights=data["weights"],
            calibrator_x=data.get("calibrator_x"),
            calibrator_y=data.get("calibrator_y"),
            model_version=data.get("model_version", "v1.1.0-woe-scorecard"),
            feature_version=data.get("feature_version", FEATURE_VERSION),
        )
        return scorecard

    def save_artifact(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        return p

    @classmethod
    def from_artifact(cls, path: str | Path) -> WoEScorecard:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class WoEScorecardTrainer:
    """Trains the Champion WoE Scorecard with L1 regularization and isotonic calibration."""

    def __init__(
        self,
        min_iv: float = 0.02,
        c_penalty: float = 0.2,
        model_version: str = "v1.1.0-woe-scorecard",
        random_state: int = 42,
    ) -> None:
        self.min_iv = min_iv
        self.c_penalty = c_penalty
        self.model_version = model_version
        self.random_state = random_state

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        groups: pd.Series | None = None,
    ) -> tuple[WoEScorecard, WoETrainingReport]:
        n_samples = len(X)
        split_point = int(n_samples * 0.8)

        # 80/20 train/validation split
        X_train, X_val = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_val = y.iloc[:split_point], y.iloc[split_point:]

        # 1. Fit WoE transformer on training split only
        transformer = WoETransformer(max_bins=5, min_samples_per_bin=20)
        transformer.fit(X_train, y_train)

        # 2. Filter features by Information Value (IV)
        selected_features = transformer.filter_features(min_iv=self.min_iv)
        if not selected_features:
            selected_features = list(X.columns)

        # 3. Transform train and validation to WoE
        X_train_woe = transformer.transform(X_train)[selected_features]
        X_val_woe = transformer.transform(X_val)[selected_features]

        # 4. Fit L1-regularized Logistic Regression
        lr = LogisticRegression(
            penalty="l1",
            solver="saga",
            C=self.c_penalty,
            class_weight="balanced",
            random_state=self.random_state,
            max_iter=1000,
        )
        lr.fit(X_train_woe, y_train)

        intercept = float(lr.intercept_[0])
        weights = {feat: float(w) for feat, w in zip(selected_features, lr.coef_[0])}

        # 5. Out-of-fold / validation calibration
        raw_val_p = lr.predict_proba(X_val_woe)[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(raw_val_p, y_val)

        # Calibrated validation predictions
        cal_val_p = np.clip(iso.predict(raw_val_p), 0.01, 0.99)
        metrics = evaluate_predictions(y_val, cal_val_p)

        # 6. Assemble Scorecard object
        scorecard = WoEScorecard(
            woe_transformer=transformer,
            intercept=intercept,
            weights=weights,
            calibrator_x=raw_val_p.tolist(),
            calibrator_y=y_val.tolist(),
            model_version=self.model_version,
        )

        iv_df = transformer.get_iv_summary()
        report = WoETrainingReport(
            model_version=self.model_version,
            feature_version=FEATURE_VERSION,
            n_train=len(X_train),
            n_val=len(X_val),
            auc=metrics.auc,
            gini=metrics.gini,
            ks=metrics.ks,
            brier=metrics.brier,
            pr_auc=metrics.pr_auc,
            selected_features=selected_features,
            iv_summary=iv_df.to_dict(orient="records"),
            calibration_bins=metrics.calibration_bins,
            intercept=intercept,
            weights=weights,
            points_offset=scorecard.offset,
            points_factor=scorecard.factor,
            notes=[
                f"L1 WoE Scorecard fitted on {len(X_train)} samples",
                f"Features selected by IV >= {self.min_iv}: {len(selected_features)}/{len(X.columns)}",
                "Isotonic probability calibration applied",
            ],
        )

        return scorecard, report

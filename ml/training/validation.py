"""Spatial GroupKFold Validation & Comprehensive Credit Risk Metrics Engine.

Guarantees zero-leakage cross-validation across village clusters and computes
Basel-grade discrimination, calibration, and class-imbalance metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, precision_recall_curve, roc_auc_score, auc as compute_auc
from sklearn.model_selection import GroupKFold


@dataclass
class ValidationMetrics:
    auc: float
    gini: float
    ks: float
    brier: float
    pr_auc: float
    n_samples: int
    default_rate: float
    calibration_bins: list[dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_ks_statistic(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Computes Kolmogorov-Smirnov (KS) statistic: max separation between goods and bads CDFs."""
    # Ensure binary 0/1
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    # Sort descending by probability of good (repayment)
    desc_order = np.argsort(-y_prob)
    y_sorted = y_true[desc_order]

    n_goods = np.sum(y_sorted == 1)
    n_bads = np.sum(y_sorted == 0)

    if n_goods == 0 or n_bads == 0:
        return 0.0

    cum_goods = np.cumsum(y_sorted == 1) / n_goods
    cum_bads = np.cumsum(y_sorted == 0) / n_bads

    ks = np.max(np.abs(cum_goods - cum_bads))
    return float(ks)


def compute_calibration_deciles(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> list[dict[str, float]]:
    """Computes empirical reliability table across probability bins."""
    bins_list = []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    for i in range(n_bins):
        lo = float(edges[i])
        hi = float(edges[i + 1])
        in_bin = (y_prob >= lo) & (y_prob < hi if i < n_bins - 1 else y_prob <= hi)
        count = int(np.sum(in_bin))
        if count > 0:
            mean_pred = float(np.mean(y_prob[in_bin]))
            obs_rate = float(np.mean(y_true[in_bin]))
        else:
            mean_pred = float((lo + hi) / 2.0)
            obs_rate = 0.0
        bins_list.append({
            "bin_lo": lo,
            "bin_hi": hi,
            "count": count,
            "mean_predicted": round(mean_pred, 4),
            "observed_rate": round(obs_rate, 4),
        })
    return bins_list


def evaluate_predictions(y_true: pd.Series | np.ndarray, y_prob: np.ndarray) -> ValidationMetrics:
    """Computes full suite of credit evaluation metrics."""
    y_arr = np.asarray(y_true, dtype=int)
    p_arr = np.asarray(y_prob, dtype=float)

    # ROC-AUC & Gini
    try:
        roc_auc = float(roc_auc_score(y_arr, p_arr))
    except Exception:
        roc_auc = 0.5
    gini = float(2.0 * roc_auc - 1.0)

    # KS
    ks = compute_ks_statistic(y_arr, p_arr)

    # Brier
    brier = float(brier_score_loss(y_arr, p_arr))

    # PR-AUC
    try:
        precision, recall, _ = precision_recall_curve(y_arr, p_arr)
        pr_auc = float(compute_auc(recall, precision))
    except Exception:
        pr_auc = float(np.mean(y_arr))

    calib_bins = compute_calibration_deciles(y_arr, p_arr, n_bins=10)
    default_rate = float(np.mean(y_arr == 0))

    return ValidationMetrics(
        auc=round(roc_auc, 5),
        gini=round(gini, 5),
        ks=round(ks, 5),
        brier=round(brier, 5),
        pr_auc=round(pr_auc, 5),
        n_samples=len(y_arr),
        default_rate=round(default_rate, 4),
        calibration_bins=calib_bins,
    )


class SpatialGroupValidator:
    """Runs 5-fold Spatial GroupKFold cross-validation on village clusters."""

    def __init__(self, n_splits: int = 5) -> None:
        self.n_splits = n_splits

    def validate(
        self,
        estimator_factory,
        X: pd.DataFrame,
        y: pd.Series,
        groups: pd.Series | np.ndarray,
    ) -> tuple[ValidationMetrics, np.ndarray]:
        """Runs GroupKFold cross-validation, returning out-of-fold metrics and predictions."""
        gkf = GroupKFold(n_splits=self.n_splits)
        oof_preds = np.zeros(len(X), dtype=float)

        for train_idx, val_idx in gkf.split(X, y, groups=groups):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            trainer = estimator_factory()
            fit_res = trainer.fit(X_train, y_train)
            fitted_predictor = fit_res[0] if isinstance(fit_res, tuple) else trainer

            # Predict probability of repayment (class 1)
            preds = fitted_predictor.predict_probability_array(X_val)
            oof_preds[val_idx] = preds

        metrics = evaluate_predictions(y, oof_preds)
        return metrics, oof_preds

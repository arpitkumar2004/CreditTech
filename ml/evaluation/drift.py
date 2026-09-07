"""Population Stability Index (PSI) and Characteristic Stability Index (CSI) Monitoring.

Tracks distribution shifts between baseline training data and live operational data
to detect agricultural seasonality, monsoonal variations, or economic shocks.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class PSIBin:
    bin_index: int
    bin_lower: float
    bin_upper: float
    expected_count: int
    actual_count: int
    expected_pct: float
    actual_pct: float
    psi_contribution: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PSIResult:
    psi: float
    status: str  # "STABLE" | "MODERATE_DRIFT" | "SEVERE_DRIFT"
    alert_level: str  # "GREEN" | "AMBER" | "RED"
    action_required: str
    num_expected: int
    num_actual: int
    bins: list[PSIBin]

    def to_dict(self) -> dict[str, Any]:
        return {
            "psi": self.psi,
            "status": self.status,
            "alert_level": self.alert_level,
            "action_required": self.action_required,
            "num_expected": self.num_expected,
            "num_actual": self.num_actual,
            "bins": [b.to_dict() for b in self.bins],
        }


def get_drift_status(psi: float) -> tuple[str, str, str]:
    """Classifies PSI value into Basel-standard stability tiers."""
    if psi < 0.10:
        return (
            "STABLE",
            "GREEN",
            "No action required. Distribution matches training baseline.",
        )
    elif psi < 0.25:
        return (
            "MODERATE_DRIFT",
            "AMBER",
            "Moderate shift detected. Notify risk officer and inspect seasonal weather anomalies.",
        )
    else:
        return (
            "SEVERE_DRIFT",
            "RED",
            "Severe distribution shift. Freeze automated straight-through approvals and require underwriter review.",
        )


def calculate_psi(
    expected: np.ndarray | list[float] | pd.Series,
    actual: np.ndarray | list[float] | pd.Series,
    num_bins: int = 10,
    min_prob: float = 1e-4,
) -> PSIResult:
    """Calculates Population Stability Index (PSI) between expected and actual distributions."""
    exp_arr = np.asarray(expected, dtype=float)
    act_arr = np.asarray(actual, dtype=float)

    exp_arr = exp_arr[~np.isnan(exp_arr)]
    act_arr = act_arr[~np.isnan(act_arr)]

    if len(exp_arr) == 0 or len(act_arr) == 0:
        return PSIResult(
            psi=0.0,
            status="STABLE",
            alert_level="GREEN",
            action_required="Insufficient samples for PSI evaluation.",
            num_expected=len(exp_arr),
            num_actual=len(act_arr),
            bins=[],
        )

    # Determine bin edges from expected quantiles
    quantiles = np.linspace(0, 1, num_bins + 1)
    raw_edges = np.percentile(exp_arr, quantiles * 100)
    unique_edges = np.unique(raw_edges)

    if len(unique_edges) < 3:
        edges = [-np.inf, float(np.median(exp_arr)), np.inf]
    else:
        unique_edges[0] = -np.inf
        unique_edges[-1] = np.inf
        edges = unique_edges.tolist()

    n_bins = len(edges) - 1
    bins: list[PSIBin] = []
    total_psi = 0.0

    n_exp = len(exp_arr)
    n_act = len(act_arr)

    for i in range(n_bins):
        lo = edges[i]
        hi = edges[i + 1]

        exp_count = int(np.sum((exp_arr >= lo) & (exp_arr < hi if hi != np.inf else exp_arr <= hi)))
        act_count = int(np.sum((act_arr >= lo) & (act_arr < hi if hi != np.inf else act_arr <= hi)))

        exp_pct = max(min_prob, exp_count / n_exp)
        act_pct = max(min_prob, act_count / n_act)

        bin_psi = (act_pct - exp_pct) * math.log(act_pct / exp_pct)
        total_psi += bin_psi

        bins.append(
            PSIBin(
                bin_index=i,
                bin_lower=float(lo) if lo != -np.inf else float(np.min(exp_arr)),
                bin_upper=float(hi) if hi != np.inf else float(np.max(exp_arr)),
                expected_count=exp_count,
                actual_count=act_count,
                expected_pct=round(exp_pct, 5),
                actual_pct=round(act_pct, 5),
                psi_contribution=round(bin_psi, 5),
            )
        )

    status, alert_level, action = get_drift_status(total_psi)

    return PSIResult(
        psi=round(total_psi, 5),
        status=status,
        alert_level=alert_level,
        action_required=action,
        num_expected=n_exp,
        num_actual=n_act,
        bins=bins,
    )


def calculate_csi(
    expected_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    features: list[str] | None = None,
    num_bins: int = 10,
) -> dict[str, Any]:
    """Calculates Characteristic Stability Index (CSI) across multiple continuous/numeric features."""
    target_cols = features or [c for c in expected_df.columns if c in actual_df.columns]
    feature_results = {}
    max_psi = 0.0
    highest_drift_feature = None

    for feat in target_cols:
        if feat not in expected_df.columns or feat not in actual_df.columns:
            continue
        try:
            exp_series = pd.to_numeric(expected_df[feat], errors="coerce").dropna()
            act_series = pd.to_numeric(actual_df[feat], errors="coerce").dropna()
            if len(exp_series) < 10 or len(act_series) < 10:
                continue

            res = calculate_psi(exp_series.to_numpy(), act_series.to_numpy(), num_bins=num_bins)
            feature_results[feat] = res.to_dict()

            if res.psi > max_psi:
                max_psi = res.psi
                highest_drift_feature = feat
        except Exception:
            continue

    overall_status, overall_alert, overall_action = get_drift_status(max_psi)

    return {
        "overall_csi": round(max_psi, 5),
        "overall_status": overall_status,
        "overall_alert": overall_alert,
        "action_required": overall_action,
        "highest_drift_feature": highest_drift_feature,
        "features": feature_results,
    }

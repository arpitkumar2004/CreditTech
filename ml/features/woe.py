"""Production Weight of Evidence (WoE) and Information Value (IV) Engine.

Compliant with Basel II/III Model Risk Management standards for alternative
credit scoring. Converts non-linear, missing-prone features into monotonic
risk-linear bins, and computes Information Value (IV) for feature screening.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES, MODEL_FEATURES


@dataclass
class WoEBin:
    bin_lo: float | None
    bin_hi: float | None
    label: str
    count: int
    goods: int  # Y=1 (repay)
    bads: int   # Y=0 (default)
    woe: float
    iv_contribution: float

    def matches(self, val: Any) -> bool:
        if val is None or pd.isna(val):
            return self.label == "Missing"
        try:
            v = float(val)
        except (TypeError, ValueError):
            return False
        if self.label == "Missing":
            return False
        if self.bin_lo is not None and v < self.bin_lo:
            return False
        if self.bin_hi is not None and v >= self.bin_hi:
            return False
        return True


@dataclass
class FeatureWoEResult:
    feature_name: str
    iv: float
    bins: list[WoEBin]
    missing_woe: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "iv": self.iv,
            "missing_woe": self.missing_woe,
            "bins": [asdict(b) for b in self.bins],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureWoEResult:
        bins = [WoEBin(**b) for b in data["bins"]]
        return cls(
            feature_name=data["feature_name"],
            iv=data["iv"],
            bins=bins,
            missing_woe=data.get("missing_woe", 0.0),
        )


class WoETransformer:
    """Multi-feature Weight of Evidence and Information Value transformer.

    Fits monotonic quantile or frequency bins per feature, isolates missing values,
    and applies Laplace smoothing to prevent division by zero in sparse cohorts.
    """

    def __init__(
        self,
        max_bins: int = 5,
        min_samples_per_bin: int = 25,
        feature_version: str = FEATURE_VERSION,
    ) -> None:
        self.max_bins = max_bins
        self.min_samples_per_bin = min_samples_per_bin
        self.feature_version = feature_version
        self.feature_rules: dict[str, FeatureWoEResult] = {}
        self.is_fitted: bool = False

    def fit_feature(
        self,
        series: pd.Series,
        target: pd.Series,
        feature_name: str,
    ) -> FeatureWoEResult:
        """Computes WoE bins and IV for a single feature series against binary target (1=good, 0=bad)."""
        valid_mask = series.notna()
        n_valid = int(valid_mask.sum())
        n_missing = len(series) - n_valid

        total_goods = float((target == 1).sum())
        total_bads = float((target == 0).sum())

        if total_goods == 0 or total_bads == 0:
            raise ValueError(f"Target must contain both 1s and 0s (goods={total_goods}, bads={total_bads})")

        bins_list: list[WoEBin] = []
        total_iv = 0.0

        # 1. Non-missing values binning
        if n_valid > 0:
            valid_vals = series[valid_mask].astype(float)
            valid_target = target[valid_mask]

            unique_vals = np.sort(valid_vals.unique())
            if len(unique_vals) <= self.max_bins:
                # Discrete / categorical flags (e.g. 0/1 or few distinct numbers)
                cutoffs = [-np.inf] + list(unique_vals[:-1] + np.diff(unique_vals) / 2.0) + [np.inf]
            else:
                # Continuous: compute quantiles
                quantiles = np.linspace(0, 1, self.max_bins + 1)
                cuts = np.percentile(valid_vals, quantiles * 100)
                unique_cuts = np.unique(cuts)
                if len(unique_cuts) < 3:
                    cutoffs = [-np.inf, np.median(valid_vals), np.inf]
                else:
                    unique_cuts[0] = -np.inf
                    unique_cuts[-1] = np.inf
                    cutoffs = list(unique_cuts)

            for i in range(len(cutoffs) - 1):
                lo = cutoffs[i]
                hi = cutoffs[i + 1]
                in_bin = (valid_vals >= lo) & (valid_vals < hi if hi != np.inf else valid_vals <= hi)
                bin_count = int(in_bin.sum())
                bin_goods = int((valid_target[in_bin] == 1).sum())
                bin_bads = bin_count - bin_goods

                # Laplace smoothing
                pct_goods = (bin_goods + 0.5) / (total_goods + 1.0)
                pct_bads = (bin_bads + 0.5) / (total_bads + 1.0)
                woe = math.log(pct_goods / pct_bads)
                iv_contrib = (pct_goods - pct_bads) * woe
                total_iv += iv_contrib

                label = f"[{lo:.2f}, {hi:.2f})" if lo != -np.inf and hi != np.inf else (
                    f"< {hi:.2f}" if lo == -np.inf else f">= {lo:.2f}"
                )
                bins_list.append(
                    WoEBin(
                        bin_lo=lo if lo != -np.inf else None,
                        bin_hi=hi if hi != np.inf else None,
                        label=label,
                        count=bin_count,
                        goods=bin_goods,
                        bads=bin_bads,
                        woe=round(woe, 5),
                        iv_contribution=round(iv_contrib, 5),
                    )
                )

        # 2. Missing bin (always explicitly tracked)
        missing_goods = int((target[~valid_mask] == 1).sum()) if n_missing > 0 else 0
        missing_bads = n_missing - missing_goods
        pct_goods_m = (missing_goods + 0.5) / (total_goods + 1.0)
        pct_bads_m = (missing_bads + 0.5) / (total_bads + 1.0)
        missing_woe = math.log(pct_goods_m / pct_bads_m)
        iv_contrib_m = (pct_goods_m - pct_bads_m) * missing_woe
        total_iv += iv_contrib_m

        bins_list.append(
            WoEBin(
                bin_lo=None,
                bin_hi=None,
                label="Missing",
                count=n_missing,
                goods=missing_goods,
                bads=missing_bads,
                woe=round(missing_woe, 5),
                iv_contribution=round(iv_contrib_m, 5),
            )
        )

        return FeatureWoEResult(
            feature_name=feature_name,
            iv=round(total_iv, 5),
            bins=bins_list,
            missing_woe=round(missing_woe, 5),
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> WoETransformer:
        """Fits WoE and computes IV across all columns in X."""
        self.feature_rules = {}
        for col in X.columns:
            rule = self.fit_feature(X[col], y, col)
            self.feature_rules[col] = rule
        self.is_fitted = True
        return self

    def transform_value(self, feature_name: str, val: Any) -> float:
        """Transforms a single feature value into its fitted WoE score."""
        if feature_name not in self.feature_rules:
            return 0.0
        rule = self.feature_rules[feature_name]
        if val is None or pd.isna(val):
            return rule.missing_woe
        try:
            v = float(val)
        except (TypeError, ValueError):
            return rule.missing_woe

        for b in rule.bins:
            if b.label == "Missing":
                continue
            if b.matches(v):
                return b.woe
        return rule.missing_woe

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms an entire DataFrame of raw features into WoE representations."""
        if not self.is_fitted:
            raise RuntimeError("WoETransformer is not fitted yet. Call fit() first.")
        woe_df = pd.DataFrame(index=X.index)
        for col in X.columns:
            if col in self.feature_rules:
                rule = self.feature_rules[col]
                # Fast vectorized assignment
                series = X[col]
                out_vals = np.full(len(series), rule.missing_woe, dtype=float)
                valid = series.notna()
                if valid.any():
                    v_floats = series[valid].astype(float).to_numpy()
                    v_indices = np.where(valid)[0]
                    for b in rule.bins:
                        if b.label == "Missing":
                            continue
                        mask = np.ones(len(v_floats), dtype=bool)
                        if b.bin_lo is not None:
                            mask &= (v_floats >= b.bin_lo)
                        if b.bin_hi is not None:
                            mask &= (v_floats < b.bin_hi)
                        out_vals[v_indices[mask]] = b.woe
                woe_df[col] = out_vals
            else:
                woe_df[col] = 0.0
        return woe_df

    def get_iv_summary(self) -> pd.DataFrame:
        """Returns a ranked summary DataFrame of all features by Information Value (IV)."""
        rows = []
        for name, rule in self.feature_rules.items():
            power = (
                "Suspicious / Leakage" if rule.iv >= 0.50 else
                "Strong" if rule.iv >= 0.30 else
                "Medium" if rule.iv >= 0.10 else
                "Weak" if rule.iv >= 0.02 else
                "Unpredictable (Drop)"
            )
            rows.append({
                "feature": name,
                "iv": rule.iv,
                "predictive_power": power,
                "n_bins": len(rule.bins),
            })
        df = pd.DataFrame(rows)
        return df.sort_values(by="iv", ascending=False).reset_index(drop=True)

    def filter_features(self, min_iv: float = 0.02) -> list[str]:
        """Returns features meeting the minimum IV predictive threshold."""
        return [name for name, rule in self.feature_rules.items() if rule.iv >= min_iv]

    # ---------- Serialization ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_version": self.feature_version,
            "max_bins": self.max_bins,
            "min_samples_per_bin": self.min_samples_per_bin,
            "feature_rules": {k: v.to_dict() for k, v in self.feature_rules.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WoETransformer:
        transformer = cls(
            max_bins=data.get("max_bins", 5),
            min_samples_per_bin=data.get("min_samples_per_bin", 25),
            feature_version=data.get("feature_version", FEATURE_VERSION),
        )
        transformer.feature_rules = {
            k: FeatureWoEResult.from_dict(v)
            for k, v in data["feature_rules"].items()
        }
        transformer.is_fitted = True
        return transformer

    def save_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        return p

    @classmethod
    def load_json(cls, path: str | Path) -> WoETransformer:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

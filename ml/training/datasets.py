"""Training data loaders — P3.2.

Two datasets are supported for the pilot v1 baseline:

  1. SyntheticSHGGenerator — deterministic, rural-context proxy data aligned to
     the 5-Cs schema in ml/features/schema.py. Used because no real CreditTech
     repayment ground truth exists yet (planning doc §8.1).

  2. HomeCreditLoader — adapter for the Kaggle "Home Credit Default Risk"
     dataset. If the CSV is not present locally, load() returns a DatasetInfo
     with available=False so the training pipeline can continue with synthetic
     data only. We NEVER fabricate rows for it.

Every returned dataset carries a DatasetInfo record (source, type, samples,
schema hash, transformations) — this is what the model registry persists as
training-data provenance (P3.6).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES


@dataclass
class DatasetInfo:
    source: str
    kind: Literal["real", "proxy", "synthetic"]
    samples: int
    features: list[str]
    feature_version: str
    schema_hash: str
    transformations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    available: bool = True


def _hash_schema(feature_names: list[str]) -> str:
    payload = json.dumps(sorted(feature_names), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


# ────────────────────────────────────────────────────────────────
# Synthetic SHG / farmer generator
# ────────────────────────────────────────────────────────────────
class SyntheticSHGGenerator:
    """Deterministic synthetic borrower dataset generator.

    Follows the schema outlined in alternative_credit_scoring_research.md §6.
    Labels are drawn from a Bernoulli over a hand-authored ground-truth logit
    that reflects domain intuition (higher SHG repayment / attendance / assets
    -> higher repay probability). This is a PROXY generator — its results
    validate pipeline machinery, not real-world predictive validity.

    The generator also emits `gender` and `landholding_band` fields that are
    excluded from model input by ml.features.pipeline but preserved separately
    for fairness evaluation (P3.4).
    """

    # Ground-truth logit for label generation (not the model's weights).
    # Sign/magnitude tuned so P(repay) roughly separates the classes.
    # Tuned so that P(repay) is ~0.5–0.75 at population mean (avoids class collapse)
    GT_INTERCEPT = -8.5
    GT_WEIGHTS = {
        "shg_repayment_rate": 3.5,
        "shg_meeting_attendance_pct": 0.02,
        "shg_savings_consistency": -1.5,        # lower std better -> negative
        "shg_membership_years": 0.08,
        "shg_grade": 1.2,
        "utility_payment_ontime_pct": 0.015,
        "upi_transaction_regularity": -1.0,
        "estimated_crop_income_kharif": 8e-6,
        "estimated_crop_income_rabi": 8e-6,
        "income_stability_cv": -1.8,
        "monthly_avg_credit_inflow": 2e-5,
        "pm_kisan_regularity": 0.6,
        "shg_cumulative_savings": 3e-5,
        "bank_balance_avg_6m": 4e-5,
        "asset_score": 1.4,
        "land_holding_acres": 0.15,
        "irrigation_access": 0.7,
        "land_quality_ndvi_avg": 1.2,
        "ndvi_trend_2season": 0.8,
        "rainfall_deviation_pct": -0.008,
        "crop_insurance_enrolled": 0.35,
    }

    def __init__(self, n: int = 2000, seed: int = 42) -> None:
        self.n = n
        self.seed = seed

    def generate(self) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, DatasetInfo]:
        """Return (X, y, sensitive_attrs, info).

        X columns == MODEL_FEATURE_NAMES (numeric-coerced).
        y is 1=repay, 0=default.
        sensitive_attrs contains gender and landholding_band (not model inputs).
        """
        rng = np.random.default_rng(self.seed)
        n = self.n

        # Draw raw features
        shg_grade_cat = rng.choice(["A", "B", "C", "D"], size=n, p=[0.25, 0.4, 0.25, 0.1])
        grade_map = {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.1}
        shg_grade = np.array([grade_map[g] for g in shg_grade_cat])

        raw = {
            "shg_repayment_rate": np.clip(rng.beta(6, 2, n), 0.05, 1.0),
            "shg_meeting_attendance_pct": np.clip(rng.normal(75, 15, n), 0, 100),
            "shg_savings_consistency": np.clip(rng.gamma(1.5, 0.3, n), 0.01, 2.0),
            "shg_membership_years": rng.integers(0, 12, n).astype(float),
            "shg_grade": shg_grade,
            "utility_payment_ontime_pct": np.clip(rng.normal(85, 12, n), 0, 100),
            "upi_transaction_regularity": np.clip(rng.gamma(2, 0.2, n), 0.05, 2.0),
            "estimated_crop_income_kharif": np.clip(rng.normal(35000, 15000, n), 0, None),
            "estimated_crop_income_rabi": np.clip(rng.normal(40000, 18000, n), 0, None),
            "income_stability_cv": np.clip(rng.gamma(2, 0.25, n), 0.05, 3.0),
            "monthly_avg_credit_inflow": np.clip(rng.normal(6000, 3500, n), 0, None),
            "pm_kisan_regularity": np.clip(rng.beta(5, 2, n), 0, 1),
            "shg_cumulative_savings": np.clip(rng.normal(4500, 3000, n), 0, None),
            "bank_balance_avg_6m": np.clip(rng.normal(5500, 3500, n), 0, None),
            "asset_score": np.clip(rng.beta(2, 3, n), 0, 1),
            "land_holding_acres": np.clip(rng.gamma(2, 1.2, n), 0, 20),
            "irrigation_access": rng.binomial(1, 0.55, n).astype(float),
            "land_quality_ndvi_avg": np.clip(rng.normal(0.55, 0.15, n), 0, 1),
            "ndvi_trend_2season": np.clip(rng.normal(0.02, 0.15, n), -1, 1),
            "rainfall_deviation_pct": rng.normal(0, 20, n),
            "crop_insurance_enrolled": rng.binomial(1, 0.35, n).astype(float),
        }
        X = pd.DataFrame(raw, columns=list(MODEL_FEATURE_NAMES))

        # Ground-truth logit -> P(repay) -> Bernoulli label
        logit = np.full(n, self.GT_INTERCEPT, dtype=float)
        for feat, w in self.GT_WEIGHTS.items():
            logit += w * X[feat].to_numpy()
        # Add label noise so it's not perfectly separable
        logit += rng.normal(0, 0.5, n)
        p_repay = 1.0 / (1.0 + np.exp(-logit))
        y = pd.Series(rng.binomial(1, p_repay, n), name="repay")

        # Sensitive / fairness-monitoring attributes — NOT features
        sensitive = pd.DataFrame({
            "gender": rng.choice(["F", "M", "OTHER"], size=n, p=[0.55, 0.44, 0.01]),
            "landholding_band": rng.choice(
                ["LANDLESS", "MARGINAL", "SMALL", "SEMI_MEDIUM", "MEDIUM", "LARGE"],
                size=n, p=[0.05, 0.35, 0.30, 0.15, 0.10, 0.05],
            ),
        })

        info = DatasetInfo(
            source="synthetic_shg_generator",
            kind="synthetic",
            samples=n,
            features=list(MODEL_FEATURE_NAMES),
            feature_version=FEATURE_VERSION,
            schema_hash=_hash_schema(list(MODEL_FEATURE_NAMES)),
            transformations=[
                f"seed={self.seed}",
                "clipping to plausible domain ranges",
                "shg_grade -> numeric via schema.category_map",
                "label = Bernoulli(sigmoid(GT_logit + N(0,0.5)))",
            ],
            limitations=[
                "labels are simulated from hand-authored ground truth, not real repayment",
                "no cohort dynamics, no calendar effects, no cross-borrower correlation",
                "AUC/Gini on this data cannot be interpreted as production predictive validity",
            ],
        )
        return X, y, sensitive, info


# ────────────────────────────────────────────────────────────────
# Home Credit Default Risk loader (Kaggle) — real proxy source
# ────────────────────────────────────────────────────────────────
class HomeCreditLoader:
    """Adapter for the Kaggle Home Credit Default Risk 'application_train.csv'.

    We deliberately do NOT ship the file or a stand-in for it. When the file is
    absent, load() returns an empty DataFrame with available=False; callers must
    handle that gracefully. When present, we perform a minimal, documented
    alignment: rename TARGET (1=default) -> repay (1=repay) and map a few
    numeric Home Credit fields into schema features that they roughly correspond
    to. This is a documented DEVELOPMENT alignment, not a claim of semantic
    equivalence.
    """

    # Deliberately conservative mapping — only fields whose meaning approximately
    # survives the transformation. Fields not mappable stay missing.
    MAPPING = {
        "AMT_INCOME_TOTAL": ("monthly_avg_credit_inflow", lambda s: s / 12.0),
        "AMT_CREDIT": ("shg_cumulative_savings", lambda s: s * 0.01),  # weak proxy
        "DAYS_EMPLOYED": ("shg_membership_years", lambda s: np.clip(-s / 365.25, 0, 30)),
    }

    def __init__(self, csv_path: str | Path | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else Path("data/home_credit/application_train.csv")

    def load(self, max_rows: int | None = 50_000) -> tuple[pd.DataFrame, pd.Series, DatasetInfo]:
        if not self.csv_path.exists():
            info = DatasetInfo(
                source="kaggle_home_credit_default_risk",
                kind="real",
                samples=0,
                features=list(MODEL_FEATURE_NAMES),
                feature_version=FEATURE_VERSION,
                schema_hash=_hash_schema(list(MODEL_FEATURE_NAMES)),
                transformations=[],
                limitations=["dataset file not present at " + str(self.csv_path)],
                available=False,
            )
            return pd.DataFrame(columns=list(MODEL_FEATURE_NAMES)), pd.Series(dtype=int, name="repay"), info

        df = pd.read_csv(self.csv_path, nrows=max_rows)
        # Home Credit TARGET: 1 = client with payment difficulties (default), 0 = other.
        y = 1 - df["TARGET"].astype(int)
        y.name = "repay"

        X = pd.DataFrame(index=df.index, columns=list(MODEL_FEATURE_NAMES), dtype=float)
        transformations: list[str] = []
        for hc_col, (feat, fn) in self.MAPPING.items():
            if hc_col in df.columns:
                X[feat] = fn(df[hc_col]).astype(float)
                transformations.append(f"{hc_col} -> {feat}")

        info = DatasetInfo(
            source="kaggle_home_credit_default_risk",
            kind="real",
            samples=len(df),
            features=list(MODEL_FEATURE_NAMES),
            feature_version=FEATURE_VERSION,
            schema_hash=_hash_schema(list(MODEL_FEATURE_NAMES)),
            transformations=transformations,
            limitations=[
                "population and feature meanings differ substantially from CreditTech rural cohort",
                "only 3 columns are aligned; remaining features stay missing (imputed at training)",
                "use as behavioural-signal development anchor, not as target population",
            ],
            available=True,
        )
        return X, y, info

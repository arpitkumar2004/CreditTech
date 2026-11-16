"""Unit tests for benchmark dataset loaders and adapters.

Verifies:
- HomeCreditLoader loads and maps empirical cashflow proxies
- GMSCLoader loads and maps Give Me Some Credit delinquency metrics
- UnifiedBenchmarkLoader fuses benchmark telemetry with rural domain priors
"""

import pandas as pd
import pytest

from ml.features.schema import MODEL_FEATURE_NAMES
from ml.training.datasets import (
    GMSCLoader,
    HomeCreditLoader,
    UnifiedBenchmarkLoader,
)


def test_home_credit_loader():
    """Verify HomeCreditLoader loads Kaggle Home Credit data with aligned features."""
    loader = HomeCreditLoader()
    X, y, info = loader.load(max_rows=250)

    assert info.available is True
    assert len(X) == 250
    assert len(y) == 250
    assert y.name == "repay"
    assert set(y.unique()).issubset({0, 1})

    # Verify mapped proxy columns exist and have non-null values
    for col in ["monthly_avg_credit_inflow", "shg_cumulative_savings", "shg_membership_years", "utility_payment_ontime_pct", "shg_repayment_rate"]:
        assert col in X.columns
        assert not X[col].isna().all()
        assert (X[col] >= 0).all()


def test_gmsc_loader():
    """Verify GMSCLoader loads Give Me Some Credit data with aligned delinquency features."""
    loader = GMSCLoader()
    X, y, info = loader.load(max_rows=200)

    assert info.available is True
    assert len(X) == 200
    assert len(y) == 200
    assert y.name == "repay"
    assert set(y.unique()).issubset({0, 1})

    for col in ["utility_payment_ontime_pct", "shg_repayment_rate", "income_stability_cv"]:
        assert col in X.columns
        assert not X[col].isna().all()


def test_unified_benchmark_loader():
    """Verify UnifiedBenchmarkLoader fuses real benchmark and rural domain features into 21 model features."""
    loader = UnifiedBenchmarkLoader(seed=99)
    X, y, sensitive, info = loader.load_fused_dataset(n_samples=300)

    assert info.available is True
    assert len(X) == 300
    assert len(y) == 300
    assert len(sensitive) == 300
    assert set(X.columns) == set(MODEL_FEATURE_NAMES)
    assert X.shape[1] == 21

    # Verify zero nulls across all 21 model features
    assert X.isna().sum().sum() == 0

    # Verify sensitive attributes for fairness monitoring
    assert "gender" in sensitive.columns
    assert "landholding_band" in sensitive.columns
    assert "village_id" in sensitive.columns
    assert "agro_climatic_zone" in sensitive.columns

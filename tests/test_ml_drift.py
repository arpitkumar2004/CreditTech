"""Unit tests for Population Stability Index (PSI) and Characteristic Stability Index (CSI)."""

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from ml.evaluation.drift import (
    calculate_csi,
    calculate_psi,
    get_drift_status,
)


def test_psi_identical_distributions():
    # If expected and actual are identical, PSI should be very close to 0.0
    rng = np.random.default_rng(42)
    expected = rng.normal(600, 50, 1000)
    actual = expected.copy()

    result = calculate_psi(expected, actual, num_bins=10)
    assert result.psi < 0.01
    assert result.status == "STABLE"
    assert result.alert_level == "GREEN"
    assert len(result.bins) == 10


def test_psi_moderate_drift():
    # Shift the mean slightly (e.g. seasonal drop in repayment scores)
    rng = np.random.default_rng(42)
    expected = rng.normal(600, 50, 2000)
    actual = rng.normal(576, 50, 2000)

    result = calculate_psi(expected, actual, num_bins=10)
    assert 0.10 <= result.psi <= 0.25
    assert result.status == "MODERATE_DRIFT"


def test_psi_severe_drift():
    # Severe shock (e.g. widespread drought, massive downward shift)
    rng = np.random.default_rng(42)
    expected = rng.normal(650, 40, 1000)
    actual = rng.normal(450, 60, 1000)

    result = calculate_psi(expected, actual, num_bins=10)
    assert result.psi >= 0.25
    assert result.status == "SEVERE_DRIFT"
    assert result.alert_level == "RED"


def test_csi_feature_breakdown():
    rng = np.random.default_rng(42)
    n = 500

    exp_df = pd.DataFrame({
        "shg_repayment_rate": rng.beta(6, 2, n),
        "rainfall_deviation_pct": rng.normal(0, 10, n),
    })

    # Actual df has severe drought in rainfall_deviation_pct
    act_df = pd.DataFrame({
        "shg_repayment_rate": rng.beta(6, 2, n),
        "rainfall_deviation_pct": rng.normal(-35, 10, n),
    })

    csi = calculate_csi(exp_df, act_df, features=["shg_repayment_rate", "rainfall_deviation_pct"])
    assert "rainfall_deviation_pct" in csi["features"]
    assert csi["highest_drift_feature"] == "rainfall_deviation_pct"
    assert csi["features"]["rainfall_deviation_pct"]["psi"] > 0.25


@pytest.mark.asyncio
async def test_drift_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/monitoring/drift")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "model_version" in data

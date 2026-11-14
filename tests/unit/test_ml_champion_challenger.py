"""Unit tests for Champion WoE Scorecard, Challenger GBDT, and Spatial Validation."""

import numpy as np
import pandas as pd
import pytest

from ml.features.schema import MODEL_FEATURE_NAMES
from ml.training.datasets import SyntheticSHGGenerator
from ml.training.gbm_challenger import GBMScorecardTrainer, MonotonicGBMScorecard
from ml.training.validation import SpatialGroupValidator, compute_ks_statistic, evaluate_predictions
from ml.training.woe_scorecard import WoEScorecard, WoEScorecardTrainer


@pytest.fixture
def sample_data():
    gen = SyntheticSHGGenerator(n=600, seed=123, n_villages=6)
    X, y, sensitive, info = gen.generate()
    return X, y, sensitive, info


def test_spatial_group_validator(sample_data):
    X, y, sensitive, _ = sample_data
    validator = SpatialGroupValidator(n_splits=3)

    metrics, oof_preds = validator.validate(
        estimator_factory=lambda: WoEScorecardTrainer(min_iv=0.01, random_state=42),
        X=X,
        y=y,
        groups=sensitive["village_id"],
    )

    assert len(oof_preds) == len(X)
    assert 0.50 <= metrics.auc <= 1.0
    assert metrics.ks > 0.10
    assert metrics.brier < 0.30


def test_champion_woe_scorecard(sample_data, tmp_path):
    X, y, _, _ = sample_data
    trainer = WoEScorecardTrainer(min_iv=0.01, random_state=42)
    scorecard, report = trainer.fit(X, y)

    # 1. Prediction & Calibration
    sample_borrower = X.iloc[0].to_dict()
    prob = scorecard.predict_probability(sample_borrower)
    assert 0.01 <= prob <= 0.99

    score_100, score_900 = scorecard.calibrate_score(prob)
    assert 0.0 <= score_100 <= 100.0
    assert 300 <= score_900 <= 900

    # 2. Points Scorecard
    pts = scorecard.compute_points(sample_borrower)
    assert 300 <= pts <= 900
    assert len(scorecard.points_table) > 5

    # 3. SHAP Explainability
    shap_vals = scorecard.compute_shap_values(sample_borrower)
    assert len(shap_vals) > 0
    assert "shap_value" in shap_vals[0]

    # 4. Persistence roundtrip
    artifact_path = tmp_path / "woe_scorecard.json"
    scorecard.save_artifact(artifact_path)
    loaded = WoEScorecard.from_artifact(artifact_path)
    assert loaded.model_version == scorecard.model_version
    assert loaded.intercept == scorecard.intercept
    assert loaded.predict_probability(sample_borrower) == prob


def test_challenger_monotonic_gbm(sample_data, tmp_path):
    X, y, _, _ = sample_data
    trainer = GBMScorecardTrainer(max_iter=30, random_state=42)
    scorecard, report = trainer.fit(X, y)

    sample_borrower = X.iloc[0].to_dict()
    prob = scorecard.predict_probability(sample_borrower)
    assert 0.01 <= prob <= 0.99

    score_100, score_900 = scorecard.calibrate_score(prob)
    assert 300 <= score_900 <= 900

    # Monotonicity test: higher repayment rate should not decrease probability
    low_repay = sample_borrower.copy()
    high_repay = sample_borrower.copy()
    low_repay["shg_repayment_rate"] = 0.30
    high_repay["shg_repayment_rate"] = 0.98

    p_low = scorecard.predict_raw_probability(low_repay)
    p_high = scorecard.predict_raw_probability(high_repay)
    assert p_high >= p_low - 1e-6

    # SHAP test
    shap_vals = scorecard.compute_shap_values(sample_borrower)
    assert len(shap_vals) == len(MODEL_FEATURE_NAMES)

    # Persistence test
    pkl_path = tmp_path / "gbm_model.pkl"
    scorecard.save_artifact(pkl_path)
    loaded = MonotonicGBMScorecard.from_artifact(pkl_path)
    assert loaded.predict_probability(sample_borrower) == prob

"""Unit tests for the Weight of Evidence (WoE) and Information Value (IV) engine."""

import numpy as np
import pandas as pd
import pytest

from ml.features.woe import WoETransformer


def test_woe_transformer_fit_and_transform(tmp_path):
    rng = np.random.default_rng(42)
    n = 500

    # Feature 1: Strong positive signal
    x1 = rng.normal(0, 1, n)
    # Feature 2: Pure noise
    x2 = rng.uniform(0, 100, n)
    # Target: depends heavily on x1
    p = 1.0 / (1.0 + np.exp(-1.5 * x1))
    y = pd.Series(rng.binomial(1, p, n), name="repay")

    # Introduce some missing values
    x1_missing = x1.copy()
    x1_missing[0:20] = np.nan

    df = pd.DataFrame({"signal_feature": x1_missing, "noise_feature": x2})

    transformer = WoETransformer(max_bins=4)
    transformer.fit(df, y)

    assert transformer.is_fitted
    assert "signal_feature" in transformer.feature_rules
    assert "noise_feature" in transformer.feature_rules

    signal_rule = transformer.feature_rules["signal_feature"]
    noise_rule = transformer.feature_rules["noise_feature"]

    # Signal feature must have higher IV than noise
    assert signal_rule.iv > noise_rule.iv
    assert signal_rule.iv > 0.10  # Medium or strong

    # Missing bin must be present
    labels = [b.label for b in signal_rule.bins]
    assert "Missing" in labels

    # Transform
    woe_df = transformer.transform(df)
    assert woe_df.shape == df.shape
    assert not woe_df.isna().any().any()

    # Serialization roundtrip
    json_file = tmp_path / "woe_test.json"
    transformer.save_json(json_file)

    loaded = WoETransformer.load_json(json_file)
    assert loaded.is_fitted
    assert loaded.feature_rules["signal_feature"].iv == signal_rule.iv

    # Feature filtering
    selected = transformer.filter_features(min_iv=0.05)
    assert "signal_feature" in selected


def test_woe_transformer_laplace_smoothing():
    # Extreme case: a bin with zero goods or zero bads
    df = pd.DataFrame({"feat": [1.0, 1.0, 2.0, 2.0]})
    y = pd.Series([1, 1, 0, 0])

    transformer = WoETransformer(max_bins=2)
    transformer.fit(df, y)

    # Should not raise ZeroDivisionError or Inf because of Laplace smoothing
    rule = transformer.feature_rules["feat"]
    for b in rule.bins:
        assert not np.isinf(b.woe)
        assert not np.isnan(b.woe)

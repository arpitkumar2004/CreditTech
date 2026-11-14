"""Unit tests for the unified model loader and BaseScorecard protocol."""

from pathlib import Path
import pytest
from ml.registry import ModelRegistry
from ml.training.base import BaseScorecard
from ml.training.loader import load_scorecard_model


def test_load_all_registered_models():
    """Verify all models in the registry store load and implement BaseScorecard."""
    registry = ModelRegistry()
    models = registry.list_models()
    assert len(models) >= 5
    for record in models:
        artifact = registry.artifact_path(record.model_version)
        assert artifact is not None and artifact.exists(), f"Artifact missing for {record.model_version}"
        scorecard = load_scorecard_model(artifact, model_type=record.model_type)
        assert isinstance(scorecard, BaseScorecard), f"{record.model_version} does not implement BaseScorecard"
        prob = scorecard.predict_probability({})
        assert 0.0 <= prob <= 1.0
        score_100, score_900 = scorecard.calibrate_score(prob)
        assert 0.0 <= score_100 <= 100.0
        assert 300 <= score_900 <= 900

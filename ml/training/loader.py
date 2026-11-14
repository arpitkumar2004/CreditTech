"""Unified model artifact loader."""

from __future__ import annotations

import json
from pathlib import Path
import pickle
from typing import Any

from ml.training.base import BaseScorecard


def load_scorecard_model(artifact_path: str | Path, model_type: str | None = None) -> BaseScorecard:
    """Load a trained model artifact into a scorecard implementing BaseScorecard.

    Supports:
    - WoEScorecard (JSON with woe_transformer)
    - LogisticScorecard (JSON with intercept and weights)
    - LogisticBaselineScorecard (Pickle dict or instance)
    - MonotonicGBMScorecard (Pickled instance)
    - RandomForestScorecard (Pickle dict)
    - StackingEnsembleScorecard (Pickle dict)
    """
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Scorecard artifact not found: {path}")

    # 1. Check if artifact is a pickle (either by extension, binary content, or fallback)
    is_pickle = False
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
            if magic.startswith(b"\x80"):
                is_pickle = True
    except Exception:
        pass

    if path.suffix == ".pkl" or is_pickle:
        with open(path, "rb") as f:
            loaded = pickle.load(f)

        # If it's already an instantiated BaseScorecard (e.g. MonotonicGBMScorecard)
        if isinstance(loaded, BaseScorecard):
            return loaded

        # If it's a serialized dictionary
        if isinstance(loaded, dict):
            if "meta_classifier" in loaded or model_type == "stacking_scorecard_v1":
                from ml.training.ensemble_scorecard import StackingEnsembleScorecard
                return StackingEnsembleScorecard.from_artifact(path)

            if model_type == "rf_scorecard_v1":
                from ml.training.rf_scorecard import RandomForestScorecard
                return RandomForestScorecard.from_artifact(path)

            from ml.training.logistic_baseline import LogisticBaselineScorecard
            return LogisticBaselineScorecard.from_artifact(path)

        raise TypeError(f"Unrecognized pickled model artifact type: {type(loaded)}")

    # 2. JSON artifact
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Expected dict in JSON artifact {path}, got {type(data)}")

    if "woe_transformer" in data or model_type == "woe_scorecard_v1":
        from ml.training.woe_scorecard import WoEScorecard
        return WoEScorecard.from_dict(data)

    from ml.training.scorecard import LogisticScorecard
    return LogisticScorecard.from_dict(data)

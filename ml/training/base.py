"""Base protocols and types for machine learning scorecards."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseScorecard(Protocol):
    """Protocol defining the standard interface for all operational scorecards."""

    model_version: str
    feature_version: str

    def predict_probability(self, features: dict[str, Any]) -> float:
        """Predict repayment probability in [0.0, 1.0] given a feature dictionary."""
        ...

    def calibrate_score(self, prob_repayment: float) -> tuple[float, int]:
        """Calibrate probability into (score_100 [0-100], score_900 [300-900])."""
        ...

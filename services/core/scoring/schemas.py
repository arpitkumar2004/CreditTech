"""Pydantic schemas for the Scoring API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScoreReasonCodeResponse(BaseModel):
    rank: int
    feature_name: str
    direction: str
    shap_value: float
    localized_text_en: str
    localized_text_hi: str | None


class ScoreRequest(BaseModel):
    """Request schema to generate a credit score for a borrower."""

    model_config = {"protected_namespaces": ()}

    borrower_id: uuid.UUID
    feature_snapshot_id: uuid.UUID | None = None
    model_version: str | None = Field(
        default=None,
        description="Pin a specific model_version. If omitted, the registry's active model is used, "
                    "falling back to the built-in default scorecard when none is registered.",
    )


class ScoreResponse(BaseModel):
    """Response containing the generated score, band, and explanations."""

    id: uuid.UUID
    borrower_id: uuid.UUID
    feature_snapshot_id: uuid.UUID
    model_version: str
    feature_version: str
    score: float = Field(..., description="Standard 0-100 score")
    score_900: int = Field(..., description="Classic 300-900 bureau-equivalent score")
    score_band: str  # EXCELLENT | GOOD | MODERATE | HIGH_RISK | VERY_HIGH_RISK
    confidence_lower: float
    confidence_upper: float
    sources_used: list[str]
    reason_codes: list[ScoreReasonCodeResponse]
    generated_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}

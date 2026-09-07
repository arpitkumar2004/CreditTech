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


class ShadowScoreResult(BaseModel):
    shadow_model_version: str
    shadow_score_100: float
    shadow_score_900: int
    score_delta_100: float
    agreement: str  # "AGREE" | "DISAGREE"
    latency_ms: float


class ActionableRecourseItem(BaseModel):
    feature_name: str
    current_value: float
    target_value: float
    projected_score_impact: float
    guidance_en: str
    guidance_hi: str | None = None


class ActionableRecourseResponse(BaseModel):
    eligible: bool
    current_score: int
    target_score: int
    projected_score: int
    pathways: list[ActionableRecourseItem]


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
    shadow_score: ShadowScoreResult | None = None
    actionable_recourse: ActionableRecourseResponse | None = None

    model_config = {"from_attributes": True, "protected_namespaces": ()}


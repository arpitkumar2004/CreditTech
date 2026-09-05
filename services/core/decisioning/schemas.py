"""Pydantic schemas for the officer decisioning API."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class OfficerDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MORE_INFO_REQUIRED = "MORE_INFO_REQUIRED"


class ModelRecommendation(StrEnum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class SourceStatus(BaseModel):
    source: str
    available: bool


class ReviewReasonCode(BaseModel):
    rank: int
    feature_name: str
    direction: str
    shap_value: float
    localized_text_en: str
    localized_text_hi: str | None = None


class ReviewPayload(BaseModel):
    """Everything a loan officer needs to make a decision."""

    model_config = {"protected_namespaces": ()}

    score_id: uuid.UUID
    borrower_id: uuid.UUID

    borrower_summary: dict

    score: float
    score_900: int
    score_band: str
    confidence_lower: float
    confidence_upper: float
    model_version: str
    feature_version: str
    model_recommendation: ModelRecommendation

    sources_used: list[str]
    source_status: list[SourceStatus]
    partial_data: bool = Field(
        ..., description="True if any of the 4 expected rails is missing"
    )

    reason_codes: list[ReviewReasonCode]
    generated_at: datetime

    existing_decision: OfficerDecisionRecord | None = None


class DecisionRequest(BaseModel):
    """Body for POST /decision — captures the officer's ruling."""

    model_config = {"protected_namespaces": ()}

    score_id: uuid.UUID
    decision: OfficerDecision
    override_reason: str | None = Field(
        default=None,
        description=(
            "Required when the officer's decision does not match the model "
            "recommendation. Rejected as invalid when decision matches "
            "recommendation (to prevent capture of a no-op override reason)."
        ),
        max_length=2000,
    )
    officer_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("override_reason")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class OfficerDecisionRecord(BaseModel):
    """Audit-trail row as returned from the API."""

    model_config = {"from_attributes": True, "protected_namespaces": ()}

    id: uuid.UUID
    score_id: uuid.UUID
    loan_application_id: uuid.UUID | None
    officer_id: str
    decision: OfficerDecision
    model_recommendation: ModelRecommendation
    is_override: bool
    override_reason: str | None
    officer_notes: str | None
    model_score_at_decision: float
    model_version_at_decision: str
    feature_version_at_decision: str
    created_at: datetime


ReviewPayload.model_rebuild()

"""Pydantic schemas for the Partner RE Handoff API."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class REDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MORE_INFO_REQUIRED = "MORE_INFO_REQUIRED"
    REFERRED = "REFERRED"


class HandoffSubmitRequest(BaseModel):
    """Request schema to trigger a loan application handoff to a partner RE."""

    score_id: uuid.UUID
    partner_re_id: str = Field(..., min_length=1, max_length=100)
    requested_amount: float = Field(..., ge=0)
    requested_tenure_months: int = Field(..., ge=1, le=60)
    purpose: str = Field(..., min_length=2, max_length=50)


class HandoffSubmitResponse(BaseModel):
    """Response containing the handoff submission result details."""

    loan_application_id: uuid.UUID
    re_application_id: str
    status: str
    submitted_at: datetime


class REDecisionWebhookPayload(BaseModel):
    """Payload received from the partner RE webhook on lending decisions."""

    re_application_id: str
    credittech_application_id: uuid.UUID
    decision: REDecision
    decided_at: datetime
    decided_by: str
    approved_amount: float | None = None
    override_reason: str | None = None

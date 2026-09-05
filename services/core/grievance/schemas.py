"""Pydantic schemas for the grievance / appeal API."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class GrievanceCategory(StrEnum):
    SCORE_DISPUTE = "SCORE_DISPUTE"
    DECISION_APPEAL = "DECISION_APPEAL"
    DATA_ACCURACY = "DATA_ACCURACY"
    CONSENT_ISSUE = "CONSENT_ISSUE"
    OTHER = "OTHER"


class GrievanceStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


# Transitions allowed from -> to. RESOLVED / CLOSED are terminal.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"IN_REVIEW", "ESCALATED", "RESOLVED"},
    "IN_REVIEW": {"RESOLVED", "ESCALATED"},
    "ESCALATED": {"RESOLVED", "IN_REVIEW"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}


class GrievanceCreate(BaseModel):
    borrower_id: uuid.UUID
    score_id: uuid.UUID | None = None
    loan_application_id: uuid.UUID | None = None
    category: GrievanceCategory
    description: str = Field(..., min_length=5, max_length=4000)
    sla_hours: int = Field(default=168, ge=1, le=720)


class GrievanceUpdate(BaseModel):
    status: GrievanceStatus
    note: str | None = Field(default=None, max_length=4000)
    assigned_to: str | None = Field(default=None, max_length=64)
    resolution_notes: str | None = Field(default=None, max_length=4000)


class GrievanceRecord(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    borrower_id: uuid.UUID
    score_id: uuid.UUID | None
    loan_application_id: uuid.UUID | None
    category: GrievanceCategory
    description: str
    status: GrievanceStatus
    sla_hours: int
    assigned_to: str | None
    resolution_notes: str | None
    created_at: datetime
    due_at: datetime
    resolved_at: datetime | None
    is_overdue: bool = False


class GrievanceAuditEntry(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    grievance_id: uuid.UUID
    from_status: str | None
    to_status: str
    actor: str
    note: str | None
    performed_at: datetime

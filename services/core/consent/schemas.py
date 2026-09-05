"""Pydantic schemas for the Consent API.

These schemas define the request/response contracts for consent operations.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ConsentPurpose(StrEnum):
    CREDIT_SCORING = "credit_scoring"
    IDENTITY_VERIFICATION = "identity_verification"
    DATA_AGGREGATION = "data_aggregation"
    SCORE_SHARING_WITH_RE = "score_sharing_with_re"
    RETRAINING_CONSENT = "retraining_consent"


class ConsentMode(StrEnum):
    APP_SELF_SERVICE = "app_self_service"
    BANK_SAKHI_ASSISTED = "bank_sakhi_assisted"
    IVR_VOICE = "ivr_voice"


class ConsentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"


class DataSource(StrEnum):
    AA = "AA"
    GEOSPATIAL = "GEOSPATIAL"
    SHG_FPO = "SHG_FPO"
    BUREAU = "BUREAU"


class FetchFrequency(StrEnum):
    ONETIME = "ONETIME"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


# ── Request Schemas ──────────────────────────────────────────


class ConsentCreateRequest(BaseModel):
    """Request body for creating a new consent record."""

    borrower_id: uuid.UUID
    purpose: ConsentPurpose
    consent_mode: ConsentMode
    data_sources: list[DataSource] = Field(default=[DataSource.AA], min_length=1)

    # AA-specific (optional)
    aa_handle: str | None = None
    fi_types: list[str] = Field(default=[])
    fi_date_range_from: datetime | None = None
    fi_date_range_to: datetime | None = None
    fetch_frequency: FetchFrequency | None = None

    # Scope descriptions
    scope_description_en: str = Field(..., min_length=10, max_length=2000)
    scope_description_hi: str | None = None
    scope_description_local: str | None = None

    # Duration
    duration_days: int = Field(default=365, ge=1, le=365)

    # Audit
    created_by: str = Field(..., min_length=1, max_length=50)
    ip_address: str | None = None
    device_id: str | None = None

    @field_validator("duration_days")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v > 365:
            raise ValueError("Consent duration cannot exceed 365 days (AA regulatory limit)")
        return v


class ConsentRevokeRequest(BaseModel):
    """Request body for revoking an existing consent."""

    revocation_reason: str = Field(..., min_length=1, max_length=255)
    revoked_by: str = Field(..., min_length=1, max_length=50)


# ── Response Schemas ─────────────────────────────────────────


class ConsentResponse(BaseModel):
    """Response for a single consent record."""

    id: uuid.UUID
    borrower_id: uuid.UUID
    purpose: str
    consent_mode: str
    data_sources: list[str]
    status: str
    scope_description_en: str
    scope_description_hi: str | None
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    hash_current: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsentVerifyResponse(BaseModel):
    """Response for consent verification check."""

    consent_id: uuid.UUID
    is_valid: bool
    status: str
    hash_chain_valid: bool
    expires_at: datetime
    remaining_days: int
    data_sources: list[str]
    issues: list[str] = Field(default=[])


class ConsentAuditEntry(BaseModel):
    """A single audit log entry."""

    id: uuid.UUID
    action: str
    actor: str
    details: dict | None
    performed_at: datetime

    model_config = {"from_attributes": True}


class ConsentAuditResponse(BaseModel):
    """Response containing the audit trail for a consent record."""

    consent_id: uuid.UUID
    entries: list[ConsentAuditEntry]
    total: int


class ConsentListResponse(BaseModel):
    """Paginated list of consent records."""

    items: list[ConsentResponse]
    total: int
    page: int
    page_size: int

"""Pydantic schemas for the Ingestion Service."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IngestionStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"


class IngestionSource(StrEnum):
    AA = "AA"
    GEOSPATIAL = "GEOSPATIAL"
    SHG_FPO = "SHG_FPO"
    BUREAU = "BUREAU"


class IngestionTriggerRequest(BaseModel):
    """Request schema to trigger a manual data aggregation run."""

    borrower_id: uuid.UUID
    purpose: str = "credit_scoring"
    data_sources: list[IngestionSource] = Field(
        default=[
            IngestionSource.AA,
            IngestionSource.GEOSPATIAL,
            IngestionSource.SHG_FPO,
            IngestionSource.BUREAU,
        ]
    )


class IngestionSourceStatus(BaseModel):
    source: IngestionSource
    status: IngestionStatus
    duration_ms: int | None = None
    error_message: str | None = None


class IngestionTriggerResponse(BaseModel):
    """Response containing the ingestion status per data rail."""

    borrower_id: uuid.UUID
    overall_status: str  # SUCCESS | PARTIAL | FAILED
    sources: list[IngestionSourceStatus]
    feature_snapshot_id: uuid.UUID | None = None
    completed_at: datetime


class SHGMemberDataInput(BaseModel):
    """Data structure for manual entry of one SHG member."""

    shg_name: str
    nabard_grade: str = Field(..., pattern="^[A-D]$")
    membership_years: int = Field(..., ge=0, le=50)
    monthly_savings: float = Field(..., ge=0)
    total_savings: float = Field(..., ge=0)
    loans_taken: int = Field(..., ge=0)
    loans_repaid: int = Field(..., ge=0)
    meeting_attendance_pct: float = Field(..., ge=0, le=100)


class FPOFarmerDataInput(BaseModel):
    """Data structure for manual entry of farmer details."""

    land_holding_acres: float = Field(..., ge=0)
    land_ownership: str = Field(..., pattern="^(OWN|LEASED|SHARECROP|LANDLESS)$")
    irrigation_access: bool
    crop_type_primary: str
    estimated_monthly_income: float = Field(..., ge=0)


class SHGFPOIngestRequest(BaseModel):
    """Request schema for uploading SHG/FPO manual entry details."""

    borrower_id: uuid.UUID
    shg_data: SHGMemberDataInput | None = None
    farmer_data: FPOFarmerDataInput | None = None
    created_by: str = Field(..., min_length=1, max_length=50)

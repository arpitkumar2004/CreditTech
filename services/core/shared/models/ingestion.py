"""Data ingestion and feature snapshot models: DataPull and FeatureSnapshot."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.core.database import Base
from services.core.shared.types import GUID, JSONB

if TYPE_CHECKING:
    from services.core.shared.models.core import Borrower


class DataPull(Base):
    __tablename__ = "data_pulls"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("source IN ('AA', 'GEOSPATIAL', 'SHG_FPO', 'BUREAU')"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'TIMEOUT', 'SKIPPED')"
        ),
        default="PENDING",
    )
    raw_ref: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Object storage path to raw response"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pulled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    borrower: Mapped[Borrower] = relationship(back_populates="data_pulls")


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"
    __table_args__ = (
        Index("idx_feature_snapshots_borrower_computed", "borrower_id", "computed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id"), nullable=False
    )
    feature_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1.0.0")
    features_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Model-ready features — NO PII"
    )
    season_tag: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("season_tag IN ('KHARIF', 'RABI', 'ZAID')"),
        nullable=False,
    )
    sources_used: Mapped[dict] = mapped_column(JSONB, default=list)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    borrower: Mapped[Borrower] = relationship(back_populates="feature_snapshots")

"""Credit scoring and explainability models: Score and ReasonCode."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
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
    from services.core.shared.models.decisioning import LoanApplication


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        Index("idx_scores_borrower_created", "borrower_id", "generated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id"), nullable=False
    )
    feature_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("feature_snapshots.id"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_lower: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_upper: Mapped[float] = mapped_column(Float, nullable=False)
    sources_used: Mapped[dict] = mapped_column(JSONB, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    borrower: Mapped[Borrower] = relationship(back_populates="scores")
    reason_codes: Mapped[list[ReasonCode]] = relationship(back_populates="score")
    loan_applications: Mapped[list[LoanApplication]] = relationship(back_populates="score")


class ReasonCode(Base):
    __tablename__ = "reason_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    score_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("scores.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("direction IN ('POSITIVE', 'NEGATIVE')"),
        nullable=False,
    )
    shap_value: Mapped[float] = mapped_column(Float, nullable=False)
    localized_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    localized_text_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    localized_text_local: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    score: Mapped[Score] = relationship(back_populates="reason_codes")


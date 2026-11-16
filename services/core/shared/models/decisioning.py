"""Loan application, officer decision, and repayment models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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
from services.core.shared.types import GUID

if TYPE_CHECKING:
    from services.core.shared.models.scoring import Score


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    __table_args__ = (
        Index("idx_loan_apps_re_decision", "partner_re_id", "officer_decision"),
        Index("idx_loan_apps_borrower_created", "borrower_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id"), nullable=False
    )
    score_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("scores.id"), nullable=False
    )
    partner_re_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Loan details
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    requested_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)

    # Decision
    officer_decision: Mapped[str | None] = mapped_column(
        String(20),
        CheckConstraint(
            "officer_decision IS NULL OR "
            "officer_decision IN ('APPROVED', 'REJECTED', 'MORE_INFO_REQUIRED', 'REFERRED')"
        ),
        nullable=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    score: Mapped[Score] = relationship(back_populates="loan_applications")


class OfficerDecisionLog(Base):
    """Immutable record of a loan officer's decision on a scored application."""

    __tablename__ = "officer_decision_log"
    __table_args__ = (
        Index("idx_ofc_decision_score", "score_id"),
        Index("idx_ofc_decision_officer", "officer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    score_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("scores.id"), nullable=False
    )
    loan_application_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("loan_applications.id"), nullable=True
    )
    officer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "decision IN ('APPROVED', 'REJECTED', 'MORE_INFO_REQUIRED')"
        ),
        nullable=False,
    )
    model_recommendation: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "model_recommendation IN ('APPROVE', 'REVIEW', 'REJECT')"
        ),
        nullable=False,
    )
    is_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    officer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_score_at_decision: Mapped[float] = mapped_column(Float, nullable=False)
    model_version_at_decision: Mapped[str] = mapped_column(String(50), nullable=False)
    feature_version_at_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Backward compatibility alias
OfficerDecision = OfficerDecisionLog


class RepaymentRecord(Base):
    __tablename__ = "repayment_records"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    loan_application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("loan_applications.id"), nullable=False
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "status IN ('CURRENT', 'DPD_1_30', 'DPD_31_60', 'DPD_61_90', 'DPD_90_PLUS', 'CLOSED')"
        ),
        nullable=False,
    )
    consented_for_retraining: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


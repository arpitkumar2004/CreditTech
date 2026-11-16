"""Grievance and fairness audit models: FairnessAuditLog, Grievance, and GrievanceAuditLog."""

from __future__ import annotations

import uuid
from datetime import datetime

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
from sqlalchemy.orm import Mapped, mapped_column

from services.core.database import Base
from services.core.shared.types import GUID


class FairnessAuditLog(Base):
    __tablename__ = "fairness_audit_log"
    __table_args__ = (
        Index("idx_fairness_period_dim", "period", "dimension"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    dimension: Mapped[str] = mapped_column(
        String(30),
        CheckConstraint("dimension IN ('GENDER', 'GEOGRAPHY', 'LANDHOLDING', 'OFFICER')"),
        nullable=False,
    )
    group_value: Mapped[str] = mapped_column(String(50), nullable=False)
    approval_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    override_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        CheckConstraint(
            "status IN ('OK', 'INSUFFICIENT_SAMPLE', 'PENDING_GOVERNANCE')"
        ),
        nullable=False,
        default="OK",
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Grievance(Base):
    """Borrower-raised grievance/appeal with an SLA clock."""

    __tablename__ = "grievances"
    __table_args__ = (
        Index("idx_grievance_status", "status"),
        Index("idx_grievance_borrower", "borrower_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id"), nullable=False
    )
    score_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("scores.id"), nullable=True
    )
    loan_application_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("loan_applications.id"), nullable=True
    )
    category: Mapped[str] = mapped_column(
        String(40),
        CheckConstraint(
            "category IN ('SCORE_DISPUTE', 'DECISION_APPEAL', "
            "'DATA_ACCURACY', 'CONSENT_ISSUE', 'OTHER')"
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'ESCALATED', 'CLOSED')"
        ),
        nullable=False,
        default="OPEN",
    )
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)
    assigned_to: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GrievanceAuditLog(Base):
    """Append-only status-transition log for a Grievance."""

    __tablename__ = "grievance_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    grievance_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("grievances.id"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


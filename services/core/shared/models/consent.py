"""Consent models: ConsentRecord and ConsentAuditLog."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.core.database import Base
from services.core.shared.types import GUID, INET, JSONB

if TYPE_CHECKING:
    from services.core.shared.models.core import Borrower


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        Index("idx_consent_borrower_status", "borrower_id", "status"),
        Index("idx_consent_expires_at", "expires_at", postgresql_where="status = 'ACTIVE'"),
        Index("idx_consent_hash_chain", "hash_current"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("borrowers.id", ondelete="RESTRICT"), nullable=False
    )

    # Consent details
    purpose: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "purpose IN ('credit_scoring', 'identity_verification', "
            "'data_aggregation', 'score_sharing_with_re', 'retraining_consent')"
        ),
        nullable=False,
    )
    consent_mode: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "consent_mode IN ('app_self_service', 'bank_sakhi_assisted', 'ivr_voice')"
        ),
        nullable=False,
    )

    # AA-specific fields
    aa_consent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    aa_handle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fi_types: Mapped[dict] = mapped_column(JSONB, default=list)
    fi_date_range_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fi_date_range_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fetch_frequency: Mapped[str | None] = mapped_column(
        String(20),
        CheckConstraint(
            "fetch_frequency IS NULL OR "
            "fetch_frequency IN ('ONETIME', 'HOURLY', 'DAILY', 'MONTHLY', 'YEARLY')"
        ),
        nullable=True,
    )

    # Data sources consented
    data_sources: Mapped[dict] = mapped_column(JSONB, default=lambda: ["AA"])

    # Scope descriptions (localized)
    scope_description_en: Mapped[str] = mapped_column(Text, nullable=False)
    scope_description_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_description_local: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('ACTIVE', 'EXPIRED', 'REVOKED', 'SUPERSEDED')"),
        default="ACTIVE",
    )

    # Hash chain (tamper evidence)
    hash_prev: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_current: Mapped[str] = mapped_column(String(64), nullable=False)

    # Audit metadata
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    consent_artifact_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    borrower: Mapped[Borrower] = relationship(back_populates="consent_records")
    audit_logs: Mapped[list[ConsentAuditLog]] = relationship(back_populates="consent")


class ConsentAuditLog(Base):
    __tablename__ = "consent_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    consent_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("consent_records.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "action IN ('CREATED', 'VERIFIED', 'REVOKED', "
            "'EXPIRED_AUTO', 'SUPERSEDED', 'ACCESSED')"
        ),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    consent: Mapped[ConsentRecord] = relationship(back_populates="audit_logs")

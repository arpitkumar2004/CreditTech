"""SQLAlchemy ORM models for CreditTech.

Schema follows the data architecture defined in §7.1 of the planning document.
PII fields (aadhaar, name, phone) are stored separately from model-ready
FeatureSnapshot records — this is enforced at the schema level, not just by convention.
"""

import uuid
from datetime import datetime

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
from services.core.shared.types import GUID, INET, JSONB


# ──────────────────────────────────────────────────────────────
# Village — reference / lookup table
# ──────────────────────────────────────────────────────────────
class Village(Base):
    __tablename__ = "villages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    site_type: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    block: Mapped[str] = mapped_column(String(100), nullable=True)
    agro_climatic_zone: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    borrowers: Mapped[list["Borrower"]] = relationship(back_populates="village")


# ──────────────────────────────────────────────────────────────
# Borrower — PII is here, NOT in FeatureSnapshot
# ──────────────────────────────────────────────────────────────
class Borrower(Base):
    __tablename__ = "borrowers"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    # PII fields — stored encrypted / hashed
    aadhaar_ref_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="SHA-256 of Aadhaar number"
    )
    name_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted"
    )
    phone_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AES-256-GCM encrypted"
    )

    # Non-PII demographic (used for fairness monitoring, not as model features)
    village_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("villages.id"), nullable=False
    )
    gender: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("gender IN ('M', 'F', 'OTHER')"),
        nullable=False,
    )
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    landholding_band: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint(
            "landholding_band IN ('LANDLESS', 'MARGINAL', 'SMALL', 'SEMI_MEDIUM', 'MEDIUM', 'LARGE')"
        ),
        nullable=True,
    )
    language: Mapped[str] = mapped_column(String(20), default="hi")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    village: Mapped["Village"] = relationship(back_populates="borrowers")
    consent_records: Mapped[list["ConsentRecord"]] = relationship(back_populates="borrower")
    data_pulls: Mapped[list["DataPull"]] = relationship(back_populates="borrower")
    feature_snapshots: Mapped[list["FeatureSnapshot"]] = relationship(back_populates="borrower")
    scores: Mapped[list["Score"]] = relationship(back_populates="borrower")


# ──────────────────────────────────────────────────────────────
# ConsentRecord — append-only, hash-chained (ADR-6)
# ──────────────────────────────────────────────────────────────
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
    borrower: Mapped["Borrower"] = relationship(back_populates="consent_records")
    audit_logs: Mapped[list["ConsentAuditLog"]] = relationship(back_populates="consent")


# ──────────────────────────────────────────────────────────────
# ConsentAuditLog — append-only mutation log
# ──────────────────────────────────────────────────────────────
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
    consent: Mapped["ConsentRecord"] = relationship(back_populates="audit_logs")


# ──────────────────────────────────────────────────────────────
# DataPull — tracks each external data source fetch
# ──────────────────────────────────────────────────────────────
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
    borrower: Mapped["Borrower"] = relationship(back_populates="data_pulls")


# ──────────────────────────────────────────────────────────────
# FeatureSnapshot — versioned, NO PII here
# ──────────────────────────────────────────────────────────────
class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

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
    borrower: Mapped["Borrower"] = relationship(back_populates="feature_snapshots")


# ──────────────────────────────────────────────────────────────
# Score — model output
# ──────────────────────────────────────────────────────────────
class Score(Base):
    __tablename__ = "scores"

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
    borrower: Mapped["Borrower"] = relationship(back_populates="scores")
    reason_codes: Mapped[list["ReasonCode"]] = relationship(back_populates="score")
    loan_applications: Mapped[list["LoanApplication"]] = relationship(back_populates="score")


# ──────────────────────────────────────────────────────────────
# ReasonCode — SHAP-derived, localized explanations
# ──────────────────────────────────────────────────────────────
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
    score: Mapped["Score"] = relationship(back_populates="reason_codes")


# ──────────────────────────────────────────────────────────────
# LoanApplication — human-in-the-loop decision record
# ──────────────────────────────────────────────────────────────
class LoanApplication(Base):
    __tablename__ = "loan_applications"

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
    score: Mapped["Score"] = relationship(back_populates="loan_applications")


# ──────────────────────────────────────────────────────────────
# OfficerDecisionLog — append-only, immutable audit of officer decisions (P4)
# ──────────────────────────────────────────────────────────────
class OfficerDecisionLog(Base):
    """Immutable record of a loan officer's decision on a scored application.

    Rows are never updated after insert. Amending a decision requires appending
    a new row. This preserves the full audit trail required by RBI Fair
    Practices Code and the pilot governance plan (§17.2 of the planning doc).
    """

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


# ──────────────────────────────────────────────────────────────
# RepaymentRecord — consented feedback loop for retraining
# ──────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────
# FairnessAuditLog — weekly batch output
# ──────────────────────────────────────────────────────────────
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
    # approval_rate is nullable so INSUFFICIENT_SAMPLE rows can be persisted
    # without inventing a rate. Governance treats null-rate rows as
    # informational (not a statistical claim).
    approval_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    override_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    # OK / INSUFFICIENT_SAMPLE / PENDING_GOVERNANCE
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


# ──────────────────────────────────────────────────────────────
# Grievance — borrower appeal / dispute channel (P5, M8)
# ──────────────────────────────────────────────────────────────
class Grievance(Base):
    """Borrower-raised grievance/appeal with an SLA clock.

    Per RBI Fair Practices Code and §17.3 / §31 of the planning doc, borrowers
    must have a formal channel to dispute a score or decision. The SLA clock
    starts at creation; escalation is auto-computed when now > due_at and the
    grievance is not RESOLVED/CLOSED.
    """

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

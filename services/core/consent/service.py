"""Consent Service — business logic for consent lifecycle management.

Implements: create, hash-chain, revoke, verify, list, audit trail.
This service is the ONLY module allowed to write consent records.
Every downstream data pull must present a valid, unexpired consent token.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.config import get_settings
from services.core.shared.logging import get_logger
from services.core.shared.models import ConsentAuditLog, ConsentRecord

from .schemas import ConsentCreateRequest, ConsentRevokeRequest

logger = get_logger("consent.service")
settings = get_settings()


def _as_utc(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to timezone-aware UTC.

    PostgreSQL preserves tzinfo on ``TIMESTAMP WITH TIME ZONE`` columns, but
    SQLite (used by the in-memory test harness) drops it. This helper lets
    the same comparison / hashing logic work on both backends.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class ConsentServiceError(Exception):
    """Base exception for consent service errors."""

    pass


class ConsentNotFoundError(ConsentServiceError):
    """Raised when a consent record is not found."""

    pass


class ConsentAlreadyRevokedError(ConsentServiceError):
    """Raised when trying to revoke an already-revoked consent."""

    pass


class ConsentService:
    """Manages the complete consent lifecycle with hash-chain tamper evidence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Hash Chain ───────────────────────────────────────────

    @staticmethod
    def _compute_genesis_hash(borrower_id: uuid.UUID) -> str:
        """Compute the genesis hash for the first consent of a borrower."""
        salt = settings.consent_genesis_salt
        payload = f"GENESIS:{salt}:{borrower_id}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_consent_hash(
        borrower_id: uuid.UUID,
        purpose: str,
        data_sources: list[str],
        issued_at: datetime,
        expires_at: datetime,
        status: str,
        prev_hash: str,
    ) -> str:
        """Compute SHA-256 hash for tamper-evident consent chain."""
        payload = json.dumps(
            {
                "borrower_id": str(borrower_id),
                "purpose": purpose,
                "data_sources": sorted(data_sources),
                "issued_at": issued_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "status": status,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def _get_latest_hash(self, borrower_id: uuid.UUID) -> str:
        """Get the hash_current of the most recent consent for this borrower."""
        result = await self.db.execute(
            select(ConsentRecord.hash_current)
            .where(ConsentRecord.borrower_id == borrower_id)
            .order_by(ConsentRecord.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return self._compute_genesis_hash(borrower_id)
        return row

    # ── Create ───────────────────────────────────────────────

    async def create_consent(self, request: ConsentCreateRequest) -> ConsentRecord:
        """Create a new consent record with hash-chain linking."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=request.duration_days)

        # Get previous hash for chain
        prev_hash = await self._get_latest_hash(request.borrower_id)

        # Supersede any existing ACTIVE consents for the same purpose + sources
        await self._supersede_existing(
            request.borrower_id, request.purpose.value, [s.value for s in request.data_sources]
        )

        # Compute hash for this record
        data_sources_str = [s.value for s in request.data_sources]
        current_hash = self._compute_consent_hash(
            borrower_id=request.borrower_id,
            purpose=request.purpose.value,
            data_sources=data_sources_str,
            issued_at=now,
            expires_at=expires_at,
            status="ACTIVE",
            prev_hash=prev_hash,
        )

        # Create the consent record
        consent = ConsentRecord(
            borrower_id=request.borrower_id,
            purpose=request.purpose.value,
            consent_mode=request.consent_mode.value,
            aa_handle=request.aa_handle,
            fi_types=request.fi_types,
            fi_date_range_from=request.fi_date_range_from,
            fi_date_range_to=request.fi_date_range_to,
            fetch_frequency=request.fetch_frequency.value if request.fetch_frequency else None,
            data_sources=data_sources_str,
            scope_description_en=request.scope_description_en,
            scope_description_hi=request.scope_description_hi,
            scope_description_local=request.scope_description_local,
            issued_at=now,
            expires_at=expires_at,
            status="ACTIVE",
            hash_prev=prev_hash,
            hash_current=current_hash,
            created_by=request.created_by,
            ip_address=request.ip_address,
            device_id=request.device_id,
        )
        self.db.add(consent)
        await self.db.flush()

        # Audit log
        audit = ConsentAuditLog(
            consent_id=consent.id,
            action="CREATED",
            actor=request.created_by,
            details={
                "purpose": request.purpose.value,
                "data_sources": data_sources_str,
                "duration_days": request.duration_days,
            },
        )
        self.db.add(audit)
        await self.db.flush()

        logger.info(
            "consent_created",
            consent_id=str(consent.id),
            borrower_id=str(request.borrower_id),
            purpose=request.purpose.value,
        )

        return consent

    async def _supersede_existing(
        self, borrower_id: uuid.UUID, purpose: str, data_sources: list[str]
    ) -> None:
        """Mark existing active consents for the same purpose as SUPERSEDED."""
        result = await self.db.execute(
            select(ConsentRecord).where(
                ConsentRecord.borrower_id == borrower_id,
                ConsentRecord.purpose == purpose,
                ConsentRecord.status == "ACTIVE",
            )
        )
        existing = result.scalars().all()
        for record in existing:
            record.status = "SUPERSEDED"
            audit = ConsentAuditLog(
                consent_id=record.id,
                action="SUPERSEDED",
                actor="system",
                details={"reason": "New consent created for same purpose"},
            )
            self.db.add(audit)

    # ── Retrieve ─────────────────────────────────────────────

    async def get_consent(self, consent_id: uuid.UUID) -> ConsentRecord:
        """Retrieve a single consent record by ID."""
        result = await self.db.execute(
            select(ConsentRecord).where(ConsentRecord.id == consent_id)
        )
        consent = result.scalar_one_or_none()
        if consent is None:
            raise ConsentNotFoundError(f"Consent {consent_id} not found")

        # Lazy expiration check
        expires_at = _as_utc(consent.expires_at)
        if consent.status == "ACTIVE" and expires_at < datetime.now(UTC):
            consent.status = "EXPIRED"
            audit = ConsentAuditLog(
                consent_id=consent.id,
                action="EXPIRED_AUTO",
                actor="system",
                details={"expired_at": expires_at.isoformat()},
            )
            self.db.add(audit)
            await self.db.flush()

        return consent

    async def list_by_borrower(
        self,
        borrower_id: uuid.UUID,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ConsentRecord], int]:
        """List consent records for a borrower with optional status filter."""
        query = select(ConsentRecord).where(ConsentRecord.borrower_id == borrower_id)
        count_query = select(func.count()).select_from(ConsentRecord).where(
            ConsentRecord.borrower_id == borrower_id
        )

        if status:
            query = query.where(ConsentRecord.status == status)
            count_query = count_query.where(ConsentRecord.status == status)

        query = query.order_by(ConsentRecord.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return list(result.scalars().all()), count_result.scalar_one()

    # ── Revoke ───────────────────────────────────────────────

    async def revoke_consent(
        self, consent_id: uuid.UUID, request: ConsentRevokeRequest
    ) -> ConsentRecord:
        """Revoke an active consent. Creates audit trail entry."""
        consent = await self.get_consent(consent_id)

        if consent.status == "REVOKED":
            raise ConsentAlreadyRevokedError(f"Consent {consent_id} already revoked")

        if consent.status != "ACTIVE":
            raise ConsentServiceError(
                f"Cannot revoke consent in status '{consent.status}'"
            )

        now = datetime.now(UTC)
        consent.status = "REVOKED"
        consent.revoked_at = now
        consent.revocation_reason = request.revocation_reason

        audit = ConsentAuditLog(
            consent_id=consent.id,
            action="REVOKED",
            actor=request.revoked_by,
            details={
                "reason": request.revocation_reason,
                "revoked_at": now.isoformat(),
            },
        )
        self.db.add(audit)
        await self.db.flush()

        logger.info(
            "consent_revoked",
            consent_id=str(consent_id),
            revoked_by=request.revoked_by,
        )

        return consent

    # ── Verify ───────────────────────────────────────────────

    async def verify_consent(self, consent_id: uuid.UUID) -> dict:
        """Verify that a consent is active and its hash chain is valid."""
        consent = await self.get_consent(consent_id)
        now = datetime.now(UTC)
        expires_at = _as_utc(consent.expires_at)
        issued_at = _as_utc(consent.issued_at)

        issues: list[str] = []
        is_valid = True

        # Check status
        if consent.status != "ACTIVE":
            is_valid = False
            issues.append(f"Consent status is {consent.status}, not ACTIVE")

        # Check expiry
        if expires_at < now:
            is_valid = False
            issues.append("Consent has expired")

        # Verify hash chain
        expected_hash = self._compute_consent_hash(
            borrower_id=consent.borrower_id,
            purpose=consent.purpose,
            data_sources=consent.data_sources,
            issued_at=issued_at,
            expires_at=expires_at,
            status="ACTIVE",  # Hash was computed at creation time when status was ACTIVE
            prev_hash=consent.hash_prev,
        )
        hash_chain_valid = expected_hash == consent.hash_current
        if not hash_chain_valid:
            is_valid = False
            issues.append("Hash chain verification failed — possible tampering")

        remaining = max(0, (expires_at - now).days)

        # Log the verification
        audit = ConsentAuditLog(
            consent_id=consent.id,
            action="VERIFIED",
            actor="system",
            details={"is_valid": is_valid, "hash_chain_valid": hash_chain_valid},
        )
        self.db.add(audit)
        await self.db.flush()

        return {
            "consent_id": consent.id,
            "is_valid": is_valid,
            "status": consent.status,
            "hash_chain_valid": hash_chain_valid,
            "expires_at": consent.expires_at,
            "remaining_days": remaining,
            "data_sources": consent.data_sources,
            "issues": issues,
        }

    # ── Audit Trail ──────────────────────────────────────────

    async def get_audit_trail(self, consent_id: uuid.UUID) -> list[ConsentAuditLog]:
        """Get the complete audit trail for a consent record."""
        # Verify consent exists
        await self.get_consent(consent_id)

        result = await self.db.execute(
            select(ConsentAuditLog)
            .where(ConsentAuditLog.consent_id == consent_id)
            .order_by(ConsentAuditLog.performed_at.asc())
        )
        return list(result.scalars().all())

    # ── Active Consent Check (for data pull authorization) ───

    async def check_active_consent(
        self,
        borrower_id: uuid.UUID,
        purpose: str,
        required_sources: list[str],
    ) -> ConsentRecord | None:
        """Check if an active, unexpired consent exists for the given purpose and sources.

        This is called by the Data Aggregation Service before initiating any data pull.
        Returns the consent record if valid, None otherwise.
        """
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(ConsentRecord).where(
                ConsentRecord.borrower_id == borrower_id,
                ConsentRecord.purpose == purpose,
                ConsentRecord.status == "ACTIVE",
            )
        )
        candidates = result.scalars().all()
        consent = next(
            (c for c in candidates if _as_utc(c.expires_at) > now),
            None,
        )

        if consent is None:
            return None

        # Check that all required sources are covered
        consented_sources = set(consent.data_sources)
        required = set(required_sources)
        if not required.issubset(consented_sources):
            return None

        return consent

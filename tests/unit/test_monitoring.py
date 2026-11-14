"""Unit tests for the Fairness Auditing and Data Retention Services."""

import uuid
from datetime import datetime, timedelta, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import Borrower, ConsentRecord, LoanApplication, Score, Village


@pytest.fixture
async def sample_village(db_session: AsyncSession) -> Village:
    village = Village(
        name="Pilot Village 1",
        site_type="IRRIGATED_COTTON",
        state="Rajasthan",
        district="Hanumangarh",
    )
    db_session.add(village)
    await db_session.flush()
    return village


@pytest.fixture
async def sample_borrower(db_session: AsyncSession, sample_village: Village) -> Borrower:
    borrower = Borrower(
        aadhaar_ref_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        name_encrypted="encrypted_name_bytes",
        phone_encrypted="encrypted_phone_bytes",
        village_id=sample_village.id,
        gender="F",
        age=30,
        landholding_band="MARGINAL",
    )
    db_session.add(borrower)
    await db_session.flush()
    return borrower


@pytest.mark.asyncio
async def test_fairness_audit_execution(
    client: AsyncClient, db_session: AsyncSession, sample_borrower: Borrower
) -> None:
    """Test executing a weekly fairness audit and creating logs."""
    # 1. Create a dummy Score and LoanApplication record
    score = Score(
        borrower_id=sample_borrower.id,
        feature_snapshot_id=uuid.uuid4(),
        model_version="v1.0.0",
        score=65.0,
        confidence_lower=60.0,
        confidence_upper=70.0,
    )
    db_session.add(score)
    await db_session.flush()

    loan_app = LoanApplication(
        borrower_id=sample_borrower.id,
        score_id=score.id,
        partner_re_id="BANK_01",
        requested_amount=30000.0,
        requested_tenure_months=12,
        purpose="AGRICULTURE",
        officer_decision="APPROVED",
        override_reason="Strong profile",
    )
    db_session.add(loan_app)
    await db_session.commit()

    # 2. Trigger via endpoint
    response = await client.post("/api/v1/monitoring/fairness-audit?period=2026-W35")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["records_audited"] >= 1


@pytest.mark.asyncio
async def test_data_retention_purging(
    client: AsyncClient, db_session: AsyncSession, sample_borrower: Borrower
) -> None:
    """Test that expired/revoked consent triggers borrower PII deletion."""
    # 1. Create an expired consent record
    consent = ConsentRecord(
        borrower_id=sample_borrower.id,
        purpose="credit_scoring",
        consent_mode="app_self_service",
        scope_description_en="I consent to share credit reports.",
        issued_at=datetime.now(UTC) - timedelta(days=60),
        expires_at=datetime.now(UTC) - timedelta(days=30),  # Expired
        status="ACTIVE",  # Lazy state transitions should catch this
        hash_prev="genesis",
        hash_current="current_hash",
        created_by="borrower",
    )
    db_session.add(consent)
    await db_session.commit()

    # 2. Execute retention purge
    response = await client.post("/api/v1/monitoring/retention-purge")
    assert response.status_code == 200
    assert response.json()["purged_records_count"] == 1

    # 3. Reload borrower to check anonymized fields
    result = await db_session.execute(
        select(Borrower).where(Borrower.id == sample_borrower.id)
    )
    borrower_reloaded = result.scalar_one()
    assert borrower_reloaded.name_encrypted == "ANONYMIZED"
    assert borrower_reloaded.phone_encrypted == "ANONYMIZED"
    assert borrower_reloaded.aadhaar_ref_hash.startswith("ANON-")

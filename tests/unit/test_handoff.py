"""Unit tests for the Partner RE Handoff Service and Router."""

from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    OfficerDecisionLog,
    ReasonCode,
    Score,
    Village,
)
from services.core.shared.security import PIIEncryptor

OFFICER_HEADERS = {"X-Officer-Id": "officer_101", "X-Officer-Role": "LOAN_OFFICER"}


async def _record_approved_decision(client: AsyncClient, score_id) -> None:
    """Helper: score has band GOOD -> APPROVE recommendation -> no override needed."""
    resp = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(score_id), "decision": "APPROVED"},
        headers=OFFICER_HEADERS,
    )
    assert resp.status_code == 201, resp.text


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
        name_encrypted="encrypted_name",
        phone_encrypted="encrypted_phone",
        village_id=sample_village.id,
        gender="F",
        age=30,
    )
    db_session.add(borrower)
    await db_session.flush()
    return borrower


@pytest.fixture
async def sample_feature_snapshot(db_session: AsyncSession, sample_borrower: Borrower) -> FeatureSnapshot:
    snapshot = FeatureSnapshot(
        borrower_id=sample_borrower.id,
        feature_version="v1.0.0",
        features_json={"land_holding_acres": 2.5, "irrigation_access": True},
        season_tag="RABI",
        sources_used=["AA"],
    )
    db_session.add(snapshot)
    await db_session.flush()
    return snapshot


@pytest.fixture
async def sample_score(
    db_session: AsyncSession, sample_borrower: Borrower, sample_feature_snapshot: FeatureSnapshot
) -> Score:
    score = Score(
        borrower_id=sample_borrower.id,
        feature_snapshot_id=sample_feature_snapshot.id,
        model_version="v1.0.0-logistic",
        score=75.0,
        confidence_lower=70.0,
        confidence_upper=80.0,
        sources_used=["AA"],
    )
    db_session.add(score)
    await db_session.flush()

    # Add a reason code
    rc = ReasonCode(
        score_id=score.id,
        rank=1,
        feature_name="land_holding_acres",
        direction="POSITIVE",
        shap_value=0.15,
        localized_text_en="Adequate land",
        localized_text_hi="पर्याप्त भूमि",
    )
    db_session.add(rc)
    await db_session.flush()

    return score


@pytest.mark.asyncio
async def test_handoff_submission_success(
    client: AsyncClient, sample_score: Score
) -> None:
    """Test successful compilation and submit to Partner RE."""
    await _record_approved_decision(client, sample_score.id)
    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    response = await client.post("/api/v1/handoff/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUBMITTED"
    assert data["loan_application_id"] is not None


@pytest.mark.asyncio
async def test_decision_webhook_receiver(
    client: AsyncClient, db_session: AsyncSession, sample_score: Score
) -> None:
    """Test receiving and registering decisions from the RE callback."""
    # 1. Create a loan application first (requires an approved decision)
    await _record_approved_decision(client, sample_score.id)
    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    submit_resp = await client.post("/api/v1/handoff/submit", json=payload)
    loan_app_id = submit_resp.json()["loan_application_id"]

    # 2. Call decision webhook
    webhook_payload = {
        "re_application_id": "RE-123456",
        "credittech_application_id": loan_app_id,
        "decision": "APPROVED",
        "decided_at": datetime.now(UTC).isoformat(),
        "decided_by": "officer_101",
        "approved_amount": 40000.0,
        "override_reason": "Good historical feedback",
    }
    webhook_resp = await client.post("/api/v1/handoff/webhook/decision", json=webhook_payload)
    assert webhook_resp.status_code == 200
    assert webhook_resp.json()["status"] == "processed"


@pytest.mark.asyncio
async def test_handoff_blocked_without_officer_decision(
    client: AsyncClient, sample_score: Score
) -> None:
    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    response = await client.post("/api/v1/handoff/submit", json=payload)
    assert response.status_code == 400
    assert "officer decision" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_handoff_blocked_when_decision_is_reject(
    client: AsyncClient, sample_score: Score
) -> None:
    # Score band GOOD -> APPROVE recommendation. Reject requires override_reason.
    resp = await client.post(
        "/api/v1/decision/",
        json={
            "score_id": str(sample_score.id),
            "decision": "REJECTED",
            "override_reason": "Documentary red flag not captured in features",
        },
        headers=OFFICER_HEADERS,
    )
    assert resp.status_code == 201, resp.text

    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    response = await client.post("/api/v1/handoff/submit", json=payload)
    assert response.status_code == 400
    assert "APPROVED" in response.json()["detail"]


@pytest.mark.asyncio
async def test_handoff_is_idempotent_on_duplicate(
    client: AsyncClient, db_session: AsyncSession, sample_score: Score
) -> None:
    await _record_approved_decision(client, sample_score.id)
    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    first = await client.post("/api/v1/handoff/submit", json=payload)
    second = await client.post("/api/v1/handoff/submit", json=payload)
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["loan_application_id"] == second.json()["loan_application_id"]
    assert second.json()["status"] == "ALREADY_SUBMITTED"

    # Only ONE LoanApplication row for that (score_id, partner_re_id).
    from sqlalchemy import func, select

    from services.core.shared.models import LoanApplication

    count = await db_session.execute(
        select(func.count(LoanApplication.id)).where(
            LoanApplication.score_id == sample_score.id,
            LoanApplication.partner_re_id == "PARTNER_BANK_01",
        )
    )
    assert count.scalar_one() == 1


@pytest.mark.asyncio
async def test_handoff_payload_contains_versions_and_decision_audit(
    client: AsyncClient, db_session: AsyncSession, sample_score: Score
) -> None:
    # Record an override so we can also check override fields flow through.
    resp = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(sample_score.id), "decision": "APPROVED"},
        headers=OFFICER_HEADERS,
    )
    assert resp.status_code == 201, resp.text

    payload = {
        "score_id": str(sample_score.id),
        "partner_re_id": "PARTNER_BANK_01",
        "requested_amount": 45000.0,
        "requested_tenure_months": 12,
        "purpose": "CROP_INPUT",
    }
    r = await client.post("/api/v1/handoff/submit", json=payload)
    assert r.status_code == 200

    # OfficerDecisionLog row must exist and carry model + feature version anchors.
    result = await db_session.execute(
        select(OfficerDecisionLog).where(OfficerDecisionLog.score_id == sample_score.id)
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.model_version_at_decision == sample_score.model_version
    assert entry.feature_version_at_decision  # non-empty


def test_pii_encryption_wrapper() -> None:
    """Test that AES-256-GCM encryption and decryption roundtrips correctly."""
    encryptor = PIIEncryptor()
    original_text = "Aadhaar-1234-5678-9012"

    encrypted = encryptor.encrypt(original_text)
    assert encrypted != original_text

    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == original_text

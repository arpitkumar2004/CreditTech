"""Unit tests for the Consent Service and routes."""


import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import Borrower, Village


@pytest.fixture
async def sample_village(db_session: AsyncSession) -> Village:
    """Create a sample village for borrower registration."""
    village = Village(
        name="Pilot Village 1",
        site_type="IRRIGATED_COTTON",
        state="Rajasthan",
        district="Hanumangarh",
        block="Sangaria",
        agro_climatic_zone="Zone I-B",
    )
    db_session.add(village)
    await db_session.flush()
    return village


@pytest.fixture
async def sample_borrower(db_session: AsyncSession, sample_village: Village) -> Borrower:
    """Create a sample borrower."""
    borrower = Borrower(
        aadhaar_ref_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        name_encrypted="encrypted_name_bytes",
        phone_encrypted="encrypted_phone_bytes",
        village_id=sample_village.id,
        gender="F",
        age=34,
        landholding_band="MARGINAL",
    )
    db_session.add(borrower)
    await db_session.flush()
    return borrower


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Verify that the health check endpoint returns 200 OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_consent(client: AsyncClient, sample_borrower: Borrower) -> None:
    """Test creating a valid consent record."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "consent_mode": "bank_sakhi_assisted",
        "data_sources": ["AA", "GEOSPATIAL"],
        "scope_description_en": "I hereby consent to share my bank accounts and satellite imagery for credit scoring.",
        "duration_days": 180,
        "created_by": "sakhi_user_01",
    }
    response = await client.post("/api/v1/consent/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["borrower_id"] == str(sample_borrower.id)
    assert data["purpose"] == "credit_scoring"
    assert data["status"] == "ACTIVE"
    assert data["hash_current"] is not None


@pytest.mark.asyncio
async def test_verify_consent(
    client: AsyncClient, db_session: AsyncSession, sample_borrower: Borrower
) -> None:
    """Test verification endpoint and hash chain validation."""
    # 1. Create a consent
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "consent_mode": "bank_sakhi_assisted",
        "data_sources": ["AA"],
        "scope_description_en": "English consent description requirement",
        "duration_days": 30,
        "created_by": "test_agent",
    }
    create_resp = await client.post("/api/v1/consent/", json=payload)
    assert create_resp.status_code == 201
    consent_id = create_resp.json()["id"]

    # 2. Verify consent
    verify_resp = await client.get(f"/api/v1/consent/{consent_id}/verify")
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_valid"] is True
    assert verify_data["hash_chain_valid"] is True


@pytest.mark.asyncio
async def test_revoke_consent(
    client: AsyncClient, db_session: AsyncSession, sample_borrower: Borrower
) -> None:
    """Test revoking an active consent."""
    # 1. Create
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "identity_verification",
        "consent_mode": "app_self_service",
        "data_sources": ["AA"],
        "scope_description_en": "Verify identity with e-KYC",
        "duration_days": 10,
        "created_by": "borrower",
    }
    create_resp = await client.post("/api/v1/consent/", json=payload)
    consent_id = create_resp.json()["id"]

    # 2. Revoke
    revoke_payload = {
        "revocation_reason": "User requested data deletion",
        "revoked_by": "borrower",
    }
    revoke_resp = await client.post(
        f"/api/v1/consent/{consent_id}/revoke", json=revoke_payload
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "REVOKED"

    # 3. Verify it is no longer valid
    verify_resp = await client.get(f"/api/v1/consent/{consent_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is False


@pytest.mark.asyncio
async def test_get_consent_audit_trail(
    client: AsyncClient, db_session: AsyncSession, sample_borrower: Borrower
) -> None:
    """Test getting chronological audit trail of consent events."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "consent_mode": "bank_sakhi_assisted",
        "data_sources": ["AA"],
        "scope_description_en": "English consent description requirement",
        "duration_days": 30,
        "created_by": "test_agent",
    }
    create_resp = await client.post("/api/v1/consent/", json=payload)
    consent_id = create_resp.json()["id"]

    # Retrieve audit trail
    audit_resp = await client.get(f"/api/v1/consent/{consent_id}/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total"] >= 1
    assert audit_data["entries"][0]["action"] == "CREATED"

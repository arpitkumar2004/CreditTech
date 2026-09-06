"""Comprehensive Horizontal & Vertical Privilege Escalation Tests.

Tests the persona security boundaries and tripwires defined in:
- docs/testing/persona_role_matrix.md
- docs/testing/data_access_matrix.md
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import (
    Borrower,
    ConsentAuditLog,
    ConsentRecord,
    FeatureSnapshot,
    Grievance,
    GrievanceAuditLog,
    Score,
    Village,
)
from services.core.shared.test_personas import (
    ADMIN_AMIT,
    BORROWER_MEENA_ID,
    BORROWER_RADHIKA_HEADERS,
    BORROWER_RADHIKA_ID,
    BORROWER_RAMU_HEADERS,
    BORROWER_RAMU_ID,
    CONSENT_RADHIKA_ID,
    GRIEVANCE_MEENA_ID,
    OFFICER_RAJESH,
    RISK_PRIYA,
    SAKHI_SUNITA,
    SCORE_RADHIKA_ID,
    SCORE_RAMU_ID,
    TRIPWIRE_BORROWER_HEADERS,
    TRIPWIRE_BORROWER_ID,
    TRIPWIRE_EXPIRED_CONSENT_ID,
    TRIPWIRE_REVOKED_CONSENT_ID,
    VILLAGE_ALPHA_ID,
    VILLAGE_BETA_ID,
)

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


@pytest.fixture
async def seeded_personas(db_session: AsyncSession) -> None:
    """Seed test database with canonical personas, scores, consents and grievances."""
    now = datetime.now(UTC)

    # 1. Villages
    v_alpha = Village(
        id=VILLAGE_ALPHA_ID,
        name="Tara Jivanpur",
        site_type="CANAL_IRRIGATED",
        state="Uttar Pradesh",
        district="Chandauli",
    )
    v_beta = Village(
        id=VILLAGE_BETA_ID,
        name="Adalhat Dryland",
        site_type="RAIN_FED",
        state="Uttar Pradesh",
        district="Mirzapur",
    )
    db_session.add_all([v_alpha, v_beta])
    await db_session.flush()

    # 2. Borrowers
    b_radhika = Borrower(
        id=BORROWER_RADHIKA_ID,
        aadhaar_ref_hash=hashlib.sha256(b"RADHIKA").hexdigest(),
        name_encrypted="enc:Radhika",
        phone_encrypted="enc:9876543210",
        village_id=VILLAGE_ALPHA_ID,
        gender="F",
        age=34,
        landholding_band="MARGINAL",
    )
    b_ramu = Borrower(
        id=BORROWER_RAMU_ID,
        aadhaar_ref_hash=hashlib.sha256(b"RAMU").hexdigest(),
        name_encrypted="enc:Ramu",
        phone_encrypted="enc:9876543212",
        village_id=VILLAGE_BETA_ID,
        gender="M",
        age=45,
        landholding_band="SMALL",
    )
    b_meena = Borrower(
        id=BORROWER_MEENA_ID,
        aadhaar_ref_hash=hashlib.sha256(b"MEENA").hexdigest(),
        name_encrypted="enc:Meena",
        phone_encrypted="enc:9876543213",
        village_id=VILLAGE_BETA_ID,
        gender="F",
        age=38,
        landholding_band="MARGINAL",
    )
    b_trap = Borrower(
        id=TRIPWIRE_BORROWER_ID,
        aadhaar_ref_hash=hashlib.sha256(b"TRAP").hexdigest(),
        name_encrypted="enc:Trap",
        phone_encrypted="enc:0000000000",
        village_id=VILLAGE_ALPHA_ID,
        gender="F",
        age=30,
        landholding_band="MARGINAL",
    )
    db_session.add_all([b_radhika, b_ramu, b_meena, b_trap])
    await db_session.flush()

    # 3. Consents (Active, Revoked, Expired)
    from services.core.config import get_settings
    settings = get_settings()
    salt = settings.consent_genesis_salt
    gen_payload = f"GENESIS:{salt}:{BORROWER_RADHIKA_ID}"
    genesis_radhika = hashlib.sha256(gen_payload.encode("utf-8")).hexdigest()

    issued_radhika = now - timedelta(days=10)
    expires_radhika = now + timedelta(days=180)
    data_sources_radhika = ["AA", "BUREAU", "GEOSPATIAL"]
    import json
    h_payload = json.dumps(
        {
            "borrower_id": str(BORROWER_RADHIKA_ID),
            "purpose": "credit_scoring",
            "data_sources": sorted(data_sources_radhika),
            "issued_at": issued_radhika.isoformat(),
            "expires_at": expires_radhika.isoformat(),
            "status": "ACTIVE",
            "prev_hash": genesis_radhika,
        },
        sort_keys=True,
    )
    hash_radhika = hashlib.sha256(h_payload.encode("utf-8")).hexdigest()

    c_radhika = ConsentRecord(
        id=CONSENT_RADHIKA_ID,
        borrower_id=BORROWER_RADHIKA_ID,
        purpose="credit_scoring",
        consent_mode="bank_sakhi_assisted",
        data_sources=data_sources_radhika,
        scope_description_en="Full credit appraisal",
        issued_at=issued_radhika,
        expires_at=expires_radhika,
        status="ACTIVE",
        hash_prev=genesis_radhika,
        hash_current=hash_radhika,
        created_by="system:seed",
    )
    c_revoked = ConsentRecord(
        id=TRIPWIRE_REVOKED_CONSENT_ID,
        borrower_id=BORROWER_RAMU_ID,
        purpose="credit_scoring",
        consent_mode="bank_sakhi_assisted",
        data_sources=["AA"],
        scope_description_en="Revoked consent test",
        issued_at=now - timedelta(days=10),
        expires_at=now + timedelta(days=180),
        status="REVOKED",
        hash_prev="genesis",
        hash_current="hash_revoked",
        created_by="system:seed",
    )
    c_expired = ConsentRecord(
        id=TRIPWIRE_EXPIRED_CONSENT_ID,
        borrower_id=BORROWER_MEENA_ID,
        purpose="credit_scoring",
        consent_mode="bank_sakhi_assisted",
        data_sources=["AA"],
        scope_description_en="Expired consent test",
        issued_at=now - timedelta(days=200),
        expires_at=now - timedelta(days=10),
        status="EXPIRED",
        hash_prev="genesis",
        hash_current="hash_expired",
        created_by="system:seed",
    )
    db_session.add_all([c_radhika, c_revoked, c_expired])
    await db_session.flush()

    # 4. Feature Snapshots & Scores
    snap_radhika = FeatureSnapshot(
        borrower_id=BORROWER_RADHIKA_ID,
        feature_version="v1.0.0",
        season_tag="KHARIF",
        sources_used=["AA", "GEOSPATIAL"],
        features_json={"shg_repayment_rate": 0.98},
    )
    snap_ramu = FeatureSnapshot(
        borrower_id=BORROWER_RAMU_ID,
        feature_version="v1.0.0",
        season_tag="KHARIF",
        sources_used=["GEOSPATIAL"],
        features_json={"shg_repayment_rate": 0.72},
    )
    db_session.add_all([snap_radhika, snap_ramu])
    await db_session.flush()

    score_radhika = Score(
        id=SCORE_RADHIKA_ID,
        borrower_id=BORROWER_RADHIKA_ID,
        feature_snapshot_id=snap_radhika.id,
        model_version="v1.1.0-woe-scorecard",
        score=78.5,
        confidence_lower=710,
        confidence_upper=770,
        sources_used=["AA", "GEOSPATIAL"],
        generated_at=now - timedelta(days=2),
    )
    score_ramu = Score(
        id=SCORE_RAMU_ID,
        borrower_id=BORROWER_RAMU_ID,
        feature_snapshot_id=snap_ramu.id,
        model_version="v1.1.0-woe-scorecard",
        score=48.0,
        confidence_lower=480,
        confidence_upper=530,
        sources_used=["GEOSPATIAL"],
        generated_at=now - timedelta(days=3),
    )
    db_session.add_all([score_radhika, score_ramu])
    await db_session.flush()

    # 5. Grievance for Meena
    g_meena = Grievance(
        id=GRIEVANCE_MEENA_ID,
        borrower_id=BORROWER_MEENA_ID,
        category="SCORE_DISPUTE",
        description="Neighboring canal agreement dispute",
        status="OPEN",
        sla_hours=168,
        created_at=now - timedelta(hours=12),
        due_at=now + timedelta(hours=156),
    )
    db_session.add(g_meena)
    await db_session.commit()


# ── 1. Horizontal Isolation Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_borrower_can_access_own_score(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Radhika Devi can retrieve her own credit score."""
    resp = await client.get(
        f"/api/v1/score/{SCORE_RADHIKA_ID}",
        headers=BORROWER_RADHIKA_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(SCORE_RADHIKA_ID)
    assert data["borrower_id"] == str(BORROWER_RADHIKA_ID)


@pytest.mark.asyncio
async def test_borrower_cannot_access_other_borrower_score(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Horizontal isolation tripwire: Radhika Devi cannot access Ramu Patel's score."""
    resp = await client.get(
        f"/api/v1/score/{SCORE_RAMU_ID}",
        headers=BORROWER_RADHIKA_HEADERS,
    )
    assert resp.status_code == 403
    assert "not authorized to view another borrower's score" in resp.text


@pytest.mark.asyncio
async def test_trap_borrower_denied_cross_access(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Horizontal isolation tripwire: Trap user cannot access Radhika's score."""
    resp = await client.get(
        f"/api/v1/score/{SCORE_RADHIKA_ID}",
        headers=TRIPWIRE_BORROWER_HEADERS,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_loan_officer_can_access_borrower_score(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Authorized Loan Officer (Rajesh Kumar) can review any borrower's score."""
    resp = await client.get(
        f"/api/v1/score/{SCORE_RADHIKA_ID}",
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(SCORE_RADHIKA_ID)


@pytest.mark.asyncio
async def test_borrower_grievance_horizontal_isolation(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Radhika cannot view Meena's grievance (403), Meena can (200), Officer can (200)."""
    # 1. Cross-borrower access -> 401 Unauthorized
    cross_resp = await client.get(
        f"/api/v1/grievances/{GRIEVANCE_MEENA_ID}",
        headers=BORROWER_RADHIKA_HEADERS,
    )
    assert cross_resp.status_code == 401

    # 2. Own borrower access -> 200
    meena_headers = {"X-Borrower-Id": str(BORROWER_MEENA_ID)}
    own_resp = await client.get(
        f"/api/v1/grievances/{GRIEVANCE_MEENA_ID}",
        headers=meena_headers,
    )
    assert own_resp.status_code == 200
    assert own_resp.json()["id"] == str(GRIEVANCE_MEENA_ID)

    # 3. Loan officer access -> 200
    officer_resp = await client.get(
        f"/api/v1/grievances/{GRIEVANCE_MEENA_ID}",
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert officer_resp.status_code == 200


# ── 2. Vertical Privilege Escalation Tests ─────────────────────────────────


@pytest.mark.asyncio
async def test_loan_officer_cannot_promote_model(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Vertical escalation tripwire: Loan Officer (OFF-001) cannot promote ML models."""
    resp = await client.post(
        "/api/v1/admin/models/v1.0.0-logistic/promote",
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert resp.status_code == 403
    assert "forbidden" in resp.text.lower()


@pytest.mark.asyncio
async def test_bank_sakhi_cannot_promote_model(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Vertical escalation tripwire: Bank Sakhi (SAKHI-001) cannot promote ML models."""
    resp = await client.post(
        "/api/v1/admin/models/v1.0.0-logistic/promote",
        headers=SAKHI_SUNITA.auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_promote_rejected(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Unauthenticated calls to /admin/models/.../promote return 401 Unauthorized."""
    resp = await client.post("/api/v1/admin/models/v1.0.0-logistic/promote")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_call_promote_endpoint(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Admin persona (ADMIN-001) has vertical authorization to trigger model promotion."""
    resp = await client.post(
        "/api/v1/admin/models/v1.0.0-logistic/promote",
        headers=ADMIN_AMIT.auth_headers,
    )
    # The promotion gate itself checks fairness/performance and returns 200 or 409,
    # but critically NOT 401 or 403 (authorization passed!).
    assert resp.status_code in {200, 409}


@pytest.mark.asyncio
async def test_bank_sakhi_cannot_record_loan_decision(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Bank Sakhi is restricted to assisted onboarding and cannot underwrite loan decisions."""
    payload = {
        "score_id": str(SCORE_RADHIKA_ID),
        "decision": "APPROVED",
        "officer_notes": "Attempted sakhi approval",
    }
    resp = await client.post(
        "/api/v1/decision/",
        json=payload,
        headers=SAKHI_SUNITA.auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_loan_officer_can_record_loan_decision(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Loan Officer (Rajesh Kumar) can record official underwriting decision."""
    payload = {
        "score_id": str(SCORE_RADHIKA_ID),
        "decision": "APPROVED",
        "officer_notes": "Verified good SHG track record",
    }
    resp = await client.post(
        "/api/v1/decision/",
        json=payload,
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["decision"] == "APPROVED"
    assert data["officer_id"] == OFFICER_RAJESH.id


# ── 3. Tripwire Consent Status Verification ────────────────────────────────


@pytest.mark.asyncio
async def test_tripwire_revoked_consent_fails_verification(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Consent verification tripwire: Revoked consent record is rejected."""
    resp = await client.get(f"/api/v1/consent/{TRIPWIRE_REVOKED_CONSENT_ID}/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["status"] == "REVOKED"


@pytest.mark.asyncio
async def test_tripwire_expired_consent_fails_verification(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Consent verification tripwire: Expired consent record is rejected."""
    resp = await client.get(f"/api/v1/consent/{TRIPWIRE_EXPIRED_CONSENT_ID}/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert data["status"] == "EXPIRED"


@pytest.mark.asyncio
async def test_active_consent_passes_verification(
    client: AsyncClient, seeded_personas: None
) -> None:
    """Active consent record for Radhika Devi passes cryptographic verification."""
    resp = await client.get(f"/api/v1/consent/{CONSENT_RADHIKA_ID}/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["status"] == "ACTIVE"
    assert data["hash_chain_valid"] is True


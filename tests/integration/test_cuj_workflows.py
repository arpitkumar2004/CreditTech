"""End-to-End Critical User Journey (CUJ) Workflow Tests.

Validates the 4 canonical user journeys with permanent test personas & data:
- CUJ-01: Field Ingestion & Scoring Journey (Bank Sakhi Sunita & Borrower Radhika)
- CUJ-02: Branch Underwriting, Override & Partner RE Handoff (Loan Officer Rajesh)
- CUJ-03: Score Dispute, SLA Clock & Officer Resolution (Borrower Meena & Officer Vikram)
- CUJ-04: MLOps Model Lifecycle & Governance Gating (Risk Officer Priya & Admin Amit)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.config import get_settings
from services.core.shared.models import (
    Borrower,
    ConsentRecord,
    FairnessAuditLog,
    FeatureSnapshot,
    Grievance,
    ReasonCode,
    Score,
    Village,
)
from services.core.shared.test_personas import (
    ADMIN_AMIT,
    BORROWER_MEENA_ID,
    BORROWER_RADHIKA_HEADERS,
    BORROWER_RADHIKA_ID,
    BORROWER_RAMU_ID,
    CONSENT_RADHIKA_ID,
    GRIEVANCE_MEENA_ID,
    OFFICER_RAJESH,
    OFFICER_VIKRAM,
    RISK_PRIYA,
    SAKHI_SUNITA,
    SCORE_RADHIKA_ID,
    SCORE_RAMU_ID,
    VILLAGE_ALPHA_ID,
    VILLAGE_BETA_ID,
)

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


@pytest.fixture
async def seeded_cuj_env(db_session: AsyncSession) -> None:
    """Seed permanent test environment with Cluster Alpha & Cluster Beta baselines."""
    now = datetime.now(UTC)
    settings = get_settings()

    # Villages
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

    # Borrowers
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
    db_session.add_all([b_radhika, b_ramu, b_meena])
    await db_session.flush()

    # Active Consent for Radhika
    salt = settings.consent_genesis_salt
    gen_payload = f"GENESIS:{salt}:{BORROWER_RADHIKA_ID}"
    genesis_radhika = hashlib.sha256(gen_payload.encode("utf-8")).hexdigest()

    issued = now - timedelta(days=5)
    expires = now + timedelta(days=180)
    data_sources = ["AA", "BUREAU", "GEOSPATIAL", "SHG_FPO"]
    h_payload = json.dumps(
        {
            "borrower_id": str(BORROWER_RADHIKA_ID),
            "purpose": "credit_scoring",
            "data_sources": sorted(data_sources),
            "issued_at": issued.isoformat(),
            "expires_at": expires.isoformat(),
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
        data_sources=data_sources,
        scope_description_en="Full credit appraisal",
        issued_at=issued,
        expires_at=expires,
        status="ACTIVE",
        hash_prev=genesis_radhika,
        hash_current=hash_radhika,
        created_by="system:seed",
    )
    db_session.add(c_radhika)
    await db_session.flush()

    # Fairness audit logs for CUJ-04
    for dim, grp, smp, rate in [
        ("GENDER", "F", 100, 0.68),
        ("GENDER", "M", 90, 0.70),
        ("GEOGRAPHY", "CANAL_IRRIGATED", 100, 0.72),
        ("GEOGRAPHY", "RAIN_FED", 90, 0.65),
    ]:
        db_session.add(
            FairnessAuditLog(
                period="2026-W36",
                dimension=dim,
                group_value=grp,
                sample_size=smp,
                approval_rate=rate,
                override_rate=0.04,
                status="OK",
                computed_at=now - timedelta(days=3),
            )
        )

    await db_session.commit()


# ── CUJ-01: Field Ingestion & Scoring Journey ──────────────────────────────


@pytest.mark.asyncio
async def test_cuj_01_field_ingestion_and_scoring(
    client: AsyncClient, seeded_cuj_env: None, db_session: AsyncSession
) -> None:
    """Bank Sakhi inputs SHG thrift, triggers feature snapshot, generates WoE score."""
    # 1. Bank Sakhi Sunita captures SHG thrift & agricultural land profile
    sakhi_payload = {
        "borrower_id": str(BORROWER_RADHIKA_ID),
        "shg_data": {
            "shg_name": "Tara Mahila SHG",
            "nabard_grade": "A",
            "membership_years": 4,
            "monthly_savings": 200.0,
            "total_savings": 9600.0,
            "loans_taken": 3,
            "loans_repaid": 3,
            "meeting_attendance_pct": 96.0,
        },
        "farmer_data": {
            "land_holding_acres": 1.8,
            "land_ownership": "OWN",
            "irrigation_access": True,
            "crop_type_primary": "Paddy",
            "estimated_monthly_income": 8500.0,
        },
        "created_by": SAKHI_SUNITA.id,
    }
    ingest_resp = await client.post("/api/v1/ingest/shg-fpo", json=sakhi_payload)
    assert ingest_resp.status_code == 201
    assert ingest_resp.json()["status"] == "success"

    # 2. Add realistic feature snapshot with all multi-rail variables
    features = {
        "shg_repayment_rate": 98.0,
        "shg_meeting_attendance_pct": 96.0,
        "shg_savings_consistency": 0.12,
        "shg_membership_years": 4.0,
        "utility_payment_ontime_pct": 98.0,
        "upi_transaction_regularity": 0.28,
        "estimated_crop_income_kharif": 55000.0,
        "estimated_crop_income_rabi": 65000.0,
        "income_stability_cv": 0.18,
        "monthly_avg_credit_inflow": 10500.0,
        "pm_kisan_regularity": 1.0,
        "shg_cumulative_savings": 9600.0,
        "bank_balance_avg_6m": 8200.0,
        "asset_score": 0.65,
        "land_holding_acres": 1.8,
        "irrigation_access": True,
        "land_quality_ndvi_avg": 0.72,
        "ndvi_trend_2season": 0.08,
        "rainfall_deviation_pct": 0.5,
        "crop_insurance_enrolled": True,
    }
    snap = FeatureSnapshot(
        borrower_id=BORROWER_RADHIKA_ID,
        feature_version="v1.0.0",
        features_json=features,
        season_tag="KHARIF",
        sources_used=["AA", "SHG_FPO", "GEOSPATIAL", "BUREAU"],
    )
    db_session.add(snap)
    await db_session.commit()

    # 3. Compute WoE Credit Score
    score_payload = {
        "borrower_id": str(BORROWER_RADHIKA_ID),
        "feature_snapshot_id": str(snap.id),
    }
    score_resp = await client.post("/api/v1/score/", json=score_payload)
    assert score_resp.status_code == 201
    score_data = score_resp.json()

    assert score_data["borrower_id"] == str(BORROWER_RADHIKA_ID)
    assert 300 <= score_data["score_900"] <= 900
    assert score_data["score_band"] in ["EXCELLENT", "GOOD", "MODERATE"]
    assert len(score_data["reason_codes"]) >= 2
    assert "localized_text_en" in score_data["reason_codes"][0]
    assert "localized_text_hi" in score_data["reason_codes"][0]

    # 4. Borrower Radhika views her own score via self-service
    radhika_view_resp = await client.get(
        f"/api/v1/score/{score_data['id']}",
        headers=BORROWER_RADHIKA_HEADERS,
    )
    assert radhika_view_resp.status_code == 200
    assert abs(radhika_view_resp.json()["score_900"] - score_data["score_900"]) <= 1


# ── CUJ-02: Branch Underwriting, Override & Partner RE Handoff ─────────────


@pytest.mark.asyncio
async def test_cuj_02_underwriting_and_partner_handoff(
    client: AsyncClient, seeded_cuj_env: None, db_session: AsyncSession
) -> None:
    """Loan Officer Rajesh reviews application, records underwriting decision, hands off to RE."""
    # 1. Setup Score for Radhika
    snap = FeatureSnapshot(
        borrower_id=BORROWER_RADHIKA_ID,
        feature_version="v1.0.0",
        features_json={"land_holding_acres": 1.8},
        season_tag="KHARIF",
        sources_used=["AA", "GEOSPATIAL"],
    )
    db_session.add(snap)
    await db_session.flush()

    score = Score(
        id=uuid.uuid4(),
        borrower_id=BORROWER_RADHIKA_ID,
        feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic",
        score=76.0,
        confidence_lower=72.0,
        confidence_upper=80.0,
        sources_used=["AA", "GEOSPATIAL"],
    )
    db_session.add(score)
    await db_session.flush()

    rc = ReasonCode(
        score_id=score.id,
        rank=1,
        feature_name="shg_repayment_rate",
        direction="POSITIVE",
        shap_value=0.35,
        localized_text_en="Excellent SHG repayment track record",
        localized_text_hi="उत्कृष्ट SHG पुनर्भुगतान ट्रैक रिकॉर्ड",
    )
    db_session.add(rc)
    await db_session.commit()

    # 2. Officer Rajesh retrieves review payload
    review_resp = await client.get(
        f"/api/v1/decision/review/{score.id}",
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    assert review_data["model_recommendation"] == "APPROVE"
    assert len(review_data["reason_codes"]) >= 1

    # 3. Officer Rajesh records official approval decision
    decision_payload = {
        "score_id": str(score.id),
        "decision": "APPROVED",
        "officer_notes": "Prompt SHG repayment and reliable canal irrigation access.",
    }
    decision_resp = await client.post(
        "/api/v1/decision/",
        json=decision_payload,
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert decision_resp.status_code == 201
    assert decision_resp.json()["officer_id"] == OFFICER_RAJESH.id

    # 4. Handoff to Partner Regulated Entity (State Bank of India)
    handoff_payload = {
        "score_id": str(score.id),
        "partner_re_id": "RE-SBI-01",
        "requested_amount": 50000.0,
        "requested_tenure_months": 12,
        "purpose": "Irrigation pump upgrade",
    }
    handoff_resp = await client.post(
        "/api/v1/handoff/submit",
        json=handoff_payload,
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert handoff_resp.status_code == 200
    handoff_data = handoff_resp.json()
    assert handoff_data["status"] == "SUBMITTED"
    assert handoff_data["loan_application_id"] is not None

    # 5. Verify immutable decision audit log
    audit_resp = await client.get(
        f"/api/v1/decision/audit/{score.id}",
        headers=OFFICER_RAJESH.auth_headers,
    )
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) == 1
    assert audit_resp.json()[0]["decision"] == "APPROVED"


# ── CUJ-03: Score Dispute, SLA Clock & Officer Resolution ──────────────────


@pytest.mark.asyncio
async def test_cuj_03_grievance_dispute_and_resolution(
    client: AsyncClient, seeded_cuj_env: None
) -> None:
    """Borrower Meena disputes score, 168h SLA clock starts, Officer Vikram resolves appeal."""
    # 1. Borrower Meena files grievance dispute
    meena_headers = {"X-Borrower-Id": str(BORROWER_MEENA_ID)}
    grievance_payload = {
        "borrower_id": str(BORROWER_MEENA_ID),
        "category": "SCORE_DISPUTE",
        "description": "Satellite vegetation index did not capture our local lift-irrigation pipeline.",
    }
    create_resp = await client.post(
        "/api/v1/grievances/",
        json=grievance_payload,
        headers=meena_headers,
    )
    assert create_resp.status_code == 201
    g_data = create_resp.json()
    grievance_id = g_data["id"]
    assert g_data["status"] == "OPEN"
    assert g_data["sla_hours"] == 168
    assert g_data["due_at"] is not None

    # 2. Officer Vikram inspects open grievances
    list_resp = await client.get(
        "/api/v1/grievances/?status=OPEN",
        headers=OFFICER_VIKRAM.auth_headers,
    )
    assert list_resp.status_code == 200
    assert any(g["id"] == grievance_id for g in list_resp.json())

    # 3. Officer Vikram resolves grievance after field verification
    update_payload = {
        "status": "RESOLVED",
        "resolution_notes": "Field verification by Bank Sakhi confirmed lift irrigation. Score updated.",
    }
    update_resp = await client.patch(
        f"/api/v1/grievances/{grievance_id}",
        json=update_payload,
        headers=OFFICER_VIKRAM.auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "RESOLVED"
    assert update_resp.json()["resolved_at"] is not None

    # 4. Verify immutable grievance audit log
    audit_resp = await client.get(
        f"/api/v1/grievances/{grievance_id}/audit",
        headers=OFFICER_VIKRAM.auth_headers,
    )
    assert audit_resp.status_code == 200
    entries = audit_resp.json()
    assert len(entries) >= 2
    assert entries[-1]["to_status"] == "RESOLVED"
    assert entries[-1]["actor"] == f"officer:{OFFICER_VIKRAM.id}"


# ── CUJ-04: MLOps Model Lifecycle & Governance Gating ──────────────────────


@pytest.mark.asyncio
async def test_cuj_04_mlops_governance_and_promotion(
    client: AsyncClient, seeded_cuj_env: None
) -> None:
    """Risk Officer Priya audits fairness parity; Admin Amit checks promotion eligibility."""
    # 1. Risk Officer Priya audits portfolio fairness metrics
    fairness_resp = await client.get(
        "/api/v1/dashboard/fairness?period=2026-W36",
        headers=RISK_PRIYA.auth_headers,
    )
    assert fairness_resp.status_code == 200
    fairness_data = fairness_resp.json()
    assert len(fairness_data["rows"]) >= 4

    # 2. Inspect ratified threshold manifest
    manifest_resp = await client.get(
        "/api/v1/admin/fairness/manifest",
        headers=RISK_PRIYA.auth_headers,
    )
    assert manifest_resp.status_code == 200
    assert "manifest_hash" in manifest_resp.json()

    # 3. Evaluate FairnessGate compliance
    gate_resp = await client.get(
        "/api/v1/admin/fairness/gate?period=2026-W36",
        headers=RISK_PRIYA.auth_headers,
    )
    assert gate_resp.status_code == 200
    assert "passed" in gate_resp.json()

    # 4. Admin Amit inspects candidate vs champion models
    models_resp = await client.get(
        "/api/v1/admin/models",
        headers=ADMIN_AMIT.auth_headers,
    )
    assert models_resp.status_code == 200
    models_list = models_resp.json()
    assert len(models_list) >= 1

    # 5. Check promotion gate eligibility dry run
    champ_version = models_list[0]["model_version"]
    check_resp = await client.get(
        f"/api/v1/admin/models/{champ_version}/promotion-check",
        headers=ADMIN_AMIT.auth_headers,
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()
    assert check_data["passed"] is True
    assert check_data["performance_pass"] is True
    assert check_data["fairness_pass"] is True

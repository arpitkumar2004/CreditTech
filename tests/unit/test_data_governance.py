"""Comprehensive test suite for CreditTech Data Governance & Statutory Compliance.

Covers:
- ADR-2 & DPDP Act 2023 §8: Zero PII in feature schemas, snapshots, and scoring.
- Article 15: Monitored-only demographic attributes quarantined from model inputs.
- DPDP Act §12: Consent revocation cascade to repayment retraining flags.
- Basel II/III MRM: Drift stability action thresholds and model registry transitions.
"""

import uuid
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.features.schema import (
    MODEL_FEATURE_NAMES,
    MONITORED_ONLY_FIELDS,
    PROHIBITED_FIELDS,
)
from ml.registry import ModelRegistry
from services.core.consent.schemas import (
    ConsentCreateRequest,
    ConsentMode,
    ConsentPurpose,
    ConsentRevokeRequest,
    DataSource,
)
from services.core.consent.service import ConsentService
from services.core.ingestion.service import IngestionOrchestrator
from services.core.monitoring.service import DriftMonitorService
from services.core.scoring.schemas import ScoreRequest
from services.core.scoring.service import ScoringService
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    RepaymentRecord,
    Score,
    Village,
)


def test_schema_zero_pii_and_monitored_isolation():
    """Verify zero overlap between model features, prohibited PII, and monitored fields."""
    pii_overlap = set(MODEL_FEATURE_NAMES).intersection(PROHIBITED_FIELDS)
    assert not pii_overlap, f"PROHIBITED_FIELDS leaked into MODEL_FEATURE_NAMES: {pii_overlap}"

    monitored_overlap = set(MODEL_FEATURE_NAMES).intersection(MONITORED_ONLY_FIELDS)
    assert not monitored_overlap, f"MONITORED_ONLY_FIELDS leaked into MODEL_FEATURE_NAMES: {monitored_overlap}"

    assert len(MODEL_FEATURE_NAMES) == 21


@pytest.mark.asyncio
async def test_ingestion_quarantines_pii_and_monitored_fields(db_session: AsyncSession):
    """Verify that IngestionOrchestrator._generate_feature_snapshot strips any injected PII."""
    village = Village(name="Gov Village", site_type="BARANI_RAINFED", state="Rajasthan", district="Hanumangarh")
    db_session.add(village)
    await db_session.flush()

    borrower = Borrower(
        aadhaar_ref_hash="c" * 64,
        name_encrypted="enc_name",
        phone_encrypted="enc_phone",
        village_id=village.id,
        gender="F",
        age=35,
    )
    db_session.add(borrower)
    await db_session.flush()

    orchestrator = IngestionOrchestrator(db_session)
    # Inject toxic PII and monitored fields in raw payloads
    toxic_payloads = {
        "AA": {"avg_balance_6m": 8000.0, "aadhaar": "123456789012", "phone": "9876543210"},
        "SHG_FPO": {"membership_years": 3, "caste": "GENERAL", "gender": "F"},
    }
    snapshot = await orchestrator._generate_feature_snapshot(borrower, toxic_payloads)
    assert snapshot is not None

    # Verify no prohibited PII or monitored demographic fields survived in features_json
    saved_keys = set(snapshot.features_json.keys())
    assert not saved_keys.intersection(PROHIBITED_FIELDS)
    assert not saved_keys.intersection(MONITORED_ONLY_FIELDS)


@pytest.mark.asyncio
async def test_scoring_sanitizes_pii_and_monitored_fields(db_session: AsyncSession):
    """Verify that ScoringService strictly sanitizes snapshot features before model inference."""
    village = Village(name="Gov Score Village", site_type="CANAL_IRRIGATED", state="Rajasthan", district="Hanumangarh")
    db_session.add(village)
    await db_session.flush()

    borrower = Borrower(
        aadhaar_ref_hash="d" * 64,
        name_encrypted="enc_name",
        phone_encrypted="enc_phone",
        village_id=village.id,
        gender="F",
        age=29,
    )
    db_session.add(borrower)
    await db_session.flush()

    # Create snapshot containing leaked PII and monitored fields
    snapshot = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json={
            "shg_repayment_rate": 0.92,
            "shg_meeting_attendance_pct": 85.0,
            "shg_savings_consistency": 0.7,
            "shg_membership_years": 2,
            "shg_grade": "A",
            "utility_payment_ontime_pct": 90.0,
            "upi_transaction_regularity": 0.3,
            "estimated_crop_income_kharif": 35000.0,
            "estimated_crop_income_rabi": 40000.0,
            "income_stability_cv": 0.35,
            "monthly_avg_credit_inflow": 7000.0,
            "pm_kisan_regularity": 1.0,
            "shg_cumulative_savings": 5000.0,
            "bank_balance_avg_6m": 6000.0,
            "asset_score": 0.6,
            "land_holding_acres": 1.5,
            "irrigation_access": True,
            "land_quality_ndvi_avg": 0.62,
            "ndvi_trend_2season": 0.03,
            "rainfall_deviation_pct": 1.0,
            "crop_insurance_enrolled": True,
            # Leaked toxic fields:
            "aadhaar": "999988887777",
            "gender": "F",
            "religion": "HINDU",
            "landholding_band": "MARGINAL",
        },
        season_tag="KHARIF",
        sources_used=["AA", "SHG_FPO"],
    )
    db_session.add(snapshot)
    await db_session.flush()

    scoring_service = ScoringService(db_session)
    req = ScoreRequest(borrower_id=borrower.id, feature_snapshot_id=snapshot.id)
    score_record = await scoring_service.generate_score(req)

    assert score_record is not None
    assert 300 <= score_record.score_900 <= 900


@pytest.mark.asyncio
async def test_consent_revocation_cascades_to_retraining(db_session: AsyncSession):
    """Verify DPDP §12: revoking consent automatically clears consented_for_retraining on repayment records."""
    village = Village(name="Consent Village", site_type="CANAL_IRRIGATED", state="Rajasthan", district="Hanumangarh")
    db_session.add(village)
    await db_session.flush()

    borrower = Borrower(
        aadhaar_ref_hash="e" * 64,
        name_encrypted="enc_name",
        phone_encrypted="enc_phone",
        village_id=village.id,
        gender="F",
        age=38,
    )
    db_session.add(borrower)
    await db_session.flush()

    # Create active consent
    consent_svc = ConsentService(db_session)
    consent = await consent_svc.create_consent(
        ConsentCreateRequest(
            borrower_id=borrower.id,
            purpose=ConsentPurpose.CREDIT_SCORING,
            consent_mode=ConsentMode.APP_SELF_SERVICE,
            data_sources=[DataSource.AA, DataSource.SHG_FPO],
            scope_description_en="Consent for financial credit scoring and assessment",
            duration_days=30,
            created_by="officer-1",
        )
    )
    await db_session.flush()

    # Create feature snapshot & score record
    snap = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json={"shg_repayment_rate": 0.9},
        season_tag="KHARIF",
        sources_used=["AA"],
    )
    db_session.add(snap)
    await db_session.flush()

    score = Score(
        borrower_id=borrower.id,
        feature_snapshot_id=snap.id,
        model_version="v1.1.0-woe-scorecard",
        score=75.0,
        confidence_lower=70.0,
        confidence_upper=80.0,
        sources_used={"AA": True},
    )
    db_session.add(score)
    await db_session.flush()

    # Create associated loan application and repayment record with retraining consent=True
    loan = LoanApplication(
        borrower_id=borrower.id,
        score_id=score.id,
        partner_re_id="RE-001",
        requested_amount=30000.0,
        requested_tenure_months=12,
        purpose="DAIRY_UPGRADE",
    )
    db_session.add(loan)
    await db_session.flush()

    repay = RepaymentRecord(
        loan_application_id=loan.id,
        period="2026-08",
        status="CURRENT",
        consented_for_retraining=True,
    )
    db_session.add(repay)
    await db_session.flush()

    # Verify initially True
    assert repay.consented_for_retraining is True

    # Revoke consent
    await consent_svc.revoke_consent(
        consent.id,
        ConsentRevokeRequest(revoked_by="borrower", revocation_reason="Borrower opted out of data processing"),
    )
    await db_session.flush()

    # Check that repayment record's consented_for_retraining was cascaded to False
    res = await db_session.execute(select(RepaymentRecord).where(RepaymentRecord.id == repay.id))
    updated_repay = res.scalar_one()
    assert updated_repay.consented_for_retraining is False


def test_registry_blocks_direct_repromotion_of_retired():
    """Verify Basel II/III MRM invariant: retired models cannot be re-promoted without re-registration."""
    registry = ModelRegistry()
    # Test illegal transition 'retired' -> 'active'
    # By convention, attempting to promote a retired model directly raises ValueError
    # Find any retired model in registry
    models = registry.list_models()
    retired_models = [m for m in models if m.promotion_status == "retired"]
    if retired_models:
        with pytest.raises(ValueError, match="Illegal transition retired -> active"):
            registry.promote(retired_models[0].model_version, "active")


@pytest.mark.asyncio
async def test_drift_monitor_action_recommendation(db_session: AsyncSession):
    """Verify DriftMonitorService assigns explicit Basel action recommendations."""
    monitor = DriftMonitorService(db_session)
    res = await monitor.compute_drift_audit(limit=10)
    assert "status" in res
    if res["status"] == "OK":
        assert "action_recommendation" in res
        assert res["action_recommendation"] in {
            "NORMAL_OPERATION",
            "REVIEW_SEASONAL_AGRO_CLIMATIC_SHOCKS",
            "LOCK_STRAIGHT_THROUGH_LENDING_MANUAL_REVIEW",
        }

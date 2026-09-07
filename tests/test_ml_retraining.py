"""Unit tests for Closed-Loop DPDP-Consented Retraining Pipeline."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ml.registry import ModelRegistry
from ml.training.retrain import DPDPRetrainingPipeline
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    RepaymentRecord,
    Score,
    Village,
)


@pytest.fixture
async def seeded_repayment_records(db_session: AsyncSession) -> dict[str, int]:
    # Seed a village
    village = Village(
        name="Retrain Village",
        site_type="CANAL_IRRIGATED",
        state="Rajasthan",
        district="Hanumangarh",
        agro_climatic_zone="CANAL_IRRIGATED_NORTH",
    )
    db_session.add(village)
    await db_session.flush()

    # Seed 2 borrowers: one consents for retraining, one does NOT
    b_consented = Borrower(
        aadhaar_ref_hash="c" * 64,
        name_encrypted="name_c", phone_encrypted="phone_c",
        village_id=village.id, gender="F", age=30, landholding_band="MARGINAL",
    )
    b_unconsented = Borrower(
        aadhaar_ref_hash="u" * 64,
        name_encrypted="name_u", phone_encrypted="phone_u",
        village_id=village.id, gender="M", age=45, landholding_band="SMALL",
    )
    db_session.add_all([b_consented, b_unconsented])
    await db_session.flush()

    # Snapshots
    sample_features = {
        "shg_repayment_rate": 0.95,
        "shg_meeting_attendance_pct": 90.0,
        "shg_savings_consistency": 0.7,
        "shg_membership_years": 4,
        "shg_grade": "A",
        "utility_payment_ontime_pct": 92.0,
        "upi_transaction_regularity": 0.5,
        "estimated_crop_income_kharif": 45000.0,
        "estimated_crop_income_rabi": 50000.0,
        "income_stability_cv": 0.30,
        "monthly_avg_credit_inflow": 8000.0,
        "pm_kisan_regularity": 1.0,
        "shg_cumulative_savings": 6000.0,
        "bank_balance_avg_6m": 7000.0,
        "asset_score": 0.6,
        "land_holding_acres": 2.5,
        "irrigation_access": True,
        "land_quality_ndvi_avg": 0.65,
        "ndvi_trend_2season": 0.05,
        "rainfall_deviation_pct": 0.0,
        "crop_insurance_enrolled": True,
    }

    snap_c = FeatureSnapshot(
        borrower_id=b_consented.id,
        feature_version="v1.0.0",
        features_json=sample_features,
        season_tag="RABI",
        sources_used=["AA", "SHG_FPO"],
    )
    snap_u = FeatureSnapshot(
        borrower_id=b_unconsented.id,
        feature_version="v1.0.0",
        features_json=sample_features,
        season_tag="RABI",
        sources_used=["AA", "SHG_FPO"],
    )
    db_session.add_all([snap_c, snap_u])
    await db_session.flush()

    # Scores
    score_c = Score(
        borrower_id=b_consented.id,
        feature_snapshot_id=snap_c.id,
        model_version="v1.1.0-woe-scorecard",
        score=75.0, confidence_lower=70.0, confidence_upper=80.0,
    )
    score_u = Score(
        borrower_id=b_unconsented.id,
        feature_snapshot_id=snap_u.id,
        model_version="v1.1.0-woe-scorecard",
        score=65.0, confidence_lower=60.0, confidence_upper=70.0,
    )
    db_session.add_all([score_c, score_u])
    await db_session.flush()

    # Loan Applications
    app_c = LoanApplication(
        borrower_id=b_consented.id,
        score_id=score_c.id,
        partner_re_id="RE-001",
        requested_amount=50000.0,
        requested_tenure_months=12,
        purpose="Agri Inputs",
        officer_decision="APPROVED",
    )
    app_u = LoanApplication(
        borrower_id=b_unconsented.id,
        score_id=score_u.id,
        partner_re_id="RE-001",
        requested_amount=40000.0,
        requested_tenure_months=12,
        purpose="Livestock",
        officer_decision="APPROVED",
    )
    db_session.add_all([app_c, app_u])
    await db_session.flush()

    # Repayment Records: Consented vs Unconsented
    rep_c = RepaymentRecord(
        loan_application_id=app_c.id,
        period="2026-M06",
        status="CURRENT",
        consented_for_retraining=True,  # Explicit DPDP Consent
    )
    rep_u = RepaymentRecord(
        loan_application_id=app_u.id,
        period="2026-M06",
        status="CURRENT",
        consented_for_retraining=False,  # NO Consent
    )
    db_session.add_all([rep_c, rep_u])
    await db_session.commit()

    return {"consented": 1, "unconsented": 1}


@pytest.mark.asyncio
async def test_dpdp_consent_filter(db_session: AsyncSession, seeded_repayment_records):
    pipeline = DPDPRetrainingPipeline(db_session)
    X, y, sensitive, n_consented = await pipeline.extract_consented_data()

    # Exactly 1 consented record should be extracted
    assert n_consented == 1
    assert len(X) == 1
    assert len(y) == 1
    assert y.iloc[0] == 1  # CURRENT -> 1 (repay)
    assert sensitive.iloc[0]["gender"] == "F"


@pytest.mark.asyncio
async def test_retraining_pipeline_execution(db_session: AsyncSession, tmp_path):
    registry = ModelRegistry(store=tmp_path / "registry")
    pipeline = DPDPRetrainingPipeline(db_session, registry=registry)

    # Run retraining (will use augmented synthetic anchor because n_consented < 20)
    result = await pipeline.run_retraining(
        model_type="woe",
        target_version_tag="v1.2.0-test-retrain",
    )

    assert result.status == "SUCCESS"
    assert result.model_version == "v1.2.0-test-retrain"
    assert result.cv_auc >= 0.50
    assert result.registered is True

    # Verify registration in ModelRegistry
    saved_record = registry.get("v1.2.0-test-retrain")
    assert saved_record is not None
    assert saved_record.promotion_status == "candidate"
    assert "consented_records_used" in saved_record.training_dataset["transformations"][0]

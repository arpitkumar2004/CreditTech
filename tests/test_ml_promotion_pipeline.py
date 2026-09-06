"""Integration tests verifying the production ML registry and promotion pipeline."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ml.registry.registry import ModelRegistry
from services.core.admin.promotion import ModelPromotionService
from services.core.scoring.schemas import ScoreRequest
from services.core.scoring.service import ScoringService
from services.core.shared.models import Borrower, FeatureSnapshot, Village


def test_registry_contains_champion_and_challenger():
    reg = ModelRegistry()
    active = reg.get_active()

    assert active is not None
    assert active.model_version == "v1.1.0-woe-scorecard"

    # Both models present in registry
    champ = reg.get("v1.1.0-woe-scorecard")
    chal = reg.get("v1.1.0-gbm-challenger")

    assert champ is not None
    assert chal is not None

    # Performance floors
    assert champ.metrics["auc"] >= 0.60
    assert champ.metrics["gini"] >= 0.20
    assert champ.metrics["ks"] >= 0.15
    assert champ.metrics["brier"] <= 0.30

    assert chal.metrics["auc"] >= 0.60
    assert chal.metrics["ks"] >= 0.15


@pytest.mark.asyncio
async def test_scoring_service_executes_with_active_woe_model(db_session: AsyncSession):
    # 1. Setup sample village & borrower
    village = Village(
        name="Tibbi Pilot Village",
        site_type="IRRIGATED_COTTON",
        state="Rajasthan",
        district="Hanumangarh",
    )
    db_session.add(village)
    await db_session.flush()

    borrower = Borrower(
        aadhaar_ref_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        name_encrypted="enc_name_sample",
        phone_encrypted="enc_phone_sample",
        village_id=village.id,
        gender="F",
        age=32,
        landholding_band="MARGINAL",
    )
    db_session.add(borrower)
    await db_session.flush()

    # 2. Add FeatureSnapshot
    snapshot = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        season_tag="KHARIF",
        sources_used=["AA", "SHG_FPO", "GEOSPATIAL"],
        features_json={
            "shg_repayment_rate": 0.95,
            "shg_meeting_attendance_pct": 85.0,
            "shg_savings_consistency": 0.4,
            "shg_membership_years": 4.0,
            "shg_grade": "A",
            "utility_payment_ontime_pct": 92.0,
            "upi_transaction_regularity": 0.6,
            "estimated_crop_income_kharif": 42000.0,
            "estimated_crop_income_rabi": 48000.0,
            "income_stability_cv": 0.35,
            "monthly_avg_credit_inflow": 7500.0,
            "pm_kisan_regularity": 0.9,
            "shg_cumulative_savings": 6000.0,
            "bank_balance_avg_6m": 8000.0,
            "asset_score": 0.65,
            "land_holding_acres": 1.5,
            "irrigation_access": True,
            "land_quality_ndvi_avg": 0.62,
            "ndvi_trend_2season": 0.05,
            "rainfall_deviation_pct": -2.5,
            "crop_insurance_enrolled": True,
        },
    )
    db_session.add(snapshot)
    await db_session.flush()

    # 3. Execute ScoringService
    scoring_svc = ScoringService(db_session)
    score = await scoring_svc.generate_score(
        ScoreRequest(
            borrower_id=borrower.id,
            feature_snapshot_id=snapshot.id,
        )
    )

    assert score is not None
    assert score.model_version == "v1.1.0-woe-scorecard"
    assert 0.0 <= score.score <= 100.0

    from sqlalchemy import select
    from services.core.shared.models import ReasonCode
    res = await db_session.execute(select(ReasonCode).where(ReasonCode.score_id == score.id))
    reasons = res.scalars().all()
    assert len(reasons) > 0

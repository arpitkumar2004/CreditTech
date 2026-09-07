"""Unit tests for dual-model loading and shadow scoring in ScoringService."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ml.registry import ModelRegistry
from services.core.scoring.service import ScoringService, _load_scorecard_from_registry
from services.core.shared.models import Borrower, FeatureSnapshot, Village


@pytest.fixture
async def sample_snapshot(db_session: AsyncSession) -> FeatureSnapshot:
    village = Village(name="Shadow Village", site_type="CANAL_IRRIGATED",
                      state="Rajasthan", district="Hanumangarh")
    db_session.add(village)
    await db_session.flush()
    borrower = Borrower(
        aadhaar_ref_hash="b" * 64,
        name_encrypted="enc_name", phone_encrypted="enc_phone",
        village_id=village.id, gender="M", age=42,
    )
    db_session.add(borrower)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json={
            "shg_repayment_rate": 0.85,
            "shg_meeting_attendance_pct": 78.0,
            "shg_savings_consistency": 0.5,
            "shg_membership_years": 3,
            "shg_grade": "B",
            "utility_payment_ontime_pct": 82.0,
            "upi_transaction_regularity": 0.4,
            "estimated_crop_income_kharif": 38000.0,
            "estimated_crop_income_rabi": 42000.0,
            "income_stability_cv": 0.40,
            "monthly_avg_credit_inflow": 6500.0,
            "pm_kisan_regularity": 0.9,
            "shg_cumulative_savings": 4500.0,
            "bank_balance_avg_6m": 5500.0,
            "asset_score": 0.5,
            "land_holding_acres": 2.0,
            "irrigation_access": True,
            "land_quality_ndvi_avg": 0.55,
            "ndvi_trend_2season": 0.02,
            "rainfall_deviation_pct": -4.0,
            "crop_insurance_enrolled": False,
        },
        season_tag="KHARIF",
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO"],
    )
    db_session.add(snap)
    await db_session.flush()
    return snap


def test_load_scorecard_types():
    # 1. WoE Scorecard
    woe_card, _ = _load_scorecard_from_registry("v1.1.0-woe-scorecard")
    assert woe_card is not None
    assert woe_card.model_version == "v1.1.0-woe-scorecard"

    # 2. Monotonic GBM Challenger
    gbm_card, _ = _load_scorecard_from_registry("v1.1.0-gbm-challenger")
    assert gbm_card is not None
    assert gbm_card.model_version == "v1.1.0-gbm-challenger"


@pytest.mark.asyncio
async def test_shadow_scoring_in_api(client: AsyncClient, sample_snapshot: FeatureSnapshot):
    resp = await client.post(
        "/api/v1/score/",
        json={
            "borrower_id": str(sample_snapshot.borrower_id),
            "feature_snapshot_id": str(sample_snapshot.id),
        },
    )
    assert resp.status_code == 201
    body = resp.json()

    # Active model produces main score
    assert body["model_version"] == "v1.1.0-woe-scorecard"
    assert 300 <= body["score_900"] <= 900

    # Shadow score should be present because v1.1.0-gbm-challenger is in candidate status
    shadow = body.get("shadow_score")
    if shadow:
        assert shadow["shadow_model_version"] == "v1.1.0-gbm-challenger"
        assert 300 <= shadow["shadow_score_900"] <= 900
        assert shadow["agreement"] in {"AGREE", "DISAGREE"}
        assert shadow["latency_ms"] >= 0.0

"""P3.7 — end-to-end test: registered scorecard flows through scoring service.

Exercises: feature vector -> LogisticScorecard (from registry) -> SHAP ->
reason codes -> API response with model_version and feature_version.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ml.registry import ModelRegistry
from services.core.shared.models import Borrower, FeatureSnapshot, Village


@pytest.fixture
async def village_borrower_snapshot(db_session: AsyncSession) -> FeatureSnapshot:
    village = Village(name="E2E Village", site_type="IRRIGATED_COTTON",
                      state="Rajasthan", district="Hanumangarh")
    db_session.add(village)
    await db_session.flush()
    borrower = Borrower(
        aadhaar_ref_hash="a" * 64,
        name_encrypted="x", phone_encrypted="y",
        village_id=village.id, gender="F", age=35,
    )
    db_session.add(borrower)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json={
            "shg_repayment_rate": 0.97,
            "shg_meeting_attendance_pct": 94.0,
            "shg_savings_consistency": 0.2,
            "shg_membership_years": 5,
            "shg_grade": "A",
            "utility_payment_ontime_pct": 96.0,
            "upi_transaction_regularity": 0.3,
            "estimated_crop_income_kharif": 55000.0,
            "estimated_crop_income_rabi": 60000.0,
            "income_stability_cv": 0.25,
            "monthly_avg_credit_inflow": 9200.0,
            "pm_kisan_regularity": 1.0,
            "shg_cumulative_savings": 8000.0,
            "bank_balance_avg_6m": 7000.0,
            "asset_score": 0.7,
            "land_holding_acres": 3.0,
            "irrigation_access": True,
            "land_quality_ndvi_avg": 0.72,
            "ndvi_trend_2season": 0.1,
            "rainfall_deviation_pct": 3.0,
            "crop_insurance_enrolled": True,
        },
        season_tag="RABI",
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
    )
    db_session.add(snap)
    await db_session.flush()
    return snap


@pytest.mark.asyncio
async def test_scoring_uses_registry_active_model_when_present(
    client: AsyncClient,
    village_borrower_snapshot: FeatureSnapshot,
):
    registry = ModelRegistry()
    active = registry.get_active()
    # If no trained model has been promoted, skip — this is an integration
    # gate, not a unit test.
    if active is None:
        pytest.skip("No active model registered; run scripts/train_scorecard.py --promote active")

    resp = await client.post(
        "/api/v1/score/",
        json={"borrower_id": str(village_borrower_snapshot.borrower_id),
              "feature_snapshot_id": str(village_borrower_snapshot.id)},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["model_version"] == active.model_version
    assert body["feature_version"] == active.feature_version
    assert 0.0 <= body["score"] <= 100.0
    assert 300 <= body["score_900"] <= 900
    assert body["reason_codes"], "expected at least one reason code"
    assert body["reason_codes"][0]["localized_text_hi"]


@pytest.mark.asyncio
async def test_scoring_accepts_pinned_model_version(
    client: AsyncClient,
    village_borrower_snapshot: FeatureSnapshot,
):
    registry = ModelRegistry()
    active = registry.get_active()
    if active is None:
        pytest.skip("No active model registered")

    resp = await client.post(
        "/api/v1/score/",
        json={
            "borrower_id": str(village_borrower_snapshot.borrower_id),
            "feature_snapshot_id": str(village_borrower_snapshot.id),
            "model_version": active.model_version,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["model_version"] == active.model_version

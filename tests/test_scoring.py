"""Unit tests for the Credit Scoring Service, Scorecard Model, and Router."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.scoring.service import ScoringService
from services.core.shared.models import Borrower, FeatureSnapshot, Village


@pytest.fixture
async def sample_village(db_session: AsyncSession) -> Village:
    """Create a sample village."""
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
    """Create a sample borrower."""
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
    """Create a feature snapshot with typical borrower features."""
    features = {
        "shg_repayment_rate": 95.0,
        "shg_meeting_attendance_pct": 92.0,
        "shg_savings_consistency": 0.15,
        "shg_membership_years": 3.0,
        "utility_payment_ontime_pct": 98.0,
        "upi_transaction_regularity": 0.25,
        "estimated_crop_income_kharif": 50000.0,
        "estimated_crop_income_rabi": 60000.0,
        "income_stability_cv": 0.2,
        "monthly_avg_credit_inflow": 9500.0,
        "pm_kisan_regularity": 1.0,
        "shg_cumulative_savings": 6500.0,
        "bank_balance_avg_6m": 7200.0,
        "asset_score": 0.6,
        "land_holding_acres": 2.5,
        "irrigation_access": True,
        "land_quality_ndvi_avg": 0.75,
        "ndvi_trend_2season": 0.05,
        "rainfall_deviation_pct": 1.5,
        "crop_insurance_enrolled": True,
    }
    snapshot = FeatureSnapshot(
        borrower_id=sample_borrower.id,
        feature_version="v1.0.0",
        features_json=features,
        season_tag="RABI",
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
    )
    db_session.add(snapshot)
    await db_session.flush()
    return snapshot


@pytest.mark.asyncio
async def test_generate_score_success(
    client: AsyncClient, sample_borrower: Borrower, sample_feature_snapshot: FeatureSnapshot
) -> None:
    """Test generating a credit score through the endpoint."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "feature_snapshot_id": str(sample_feature_snapshot.id),
    }
    response = await client.post("/api/v1/score/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["borrower_id"] == str(sample_borrower.id)
    assert data["feature_snapshot_id"] == str(sample_feature_snapshot.id)
    assert 0.0 <= data["score"] <= 100.0
    assert 300 <= data["score_900"] <= 900
    assert data["score_band"] in ["EXCELLENT", "GOOD", "MODERATE", "HIGH_RISK", "VERY_HIGH_RISK"]
    assert len(data["reason_codes"]) >= 1
    assert "localized_text_en" in data["reason_codes"][0]
    assert "localized_text_hi" in data["reason_codes"][0]


@pytest.mark.asyncio
async def test_get_score_by_id(
    client: AsyncClient, sample_borrower: Borrower, sample_feature_snapshot: FeatureSnapshot
) -> None:
    """Test retrieving generated score history by ID."""
    # 1. Create a score
    payload = {
        "borrower_id": str(sample_borrower.id),
        "feature_snapshot_id": str(sample_feature_snapshot.id),
    }
    create_resp = await client.post("/api/v1/score/", json=payload)
    assert create_resp.status_code == 201
    score_id = create_resp.json()["id"]

    # 2. Retrieve by ID
    get_resp = await client.get(f"/api/v1/score/{score_id}")
    assert get_resp.status_code == 200

    data = get_resp.json()
    assert data["id"] == score_id
    assert len(data["reason_codes"]) >= 1
    assert data["reason_codes"][0]["localized_text_en"] is not None


@pytest.mark.parametrize(
    "score,expected_band",
    [
        (85.0, "EXCELLENT"),
        (72.0, "GOOD"),
        (55.0, "MODERATE"),
        (45.0, "HIGH_RISK"),
        (25.0, "VERY_HIGH_RISK"),
    ],
)
def test_score_band_mappings(score: float, expected_band: str) -> None:
    """Verify numeric to categorical score bands maps correctly."""
    assert ScoringService.get_score_band(score) == expected_band

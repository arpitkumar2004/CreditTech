"""Unit tests for the Ingestion Service, Connectors, and Routers."""

from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.ingestion.schemas import IngestionSource, IngestionStatus
from services.core.shared.models import Borrower, ConsentRecord, Village


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
async def active_consent(db_session: AsyncSession, sample_borrower: Borrower) -> ConsentRecord:
    """Create an active consent record covering all sources."""
    consent = ConsentRecord(
        borrower_id=sample_borrower.id,
        purpose="credit_scoring",
        consent_mode="bank_sakhi_assisted",
        data_sources=["AA", "GEOSPATIAL", "BUREAU", "SHG_FPO"],
        scope_description_en="I consent to share AA, geospatial, bureau and SHG details.",
        expires_at=datetime.now(UTC) + pytest.importorskip("datetime").timedelta(days=30),
        status="ACTIVE",
        hash_prev="genesis",
        hash_current="current",
        created_by="sakhi",
    )
    db_session.add(consent)
    await db_session.flush()
    return consent


@pytest.mark.asyncio
async def test_trigger_ingestion_success(
    client: AsyncClient, sample_borrower: Borrower, active_consent: ConsentRecord
) -> None:
    """Test successful data aggregation trigger endpoint with all mocks responding."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "data_sources": ["AA", "GEOSPATIAL", "BUREAU"],
    }
    # Override settings for dev mock endpoints (since the router mounts /mock internally)
    with patch("services.core.ingestion.connectors.settings.aa_base_url", "http://testserver/api/v1/mock/aa"), \
         patch("services.core.ingestion.connectors.settings.geospatial_base_url", "http://testserver/api/v1/mock/geospatial"), \
         patch("services.core.ingestion.connectors.settings.bureau_base_url", "http://testserver/api/v1/mock/bureau"):

        response = await client.post("/api/v1/ingest/trigger", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["borrower_id"] == str(sample_borrower.id)
        assert data["overall_status"] == "SUCCESS"
        assert len(data["sources"]) == 4  # AA, GEOSPATIAL, BUREAU, plus internal SHG_FPO
        assert data["feature_snapshot_id"] is not None


@pytest.mark.asyncio
async def test_trigger_ingestion_graceful_degradation(
    client: AsyncClient, sample_borrower: Borrower, active_consent: ConsentRecord
) -> None:
    """Test that a timeout/failure in one connector (e.g. Geospatial) does not crash the overall pipeline."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "data_sources": ["AA", "GEOSPATIAL"],
    }

    # Mock Geospatial client to raise a timeout, but AA client succeeds
    with patch("services.core.ingestion.connectors.settings.aa_base_url", "http://testserver/api/v1/mock/aa"), \
         patch("services.core.ingestion.connectors.GeospatialConnector.fetch_satellite_data", new_callable=AsyncMock) as mock_geo:

        mock_geo.side_effect = Exception("Geospatial connection timed out")

        response = await client.post("/api/v1/ingest/trigger", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["borrower_id"] == str(sample_borrower.id)
        assert data["overall_status"] == "PARTIAL"

        # Verify status per source
        sources = {s["source"]: s["status"] for s in data["sources"]}
        assert sources[IngestionSource.AA.value] == IngestionStatus.SUCCESS.value
        assert sources[IngestionSource.GEOSPATIAL.value] == IngestionStatus.FAILED.value
        assert data["feature_snapshot_id"] is not None  # Snapshot still generated with remaining features


@pytest.mark.parametrize(
    "down_source,down_patch_target",
    [
        (IngestionSource.AA, "services.core.ingestion.connectors.AccountAggregatorConnector.fetch_bank_data"),
        (IngestionSource.GEOSPATIAL, "services.core.ingestion.connectors.GeospatialConnector.fetch_satellite_data"),
        (IngestionSource.BUREAU, "services.core.ingestion.connectors.BureauConnector.fetch_credit_profile"),
    ],
)
@pytest.mark.asyncio
async def test_graceful_degradation_every_single_rail_down(
    client: AsyncClient,
    sample_borrower: Borrower,
    active_consent: ConsentRecord,
    down_source: IngestionSource,
    down_patch_target: str,
) -> None:
    """P2 DoD: graceful degradation for every single-rail-down combination.

    Requests all three external rails; forces exactly one to fail; verifies the
    other two succeed, overall status is PARTIAL, and a feature snapshot is still
    produced from the surviving rails.
    """
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "data_sources": ["AA", "GEOSPATIAL", "BUREAU"],
    }
    with patch("services.core.ingestion.connectors.settings.aa_base_url", "http://testserver/api/v1/mock/aa"), \
         patch("services.core.ingestion.connectors.settings.geospatial_base_url", "http://testserver/api/v1/mock/geospatial"), \
         patch("services.core.ingestion.connectors.settings.bureau_base_url", "http://testserver/api/v1/mock/bureau"), \
         patch(down_patch_target, new_callable=AsyncMock) as mock_fail:
        mock_fail.side_effect = Exception(f"{down_source.value} rail down")

        response = await client.post("/api/v1/ingest/trigger", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "PARTIAL"
        sources = {s["source"]: s["status"] for s in data["sources"]}
        assert sources[down_source.value] == IngestionStatus.FAILED.value
        for other in (IngestionSource.AA, IngestionSource.GEOSPATIAL, IngestionSource.BUREAU):
            if other != down_source:
                assert sources[other.value] == IngestionStatus.SUCCESS.value, (
                    f"expected {other.value} to survive when {down_source.value} is down"
                )
        assert data["feature_snapshot_id"] is not None


@pytest.mark.asyncio
async def test_graceful_degradation_all_rails_down(
    client: AsyncClient, sample_borrower: Borrower, active_consent: ConsentRecord
) -> None:
    """When every external rail fails, the pipeline reports FAILED but does not crash."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "purpose": "credit_scoring",
        "data_sources": ["AA", "GEOSPATIAL", "BUREAU"],
    }
    with patch("services.core.ingestion.connectors.AccountAggregatorConnector.fetch_bank_data", new_callable=AsyncMock) as mock_aa, \
         patch("services.core.ingestion.connectors.GeospatialConnector.fetch_satellite_data", new_callable=AsyncMock) as mock_geo, \
         patch("services.core.ingestion.connectors.BureauConnector.fetch_credit_profile", new_callable=AsyncMock) as mock_bur:
        mock_aa.side_effect = Exception("AA down")
        mock_geo.side_effect = Exception("Geo down")
        mock_bur.side_effect = Exception("Bureau down")

        response = await client.post("/api/v1/ingest/trigger", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "FAILED"


@pytest.mark.asyncio
async def test_shg_fpo_manual_data_upload(client: AsyncClient, sample_borrower: Borrower) -> None:
    """Test uploading manual entry details captured by Bank Sakhi."""
    payload = {
        "borrower_id": str(sample_borrower.id),
        "shg_data": {
            "shg_name": "Marudhara Mahila",
            "nabard_grade": "A",
            "membership_years": 3,
            "monthly_savings": 150.0,
            "total_savings": 4500.0,
            "loans_taken": 2,
            "loans_repaid": 2,
            "meeting_attendance_pct": 98.0
        },
        "farmer_data": {
            "land_holding_acres": 2.5,
            "land_ownership": "OWN",
            "irrigation_access": True,
            "crop_type_primary": "Cotton",
            "estimated_monthly_income": 7200.0
        },
        "created_by": "sakhi_user"
    }
    response = await client.post("/api/v1/ingest/shg-fpo", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"

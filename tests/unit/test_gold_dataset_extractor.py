"""Unit tests for Consent-Gated Gold Dataset Extractor and Parquet Support.

Validates:
- Canonical 5-table relational join: RepaymentRecord -> LoanApplication -> Score -> FeatureSnapshot + Borrower + Village
- Strict DPDP Consent Filter (consented_for_retraining == True)
- Maturity window filtering (disbursed_at <= maturity_cutoff)
- Target labeling ($Y \\in \\{0, 1\\}$) and exclusion of transitional DPD
- Zero-PII assertions enforcing PROHIBITED_FIELDS exclusion
- Feature flattening into columns matching MODEL_FEATURE_NAMES
- Parquet and CSV export functionality with metadata JSON
- Dry-run CLI execution without file emission
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ml.features.schema import MODEL_FEATURE_NAMES, PROHIBITED_FIELDS
from scripts.extract_gold_dataset import (
    export_dataset,
    extract_gold_dataset,
    run_extraction,
)
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    RepaymentRecord,
    Score,
    Village,
)


async def _create_test_hierarchy(
    db: AsyncSession,
    *,
    status: str = "CURRENT",
    consented: bool = True,
    decided_at: datetime | None = None,
    features_json: dict | None = None,
) -> tuple[Village, Borrower, FeatureSnapshot, Score, LoanApplication, RepaymentRecord]:
    """Helper to create a full 5-table joined test hierarchy."""
    uid = uuid.uuid4().hex[:8]

    village = Village(
        id=uuid.uuid4(),
        name=f"Village_{uid}",
        site_type="PILOT",
        state="Uttar Pradesh",
        district="Chandauli",
        agro_climatic_zone="Middle Gangetic Plain",
    )
    db.add(village)
    await db.flush()

    borrower = Borrower(
        id=uuid.uuid4(),
        village_id=village.id,
        aadhaar_ref_hash=f"TEST_HASH_{uid}",
        name_encrypted=f"TEST_ENC_NAME_{uid}",
        phone_encrypted=f"TEST_ENC_PHONE_{uid}",
        gender="F",
        age=32,
        landholding_band="MARGINAL",
    )
    db.add(borrower)
    await db.flush()

    default_features = {
        "shg_repayment_rate": 0.95,
        "shg_meeting_attendance_pct": 88.0,
        "land_holding_acres": 1.5,
        "shg_cumulative_savings": 5000.0,
    }
    snapshot = FeatureSnapshot(
        id=uuid.uuid4(),
        borrower_id=borrower.id,
        feature_version="v1.0.0",
        features_json=features_json if features_json is not None else default_features,
        season_tag="KHARIF",
    )
    db.add(snapshot)
    await db.flush()

    score = Score(
        id=uuid.uuid4(),
        borrower_id=borrower.id,
        feature_snapshot_id=snapshot.id,
        model_version="v1.1.0-woe-scorecard",
        score=710.0,
        confidence_lower=680.0,
        confidence_upper=735.0,
    )
    db.add(score)
    await db.flush()

    app_decided = decided_at or (datetime.now(UTC) - timedelta(days=400))
    app = LoanApplication(
        id=uuid.uuid4(),
        borrower_id=borrower.id,
        score_id=score.id,
        partner_re_id="RE-TEST-01",
        requested_amount=35000.0,
        requested_tenure_months=12,
        purpose="DAIRY_FARMING",
        officer_decision="APPROVED",
        decided_at=app_decided,
        approved_amount=35000.0,
        created_at=app_decided - timedelta(days=1),
    )
    db.add(app)
    await db.flush()

    repayment = RepaymentRecord(
        id=uuid.uuid4(),
        loan_application_id=app.id,
        period="2026-M06",
        status=status,
        consented_for_retraining=consented,
        recorded_at=app_decided + timedelta(days=30),
    )
    db.add(repayment)
    await db.flush()

    return village, borrower, snapshot, score, app, repayment


@pytest.mark.asyncio
async def test_relational_join_extraction(db_session: AsyncSession):
    """Verify canonical 5-table relational join retrieves expected attributes."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=450)
    features = {
        "shg_repayment_rate": 0.98,
        "shg_meeting_attendance_pct": 92.0,
        "land_holding_acres": 2.2,
    }
    village, borrower, snapshot, score, app, repayment = await _create_test_hierarchy(
        db_session,
        status="CURRENT",
        consented=True,
        decided_at=decided,
        features_json=features,
    )

    df, metadata = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    assert len(df) == 1
    row = df.iloc[0]
    assert str(row["repayment_id"]) == str(repayment.id)
    assert row["repayment_status"] == "CURRENT"
    assert row["gender"] == borrower.gender
    assert row["landholding_band"] == borrower.landholding_band
    assert row["village_name"] == village.name
    assert row["agro_climatic_zone"] == village.agro_climatic_zone
    assert row["target"] == 1
    assert row["shg_repayment_rate"] == 0.98
    assert row["shg_meeting_attendance_pct"] == 92.0
    assert row["land_holding_acres"] == 2.2

    assert metadata["row_count"] == 1
    assert metadata["positive_rate"] == 1.0
    assert metadata["feature_count"] == len(MODEL_FEATURE_NAMES)


@pytest.mark.asyncio
async def test_dpdp_consent_filter(db_session: AsyncSession):
    """Verify strictly only rows with consented_for_retraining == True are extracted."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=400)

    # Consented record
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=decided
    )
    # Non-consented record
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=False, decided_at=decided
    )

    df, metadata = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    assert len(df) == 1
    assert metadata["row_count"] == 1


@pytest.mark.asyncio
async def test_maturity_window_filtering(db_session: AsyncSession):
    """Verify maturity cutoff excludes immature loans (< 12 months)."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    mature_date = ref_date - timedelta(days=400)  # ~13.3 months ago
    immature_date = ref_date - timedelta(days=60)  # ~2 months ago

    # Mature loan
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=mature_date
    )
    # Immature loan
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=immature_date
    )

    df, metadata = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    assert len(df) == 1
    assert metadata["row_count"] == 1


@pytest.mark.asyncio
async def test_target_labeling_and_intermediate_dpd_exclusion(db_session: AsyncSession):
    """Verify target labeling: Y=1 for CURRENT/CLOSED, Y=0 for DPD_90_PLUS, intermediate DPD excluded."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=400)

    # Target 1 (Good): CURRENT and CLOSED
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=decided
    )
    await _create_test_hierarchy(
        db_session, status="CLOSED", consented=True, decided_at=decided
    )
    # Target 0 (Default): DPD_90_PLUS
    await _create_test_hierarchy(
        db_session, status="DPD_90_PLUS", consented=True, decided_at=decided
    )
    # Intermediate DPD (Excluded from dataset to eliminate label noise)
    await _create_test_hierarchy(
        db_session, status="DPD_1_30", consented=True, decided_at=decided
    )
    await _create_test_hierarchy(
        db_session, status="DPD_31_60", consented=True, decided_at=decided
    )
    await _create_test_hierarchy(
        db_session, status="DPD_61_90", consented=True, decided_at=decided
    )

    df, metadata = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    # Only CURRENT, CLOSED, and DPD_90_PLUS should be included
    assert len(df) == 3
    assert set(df["repayment_status"]) == {"CURRENT", "CLOSED", "DPD_90_PLUS"}

    current_closed_targets = df[df["repayment_status"].isin(["CURRENT", "CLOSED"])]["target"]
    assert (current_closed_targets == 1).all()

    default_targets = df[df["repayment_status"] == "DPD_90_PLUS"]["target"]
    assert (default_targets == 0).all()

    assert metadata["row_count"] == 3
    assert pytest.approx(metadata["positive_rate"], rel=1e-3) == 2 / 3


@pytest.mark.asyncio
async def test_zero_pii_assertion(db_session: AsyncSession):
    """Verify prohibited fields from PROHIBITED_FIELDS never appear in extract or export."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=400)

    # 1. Normal extraction has zero PII columns
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=decided
    )
    df, _ = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    columns_set = set(df.columns)
    forbidden_present = columns_set & PROHIBITED_FIELDS
    assert not forbidden_present, f"Prohibited fields found in dataset: {forbidden_present}"

    # 2. Corrupted features_json with PII raises ValueError
    corrupted_features = {
        "shg_repayment_rate": 0.90,
        "name": "Jane Doe",
        "aadhaar": "1234-5678-9012",
    }
    await _create_test_hierarchy(
        db_session,
        status="CURRENT",
        consented=True,
        decided_at=decided,
        features_json=corrupted_features,
    )

    with pytest.raises(ValueError, match="Zero-PII violation"):
        await extract_gold_dataset(
            db_session, maturity_months=12, reference_date=ref_date
        )

    # 3. Exporting a DataFrame with injected PII column raises ValueError
    bad_df = df.copy()
    bad_df["phone"] = "9876543210"
    with pytest.raises(ValueError, match="Zero-PII violation"):
        export_dataset(bad_df, {"row_count": len(bad_df)}, output_dir="temp_test")


@pytest.mark.asyncio
async def test_feature_columns_flattened(db_session: AsyncSession):
    """Verify features_json is unpacked into columns matching MODEL_FEATURE_NAMES."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=400)
    features = {
        "shg_repayment_rate": 0.88,
        "shg_meeting_attendance_pct": 75.0,
        "shg_savings_consistency": 0.90,
        "monthly_avg_credit_inflow": 12000.0,
    }
    await _create_test_hierarchy(
        db_session,
        status="CURRENT",
        consented=True,
        decided_at=decided,
        features_json=features,
    )

    df, metadata = await extract_gold_dataset(
        db_session, maturity_months=12, reference_date=ref_date
    )

    for feature_name in MODEL_FEATURE_NAMES:
        assert feature_name in df.columns

    assert df["shg_repayment_rate"].iloc[0] == 0.88
    assert df["shg_meeting_attendance_pct"].iloc[0] == 75.0
    assert df["shg_savings_consistency"].iloc[0] == 0.90
    assert df["monthly_avg_credit_inflow"].iloc[0] == 12000.0
    assert metadata["feature_count"] == len(MODEL_FEATURE_NAMES)


def test_export_dataset_parquet_and_csv(tmp_path: Path):
    """Verify export_dataset creates valid Parquet and CSV files with metadata JSON."""
    df = pd.DataFrame(
        {
            "repayment_id": [str(uuid.uuid4()), str(uuid.uuid4())],
            "repayment_status": ["CURRENT", "DPD_90_PLUS"],
            "target": [1, 0],
            "shg_repayment_rate": [0.95, 0.40],
            "village_name": ["Rampur", "Bhadohi"],
        }
    )
    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": len(df),
        "positive_rate": 0.5,
        "feature_count": 1,
    }

    # 1. Parquet Export
    parquet_path = export_dataset(df, metadata, output_dir=tmp_path, format="parquet")
    assert parquet_path.exists()
    assert parquet_path.suffix == ".parquet"
    read_df = pd.read_parquet(parquet_path)
    assert len(read_df) == 2
    assert "target" in read_df.columns

    meta_path = parquet_path.with_name(f"{parquet_path.stem}_metadata.json")
    assert meta_path.exists()
    with open(meta_path, encoding="utf-8") as f:
        meta_content = json.load(f)
    assert meta_content["row_count"] == 2
    assert meta_content["positive_rate"] == 0.5

    # 2. CSV Export
    csv_path = export_dataset(df, metadata, output_dir=tmp_path, format="csv")
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"
    read_csv = pd.read_csv(csv_path)
    assert len(read_csv) == 2


@pytest.mark.asyncio
async def test_cli_dry_run(db_session: AsyncSession, tmp_path: Path):
    """Verify dry-run mode executes query without writing files to disk."""
    ref_date = datetime(2026, 11, 16, tzinfo=UTC)
    decided = ref_date - timedelta(days=400)
    await _create_test_hierarchy(
        db_session, status="CURRENT", consented=True, decided_at=decided
    )

    exit_code = await run_extraction(
        output_dir=tmp_path,
        maturity_months=12,
        dry_run=True,
        reference_date=ref_date,
        db_session=db_session,
    )

    assert exit_code == 0
    # tmp_path should remain empty because of dry-run
    assert list(tmp_path.iterdir()) == []

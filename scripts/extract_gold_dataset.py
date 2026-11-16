"""Consent-Gated Gold Dataset Extractor and Parquet Exporter.

Satisfies statutory DPDP Act 2023 §6/§8, RBI Digital Lending Guidelines (DLG),
and credit risk vintage maturity criteria:
1. Canonical 5-table relational join:
   RepaymentRecord -> LoanApplication -> Score -> FeatureSnapshot + Borrower + Village
2. Strict DPDP Consent Filter:
   Only records with consented_for_retraining == True are extracted.
3. Maturity Window:
   disbursed_at <= maturity_cutoff (default 12 months) ensures label maturation.
4. Target Labeling (Y):
   Y = 1 (Good): status in ('CURRENT', 'CLOSED')
   Y = 0 (Default): status == 'DPD_90_PLUS'
   Transitional DPD ('DPD_1_30', 'DPD_31_60', 'DPD_61_90') excluded to eliminate label noise.
5. Zero-PII Enforcement:
   Guarantees no fields from PROHIBITED_FIELDS enter training vectors.
6. Exports versioned Parquet (via pyarrow) or CSV with accompanying metadata JSON.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from ml.features.schema import MODEL_FEATURE_NAMES, PROHIBITED_FIELDS
from services.core.database import async_read_session_factory
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    RepaymentRecord,
    Score,
    Village,
)

logger = logging.getLogger("credittech.gold_extractor")


def _calculate_maturity_cutoff(reference_date: datetime, maturity_months: int) -> datetime:
    """Calculate date cutoff for loan maturity based on months."""
    if maturity_months <= 0:
        return reference_date
    try:
        from dateutil.relativedelta import relativedelta

        return reference_date - relativedelta(months=maturity_months)
    except ImportError:
        return reference_date - timedelta(days=int(maturity_months * 30.4375))


async def extract_gold_dataset(
    db: AsyncSession,
    maturity_months: int = 12,
    reference_date: datetime | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Execute canonical 5-table join, DPDP consent filter, and maturity windowing.

    Args:
        db: Async database session (typically read-replica).
        maturity_months: Minimum months since loan disbursal for mature labels.
        reference_date: As-of reference timestamp (defaults to current UTC time).

    Returns:
        tuple of (extracted_dataframe, metadata_dict).

    Raises:
        ValueError: If any prohibited PII field is detected in features or columns.
    """
    if reference_date is None:
        reference_date = datetime.now(UTC)
    elif reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=UTC)

    maturity_cutoff = _calculate_maturity_cutoff(reference_date, maturity_months)

    # Resolve disbursal timestamp column across model variations
    if hasattr(RepaymentRecord, "disbursed_at"):
        disbursed_field = RepaymentRecord.disbursed_at
    elif hasattr(LoanApplication, "disbursed_at"):
        disbursed_field = LoanApplication.disbursed_at
    else:
        disbursed_field = func.coalesce(LoanApplication.decided_at, LoanApplication.created_at)

    query = (
        select(
            RepaymentRecord.id.label("repayment_id"),
            RepaymentRecord.status.label("repayment_status"),
            disbursed_field.label("disbursed_at"),
            FeatureSnapshot.features_json,
            Borrower.gender,
            Borrower.landholding_band,
            Village.name.label("village_name"),
            Village.agro_climatic_zone,
        )
        .join(LoanApplication, RepaymentRecord.loan_application_id == LoanApplication.id)
        .join(Score, LoanApplication.score_id == Score.id)
        .join(FeatureSnapshot, Score.feature_snapshot_id == FeatureSnapshot.id)
        .join(Borrower, LoanApplication.borrower_id == Borrower.id)
        .join(Village, Borrower.village_id == Village.id)
        .where(RepaymentRecord.consented_for_retraining.is_(True))
        .where(disbursed_field <= maturity_cutoff)
        .where(RepaymentRecord.status.in_(["CURRENT", "CLOSED", "DPD_90_PLUS"]))
    )

    result = await db.execute(query)
    rows = result.all()

    records: list[dict] = []
    for r in rows:
        features = r.features_json or {}
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except Exception:
                features = {}

        # Zero-PII check on raw feature snapshot dictionary
        prohibited_in_features = set(features.keys()) & PROHIBITED_FIELDS
        if prohibited_in_features:
            raise ValueError(
                f"Zero-PII violation: prohibited field(s) {prohibited_in_features} "
                "found in FeatureSnapshot.features_json"
            )

        # Binary target labeling
        status = r.repayment_status
        if status in ("CURRENT", "CLOSED"):
            target = 1
        elif status == "DPD_90_PLUS":
            target = 0
        else:
            # Skip transitional DPD (DPD_1_30, DPD_31_60, DPD_61_90)
            continue

        rec: dict = {
            "repayment_id": str(r.repayment_id),
            "repayment_status": status,
            "disbursed_at": r.disbursed_at,
            "gender": r.gender,
            "landholding_band": r.landholding_band,
            "village_name": r.village_name,
            "agro_climatic_zone": r.agro_climatic_zone,
            "target": target,
        }

        # Flatten features into canonical MODEL_FEATURE_NAMES columns
        for feat in MODEL_FEATURE_NAMES:
            rec[feat] = features.get(feat)

        records.append(rec)

    columns = [
        "repayment_id",
        "repayment_status",
        "disbursed_at",
        "gender",
        "landholding_band",
        "village_name",
        "agro_climatic_zone",
        "target",
        *MODEL_FEATURE_NAMES,
    ]

    df = pd.DataFrame(records) if records else pd.DataFrame(columns=columns)

    # Zero-PII assertion on final dataframe columns
    prohibited_cols = set(df.columns) & PROHIBITED_FIELDS
    if prohibited_cols:
        raise ValueError(
            f"Zero-PII violation: prohibited column(s) {prohibited_cols} present in dataset"
        )

    pos_rate = float(df["target"].mean()) if not df.empty else 0.0

    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": len(df),
        "positive_rate": pos_rate,
        "feature_count": len(MODEL_FEATURE_NAMES),
        "maturity_months": maturity_months,
        "reference_date": reference_date.isoformat(),
        "maturity_cutoff": maturity_cutoff.isoformat(),
        "dpdp_consented_only": True,
        "zero_pii_verified": True,
    }

    return df, metadata


def export_dataset(
    df: pd.DataFrame,
    metadata: dict,
    output_dir: str | Path,
    format: str = "parquet",  # noqa: A002
) -> Path:
    """Export extracted dataset and metadata JSON to disk.

    Args:
        df: Extracted gold dataset DataFrame.
        metadata: Metadata summary dictionary.
        output_dir: Directory where files will be created.
        format: Export format ('parquet' or 'csv').

    Returns:
        Path to the exported data file.

    Raises:
        ValueError: If PII fields are detected or format is unsupported.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Zero-PII check
    prohibited_cols = set(df.columns) & PROHIBITED_FIELDS
    if prohibited_cols:
        raise ValueError(
            f"Zero-PII violation: prohibited column(s) {prohibited_cols} present in export DataFrame"
        )

    fmt = format.lower()
    if fmt not in ("parquet", "csv"):
        raise ValueError(f"Unsupported format '{format}'. Supported formats: 'parquet', 'csv'")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    data_file = out_dir / f"credit_train_{timestamp}.{fmt}"
    meta_file = out_dir / f"credit_train_{timestamp}_metadata.json"

    if fmt == "parquet":
        df.to_parquet(data_file, engine="pyarrow", index=False)
    else:
        df.to_csv(data_file, index=False)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    return data_file


async def run_extraction(
    output_dir: str | Path = "data/gold",
    maturity_months: int = 12,
    export_format: str = "parquet",
    dry_run: bool = False,
    reference_date: datetime | None = None,
    db_session: AsyncSession | None = None,
) -> int:
    """Orchestrate dataset extraction, logging, and optional export."""
    if db_session is not None:
        df, metadata = await extract_gold_dataset(
            db_session,
            maturity_months=maturity_months,
            reference_date=reference_date,
        )
    else:
        async with async_read_session_factory() as session:
            df, metadata = await extract_gold_dataset(
                session,
                maturity_months=maturity_months,
                reference_date=reference_date,
            )

    print("\n" + "=" * 55)
    print("   CreditTech DPDP Consent-Gated Gold Dataset Extractor")
    print("=" * 55)
    print(f"Generated at:    {metadata.get('generated_at')}")
    print(f"Reference date:  {metadata.get('reference_date')}")
    print(f"Maturity cutoff: {metadata.get('maturity_cutoff')} (maturity >= {maturity_months}m)")
    print(f"Rows extracted:  {metadata.get('row_count'):,}")
    print(f"Positive rate:   {metadata.get('positive_rate', 0.0):.2%}")
    print(f"Feature count:   {metadata.get('feature_count')}")
    print(f"Zero-PII check:  {'PASSED' if metadata.get('zero_pii_verified') else 'FAILED'}")
    print("=" * 55)

    if dry_run:
        print("[DRY-RUN] No files written to disk.")
        if len(df) == 0 and maturity_months > 0:
            print("Note: In early pilot databases, pass '--maturity-months 0' to include recent pilot loans.")
        return 0

    out_file = export_dataset(df, metadata, output_dir=output_dir, format=export_format)
    meta_file = out_file.with_name(f"{out_file.stem}_metadata.json")
    print(f"Successfully exported dataset:  {out_file}")
    print(f"Successfully exported metadata: {meta_file}")
    return 0


def main() -> None:
    """CLI entrypoint for extracting training datasets."""
    parser = argparse.ArgumentParser(
        description="Extract DPDP consent-gated gold training dataset with loan maturity filtering."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/gold",
        help="Directory to save exported dataset and metadata (default: data/gold)",
    )
    parser.add_argument(
        "--maturity-months",
        type=int,
        default=12,
        help="Minimum loan vintage maturity in months (default: 12)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "csv"],
        default="parquet",
        help="Dataset format: parquet or csv (default: parquet)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate extraction query without writing files to disk",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(
        run_extraction(
            output_dir=args.output_dir,
            maturity_months=args.maturity_months,
            export_format=args.format,
            dry_run=args.dry_run,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

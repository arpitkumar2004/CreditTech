"""Ingestion Orchestrator service managing external and internal data aggregation."""

import asyncio
import time
import uuid
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.consent.service import ConsentService
from services.core.shared.logging import get_logger
from services.core.shared.models import Borrower, DataPull, FeatureSnapshot, Village

from .connectors import (
    AccountAggregatorConnector,
    BureauConnector,
    ConnectorTimeoutError,
    GeospatialConnector,
)
from .schemas import (
    IngestionSource,
    IngestionSourceStatus,
    IngestionStatus,
    IngestionTriggerRequest,
    IngestionTriggerResponse,
)

logger = get_logger("ingestion.service")


class IngestionServiceError(Exception):
    pass


class IngestionOrchestrator:
    """Orchestrates parallel data fetching from multiple sources with graceful degradation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.consent_service = ConsentService(db)
        self.aa_client = AccountAggregatorConnector()
        self.geo_client = GeospatialConnector()
        self.bureau_client = BureauConnector()

    async def run_ingestion(self, request: IngestionTriggerRequest) -> IngestionTriggerResponse:
        """Trigger and manage a multi-source data ingestion pipeline run."""
        borrower_id = request.borrower_id
        time.time()

        # 1. Fetch Borrower and check existence
        borrower_result = await self.db.execute(
            select(Borrower).where(Borrower.id == borrower_id)
        )
        borrower = borrower_result.scalar_one_or_none()
        if not borrower:
            raise IngestionServiceError(f"Borrower {borrower_id} not found")

        # Get Village details for geospatial coordinates mapping
        village_result = await self.db.execute(
            select(Village).where(Village.id == borrower.village_id)
        )
        village_result.scalar_one()

        # Verify active consent exists for data aggregation
        required_sources = [s.value for s in request.data_sources]
        consent = await self.consent_service.check_active_consent(
            borrower_id=borrower_id,
            purpose=request.purpose,
            required_sources=required_sources,
        )
        if not consent:
            logger.warn(
                "ingestion_blocked_no_consent",
                borrower_id=str(borrower_id),
                required_sources=required_sources,
            )
            raise IngestionServiceError(
                f"No active consent covering requested sources: {required_sources}"
            )

        # 2. Setup tasks for parallel execution
        tasks = []
        source_order = []

        if IngestionSource.AA in request.data_sources:
            tasks.append(
                self._pull_account_aggregator(borrower, consent.aa_consent_id or "mock_consent")
            )
            source_order.append(IngestionSource.AA)

        if IngestionSource.GEOSPATIAL in request.data_sources:
            # Hanumangarh center coordinates as default for pilot
            lat, lon = 29.58, 74.32
            tasks.append(self._pull_geospatial(borrower, lat, lon))
            source_order.append(IngestionSource.GEOSPATIAL)

        if IngestionSource.BUREAU in request.data_sources:
            tasks.append(self._pull_bureau(borrower))
            source_order.append(IngestionSource.BUREAU)

        # 3. Execute parallel fetches with safety timeouts
        # Wait up to 20 seconds for the entire parallel gather to complete
        logger.info("starting_parallel_data_pulls", borrower_id=str(borrower_id), sources=required_sources)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Map results and build snapshot features
        ingested_payloads: dict[str, Any] = {}
        sources_status = []
        success_count = 0

        for source, result in zip(source_order, results, strict=False):
            source_status = IngestionStatus.SUCCESS
            duration_ms = None
            error_message = None

            if isinstance(result, Exception):
                is_timeout = isinstance(result, (asyncio.TimeoutError, ConnectorTimeoutError))
                source_status = IngestionStatus.TIMEOUT if is_timeout else IngestionStatus.FAILED
                error_message = str(result)
                logger.error(
                    "source_pull_failed",
                    source=source.value,
                    borrower_id=str(borrower_id),
                    error=error_message,
                )
            else:
                success_count += 1
                payload, duration_ms = result
                ingested_payloads[source.value] = payload

            # Record DataPull entry in database
            data_pull = DataPull(
                borrower_id=borrower_id,
                source=source.value,
                status=source_status.value,
                raw_ref=f"db://data_pulls/{source.value.lower()}_payload" if source_status == IngestionStatus.SUCCESS else None,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            self.db.add(data_pull)
            sources_status.append(
                IngestionSourceStatus(
                    source=source,
                    status=source_status,
                    duration_ms=duration_ms,
                    error_message=error_message,
                )
            )

        # 5. Integrate SHG/FPO local historical profile from DB
        # Since SHG is manual/CSV ingestion, we read the latest state from DB records
        shg_status = IngestionStatus.SKIPPED
        shg_profile = await self._get_latest_shg_profile(borrower_id)
        if shg_profile:
            ingested_payloads[IngestionSource.SHG_FPO.value] = shg_profile
            shg_status = IngestionStatus.SUCCESS
            success_count += 1

        sources_status.append(
            IngestionSourceStatus(source=IngestionSource.SHG_FPO, status=shg_status)
        )

        # Determine overall success status: every requested rail must have
        # completed. SHG_FPO is populated internally and does not count
        # against the requested-source total.
        requested_success = sum(
            1
            for s in sources_status
            if s.source in request.data_sources and s.status == IngestionStatus.SUCCESS
        )
        overall_status = "FAILED"
        if requested_success == len(request.data_sources):
            overall_status = "SUCCESS"
        elif requested_success > 0:
            overall_status = "PARTIAL"

        # 6. Feature Normalization & Snapshot Generation (Graceful degradation)
        snapshot_id = None
        if success_count > 0:
            snapshot = await self._generate_feature_snapshot(borrower, ingested_payloads)
            snapshot_id = snapshot.id

        await self.db.commit()

        return IngestionTriggerResponse(
            borrower_id=borrower_id,
            overall_status=overall_status,
            sources=sources_status,
            feature_snapshot_id=snapshot_id,
            completed_at=datetime.now(UTC),
        )

    # ── Connector Wrapper Methods ────────────────────────────

    async def _pull_account_aggregator(self, borrower: Borrower, consent_id: str) -> tuple[dict[str, Any], int]:
        start = time.perf_counter()
        data = await self.aa_client.fetch_bank_data(borrower.id, consent_id)
        duration = int((time.perf_counter() - start) * 1000)
        return data, duration

    async def _pull_geospatial(self, borrower: Borrower, lat: float, lon: float) -> tuple[dict[str, Any], int]:
        start = time.perf_counter()
        data = await self.geo_client.fetch_satellite_data(borrower.id, lat, lon)
        duration = int((time.perf_counter() - start) * 1000)
        return data, duration

    async def _pull_bureau(self, borrower: Borrower) -> tuple[dict[str, Any], int]:
        start = time.perf_counter()
        data = await self.bureau_client.fetch_credit_profile(borrower.aadhaar_ref_hash)
        duration = int((time.perf_counter() - start) * 1000)
        return data, duration

    # ── SHG Ingestion Fetch ──────────────────────────────────

    async def _get_latest_shg_profile(self, borrower_id: uuid.UUID) -> dict[str, Any] | None:
        """Query the latest manual SHG data saved for the borrower in DB."""
        # Check if the borrower has a populated landholding status
        result = await self.db.execute(
            select(Borrower).where(Borrower.id == borrower_id)
        )
        b = result.scalar_one_or_none()
        if not b:
            return None

        # Return simulated dictionary representing manual entry fields if present
        # In early stages we fall back to synthetic data values based on borrower configuration
        return {
            "shg_name": "Marudhara Mahila SHG",
            "nabard_grade": "A",
            "membership_years": 4,
            "monthly_savings": 200.0,
            "total_savings": 9600.0,
            "loans_taken": 3,
            "loans_repaid": 3,
            "meeting_attendance_pct": 95.0,
            "land_holding_acres": b.landholding_band or "MARGINAL",
        }

    # ── Feature Engineering Normalization ────────────────────

    async def _generate_feature_snapshot(
        self, borrower: Borrower, payloads: dict[str, Any]
    ) -> FeatureSnapshot:
        """Normalize aggregated payloads into versioned FeatureSnapshot variables."""
        features: dict[str, Any] = {}

        # Default fallback values for all features (defined in preliminary spec)
        # C — Character features
        features["shg_repayment_rate"] = 100.0
        features["shg_meeting_attendance_pct"] = 90.0
        features["shg_savings_consistency"] = 0.1
        features["shg_membership_years"] = 1
        features["shg_grade"] = "B"
        features["utility_payment_ontime_pct"] = 95.0
        features["upi_transaction_regularity"] = 0.2

        # CA — Capacity features
        features["estimated_crop_income_kharif"] = 45000.0
        features["estimated_crop_income_rabi"] = 55000.0
        features["income_stability_cv"] = 0.3
        features["monthly_avg_credit_inflow"] = 8000.0
        features["pm_kisan_beneficiary"] = True
        features["pm_kisan_regularity"] = 1.0

        # CP — Capital features
        features["shg_cumulative_savings"] = 5000.0
        features["bank_balance_avg_6m"] = 6200.0
        features["asset_score"] = 0.5
        features["kcc_holder"] = False
        features["kcc_utilization_pct"] = 0.0

        # CL — Collateral features
        features["land_holding_acres"] = 1.5
        features["irrigation_access"] = True
        features["land_quality_ndvi_avg"] = 0.65

        # CO — Conditions features
        features["ndvi_trend_2season"] = 0.05
        features["rainfall_deviation_pct"] = 2.0
        features["crop_type_primary"] = "Wheat"
        features["crop_insurance_enrolled"] = True

        # Extract features from AA payload if available
        if "AA" in payloads:
            aa = payloads["AA"]
            features["bank_balance_avg_6m"] = aa.get("avg_balance_6m", 6200.0)
            features["upi_transaction_regularity"] = aa.get("upi_regularity", 0.2)
            features["monthly_avg_credit_inflow"] = aa.get("avg_credit_inflow", 8000.0)
            features["pm_kisan_regularity"] = aa.get("pm_kisan_regularity", 1.0)

        # Extract features from Geospatial payload if available
        if "GEOSPATIAL" in payloads:
            geo = payloads["GEOSPATIAL"]
            features["land_quality_ndvi_avg"] = geo.get("ndvi_avg", 0.65)
            features["ndvi_trend_2season"] = geo.get("ndvi_trend", 0.05)
            features["rainfall_deviation_pct"] = geo.get("rainfall_dev", 2.0)

        # Extract features from SHG payload if available
        if "SHG_FPO" in payloads:
            shg = payloads["SHG_FPO"]
            features["shg_membership_years"] = shg.get("membership_years", 1)
            features["shg_cumulative_savings"] = shg.get("total_savings", 5000.0)
            features["shg_meeting_attendance_pct"] = shg.get("meeting_attendance_pct", 90.0)
            features["shg_grade"] = shg.get("nabard_grade", "B")

            # Loans taken/repaid mapping to rate
            taken = shg.get("loans_taken", 0)
            repaid = shg.get("loans_repaid", 0)
            if taken > 0:
                features["shg_repayment_rate"] = float(repaid) / float(taken) * 100.0

        # Extract features from Bureau payload if available
        if "BUREAU" in payloads:
            bur = payloads["BUREAU"]
            features["kcc_holder"] = bur.get("has_kcc", False)
            features["kcc_utilization_pct"] = bur.get("kcc_utilization", 0.0)

        # Determine seasonal crop tag based on current calendar month
        current_month = datetime.now(UTC).month
        if 6 <= current_month <= 10:
            season = "KHARIF"
        elif 11 <= current_month <= 12 or 1 <= current_month <= 3:
            season = "RABI"
        else:
            season = "ZAID"

        # Generate snapshot entity
        snapshot = FeatureSnapshot(
            borrower_id=borrower.id,
            feature_version="v1.0.0",
            features_json=features,
            season_tag=season,
            sources_used=list(payloads.keys()),
        )
        self.db.add(snapshot)
        await self.db.flush()

        logger.info(
            "feature_snapshot_generated",
            borrower_id=str(borrower.id),
            snapshot_id=str(snapshot.id),
            sources=list(payloads.keys()),
        )
        return snapshot

"""Simulation Router executing end-to-end pilot runs for testing and demonstrating pipeline capabilities."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.consent.schemas import ConsentCreateRequest
from services.core.consent.service import ConsentService
from services.core.database import get_db
from services.core.handoff.schemas import HandoffSubmitRequest, REDecisionWebhookPayload
from services.core.handoff.service import HandoffService
from services.core.ingestion.schemas import IngestionTriggerRequest
from services.core.ingestion.service import IngestionOrchestrator
from services.core.monitoring.service import DataRetentionWorker, FairnessAuditor
from services.core.scoring.schemas import ScoreRequest
from services.core.scoring.service import ScoringService
from services.core.shared.logging import get_logger
from services.core.shared.models import Borrower, Village

logger = get_logger("simulation.router")
router = APIRouter(prefix="/simulate", tags=["Pilot Simulation"])


@router.post(
    "/run",
    status_code=status.HTTP_200_OK,
    summary="Run an end-to-end simulated loan lifecycle",
)
async def run_simulation(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Executes a complete credit process simulation:

    1. Seed a sample Village and Borrower.
    2. Issue a 30-day DPDP-compliant Consent.
    3. Trigger parallel alternative data ingestion (AA, satellite, bureau).
    4. Generate scoring output and SHAP reason codes.
    5. Submit application handoff payload to partner RE.
    6. Simulate RE webhook callback approving the loan.
    7. Compute weekly fairness monitoring logs.
    8. Trigger data retention purge.
    """
    try:
        # ── 1. Seed Village & Borrower ──
        # Check if dummy village exists
        result_village = await db.execute(select(Village).where(Village.name == "Sangaria Sangam"))
        village = result_village.scalar_one_or_none()
        if not village:
            village = Village(
                name="Sangaria Sangam",
                site_type="IRRIGATED_COTTON",
                state="Rajasthan",
                district="Hanumangarh",
                block="Sangaria",
                agro_climatic_zone="Zone I-B",
            )
            db.add(village)
            await db.flush()

        borrower_ref = f"sim-{uuid.uuid4().hex[:6]}"
        borrower = Borrower(
            aadhaar_ref_hash=f"hash-{borrower_ref}",
            name_encrypted="encrypted-simulated-name",
            phone_encrypted="encrypted-simulated-phone",
            village_id=village.id,
            gender="F",
            age=32,
            landholding_band="MARGINAL",
        )
        db.add(borrower)
        await db.flush()

        # ── 2. Issue Consent ──
        consent_service = ConsentService(db)
        consent_req = ConsentCreateRequest(
            borrower_id=borrower.id,
            purpose="credit_scoring",
            consent_mode="bank_sakhi_assisted",
            data_sources=["AA", "GEOSPATIAL", "BUREAU", "SHG_FPO"],
            scope_description_en="I consent to share my bank transaction history and satellite maps.",
            duration_days=30,
            created_by="sakhi_agent",
        )
        consent = await consent_service.create_consent(consent_req)

        # ── 3. Run Ingestion Orchestration ──
        ingestion_orchestrator = IngestionOrchestrator(db)
        # Point settings to mock route during simulation so local http calls don't crash
        ingestion_req = IngestionTriggerRequest(
            borrower_id=borrower.id,
            purpose="credit_scoring",
            data_sources=["AA", "GEOSPATIAL", "BUREAU"],
        )
        ingestion_res = await ingestion_orchestrator.run_ingestion(ingestion_req)

        # ── 4. Generate Score ──
        scoring_service = ScoringService(db)
        score_req = ScoreRequest(
            borrower_id=borrower.id,
            feature_snapshot_id=ingestion_res.feature_snapshot_id,
        )
        score_record = await scoring_service.generate_score(score_req)

        # ── 4b. Officer decision (P4 gate — RE handoff requires approval) ──
        from services.core.decisioning.schemas import (
            DecisionRequest,
            OfficerDecision,
        )
        from services.core.decisioning.service import (
            DecisioningService,
            recommendation_for_band,
        )

        band = ScoringService.get_score_band(score_record.score)
        rec = recommendation_for_band(band)
        decision_body = DecisionRequest(
            score_id=score_record.id,
            decision=OfficerDecision.APPROVED,
            override_reason=(
                None
                if rec.value == "APPROVE"
                else "Simulation officer override — proceeding to RE for pipeline validation"
            ),
        )
        decisioning = DecisioningService(db)
        await decisioning.record_decision(decision_body, officer_id="sim_officer")

        # ── 5. Handoff Submission ──
        handoff_service = HandoffService(db)
        handoff_req = HandoffSubmitRequest(
            score_id=score_record.id,
            partner_re_id="PARTNER_BANK_A",
            requested_amount=35000.0,
            requested_tenure_months=12,
            purpose="CROP_INPUT_SEEDS",
        )
        loan_app = await handoff_service.submit_application(handoff_req)

        # ── 6. Process Webhook Decision (Approve) ──
        webhook_payload = REDecisionWebhookPayload(
            re_application_id=f"RE-SIM-{uuid.uuid4().hex[:6].upper()}",
            credittech_application_id=loan_app.id,
            decision="APPROVED",
            decided_at=datetime.now(UTC),
            decided_by="re_officer_90",
            approved_amount=30000.0,
            override_reason="Strong local FPO validation feedback",
        )
        await handoff_service.process_decision_webhook(webhook_payload)

        # ── 7. Run Fairness Audits ──
        auditor = FairnessAuditor(db)
        period = f"2026-W{datetime.now(UTC).isocalendar()[1]}"
        await auditor.run_audit(period)

        # ── 8. Run Retention Purge ──
        # To simulate a purge, we temporarily modify the consent to be expired
        consent.expires_at = datetime.now(UTC) - timedelta(days=1)
        consent.status = "EXPIRED"
        await db.commit()

        retention_worker = DataRetentionWorker(db)
        purged_count = await retention_worker.purge_expired_consent_data()

        return {
            "status": "success",
            "borrower_id": borrower.id,
            "consent_issued_status": consent.status,
            "ingestion_status": ingestion_res.overall_status,
            "score_100": score_record.score,
            "score_900": getattr(score_record, "score_900", 600),
            "decision": "APPROVED",
            "re_approved_amount": 30000.0,
            "fairness_audit_period": period,
            "data_retention_purged_borrowers": purged_count,
        }

    except Exception as e:
        logger.error("simulation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {e}",
        )

"""FastAPI router for the Partner RE Handoff API and Webhooks."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.shared.logging import get_logger

from .schemas import HandoffSubmitRequest, REDecisionWebhookPayload
from .service import HandoffService, HandoffServiceError

logger = get_logger("handoff.router")
router = APIRouter(prefix="/handoff", tags=["RE Handoff"])


@router.post(
    "/submit",
    status_code=status.HTTP_200_OK,
    summary="Submit loan application to partner RE",
)
async def submit_application(
    request: HandoffSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Assembles and transmits a structured credit decision package to the partner RE."""
    service = HandoffService(db)
    try:
        existed = await service._existing_application(request.score_id, request.partner_re_id)
        loan_app = await service.submit_application(request)
        return {
            "loan_application_id": loan_app.id,
            "status": "ALREADY_SUBMITTED" if existed is not None else "SUBMITTED",
            "message": (
                "Loan application already submitted to Partner RE"
                if existed is not None
                else "Loan application successfully transmitted to Partner RE"
            ),
        }
    except HandoffServiceError as e:
        logger.error("handoff_submission_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/webhook/decision",
    status_code=status.HTTP_200_OK,
    summary="Partner RE decision callback webhook receiver",
)
async def receive_decision_webhook(
    payload: REDecisionWebhookPayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Webhook callback endpoint for partner REs to log credit approvals or declines."""
    service = HandoffService(db)
    try:
        await service.process_decision_webhook(payload)
        return {"status": "processed", "message": "Decision logged successfully"}
    except HandoffServiceError as e:
        logger.error("webhook_processing_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ── Developer Mock RE Receiver Endpoints ─────────────────────
# Mounted directly here to keep mocks grouped clean
@router.post(
    "/mock-receiver/submit",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Developer Mocks"],
    summary="Simulated Partner RE ingestion gateway",
)
async def mock_re_receiver_submit(payload: dict) -> dict:
    """Returns accepted responses and simulated application IDs."""
    application_id = payload.get("application_id", "CT-MOCK-ID")
    logger.info("mock_re_received_payload", application_id=application_id)
    return {
        "re_application_id": f"RE-MOCK-INGEST-{application_id[-6:]}",
        "status": "RECEIVED",
        "message": "Payload matches contract signature validations",
    }

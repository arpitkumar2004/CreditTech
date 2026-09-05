"""FastAPI router for the Ingestion API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.shared.logging import get_logger

from .schemas import IngestionTriggerRequest, IngestionTriggerResponse, SHGFPOIngestRequest
from .service import IngestionOrchestrator, IngestionServiceError

logger = get_logger("ingestion.router")
router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post(
    "/trigger",
    response_model=IngestionTriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger parallel data ingestion pipeline",
)
async def trigger_ingestion(
    request: IngestionTriggerRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestionTriggerResponse:
    """Trigger parallel fetches from AA, Geospatial, and Bureau, integrating them with local SHG data."""
    orchestrator = IngestionOrchestrator(db)
    try:
        response = await orchestrator.run_ingestion(request)
        return response
    except IngestionServiceError as e:
        logger.error("ingestion_trigger_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/shg-fpo",
    status_code=status.HTTP_201_CREATED,
    summary="Save manual SHG/FPO profile data",
)
async def submit_shg_fpo_data(
    request: SHGFPOIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit manual SHG / FPO data captured by a Bank Sakhi for a borrower."""
    # Registering manual profile updates properties in the local DB.
    # In development/prototype, this logs and confirms receipt.
    logger.info(
        "shg_fpo_manual_data_received",
        borrower_id=str(request.borrower_id),
        created_by=request.created_by,
    )
    return {
        "status": "success",
        "borrower_id": request.borrower_id,
        "message": "Manual SHG/FPO records registered successfully",
    }

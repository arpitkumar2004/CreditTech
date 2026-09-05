"""FastAPI router for the Scoring API."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.core.database import get_db
from services.core.shared.logging import get_logger
from services.core.shared.models import Score

from .schemas import ScoreRequest, ScoreResponse
from .service import ScoringService, ScoringServiceError

logger = get_logger("scoring.router")
router = APIRouter(prefix="/score", tags=["Credit Scoring"])


@router.post(
    "/",
    response_model=ScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a credit score",
)
async def generate_score(
    request: ScoreRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Generate and persist a calibrated credit score and reasons using the latest FeatureSnapshot."""
    service = ScoringService(db, model_version=request.model_version)
    try:
        score_record = await service.generate_score(request)

        # Format response matching pydantic model
        return {
            "id": score_record.id,
            "borrower_id": score_record.borrower_id,
            "feature_snapshot_id": score_record.feature_snapshot_id,
            "model_version": score_record.model_version,
            "feature_version": service.scorecard.feature_version,
            "score": score_record.score,
            "score_900": getattr(score_record, "score_900", 600),
            "score_band": service.get_score_band(score_record.score),
            "confidence_lower": score_record.confidence_lower,
            "confidence_upper": score_record.confidence_upper,
            "sources_used": score_record.sources_used,
            "reason_codes": getattr(score_record, "transient_reason_codes", []),
            "generated_at": score_record.generated_at,
        }
    except ScoringServiceError as e:
        logger.error("failed_to_generate_score", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{score_id}",
    response_model=ScoreResponse,
    summary="Retrieve historical credit score",
)
async def get_historical_score(
    score_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a previously generated credit score along with its reason codes."""
    # Eagerly load reason codes relation
    result = await db.execute(
        select(Score)
        .options(selectinload(Score.reason_codes))
        .where(Score.id == score_id)
    )
    score_record = result.scalar_one_or_none()
    if not score_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score {score_id} not found",
        )

    # Re-calculate 900 score dynamically for display (not stored in DB).
    # Use the model_version that was used at scoring time so calibration matches.
    prob_repay = score_record.score / 100.0
    service = ScoringService(db, model_version=score_record.model_version)
    _, score_900 = service.scorecard.calibrate_score(prob_repay)

    return {
        "id": score_record.id,
        "borrower_id": score_record.borrower_id,
        "feature_snapshot_id": score_record.feature_snapshot_id,
        "model_version": score_record.model_version,
        "feature_version": service.scorecard.feature_version,
        "score": score_record.score,
        "score_900": score_900,
        "score_band": service.get_score_band(score_record.score),
        "confidence_lower": score_record.confidence_lower,
        "confidence_upper": score_record.confidence_upper,
        "sources_used": score_record.sources_used,
        "reason_codes": score_record.reason_codes,
        "generated_at": score_record.generated_at,
    }

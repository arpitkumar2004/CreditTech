"""FastAPI router — Loan Officer Decision Interface (P4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.shared.logging import get_logger

from .auth import require_officer
from .schemas import (
    DecisionRequest,
    OfficerDecisionRecord,
    ReviewPayload,
)
from .service import DecisioningError, DecisioningService

logger = get_logger("decisioning.router")
router = APIRouter(prefix="/decision", tags=["Officer Decisioning"])


@router.get(
    "/applications",
    summary="List all loan applications for officer review",
)
async def list_applications(
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = DecisioningService(db)
    return await service.list_applications()


@router.get(
    "/applications/{application_id}",
    response_model=ReviewPayload,
    summary="Full application review pack",
)
async def get_application_review(
    application_id: uuid.UUID,
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> ReviewPayload:
    service = DecisioningService(db)
    try:
        return await service.get_application_review(application_id)
    except DecisioningError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/review/{score_id}",
    response_model=ReviewPayload,
    summary="Assemble the officer review pack for a score",
)
async def get_review(
    score_id: uuid.UUID,
    officer_id: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> ReviewPayload:
    service = DecisioningService(db)
    try:
        payload = await service.build_review_payload(score_id)
    except DecisioningError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    logger.info(
        "review_payload_returned",
        score_id=str(score_id),
        officer_id=officer_id,
        partial_data=payload.partial_data,
    )
    return payload


@router.post(
    "/",
    response_model=OfficerDecisionRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Record a loan officer decision (approve/reject/more-info)",
)
async def record_decision(
    request: DecisionRequest,
    officer_id: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> OfficerDecisionRecord:
    service = DecisioningService(db)
    try:
        entry = await service.record_decision(request, officer_id=officer_id)
    except DecisioningError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return OfficerDecisionRecord.model_validate(entry)


@router.get(
    "/audit/{score_id}",
    response_model=list[OfficerDecisionRecord],
    summary="Immutable audit trail of decisions for a score",
)
async def get_audit(
    score_id: uuid.UUID,
    officer_id: str = Depends(require_officer),  # noqa: ARG001 — auth-only
    db: AsyncSession = Depends(get_db),
) -> list[OfficerDecisionRecord]:
    service = DecisioningService(db)
    entries = await service.get_audit_trail(score_id)
    return [OfficerDecisionRecord.model_validate(e) for e in entries]


@router.get(
    "/applications",
    summary="List all loan applications for officer dashboard",
)
async def list_applications(
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    service = DecisioningService(db)
    return await service.list_applications()


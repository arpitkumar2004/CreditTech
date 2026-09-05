"""FastAPI router for the Consent API.

Implements all endpoints defined in the Phase 0 ConsentRecord Schema Spec.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.shared.logging import get_logger

from .schemas import (
    ConsentAuditResponse,
    ConsentCreateRequest,
    ConsentListResponse,
    ConsentResponse,
    ConsentRevokeRequest,
    ConsentVerifyResponse,
)
from .service import (
    ConsentAlreadyRevokedError,
    ConsentNotFoundError,
    ConsentService,
    ConsentServiceError,
)

logger = get_logger("consent.router")
router = APIRouter(prefix="/consent", tags=["Consent Management"])


@router.post(
    "/",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new consent record",
)
async def create_consent(
    request: ConsentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new time-bound, revocable consent record for a borrower.

    The record is append-only and cryptographically linked to the previous
    consent record for this borrower to ensure tamper-evidence.
    """
    service = ConsentService(db)
    try:
        consent = await service.create_consent(request)
        return consent
    except ConsentServiceError as e:
        logger.error("failed_to_create_consent", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{consent_id}",
    response_model=ConsentResponse,
    summary="Retrieve a single consent record",
)
async def get_consent(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a consent record by its UUID.

    Performs lazy expiry check and updates status if expired.
    """
    service = ConsentService(db)
    try:
        consent = await service.get_consent(consent_id)
        return consent
    except ConsentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/borrower/{borrower_id}",
    response_model=ConsentListResponse,
    summary="List all consent records for a borrower",
)
async def list_borrower_consents(
    borrower_id: uuid.UUID,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by consent status (ACTIVE, EXPIRED, REVOKED, SUPERSEDED)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all consent records associated with a specific borrower, sorted by creation time."""
    service = ConsentService(db)
    items, total = await service.list_by_borrower(
        borrower_id=borrower_id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{consent_id}/revoke",
    response_model=ConsentResponse,
    summary="Revoke an active consent record",
)
async def revoke_consent(
    consent_id: uuid.UUID,
    request: ConsentRevokeRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Revoke an active consent. This is a non-reversible operation."""
    service = ConsentService(db)
    try:
        consent = await service.revoke_consent(consent_id, request)
        return consent
    except ConsentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (ConsentAlreadyRevokedError, ConsentServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{consent_id}/verify",
    response_model=ConsentVerifyResponse,
    summary="Verify consent validity and tamper status",
)
async def verify_consent(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verify that a consent is ACTIVE, not expired, and hash chain is intact."""
    service = ConsentService(db)
    try:
        verification = await service.verify_consent(consent_id)
        return verification
    except ConsentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{consent_id}/audit",
    response_model=ConsentAuditResponse,
    summary="Retrieve audit trail for a consent record",
)
async def get_consent_audit(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve an chronological list of all lifecycle changes for a given consent record."""
    service = ConsentService(db)
    try:
        entries = await service.get_audit_trail(consent_id)
        return {
            "consent_id": consent_id,
            "entries": entries,
            "total": len(entries),
        }
    except ConsentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

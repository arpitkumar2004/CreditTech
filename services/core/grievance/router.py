"""Grievance / appeal channel router.

Borrower-facing endpoints (POST /grievances, GET /grievances/{id}) require an
`X-Borrower-Id` header for the pilot; the router validates it matches the
grievance's borrower_id on lookup. Officer-facing endpoints (PATCH, list, audit,
auto-escalate) require the P4 officer headers.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.decisioning.auth import require_officer
from services.core.shared.logging import get_logger

from .schemas import (
    GrievanceAuditEntry,
    GrievanceCreate,
    GrievanceRecord,
    GrievanceUpdate,
)
from .service import GrievanceError, GrievanceService, to_record

logger = get_logger("grievance.router")
router = APIRouter(prefix="/grievances", tags=["Grievance / Appeal"])


def require_borrower(
    x_borrower_id: str | None = Header(default=None, alias="X-Borrower-Id"),
) -> str:
    if not x_borrower_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Borrower-Id header",
        )
    return x_borrower_id.strip()


@router.post(
    "/",
    response_model=GrievanceRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Create a grievance / appeal (starts SLA clock)",
)
async def create_grievance(
    req: GrievanceCreate,
    borrower_id: str = Depends(require_borrower),
    db: AsyncSession = Depends(get_db),
) -> GrievanceRecord:
    # Enforce that the header-borrower matches the payload borrower_id
    if str(req.borrower_id) != borrower_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Borrower id in header does not match request body",
        )
    svc = GrievanceService(db)
    try:
        g = await svc.create(req, actor=f"borrower:{borrower_id}")
    except GrievanceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return to_record(g)


@router.get(
    "/{grievance_id}",
    response_model=GrievanceRecord,
    summary="Fetch a grievance (borrower or officer)",
)
async def get_grievance(
    grievance_id: uuid.UUID,
    x_borrower_id: str | None = Header(default=None, alias="X-Borrower-Id"),
    x_officer_id: str | None = Header(default=None, alias="X-Officer-Id"),
    x_officer_role: str | None = Header(default=None, alias="X-Officer-Role"),
    db: AsyncSession = Depends(get_db),
) -> GrievanceRecord:
    svc = GrievanceService(db)
    try:
        g = await svc.get(grievance_id)
    except GrievanceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    officer_ok = bool(
        x_officer_id
        and x_officer_role
        and x_officer_role.upper() in {"LOAN_OFFICER", "SUPERVISOR", "ADMIN", "RISK_OFFICER"}
    )
    borrower_ok = x_borrower_id is not None and x_borrower_id.strip() == str(g.borrower_id)
    if not (officer_ok or borrower_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing/invalid borrower or officer credentials",
        )
    return to_record(g)


@router.get(
    "/",
    response_model=list[GrievanceRecord],
    summary="List grievances (officer view)",
)
async def list_grievances(
    status_filter: str | None = Query(default=None, alias="status"),
    borrower_id: uuid.UUID | None = None,
    overdue_only: bool = False,
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> list[GrievanceRecord]:
    svc = GrievanceService(db)
    items = await svc.list(
        status=status_filter, borrower_id=borrower_id, include_overdue_only=overdue_only,
    )
    return [to_record(g) for g in items]


@router.patch(
    "/{grievance_id}",
    response_model=GrievanceRecord,
    summary="Update grievance status (officer)",
)
async def update_grievance(
    grievance_id: uuid.UUID,
    req: GrievanceUpdate,
    officer_id: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> GrievanceRecord:
    svc = GrievanceService(db)
    try:
        g = await svc.update(grievance_id, req, actor=f"officer:{officer_id}")
    except GrievanceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return to_record(g)


@router.get(
    "/{grievance_id}/audit",
    response_model=list[GrievanceAuditEntry],
    summary="Immutable audit trail for a grievance (officer)",
)
async def get_audit(
    grievance_id: uuid.UUID,
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> list[GrievanceAuditEntry]:
    svc = GrievanceService(db)
    rows = await svc.get_audit_trail(grievance_id)
    return [GrievanceAuditEntry.model_validate(r) for r in rows]


@router.post(
    "/escalate-overdue",
    summary="Auto-escalate grievances past SLA (system/officer job)",
)
async def escalate_overdue(
    officer_id: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = GrievanceService(db)
    n = await svc.escalate_overdue(actor=f"officer:{officer_id}")
    return {"escalated": n}

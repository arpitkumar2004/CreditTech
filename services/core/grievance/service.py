"""Grievance service — creation, status transitions, SLA clock."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.logging import get_logger
from services.core.shared.models import Borrower, Grievance, GrievanceAuditLog

from .schemas import (
    ALLOWED_TRANSITIONS,
    GrievanceCreate,
    GrievanceRecord,
    GrievanceUpdate,
)

logger = get_logger("grievance.service")


class GrievanceError(Exception):
    pass


def _is_overdue(g: Grievance, now: datetime | None = None) -> bool:
    if g.status in {"RESOLVED", "CLOSED"}:
        return False
    now = now or datetime.now(UTC)
    due = g.due_at
    # SQLite may return naive datetimes; treat as UTC.
    if due.tzinfo is None:
        due = due.replace(tzinfo=UTC)
    return now > due


def to_record(g: Grievance) -> GrievanceRecord:
    return GrievanceRecord(
        id=g.id,
        borrower_id=g.borrower_id,
        score_id=g.score_id,
        loan_application_id=g.loan_application_id,
        category=g.category,
        description=g.description,
        status=g.status,
        sla_hours=g.sla_hours,
        assigned_to=g.assigned_to,
        resolution_notes=g.resolution_notes,
        created_at=g.created_at,
        due_at=g.due_at,
        resolved_at=g.resolved_at,
        is_overdue=_is_overdue(g),
    )


class GrievanceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, req: GrievanceCreate, actor: str) -> Grievance:
        # Validate borrower exists (grievance is borrower-scoped)
        bres = await self.db.execute(
            select(Borrower).where(Borrower.id == req.borrower_id)
        )
        if bres.scalar_one_or_none() is None:
            raise GrievanceError(f"Borrower {req.borrower_id} not found")

        now = datetime.now(UTC)
        due = now + timedelta(hours=req.sla_hours)
        g = Grievance(
            borrower_id=req.borrower_id,
            score_id=req.score_id,
            loan_application_id=req.loan_application_id,
            category=req.category.value,
            description=req.description,
            status="OPEN",
            sla_hours=req.sla_hours,
            due_at=due,
        )
        self.db.add(g)
        await self.db.flush()
        self.db.add(
            GrievanceAuditLog(
                grievance_id=g.id,
                from_status=None,
                to_status="OPEN",
                actor=actor,
                note="Grievance opened",
            )
        )
        await self.db.commit()
        logger.info("grievance_created", grievance_id=str(g.id), category=req.category.value)
        return g

    async def get(self, grievance_id: uuid.UUID) -> Grievance:
        r = await self.db.execute(select(Grievance).where(Grievance.id == grievance_id))
        g = r.scalar_one_or_none()
        if g is None:
            raise GrievanceError(f"Grievance {grievance_id} not found")
        return g

    async def list(
        self,
        *,
        status: str | None = None,
        borrower_id: uuid.UUID | None = None,
        include_overdue_only: bool = False,
    ) -> list[Grievance]:
        stmt = select(Grievance).order_by(Grievance.created_at.desc())
        if status:
            stmt = stmt.where(Grievance.status == status.upper())
        if borrower_id:
            stmt = stmt.where(Grievance.borrower_id == borrower_id)
        rows = await self.db.execute(stmt)
        items = list(rows.scalars().all())
        if include_overdue_only:
            items = [g for g in items if _is_overdue(g)]
        return items

    async def update(
        self,
        grievance_id: uuid.UUID,
        req: GrievanceUpdate,
        actor: str,
    ) -> Grievance:
        g = await self.get(grievance_id)
        new_status = req.status.value
        if new_status not in ALLOWED_TRANSITIONS.get(g.status, set()) and new_status != g.status:
            raise GrievanceError(
                f"Invalid transition {g.status} -> {new_status}"
            )
        prev = g.status
        g.status = new_status
        if req.assigned_to is not None:
            g.assigned_to = req.assigned_to
        if req.resolution_notes is not None:
            g.resolution_notes = req.resolution_notes
        if new_status in {"RESOLVED", "CLOSED"} and g.resolved_at is None:
            g.resolved_at = datetime.now(UTC)

        self.db.add(
            GrievanceAuditLog(
                grievance_id=g.id,
                from_status=prev,
                to_status=new_status,
                actor=actor,
                note=req.note,
            )
        )
        await self.db.commit()
        logger.info(
            "grievance_status_updated",
            grievance_id=str(g.id), from_status=prev, to_status=new_status,
        )
        return g

    async def escalate_overdue(self, actor: str = "system") -> int:
        """Auto-escalate OPEN/IN_REVIEW grievances past SLA. Returns count."""
        items = await self.list(include_overdue_only=True)
        n = 0
        for g in items:
            if g.status in {"OPEN", "IN_REVIEW"}:
                prev = g.status
                g.status = "ESCALATED"
                self.db.add(
                    GrievanceAuditLog(
                        grievance_id=g.id,
                        from_status=prev,
                        to_status="ESCALATED",
                        actor=actor,
                        note="Auto-escalated (SLA exceeded)",
                    )
                )
                n += 1
        if n:
            await self.db.commit()
        return n

    async def get_audit_trail(self, grievance_id: uuid.UUID) -> list[GrievanceAuditLog]:
        r = await self.db.execute(
            select(GrievanceAuditLog)
            .where(GrievanceAuditLog.grievance_id == grievance_id)
            .order_by(GrievanceAuditLog.performed_at.asc())
        )
        return list(r.scalars().all())


__all__ = ["GrievanceService", "GrievanceError", "to_record"]

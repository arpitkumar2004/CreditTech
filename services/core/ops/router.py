"""P6 — Ops router: smoke tests + DR."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from services.core.decisioning.auth import require_officer

from .smoke import run_all

router = APIRouter(prefix="/ops", tags=["Ops — Smoke Tests & DR"])


@router.post("/smoke/integrations", summary="Run production-integration smoke checks")
async def smoke_integrations(_: str = Depends(require_officer)) -> dict:
    return await run_all()


__all__ = ["router"]

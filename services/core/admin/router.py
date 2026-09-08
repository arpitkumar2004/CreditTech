"""P6 — Admin router: model promotion + fairness gate inspection."""

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.decisioning.auth import require_admin, require_officer
from services.core.monitoring.governance import (
    FairnessGate,
    ManifestError,
    load_manifest,
    manifest_hash,
)

from ml.registry import ModelRegistry
from .promotion import ModelPromotionService, PromotionBlocked

router = APIRouter(prefix="/admin", tags=["Admin — Model Promotion & Governance"])


@router.get("/models", summary="List all registered models with metrics and promotion status")
async def list_models(_: str = Depends(require_officer)) -> list[dict]:
    reg = ModelRegistry()
    return [m.to_dict() for m in reg.list_models()]


@router.get("/fairness/manifest", summary="Read the ratified fairness threshold manifest")
async def get_manifest(_: str = Depends(require_officer)) -> dict:
    try:
        m = load_manifest()
    except ManifestError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"manifest_hash": manifest_hash(m), "manifest": m}


@router.get("/fairness/gate", summary="Evaluate FairnessGate on the latest period")
async def evaluate_gate(
    period: str | None = None,
    _: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    gate = FairnessGate(db)
    result = await gate.evaluate(period=period)
    return result.to_dict()


@router.post("/models/{model_version}/promote", summary="Promote a model to active (gated)")
async def promote_model(
    model_version: str,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ModelPromotionService(db)
    try:
        report = await svc.promote_to_active(model_version)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PromotionBlocked as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.report.to_dict())
    return {"promoted": True, "report": report.to_dict()}


@router.get("/models/{model_version}/promotion-check", summary="Dry-run promotion check")
async def promotion_check(
    model_version: str,
    _: str = Depends(require_officer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ModelPromotionService(db)
    try:
        report = await svc.evaluate(model_version)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return report.to_dict()


@router.get("/report/html", response_class=HTMLResponse, summary="Serve publication-grade model evaluation report")
async def get_model_evaluation_report(_: str = Depends(require_officer)) -> HTMLResponse:
    report_path = Path("data/reports/CreditTech_Comprehensive_Model_Report.html")
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Model evaluation report not found.")
    return HTMLResponse(content=report_path.read_text(encoding="utf-8"))


__all__ = ["router"]

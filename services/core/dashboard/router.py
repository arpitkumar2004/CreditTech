"""Institutional dashboard endpoints + score-report renderer.

Read-only. Officer-header authenticated for the pilot. The RE partner and
NABARD stakeholder both consume from these endpoints (§17.2).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.decisioning.auth import require_officer
from services.core.monitoring.service import FairnessAuditor

from .pdf import html_to_pdf
from .service import DashboardError, DashboardService

router = APIRouter(prefix="/dashboard", tags=["Institutional Dashboard"])


@router.get("/portfolio", summary="Portfolio metrics (aggregate, non-PII)")
async def portfolio(
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await DashboardService(db).portfolio_metrics()


@router.get("/charts", summary="Persona-tailored decision graphs and charts")
async def dashboard_charts(
    persona: str = Query(default="admin", description="Target persona: admin, officer, or borrower"),
    model_version: str | None = Query(default=None, description="Optional model version filter"),
    borrower_id: uuid.UUID | None = Query(default=None, description="Optional borrower UUID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await DashboardService(db).get_persona_charts(
        persona=persona,
        borrower_id=borrower_id,
        model_version=model_version,
    )


@router.get("/fairness", summary="Latest fairness audit rows")
async def fairness(
    period: str | None = Query(default=None),
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await DashboardService(db).fairness_latest(period=period)


@router.get(
    "/fairness/export.csv",
    summary="Fairness export (CSV for external auditor)",
    response_class=Response,
)
async def fairness_export(
    period: str | None = Query(default=None),
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> Response:
    csv_data = await FairnessAuditor(db).export_csv(period=period)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=fairness_audit_{period or 'all'}.csv"
            )
        },
    )


report_router = APIRouter(prefix="/report", tags=["Score Report"])


@report_router.get(
    "/score/{score_id}",
    summary="Branded HTML score report for a scored application",
    response_class=HTMLResponse,
)
async def score_report(
    score_id: uuid.UUID,
    partner_re_id: str | None = Query(default=None),
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    try:
        html = await DashboardService(db).render_score_report_html(
            score_id, partner_re_id=partner_re_id
        )
    except DashboardError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return HTMLResponse(content=html, status_code=200)


@report_router.get(
    "/score/{score_id}/pdf",
    summary="Branded PDF score report (P6)",
    response_class=Response,
)
async def score_report_pdf(
    score_id: uuid.UUID,
    partner_re_id: str | None = Query(default=None),
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        html_str = await DashboardService(db).render_score_report_html(
            score_id, partner_re_id=partner_re_id
        )
    except DashboardError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    pdf_bytes, backend = html_to_pdf(html_str)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="score_{score_id}.pdf"',
            "X-PDF-Backend": backend,
        },
    )

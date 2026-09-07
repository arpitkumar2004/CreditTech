"""FastAPI router for monitoring metrics and data retention jobs."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.database import get_db
from services.core.decisioning.auth import require_officer
from services.core.shared.logging import get_logger

from .service import DataRetentionWorker, DriftMonitorService, FairnessAuditor

logger = get_logger("monitoring.router")
router = APIRouter(prefix="/monitoring", tags=["Monitoring & Compliance"])


@router.post(
    "/fairness-audit",
    status_code=status.HTTP_200_OK,
    summary="Trigger weekly fairness audit calculations",
)
async def run_fairness_audit(
    period: str = Query(..., description="Audit period label, e.g. '2026-W35'"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculates approval and override rates across demographic subgroups and saves logs in DB."""
    auditor = FairnessAuditor(db)
    try:
        logs = await auditor.run_audit(period)
        return {
            "status": "success",
            "period": period,
            "records_audited": len(logs),
            "message": "Demographic parity metrics calculated and logged.",
        }
    except Exception as e:
        logger.error("fairness_audit_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit failed: {e}",
        )


@router.post(
    "/retention-purge",
    status_code=status.HTTP_200_OK,
    summary="Trigger DPDP data retention cleanup loop",
)
async def run_retention_purge(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Scans and purges PII columns for borrowers with expired/revoked consents."""
    worker = DataRetentionWorker(db)
    try:
        purged_count = await worker.purge_expired_consent_data()
        return {
            "status": "success",
            "purged_records_count": purged_count,
            "message": f"Successfully anonymized PII profiles for {purged_count} borrowers.",
        }
    except Exception as e:
        logger.error("retention_purge_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retention job failed: {e}",
        )


@router.get(
    "/fairness-audit",
    summary="List persisted fairness audit rows (filter by period/dimension)",
)
async def list_fairness_audits(
    period: str | None = Query(default=None),
    dimension: str | None = Query(default=None),
    officer_id: str = Depends(require_officer),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = await FairnessAuditor(db).list_logs(period=period, dimension=dimension)
    return {
        "count": len(rows),
        "rows": [
            {
                "id": str(r.id),
                "period": r.period,
                "dimension": r.dimension,
                "group_value": r.group_value,
                "sample_size": r.sample_size,
                "approval_rate": r.approval_rate,
                "override_rate": r.override_rate,
                "status": r.status,
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            }
            for r in rows
        ],
    }


@router.get(
    "/fairness-audit/export.csv",
    summary="CSV export of fairness audit rows",
    response_class=Response,
)
async def export_fairness_audits(
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


@router.get(
    "/drift",
    summary="Retrieve Population Stability Index (PSI) and Characteristic Stability Index (CSI) drift metrics",
)
async def get_drift_metrics(
    limit: int = Query(500, description="Max historical scores/features to evaluate"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculates operational and seasonal distribution drift across live scoring data."""
    monitor = DriftMonitorService(db)
    try:
        return await monitor.compute_drift_audit(limit=limit)
    except Exception as e:
        logger.error("drift_audit_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift audit failed: {e}",
        )

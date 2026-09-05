"""Portfolio metrics, fairness views, and branded score-report artifact."""

from __future__ import annotations

import uuid
from html import escape

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.core.decisioning.service import recommendation_for_band
from services.core.scoring.service import ScoringService
from services.core.shared.models import (
    Borrower,
    FairnessAuditLog,
    Grievance,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)


class DashboardError(Exception):
    pass


class DashboardService:
    """Portfolio/monitoring aggregates. Non-PII, aggregate metrics only."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def portfolio_metrics(self) -> dict:
        total_apps = (await self.db.execute(
            select(func.count(LoanApplication.id))
        )).scalar_one()
        approved = (await self.db.execute(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.officer_decision == "APPROVED"
            )
        )).scalar_one()
        rejected = (await self.db.execute(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.officer_decision == "REJECTED"
            )
        )).scalar_one()
        more_info = (await self.db.execute(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.officer_decision == "MORE_INFO_REQUIRED"
            )
        )).scalar_one()
        pending = (await self.db.execute(
            select(func.count(LoanApplication.id)).where(
                LoanApplication.officer_decision.is_(None)
            )
        )).scalar_one()
        disbursement = (await self.db.execute(
            select(func.coalesce(func.sum(LoanApplication.requested_amount), 0.0)).where(
                LoanApplication.officer_decision == "APPROVED"
            )
        )).scalar_one()
        scores = (await self.db.execute(select(func.count(Score.id)))).scalar_one()
        borrowers = (await self.db.execute(select(func.count(Borrower.id)))).scalar_one()
        override_count = (await self.db.execute(
            select(func.count(OfficerDecisionLog.id)).where(
                OfficerDecisionLog.is_override.is_(True)
            )
        )).scalar_one()
        decisions_total = (await self.db.execute(
            select(func.count(OfficerDecisionLog.id))
        )).scalar_one()
        grievances_open = (await self.db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.status.in_(["OPEN", "IN_REVIEW", "ESCALATED"])
            )
        )).scalar_one()
        return {
            "borrowers": int(borrowers),
            "scores_generated": int(scores),
            "applications_total": int(total_apps),
            "applications_pending": int(pending),
            "applications_approved": int(approved),
            "applications_rejected": int(rejected),
            "applications_more_info": int(more_info),
            "approval_rate": (float(approved) / total_apps) if total_apps else None,
            "disbursed_amount_approved": float(disbursement),
            "officer_decisions_total": int(decisions_total),
            "officer_override_count": int(override_count),
            "officer_override_rate": (
                float(override_count) / decisions_total if decisions_total else None
            ),
            "grievances_open": int(grievances_open),
        }

    async def fairness_latest(self, period: str | None = None) -> dict:
        stmt = select(FairnessAuditLog)
        if period:
            stmt = stmt.where(FairnessAuditLog.period == period)
        else:
            latest_period = (
                await self.db.execute(
                    select(FairnessAuditLog.period)
                    .order_by(FairnessAuditLog.computed_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if not latest_period:
                return {"period": None, "rows": [], "note": "No fairness audits have been run."}
            stmt = stmt.where(FairnessAuditLog.period == latest_period)
            period = latest_period
        rows = (await self.db.execute(stmt.order_by(
            FairnessAuditLog.dimension, FairnessAuditLog.group_value
        ))).scalars().all()
        return {
            "period": period,
            "rows": [
                {
                    "dimension": r.dimension,
                    "group_value": r.group_value,
                    "sample_size": r.sample_size,
                    "approval_rate": r.approval_rate,
                    "override_rate": r.override_rate,
                    "status": r.status,
                }
                for r in rows
            ],
            "governance_note": (
                "Descriptive statistics only. Parity thresholds are ratified "
                "separately by the external fairness auditor (§8.3, §17.2). "
                "Rows with status='INSUFFICIENT_SAMPLE' are informational."
            ),
        }

    async def render_score_report_html(
        self, score_id: uuid.UUID, partner_re_id: str | None = None
    ) -> str:
        """Branded HTML score report for a scored application."""
        r = await self.db.execute(
            select(Score)
            .options(selectinload(Score.reason_codes))
            .where(Score.id == score_id)
        )
        score = r.scalar_one_or_none()
        if score is None:
            raise DashboardError(f"Score {score_id} not found")
        b = (await self.db.execute(
            select(Borrower).where(Borrower.id == score.borrower_id)
        )).scalar_one()
        village = None
        if b.village_id:
            village = (await self.db.execute(
                select(Village).where(Village.id == b.village_id)
            )).scalar_one_or_none()
        latest_decision = (await self.db.execute(
            select(OfficerDecisionLog)
            .where(OfficerDecisionLog.score_id == score.id)
            .order_by(OfficerDecisionLog.created_at.desc())
        )).scalars().first()

        band = ScoringService.get_score_band(score.score)
        rec = recommendation_for_band(band)
        svc = ScoringService(self.db, model_version=score.model_version)
        _, score_900 = svc.scorecard.calibrate_score(score.score / 100.0)

        reasons_html = "".join(
            f"<li><strong>{escape(rc.direction)}</strong> "
            f"{escape(rc.localized_text_en)}"
            f"{(' — ' + escape(rc.localized_text_hi)) if rc.localized_text_hi else ''}"
            f"</li>"
            for rc in sorted(score.reason_codes, key=lambda x: x.rank)
        ) or "<li>(No reason codes recorded)</li>"

        decision_block = "<p><em>No officer decision recorded yet.</em></p>"
        if latest_decision:
            decision_block = (
                f"<p><strong>Decision:</strong> {escape(latest_decision.decision)}<br/>"
                f"<strong>Officer:</strong> {escape(latest_decision.officer_id)}<br/>"
                f"<strong>Override:</strong> {'Yes' if latest_decision.is_override else 'No'}<br/>"
                f"<strong>Reason:</strong> {escape(latest_decision.override_reason or '—')}</p>"
            )

        return f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>CreditTech Score Report — {score.id}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 780px; margin: 2rem auto; color: #222; }}
  header {{ border-bottom: 3px solid #1a3a6c; padding-bottom: 12px; margin-bottom: 20px; }}
  h1 {{ color: #1a3a6c; margin: 0 0 4px 0; }}
  .meta {{ color: #666; font-size: 0.9rem; }}
  .score-card {{ background: #f4f7fb; padding: 16px; border-left: 5px solid #1a3a6c; margin: 16px 0; }}
  .band-EXCELLENT, .band-GOOD {{ color: #0a7d2b; }}
  .band-MODERATE {{ color: #b8860b; }}
  .band-HIGH_RISK, .band-VERY_HIGH_RISK {{ color: #b12727; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  td, th {{ padding: 6px 10px; border-bottom: 1px solid #e0e0e0; text-align: left; }}
  footer {{ font-size: 0.8rem; color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }}
</style></head><body>
<header>
  <h1>CreditTech — Alternative Credit Score Report</h1>
  <div class="meta">Score ID: {score.id} · Generated: {escape(score.generated_at.isoformat())}
    {(' · Partner RE: ' + escape(partner_re_id)) if partner_re_id else ''}</div>
</header>

<h2>Borrower (non-PII summary)</h2>
<table>
  <tr><th>Borrower ID</th><td>{b.id}</td></tr>
  <tr><th>Gender</th><td>{escape(b.gender or '—')}</td></tr>
  <tr><th>Age band</th><td>{b.age or '—'}</td></tr>
  <tr><th>Landholding</th><td>{escape(b.landholding_band or '—')}</td></tr>
  <tr><th>Village</th><td>{escape(village.name if village else '—')}</td></tr>
  <tr><th>District / State</th><td>{escape(village.district if village else '—')} / {escape(village.state if village else '—')}</td></tr>
</table>

<div class="score-card">
  <h2>Score</h2>
  <p><strong>Score:</strong> {score.score:.1f} / 100 (900-scale: {score_900})<br/>
     <strong>Band:</strong> <span class="band-{band}">{band}</span><br/>
     <strong>Confidence:</strong> [{score.confidence_lower:.1f}, {score.confidence_upper:.1f}]<br/>
     <strong>Model:</strong> {escape(score.model_version)} · <strong>Features:</strong> {escape(svc.scorecard.feature_version)}<br/>
     <strong>Model recommendation:</strong> {rec.value}</p>
</div>

<h2>Reason codes</h2>
<ol>{reasons_html}</ol>

<h2>Officer decision</h2>
{decision_block}

<footer>
  This report was generated by the CreditTech pilot service. The loan officer remains
  the final decision-maker; the model contributes a recommendation only. Auditable
  decision trail is stored in <code>officer_decision_log</code>.
</footer>
</body></html>"""

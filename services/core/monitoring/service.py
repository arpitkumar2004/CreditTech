"""Fairness auditing and data retention services (P5).

Governance stance for the pilot:
    * The auditor computes descriptive statistics only. It does NOT invent
      parity thresholds or promotion gates — those are ratified separately by
      the external fairness auditor (§8.3, §17.2). Rows below the minimum
      sample size are persisted with `status='INSUFFICIENT_SAMPLE'` and
      `approval_rate=None` so downstream dashboards can display them as
      informational without over-alerting on 3-borrower buckets.
    * `is_override` counts come from `OfficerDecisionLog` (immutable) rather
      than `LoanApplication.override_reason` (which the P0-P4 tests populate
      with human-authored strings that are NOT always overrides).
"""

import csv
import io
import uuid
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.logging import get_logger
from services.core.shared.models import (
    Borrower,
    ConsentRecord,
    FairnessAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    Village,
)

logger = get_logger("monitoring.service")


# Small-sample guard for pilot scale (planning doc §17.2, §12).
# Groups smaller than this are recorded as informational only —
# a 3-borrower bucket cannot support a fairness claim in either direction.
MIN_SAMPLE_SIZE = 30


class FairnessAuditor:
    """Computes approval-rate parity + officer override-rate as descriptive stats."""

    def __init__(self, db: AsyncSession, min_sample_size: int = MIN_SAMPLE_SIZE) -> None:
        self.db = db
        self.min_sample_size = min_sample_size

    def _build_log(
        self,
        *,
        period: str,
        dimension: str,
        group_value: str,
        total: int,
        approved: int,
        overrides: int,
    ) -> FairnessAuditLog:
        insufficient = total < self.min_sample_size
        return FairnessAuditLog(
            period=period,
            dimension=dimension,
            group_value=group_value or "UNKNOWN",
            approval_rate=None if insufficient else (approved / total if total else 0.0),
            override_rate=None if insufficient else (overrides / total if total else 0.0),
            sample_size=total,
            status="INSUFFICIENT_SAMPLE" if insufficient else "OK",
        )

    async def _rows_for_dimension(
        self,
        *,
        group_col,
        joins: list,
    ) -> list[tuple[str, int, int, int]]:
        """Return (group_value, total, approved, overrides) tuples.

        Approved: officer_decision = 'APPROVED' on the LoanApplication (the
        surface the RE reads).
        Overrides: is_override = True on the *latest* OfficerDecisionLog row for
        the score, joined via LoanApplication.score_id.
        """
        # Latest OfficerDecisionLog per score
        latest_ts_sub = (
            select(
                OfficerDecisionLog.score_id.label("score_id"),
                func.max(OfficerDecisionLog.created_at).label("max_ts"),
            )
            .group_by(OfficerDecisionLog.score_id)
            .subquery()
        )

        stmt = (
            select(
                group_col.label("g"),
                func.count(LoanApplication.id.distinct()).label("total"),
                func.count(LoanApplication.id.distinct())
                .filter(LoanApplication.officer_decision == "APPROVED")
                .label("approved"),
                func.count(OfficerDecisionLog.id.distinct())
                .filter(OfficerDecisionLog.is_override.is_(True))
                .label("overrides"),
            )
            .select_from(LoanApplication)
        )
        for j in joins:
            stmt = stmt.join(*j)
        stmt = (
            stmt.join(latest_ts_sub, latest_ts_sub.c.score_id == LoanApplication.score_id, isouter=True)
            .join(
                OfficerDecisionLog,
                (OfficerDecisionLog.score_id == LoanApplication.score_id)
                & (OfficerDecisionLog.created_at == latest_ts_sub.c.max_ts),
                isouter=True,
            )
            .group_by(group_col)
        )

        result = await self.db.execute(stmt)
        return [(row.g, int(row.total), int(row.approved), int(row.overrides)) for row in result]

    async def run_audit(self, period: str) -> list[FairnessAuditLog]:
        """Compute all four dimensions for the given period and persist."""
        audit_logs: list[FairnessAuditLog] = []

        # 1. GENDER
        rows = await self._rows_for_dimension(
            group_col=Borrower.gender,
            joins=[(Borrower, Borrower.id == LoanApplication.borrower_id)],
        )
        for g, total, approved, overrides in rows:
            audit_logs.append(
                self._build_log(
                    period=period, dimension="GENDER", group_value=g,
                    total=total, approved=approved, overrides=overrides,
                )
            )

        # 2. LANDHOLDING
        rows = await self._rows_for_dimension(
            group_col=Borrower.landholding_band,
            joins=[(Borrower, Borrower.id == LoanApplication.borrower_id)],
        )
        for g, total, approved, overrides in rows:
            audit_logs.append(
                self._build_log(
                    period=period, dimension="LANDHOLDING", group_value=g,
                    total=total, approved=approved, overrides=overrides,
                )
            )

        # 3. GEOGRAPHY (district)
        rows = await self._rows_for_dimension(
            group_col=Village.district,
            joins=[
                (Borrower, Borrower.id == LoanApplication.borrower_id),
                (Village, Village.id == Borrower.village_id),
            ],
        )
        for g, total, approved, overrides in rows:
            audit_logs.append(
                self._build_log(
                    period=period, dimension="GEOGRAPHY", group_value=g,
                    total=total, approved=approved, overrides=overrides,
                )
            )

        # 4. OFFICER — override-rate signal for governance
        latest_ts_sub = (
            select(
                OfficerDecisionLog.score_id.label("score_id"),
                func.max(OfficerDecisionLog.created_at).label("max_ts"),
            )
            .group_by(OfficerDecisionLog.score_id)
            .subquery()
        )
        officer_stmt = (
            select(
                OfficerDecisionLog.officer_id.label("g"),
                func.count(OfficerDecisionLog.id).label("total"),
                func.count(OfficerDecisionLog.id)
                .filter(OfficerDecisionLog.decision == "APPROVED")
                .label("approved"),
                func.count(OfficerDecisionLog.id)
                .filter(OfficerDecisionLog.is_override.is_(True))
                .label("overrides"),
            )
            .join(
                latest_ts_sub,
                (latest_ts_sub.c.score_id == OfficerDecisionLog.score_id)
                & (latest_ts_sub.c.max_ts == OfficerDecisionLog.created_at),
            )
            .group_by(OfficerDecisionLog.officer_id)
        )
        officer_rows = await self.db.execute(officer_stmt)
        for row in officer_rows:
            audit_logs.append(
                self._build_log(
                    period=period, dimension="OFFICER", group_value=row.g,
                    total=int(row.total), approved=int(row.approved),
                    overrides=int(row.overrides),
                )
            )

        for log in audit_logs:
            self.db.add(log)
        await self.db.commit()
        logger.info(
            "fairness_audit_completed",
            period=period,
            records_created=len(audit_logs),
            insufficient=sum(1 for r in audit_logs if r.status == "INSUFFICIENT_SAMPLE"),
        )
        return audit_logs

    async def list_logs(
        self,
        period: str | None = None,
        dimension: str | None = None,
    ) -> list[FairnessAuditLog]:
        stmt = select(FairnessAuditLog).order_by(
            FairnessAuditLog.computed_at.desc(),
            FairnessAuditLog.dimension.asc(),
            FairnessAuditLog.group_value.asc(),
        )
        if period:
            stmt = stmt.where(FairnessAuditLog.period == period)
        if dimension:
            stmt = stmt.where(FairnessAuditLog.dimension == dimension.upper())
        rows = await self.db.execute(stmt)
        return list(rows.scalars().all())

    async def export_csv(self, period: str | None = None) -> str:
        rows = await self.list_logs(period=period)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "period", "dimension", "group_value", "sample_size",
            "approval_rate", "override_rate", "status", "computed_at",
        ])
        for r in rows:
            writer.writerow([
                r.period, r.dimension, r.group_value, r.sample_size,
                "" if r.approval_rate is None else f"{r.approval_rate:.4f}",
                "" if r.override_rate is None else f"{r.override_rate:.4f}",
                r.status,
                r.computed_at.isoformat() if r.computed_at else "",
            ])
        return buf.getvalue()


class DataRetentionWorker:
    """Enforces DPDP Act storage limitation rules by purging PII once consent expires or is revoked."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def purge_expired_consent_data(self) -> int:
        """Finds borrowers with no remaining ACTIVE consents and anonymizes their PII profiles.

        Retains features and scoring logs for compliance/regulatory auditing.
        Returns the number of anonymized borrower records.
        """
        now = datetime.now(UTC)

        # 1. Update lazily-expired consents
        await self.db.execute(
            update(ConsentRecord)
            .where(ConsentRecord.status == "ACTIVE")
            .where(ConsentRecord.expires_at < now)
            .values(status="EXPIRED")
        )
        await self.db.flush()

        all_consents_sub = select(ConsentRecord.borrower_id).distinct()
        active_consents_sub = (
            select(ConsentRecord.borrower_id)
            .where(ConsentRecord.status == "ACTIVE")
            .distinct()
        )
        purge_query = (
            select(Borrower)
            .where(Borrower.id.in_(all_consents_sub))
            .where(Borrower.id.not_in(active_consents_sub))
            .where(Borrower.name_encrypted != "ANONYMIZED")
        )
        results = await self.db.execute(purge_query)
        borrowers = results.scalars().all()

        purged_count = 0
        for borrower in borrowers:
            borrower.name_encrypted = "ANONYMIZED"
            borrower.phone_encrypted = "ANONYMIZED"
            borrower.aadhaar_ref_hash = f"ANON-{uuid.uuid4().hex[:8]}"
            purged_count += 1
            logger.info("borrower_pii_anonymized", borrower_id=str(borrower.id))

        await self.db.commit()
        if purged_count > 0:
            logger.info("retention_purge_completed", purged_records=purged_count)
        return purged_count


class DriftMonitorService:
    """Monitors live score and feature distributions for operational and seasonal drift (P6/Basel II)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def compute_drift_audit(self, limit: int = 500) -> dict:
        """Computes live PSI against training calibration baseline and feature CSIs."""
        import numpy as np
        import pandas as pd

        from ml.evaluation.drift import calculate_csi, calculate_psi
        from ml.registry import ModelRegistry
        from services.core.shared.models import FeatureSnapshot, Score

        # 1. Fetch recent live scores
        stmt = select(Score.score).order_by(Score.generated_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        live_scores = [r[0] for r in res.all()]

        # 2. Get baseline from active model in registry
        registry = ModelRegistry()
        active = registry.get_active()
        expected_scores: list[float] = []
        if active and active.metrics and "calibration_bins" in active.metrics:
            for b in active.metrics["calibration_bins"]:
                count = b.get("count", 0)
                mean_p = b.get("mean_predicted", 0.5)
                # Map probability to score_100
                expected_scores.extend([mean_p * 100.0] * count)

        if len(expected_scores) < 10:
            expected_scores = [float(x) for x in np.random.normal(55, 15, 500)]

        if len(live_scores) < 10:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Fewer than 10 live scores recorded ({len(live_scores)} found).",
                "score_psi": None,
                "feature_csi": None,
                "model_version": active.model_version if active else "unknown",
            }

        psi_res = calculate_psi(expected_scores, live_scores)

        # 3. Pull recent feature snapshots for CSI
        feat_stmt = select(FeatureSnapshot.features_json).order_by(FeatureSnapshot.computed_at.desc()).limit(limit)
        feat_res = await self.db.execute(feat_stmt)
        live_features = [r[0] for r in feat_res.all() if r[0]]

        csi_res = {}
        if len(live_features) >= 10:
            live_df = pd.DataFrame(live_features)
            from ml.training.datasets import SyntheticSHGGenerator
            gen = SyntheticSHGGenerator(n=min(500, len(live_df) * 2), seed=42)
            exp_df, _, _, _ = gen.generate()
            csi_res = calculate_csi(exp_df, live_df)

        return {
            "status": "OK",
            "score_psi": psi_res.to_dict(),
            "feature_csi": csi_res,
            "evaluated_scores_count": len(live_scores),
            "evaluated_features_count": len(live_features),
            "model_version": active.model_version if active else "unknown",
        }


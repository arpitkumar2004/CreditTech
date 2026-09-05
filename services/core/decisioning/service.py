"""Decisioning service — assembles review pack, captures officer decisions.

Design invariants (P4):
    * The model does NOT decide. The officer is the decision-maker; the model
      contributes a recommendation and reason codes.
    * override_reason is MANDATORY when officer's decision does not match the
      model recommendation (as defined by score band -> recommendation map).
    * OfficerDecisionLog rows are append-only. If a decision needs to change,
      a new row is inserted; the earlier one remains for audit.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.core.scoring.service import ScoringService
from services.core.shared.logging import get_logger
from services.core.shared.models import (
    Borrower,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)

from .schemas import (
    DecisionRequest,
    ModelRecommendation,
    OfficerDecision,
    OfficerDecisionRecord,
    ReviewPayload,
    ReviewReasonCode,
    SourceStatus,
)

logger = get_logger("decisioning.service")

EXPECTED_RAILS = ("AA", "GEOSPATIAL", "SHG_FPO", "BUREAU")


class DecisioningError(Exception):
    pass


def recommendation_for_band(band: str) -> ModelRecommendation:
    """Score band -> model recommendation.

    Matches the RE contract band mapping (docs/phase0/re_api_handoff_spec.md §4):
        EXCELLENT/GOOD -> APPROVE
        MODERATE       -> REVIEW (loan-officer discretion)
        HIGH_RISK/VERY_HIGH_RISK -> REJECT
    """
    if band in ("EXCELLENT", "GOOD"):
        return ModelRecommendation.APPROVE
    if band == "MODERATE":
        return ModelRecommendation.REVIEW
    return ModelRecommendation.REJECT


def is_override(decision: OfficerDecision, rec: ModelRecommendation) -> bool:
    """A decision is an override when it disagrees with the model.

    REVIEW recommendations are inherently discretionary and never count as an
    override — no matter what the officer chooses — because the model itself
    declined to recommend a specific action.
    """
    if rec == ModelRecommendation.REVIEW:
        return False
    if rec == ModelRecommendation.APPROVE:
        return decision != OfficerDecision.APPROVED
    # REJECT
    return decision != OfficerDecision.REJECTED


class DecisioningService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _load_score(self, score_id: uuid.UUID) -> Score:
        result = await self.db.execute(
            select(Score)
            .options(selectinload(Score.reason_codes))
            .where(Score.id == score_id)
        )
        score = result.scalar_one_or_none()
        if not score:
            raise DecisioningError(f"Score {score_id} not found")
        return score

    async def build_review_payload(self, score_id: uuid.UUID) -> ReviewPayload:
        score = await self._load_score(score_id)

        borrower_result = await self.db.execute(
            select(Borrower).where(Borrower.id == score.borrower_id)
        )
        borrower = borrower_result.scalar_one()
        village_row: Village | None = None
        if borrower.village_id is not None:
            v = await self.db.execute(
                select(Village).where(Village.id == borrower.village_id)
            )
            village_row = v.scalar_one_or_none()

        band = ScoringService.get_score_band(score.score)
        rec = recommendation_for_band(band)

        prob_repay = score.score / 100.0
        service = ScoringService(self.db, model_version=score.model_version)
        _, score_900 = service.scorecard.calibrate_score(prob_repay)
        feature_version = service.scorecard.feature_version

        sources_used = list(score.sources_used or [])
        source_status = [
            SourceStatus(source=s, available=s in sources_used)
            for s in EXPECTED_RAILS
        ]
        partial = any(not st.available for st in source_status)

        reason_codes = [
            ReviewReasonCode(
                rank=rc.rank,
                feature_name=rc.feature_name,
                direction=rc.direction,
                shap_value=rc.shap_value,
                localized_text_en=rc.localized_text_en,
                localized_text_hi=rc.localized_text_hi,
            )
            for rc in sorted(score.reason_codes, key=lambda r: r.rank)
        ]

        # If there is any existing decision, surface the most recent one.
        existing_result = await self.db.execute(
            select(OfficerDecisionLog)
            .where(OfficerDecisionLog.score_id == score.id)
            .order_by(OfficerDecisionLog.created_at.desc())
        )
        existing = existing_result.scalars().first()

        return ReviewPayload(
            score_id=score.id,
            borrower_id=borrower.id,
            borrower_summary={
                "borrower_id": str(borrower.id),
                "gender": borrower.gender,
                "age": borrower.age,
                "landholding_band": borrower.landholding_band,
                "village": village_row.name if village_row else None,
                "district": village_row.district if village_row else None,
                "state": village_row.state if village_row else None,
                "language": borrower.language,
            },
            score=score.score,
            score_900=score_900,
            score_band=band,
            confidence_lower=score.confidence_lower,
            confidence_upper=score.confidence_upper,
            model_version=score.model_version,
            feature_version=feature_version,
            model_recommendation=rec,
            sources_used=sources_used,
            source_status=source_status,
            partial_data=partial,
            reason_codes=reason_codes,
            generated_at=score.generated_at,
            existing_decision=(
                OfficerDecisionRecord.model_validate(existing) if existing else None
            ),
        )

    async def record_decision(
        self,
        request: DecisionRequest,
        officer_id: str,
    ) -> OfficerDecisionLog:
        score = await self._load_score(request.score_id)
        band = ScoringService.get_score_band(score.score)
        rec = recommendation_for_band(band)
        override = is_override(request.decision, rec)

        if override and not request.override_reason:
            raise DecisioningError(
                "override_reason is required when the officer's decision "
                f"({request.decision.value}) differs from the model "
                f"recommendation ({rec.value})."
            )
        if not override and request.override_reason:
            raise DecisioningError(
                "override_reason must be empty when the decision matches "
                "the model recommendation."
            )

        # If a LoanApplication already exists for this score, link it.
        la_result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.score_id == score.id)
        )
        loan_app = la_result.scalars().first()

        service = ScoringService(self.db, model_version=score.model_version)

        entry = OfficerDecisionLog(
            score_id=score.id,
            loan_application_id=loan_app.id if loan_app else None,
            officer_id=officer_id,
            decision=request.decision.value,
            model_recommendation=rec.value,
            is_override=override,
            override_reason=request.override_reason,
            officer_notes=request.officer_notes,
            model_score_at_decision=score.score,
            model_version_at_decision=score.model_version,
            feature_version_at_decision=service.scorecard.feature_version,
        )
        self.db.add(entry)
        await self.db.flush()

        # Mirror onto LoanApplication.officer_decision if one exists — this is
        # the field the RE handoff payload reads. The immutable audit trail
        # remains OfficerDecisionLog.
        if loan_app is not None:
            loan_app.officer_decision = request.decision.value
            loan_app.override_reason = request.override_reason
            loan_app.decided_at = entry.created_at

        await self.db.commit()
        logger.info(
            "officer_decision_recorded",
            score_id=str(score.id),
            officer_id=officer_id,
            decision=request.decision.value,
            model_recommendation=rec.value,
            is_override=override,
        )
        return entry

    async def get_audit_trail(self, score_id: uuid.UUID) -> list[OfficerDecisionLog]:
        result = await self.db.execute(
            select(OfficerDecisionLog)
            .where(OfficerDecisionLog.score_id == score_id)
            .order_by(OfficerDecisionLog.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_latest_decision(
        self, score_id: uuid.UUID
    ) -> OfficerDecisionLog | None:
        result = await self.db.execute(
            select(OfficerDecisionLog)
            .where(OfficerDecisionLog.score_id == score_id)
            .order_by(OfficerDecisionLog.created_at.desc())
        )
        return result.scalars().first()


__all__: list[Any] = [
    "DecisioningService",
    "DecisioningError",
    "recommendation_for_band",
    "is_override",
    "EXPECTED_RAILS",
]

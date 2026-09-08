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
    FeatureSnapshot,
    LoanApplication,
    OfficerDecisionLog,
    Score,
    Village,
)
from services.core.shared.scoring_utils import clean_borrower_name, normalize_score

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

        feat_stmt = select(FeatureSnapshot).where(FeatureSnapshot.id == score.feature_snapshot_id)
        feat_res = await self.db.execute(feat_stmt)
        feat_snapshot = feat_res.scalar_one_or_none()
        features = feat_snapshot.features_json if feat_snapshot else {}

        norm = normalize_score(score.score, score.confidence_lower, score.confidence_upper)
        rec = recommendation_for_band(norm["band"])
        display_name = clean_borrower_name(borrower.name_encrypted, borrower.id)

        service = ScoringService(self.db, model_version=score.model_version)
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
            borrower_name=display_name,
            borrower_summary={
                "borrower_id": str(borrower.id),
                "borrower_name": display_name,
                "gender": borrower.gender,
                "age": borrower.age,
                "landholding_band": borrower.landholding_band,
                "village": village_row.name if village_row else None,
                "district": village_row.district if village_row else None,
                "state": village_row.state if village_row else None,
                "language": borrower.language,
            },
            score=norm["score_100"],
            score_900=norm["score_900"],
            score_band=norm["band"],
            confidence_lower=float(norm["confidence_lower_100"]),
            confidence_upper=float(norm["confidence_upper_100"]),
            model_version=score.model_version,
            feature_version=feature_version,
            model_recommendation=rec,
            sources_used=sources_used,
            source_status=source_status,
            partial_data=partial,
            reason_codes=reason_codes,
            features=features,
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
        norm = normalize_score(score.score, score.confidence_lower, score.confidence_upper)
        rec = recommendation_for_band(norm["band"])
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

    async def list_applications(self) -> list[dict]:
        """Fetch all loan applications with borrower, score, and village context for officer review."""
        stmt = (
            select(LoanApplication, Borrower, Score, Village)
            .join(Borrower, Borrower.id == LoanApplication.borrower_id)
            .join(Score, Score.id == LoanApplication.score_id)
            .outerjoin(Village, Village.id == Borrower.village_id)
            .order_by(LoanApplication.created_at.desc())
        )
        res = await self.db.execute(stmt)
        apps = []
        for app, borrower, score, village in res.all():
            norm = normalize_score(score.score, score.confidence_lower, score.confidence_upper)
            rec = recommendation_for_band(norm["band"])
            display_name = clean_borrower_name(borrower.name_encrypted, borrower.id)
            apps.append({
                "id": str(app.id),
                "borrower_id": str(borrower.id),
                "borrower_name": display_name,
                "village": village.name if village else "Pilot Sangaria Village",
                "district": village.district if village else "Hanumangarh",
                "state": village.state if village else "Rajasthan",
                "gender": borrower.gender,
                "age": borrower.age,
                "landholding_band": borrower.landholding_band,
                "requested_amount": app.requested_amount,
                "requested_tenure_months": app.requested_tenure_months,
                "purpose": app.purpose,
                "score_id": str(score.id),
                "score_900": norm["score_900"],
                "score_100": norm["score_100"],
                "band": norm["band"],
                "confidence_lower": norm["confidence_lower_900"],
                "confidence_upper": norm["confidence_upper_900"],
                "model_recommendation": rec.value,
                "decision": app.officer_decision or "PENDING",
                "override_reason": app.override_reason,
                "submitted_at": app.created_at.isoformat() if app.created_at else None,
                "decided_at": app.decided_at.isoformat() if app.decided_at else None,
            })
        return apps

    async def get_application_review(self, application_id: uuid.UUID) -> ReviewPayload:
        """Retrieve full review payload by loan application ID or score ID."""
        la_result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        loan_app = la_result.scalars().first()
        if loan_app and loan_app.score_id:
            payload = await self.build_review_payload(loan_app.score_id)
            payload.borrower_summary["application_id"] = str(loan_app.id)
            payload.borrower_summary["requested_amount"] = loan_app.requested_amount
            payload.borrower_summary["requested_tenure_months"] = loan_app.requested_tenure_months
            payload.borrower_summary["purpose"] = loan_app.purpose
            return payload
        return await self.build_review_payload(application_id)


__all__: list[Any] = [
    "DecisioningService",
    "DecisioningError",
    "recommendation_for_band",
    "is_override",
    "EXPECTED_RAILS",
]

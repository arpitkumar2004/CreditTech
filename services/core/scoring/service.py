from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.evaluation.explain import ScorecardSHAPExplainer
from ml.registry import ModelRegistry
from ml.training.scorecard import LogisticScorecard
from services.core.explainability.service import ExplainabilityService
from services.core.shared.logging import get_logger
from services.core.shared.models import FeatureSnapshot, ReasonCode, Score

from .schemas import ScoreRequest

logger = get_logger("scoring.service")


def _load_scorecard_from_registry(model_version: str | None) -> tuple[Any, dict | None]:
    """Prefer a registered artifact; fall back to the built-in default scorecard.

    Returns (scorecard, feature_means_or_none). feature_means is used as SHAP
    reference values when available, so explanations reflect the actual trained
    baseline rather than a domain prior.
    """
    registry = ModelRegistry()
    record = registry.get(model_version) if model_version else registry.get_active()
    if record is None:
        return LogisticScorecard(), None
    artifact = registry.artifact_path(record.model_version)
    if artifact is None or not artifact.exists():
        return LogisticScorecard(), None

    import json
    scorecard = None

    # Check if artifact is a pickle (e.g. MonotonicGBMScorecard)
    is_pickle = False
    try:
        with open(artifact, "rb") as f:
            magic = f.read(2)
            if magic.startswith(b"\x80"):
                is_pickle = True
    except Exception:
        pass

    if is_pickle or artifact.suffix == ".pkl" or (artifact.parent / "scorecard.pkl").exists() and not artifact.exists():
        from ml.training.gbm_challenger import MonotonicGBMScorecard
        pkl_path = artifact if is_pickle else (artifact.parent / "scorecard.pkl")
        scorecard = MonotonicGBMScorecard.from_artifact(pkl_path)
    else:
        with open(artifact, encoding="utf-8") as f:
            data = json.load(f)

        if "woe_transformer" in data:
            from ml.training.woe_scorecard import WoEScorecard
            scorecard = WoEScorecard.from_dict(data)
        else:
            scorecard = LogisticScorecard.from_dict(data)

    # Pull the training-set feature means from the report if present.
    report_path = artifact.parent / "training_report.json"
    feature_means: dict | None = None
    if report_path.exists():
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
        feature_means = report.get("feature_means") or None
    return scorecard, feature_means


class ScoringServiceError(Exception):
    pass


class ScoringService:
    """Core scoring orchestrator linking ML models, SHAP explainers, and DB models."""

    def __init__(self, db: AsyncSession, model_version: str | None = None) -> None:
        self.db = db
        self.scorecard, feature_means = _load_scorecard_from_registry(model_version)
        self.shap_explainer = ScorecardSHAPExplainer(self.scorecard, reference_values=feature_means)
        self.explain_service = ExplainabilityService()

    async def generate_score(self, request: ScoreRequest) -> Score:
        """Execute scoring pipeline for a borrower, returning a saved Score ORM record."""
        # 1. Fetch the feature snapshot
        if request.feature_snapshot_id:
            stmt = select(FeatureSnapshot).where(
                FeatureSnapshot.id == request.feature_snapshot_id,
                FeatureSnapshot.borrower_id == request.borrower_id,
            )
        else:
            # Fall back to latest snapshot
            stmt = (
                select(FeatureSnapshot)
                .where(FeatureSnapshot.borrower_id == request.borrower_id)
                .order_by(FeatureSnapshot.computed_at.desc())
                .limit(1)
            )

        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise ScoringServiceError(
                f"No feature snapshot found for borrower {request.borrower_id}"
            )

        # 2. Run logistic model prediction
        features = snapshot.features_json
        prob_repay = self.scorecard.predict_probability(features)

        # 3. Calibrate scores
        score_100, score_900 = self.scorecard.calibrate_score(prob_repay)

        # 4. Calculate dynamic confidence bands based on sources count (ADR-5)
        # Fewer sources = higher uncertainty = wider confidence interval
        sources = snapshot.sources_used
        num_sources = len(sources)
        if num_sources >= 4:
            spread = 5.0
        elif num_sources == 3:
            spread = 8.0
        elif num_sources == 2:
            spread = 12.0
        else:
            spread = 18.0

        conf_lower = max(0.0, score_100 - spread)
        conf_upper = min(100.0, score_100 + spread)

        # 5. Save Score record to DB
        # Bind the loaded scorecard's version to the record — the request may
        # request a specific version or omit it (registry active is used).
        effective_model_version = self.scorecard.model_version
        score_record = Score(
            borrower_id=request.borrower_id,
            feature_snapshot_id=snapshot.id,
            model_version=effective_model_version,
            score=score_100,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            sources_used=sources,
        )
        self.db.add(score_record)
        await self.db.flush()

        # 6. Generate SHAP explanations
        shap_values = self.shap_explainer.compute_shap_values(features)
        rendered_codes = self.explain_service.render_reason_codes(shap_values, limit=5)

        # Save ReasonCode records to DB linked to Score
        for code in rendered_codes:
            rc_record = ReasonCode(
                score_id=score_record.id,
                rank=code["rank"],
                feature_name=code["feature_name"],
                direction=code["direction"],
                shap_value=code["shap_value"],
                localized_text_en=code["localized_text_en"],
                localized_text_hi=code["localized_text_hi"],
            )
            self.db.add(rc_record)

        await self.db.commit()

        logger.info(
            "score_generated",
            borrower_id=str(request.borrower_id),
            score_100=score_100,
            score_900=score_900,
            sources=sources,
        )

        # Attach computed 900 score for serializing in router if needed
        # (Since score_900 is calibrated on the fly but not stored in DB)
        score_record.score_900 = score_900  # type: ignore[attr-defined]
        score_record.transient_reason_codes = rendered_codes  # type: ignore[attr-defined]

        # 7. Execute Challenger Shadow Scoring
        score_record.shadow_score = self._run_shadow_scoring(features, score_100, score_900)  # type: ignore[attr-defined]

        # 8. Compute Actionable Recourse if score is below auto-approve threshold (< 650)
        recourse_result = None
        if score_900 < 650 or self.get_score_band(score_100) in {"MODERATE", "HIGH_RISK", "VERY_HIGH_RISK"}:
            try:
                from ml.evaluation.recourse import CounterfactualRecourseEngine
                engine = CounterfactualRecourseEngine(self.scorecard)
                recourse_result = engine.generate_recourse(features, target_score=650)
            except Exception as err:
                logger.warning("recourse_generation_failed", error=str(err))
        score_record.actionable_recourse = recourse_result  # type: ignore[attr-defined]

        return score_record

    def _run_shadow_scoring(
        self,
        features: dict[str, Any],
        active_score_100: float,
        active_score_900: int,
    ) -> dict[str, Any] | None:
        """Runs the registered candidate/challenger model in shadow mode without blocking main flow."""
        try:
            import time
            registry = ModelRegistry()
            records = registry.list_all()
            challenger_record = None
            for r in records:
                if r.promotion_status == "candidate" and r.model_version != self.scorecard.model_version:
                    challenger_record = r
                    break

            if challenger_record is None:
                return None

            t0 = time.perf_counter()
            challenger_card, _ = _load_scorecard_from_registry(challenger_record.model_version)
            if challenger_card is None:
                return None

            shadow_prob = challenger_card.predict_probability(features)
            shadow_100, shadow_900 = challenger_card.calibrate_score(shadow_prob)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            def get_rec(s900: int) -> str:
                if s900 >= 650:
                    return "APPROVE"
                elif s900 >= 550:
                    return "REVIEW"
                return "REJECT"

            agreement = "AGREE" if get_rec(active_score_900) == get_rec(shadow_900) else "DISAGREE"

            return {
                "shadow_model_version": challenger_record.model_version,
                "shadow_score_100": shadow_100,
                "shadow_score_900": shadow_900,
                "score_delta_100": round(shadow_100 - active_score_100, 1),
                "agreement": agreement,
                "latency_ms": elapsed_ms,
            }
        except Exception as err:
            logger.warning("shadow_scoring_skipped", error=str(err))
            return None

    @staticmethod
    def get_score_band(score_100: float) -> str:
        """Map 0-100 score to functional assessment bands."""
        if score_100 >= 81.0:
            return "EXCELLENT"
        elif score_100 >= 66.0:
            return "GOOD"
        elif score_100 >= 51.0:
            return "MODERATE"
        elif score_100 >= 31.0:
            return "HIGH_RISK"
        return "VERY_HIGH_RISK"

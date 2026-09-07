"""Closed-Loop DPDP-Consented Retraining Pipeline for CreditTech.

Extracts matured loan repayment outcomes for borrowers who gave explicit
re-training consent under the Digital Personal Data Protection (DPDP) Act 2023.
Performs Spatial Group cross-validation across pilot village clusters, trains candidate models,
audits fairness gates, and registers validated models in ModelRegistry.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.features.schema import FEATURE_VERSION, MODEL_FEATURE_NAMES
from ml.registry import ModelRegistry
from ml.training.datasets import DatasetInfo, SyntheticSHGGenerator
from ml.training.gbm_challenger import GBMScorecardTrainer
from ml.training.validation import SpatialGroupValidator
from ml.training.woe_scorecard import WoEScorecardTrainer
from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    LoanApplication,
    RepaymentRecord,
    Score,
    Village,
)


@dataclass
class RetrainingResult:
    status: str  # "SUCCESS" | "INSUFFICIENT_DATA" | "FAILED"
    message: str
    model_version: str | None
    model_type: str | None
    n_consented_records: int
    n_total_samples: int
    cv_auc: float
    cv_gini: float
    cv_ks: float
    cv_brier: float
    fairness_passed: bool
    registered: bool
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DPDPRetrainingPipeline:
    """Orchestrates closed-loop model retraining adhering to DPDP consent boundaries."""

    def __init__(
        self,
        db: AsyncSession,
        registry: ModelRegistry | None = None,
        min_consented_samples: int = 20,
    ) -> None:
        self.db = db
        self.registry = registry or ModelRegistry()
        self.min_consented_samples = min_consented_samples

    async def extract_consented_data(
        self,
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, int]:
        """Extracts feature vectors and ground-truth labels for consented borrowers."""
        # Join RepaymentRecord -> LoanApplication -> Score -> FeatureSnapshot + Borrower + Village
        stmt = (
            select(
                RepaymentRecord.status,
                FeatureSnapshot.features_json,
                Borrower.gender,
                Borrower.landholding_band,
                Village.name.label("village_name"),
                Village.agro_climatic_zone,
            )
            .join(LoanApplication, RepaymentRecord.loan_application_id == LoanApplication.id)
            .join(Score, LoanApplication.score_id == Score.id)
            .join(FeatureSnapshot, Score.feature_snapshot_id == FeatureSnapshot.id)
            .join(Borrower, LoanApplication.borrower_id == Borrower.id)
            .join(Village, Borrower.village_id == Village.id)
            .where(RepaymentRecord.consented_for_retraining == True)  # noqa: E712 - Strict DPDP Consent Guard
        )

        res = await self.db.execute(stmt)
        rows = res.all()

        if not rows:
            return pd.DataFrame(), pd.Series(dtype=int), pd.DataFrame(), 0

        feature_dicts = []
        labels = []
        sensitive_dicts = []

        for row in rows:
            status, features_json, gender, landholding, village_name, zone = row
            # Ground truth labeling:
            # 1 = Repayed / Good: CURRENT, CLOSED
            # 0 = Default / Bad: DPD_90_PLUS
            if status in {"CURRENT", "CLOSED"}:
                y_val = 1
            elif status == "DPD_90_PLUS":
                y_val = 0
            else:
                # Ambiguous intermediate delinquency (e.g. DPD_1_30) is skipped
                continue

            from ml.features.pipeline import _coerce
            coerced_row = {
                feat: _coerce((features_json or {}).get(feat), feat)
                for feat in MODEL_FEATURE_NAMES
            }
            feature_dicts.append(coerced_row)
            labels.append(y_val)
            sensitive_dicts.append({
                "gender": gender,
                "landholding_band": landholding,
                "village_id": village_name,
                "agro_climatic_zone": zone or "CANAL_IRRIGATED_NORTH",
            })

        if not feature_dicts:
            return pd.DataFrame(), pd.Series(dtype=int), pd.DataFrame(), len(rows)

        X_real = pd.DataFrame(feature_dicts)
        # Ensure all MODEL_FEATURE_NAMES are present
        for col in MODEL_FEATURE_NAMES:
            if col not in X_real.columns:
                X_real[col] = np.nan
        X_real = X_real[list(MODEL_FEATURE_NAMES)].astype(float)
        y_real = pd.Series(labels, name="repay", dtype=int)
        sensitive_df = pd.DataFrame(sensitive_dicts)

        # Strict Data Governance Invariant (DPDP Act 2023 & Article 15):
        from ml.features.schema import MONITORED_ONLY_FIELDS, PROHIBITED_FIELDS
        prohibited_in_X = set(X_real.columns).intersection(PROHIBITED_FIELDS)
        if prohibited_in_X:
            raise ValueError(f"Data Governance Violation: PROHIBITED_FIELDS detected in training matrix: {prohibited_in_X}")
        monitored_in_X = set(X_real.columns).intersection(MONITORED_ONLY_FIELDS)
        if monitored_in_X:
            raise ValueError(f"Data Governance Violation: MONITORED_ONLY_FIELDS detected in training matrix: {monitored_in_X}")

        return X_real, y_real, sensitive_df, len(rows)

    async def run_retraining(
        self,
        model_type: str = "woe",  # "woe" or "gbm"
        target_version_tag: str | None = None,
    ) -> RetrainingResult:
        """Runs retraining pipeline, validates spatial cross-validation, and registers candidate."""
        X_real, y_real, sensitive_df, n_consented = await self.extract_consented_data()

        # Check if we have sufficient consented samples
        if len(X_real) < self.min_consented_samples:
            # Augment with synthetic benchmark cohort to preserve stability at pilot start
            gen = SyntheticSHGGenerator(n=1000, seed=42, n_villages=6)
            X_syn, y_syn, sens_syn, _ = gen.generate()

            if len(X_real) > 0:
                X_combined = pd.concat([X_real, X_syn], ignore_index=True)
                y_combined = pd.concat([y_real, y_syn], ignore_index=True)
                sensitive_combined = pd.concat([sensitive_df, sens_syn], ignore_index=True)
            else:
                X_combined, y_combined, sensitive_combined = X_syn, y_syn, sens_syn
            used_synthetic = True
        else:
            X_combined = X_real
            y_combined = y_real
            sensitive_combined = sensitive_df
            used_synthetic = False

        version_id = target_version_tag or f"v1.2.0-{model_type}-retrained-{datetime.now(UTC).strftime('%Y%m%d%H%M')}"

        # 1. Spatial Cross-Validation across Village Clusters
        validator = SpatialGroupValidator(n_splits=min(5, len(sensitive_combined["village_id"].unique())))

        if model_type == "gbm":
            trainer = GBMScorecardTrainer(model_version=version_id, max_iter=50, random_state=42)
            eval_metrics, oof_preds = validator.validate(
                estimator_factory=lambda: GBMScorecardTrainer(model_version=version_id, max_iter=50, random_state=42),
                X=X_combined,
                y=y_combined,
                groups=sensitive_combined["village_id"],
            )
            scorecard, report = trainer.fit(X_combined, y_combined, groups=sensitive_combined["village_id"])
        else:
            trainer = WoEScorecardTrainer(model_version=version_id, min_iv=0.01, random_state=42)
            eval_metrics, oof_preds = validator.validate(
                estimator_factory=lambda: WoEScorecardTrainer(model_version=version_id, min_iv=0.01, random_state=42),
                X=X_combined,
                y=y_combined,
                groups=sensitive_combined["village_id"],
            )
            scorecard, report = trainer.fit(X_combined, y_combined)

        # 2. Check Fairness Gate
        groups_dict = {}
        for attr in ["gender", "landholding_band"]:
            g_col = sensitive_combined[attr]
            rates = {}
            for g_val in g_col.unique():
                idx = g_col == g_val
                if idx.sum() > 0:
                    pred_approve = (oof_preds[idx] >= 0.50).mean()
                    rates[str(g_val)] = {"approval_rate": float(pred_approve), "n": int(idx.sum())}
            groups_dict[attr] = rates

        # Compute max disparity
        fairness_passed = True
        fairness_results = []
        for attr, grps in groups_dict.items():
            app_rates = [v["approval_rate"] for v in grps.values() if v["n"] >= 10]
            max_disp = (max(app_rates) - min(app_rates)) if app_rates else 0.0
            passed = max_disp <= 0.20  # P6 threshold
            if not passed:
                fairness_passed = False
            fairness_results.append({
                "attribute": attr,
                "groups": grps,
                "max_disparity": round(max_disp, 4),
                "threshold": 0.20,
                "status": "ok" if passed else "breached",
            })

        # 3. Register as Candidate in ModelRegistry
        info = DatasetInfo(
            source="dpdp_consented_repayment_records" + ("_augmented" if used_synthetic else ""),
            kind="fused" if used_synthetic else "real",
            samples=len(X_combined),
            features=list(MODEL_FEATURE_NAMES),
            feature_version=FEATURE_VERSION,
            schema_hash="2556de253967272a",
            transformations=[
                f"consented_records_used={n_consented}",
                f"used_synthetic_anchor={used_synthetic}",
                f"spatial_villages={len(sensitive_combined['village_id'].unique())}",
            ],
            limitations=[
                f"trained on {n_consented} real consented outcomes + {'synthetic anchor' if used_synthetic else 'pure pilot data'}",
                "DPDP Act 2023 consent boundaries verified prior to ingestion",
            ],
            available=True,
        )

        self.registry.register(
            scorecard=scorecard,
            training_report=report,
            dataset_info=info,
            fairness_results=fairness_results,
            model_type=f"{model_type}_scorecard_v1",
            notes=[
                f"Closed-loop retrained candidate with {n_consented} DPDP-consented pilot outcomes",
                f"Spatial CV: AUC={eval_metrics.auc:.4f}, KS={eval_metrics.ks:.4f}, Brier={eval_metrics.brier:.4f}",
            ],
        )

        return RetrainingResult(
            status="SUCCESS",
            message=f"Model {version_id} retrained and registered as candidate.",
            model_version=version_id,
            model_type=model_type,
            n_consented_records=n_consented,
            n_total_samples=len(X_combined),
            cv_auc=round(eval_metrics.auc, 4),
            cv_gini=round(eval_metrics.gini, 4),
            cv_ks=round(eval_metrics.ks, 4),
            cv_brier=round(eval_metrics.brier, 4),
            fairness_passed=fairness_passed,
            registered=True,
            timestamp=datetime.now(UTC).isoformat(),
        )

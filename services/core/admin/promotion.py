"""P6 — Model promotion pipeline.

Blocks `active` promotion when either:
    * Registered model performance falls below ratified minimum thresholds
      (AUC / Gini / KS / Brier — pilot minimums), OR
    * FairnessGate reports any threshold breach on the latest fairness period.

`candidate -> validated` and `validated -> retired` remain unchecked (they
are pre-promotion states). Only the final `-> active` transition is gated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ml.registry.registry import ModelRegistry
from services.core.monitoring.governance import FairnessGate, FairnessGateResult

# Ratified performance minimums (pilot §12.3, aligned with existing
# ml/training/scorecard.py thresholds; documented as the promotion floor).
PERFORMANCE_MINIMUMS = {
    "auc": 0.60,
    "gini": 0.20,
    "ks": 0.15,
    "brier_max": 0.30,
}


class PromotionBlocked(Exception):
    def __init__(self, report: "PromotionReport") -> None:
        super().__init__("Promotion blocked by P6 gate")
        self.report = report


@dataclass
class PromotionReport:
    model_version: str
    to_status: str
    performance_pass: bool
    fairness_pass: bool
    performance_details: dict[str, Any]
    fairness_details: dict[str, Any]
    plots_data: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.performance_pass and self.fairness_pass

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"passed": self.passed}


def _check_performance(metrics: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    failed: dict[str, Any] = {}
    auc = metrics.get("auc")
    gini = metrics.get("gini")
    ks = metrics.get("ks")
    brier = metrics.get("brier")

    if auc is None or auc < PERFORMANCE_MINIMUMS["auc"]:
        failed["auc"] = {"value": auc, "min": PERFORMANCE_MINIMUMS["auc"]}
    if gini is None or gini < PERFORMANCE_MINIMUMS["gini"]:
        failed["gini"] = {"value": gini, "min": PERFORMANCE_MINIMUMS["gini"]}
    if ks is None or ks < PERFORMANCE_MINIMUMS["ks"]:
        failed["ks"] = {"value": ks, "min": PERFORMANCE_MINIMUMS["ks"]}
    if brier is None or brier > PERFORMANCE_MINIMUMS["brier_max"]:
        failed["brier"] = {"value": brier, "max": PERFORMANCE_MINIMUMS["brier_max"]}

    return (len(failed) == 0, {"minimums": PERFORMANCE_MINIMUMS, "failed": failed})


class ModelPromotionService:
    def __init__(
        self,
        db: AsyncSession,
        registry: ModelRegistry | None = None,
        gate: FairnessGate | None = None,
    ) -> None:
        self.db = db
        self.registry = registry or ModelRegistry()
        self.gate = gate or FairnessGate(db)

    async def evaluate(self, model_version: str) -> PromotionReport:
        rec = self.registry.get(model_version)
        if rec is None:
            raise KeyError(f"Model {model_version} not in registry")

        perf_pass, perf_details = _check_performance(rec.metrics)
        gate_result: FairnessGateResult = await self.gate.evaluate()
        fairness_pass = gate_result.passed
        # Load plots data if manifest exists
        plots_data: dict[str, Any] = {}
        store_path = getattr(self.registry, "store", None)
        if store_path:
            plots_manifest_file = store_path / model_version / "plots" / "plots_manifest.json"
            if plots_manifest_file.exists():
                try:
                    import json
                    with open(plots_manifest_file, "r", encoding="utf-8") as f:
                        plots_data = json.load(f)
                except Exception:
                    plots_data = {}

        return PromotionReport(
            model_version=model_version,
            to_status="active",
            performance_pass=perf_pass,
            fairness_pass=fairness_pass,
            performance_details=perf_details,
            fairness_details=gate_result.to_dict(),
            plots_data=plots_data,
        )

    async def promote_to_active(self, model_version: str) -> PromotionReport:
        report = await self.evaluate(model_version)
        if not report.passed:
            raise PromotionBlocked(report)
        # First move candidate -> validated (if needed), then -> active.
        rec = self.registry.get(model_version)
        if rec and rec.promotion_status == "candidate":
            self.registry.promote(model_version, "validated")
        self.registry.promote(model_version, "active")
        return report


__all__ = [
    "ModelPromotionService", "PromotionReport", "PromotionBlocked",
    "PERFORMANCE_MINIMUMS",
]

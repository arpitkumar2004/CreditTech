"""P6 — Fairness governance thresholds and promotion gate.

Design invariants (§8.3, §17.2):
    * Thresholds are ratified externally. They live in a signed JSON manifest
      (`config/fairness_thresholds.json`) and are loaded at runtime; the
      backend does NOT invent them.
    * A model cannot be promoted to `active` while any dimension breaches a
      ratified threshold on the *latest* fairness period.
    * INSUFFICIENT_SAMPLE rows are skipped — no signal, no gate action.
    * The gate is descriptive-first: on failure it returns a structured
      report the model owner and external auditor can act on, never a silent
      block.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import FairnessAuditLog

DEFAULT_MANIFEST = Path(__file__).resolve().parents[3] / "config" / "fairness_thresholds.json"


@dataclass
class ThresholdBreach:
    dimension: str
    group_value: str
    metric: str
    value: float
    threshold: float
    rule: str  # e.g. "min_approval_rate", "max_override_rate", "max_approval_gap"


@dataclass
class FairnessGateResult:
    passed: bool
    period: str | None
    manifest_hash: str
    breaches: list[ThresholdBreach]
    skipped_insufficient: int
    evaluated_rows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "period": self.period,
            "manifest_hash": self.manifest_hash,
            "breaches": [asdict(b) for b in self.breaches],
            "skipped_insufficient": self.skipped_insufficient,
            "evaluated_rows": self.evaluated_rows,
        }


class ManifestError(Exception):
    pass


def load_manifest(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_MANIFEST
    if not p.exists():
        raise ManifestError(f"Fairness thresholds manifest not found: {p}")
    with open(p, encoding="utf-8") as f:
        manifest = json.load(f)
    required = {"version", "ratified_by", "ratified_at", "thresholds"}
    if not required.issubset(manifest.keys()):
        raise ManifestError(f"Manifest missing required keys: {required - manifest.keys()}")
    return manifest


def manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


class FairnessGate:
    """Evaluates the latest fairness audit rows against a ratified threshold manifest."""

    def __init__(self, db: AsyncSession, manifest: dict[str, Any] | None = None) -> None:
        self.db = db
        self.manifest = manifest or load_manifest()

    async def _latest_period(self) -> str | None:
        r = await self.db.execute(
            select(FairnessAuditLog.period)
            .order_by(FairnessAuditLog.computed_at.desc())
            .limit(1)
        )
        row = r.first()
        return row[0] if row else None

    async def evaluate(self, period: str | None = None) -> FairnessGateResult:
        period = period or await self._latest_period()
        thresholds = self.manifest["thresholds"]
        breaches: list[ThresholdBreach] = []
        skipped = 0
        evaluated = 0

        if period is None:
            return FairnessGateResult(
                passed=False, period=None, manifest_hash=manifest_hash(self.manifest),
                breaches=[], skipped_insufficient=0, evaluated_rows=0,
            )

        rows = (await self.db.execute(
            select(FairnessAuditLog).where(FairnessAuditLog.period == period)
        )).scalars().all()

        # Group rows by dimension for approval-gap checks.
        by_dim: dict[str, list[FairnessAuditLog]] = {}
        for r in rows:
            if r.status == "INSUFFICIENT_SAMPLE":
                skipped += 1
                continue
            evaluated += 1
            by_dim.setdefault(r.dimension, []).append(r)

        for dim, group_rows in by_dim.items():
            rule = thresholds.get(dim, {})
            min_ar = rule.get("min_approval_rate")
            max_or = rule.get("max_override_rate")
            max_gap = rule.get("max_approval_gap")

            if min_ar is not None:
                for r in group_rows:
                    if r.approval_rate is not None and r.approval_rate < min_ar:
                        breaches.append(ThresholdBreach(
                            dimension=dim, group_value=r.group_value,
                            metric="approval_rate", value=float(r.approval_rate),
                            threshold=float(min_ar), rule="min_approval_rate",
                        ))
            if max_or is not None:
                for r in group_rows:
                    if r.override_rate is not None and r.override_rate > max_or:
                        breaches.append(ThresholdBreach(
                            dimension=dim, group_value=r.group_value,
                            metric="override_rate", value=float(r.override_rate),
                            threshold=float(max_or), rule="max_override_rate",
                        ))
            if max_gap is not None and len(group_rows) > 1:
                rates = [r.approval_rate for r in group_rows if r.approval_rate is not None]
                if len(rates) > 1:
                    gap = max(rates) - min(rates)
                    if gap > max_gap:
                        breaches.append(ThresholdBreach(
                            dimension=dim, group_value="<across-groups>",
                            metric="approval_gap", value=float(gap),
                            threshold=float(max_gap), rule="max_approval_gap",
                        ))

        return FairnessGateResult(
            passed=(len(breaches) == 0),
            period=period,
            manifest_hash=manifest_hash(self.manifest),
            breaches=breaches,
            skipped_insufficient=skipped,
            evaluated_rows=evaluated,
        )


__all__ = [
    "FairnessGate", "FairnessGateResult", "ThresholdBreach",
    "load_manifest", "manifest_hash", "ManifestError", "DEFAULT_MANIFEST",
]

"""Model registry — P3.6.

File-based JSON registry that tracks:
    * model_version, feature_version
    * training-dataset provenance (source, kind, hash, transformations, limitations)
    * evaluation metrics (auc, gini, ks, brier, calibration bins)
    * fairness results (per-attribute)
    * artifact path (relative to registry root)
    * promotion status: candidate -> validated -> active

Training success alone does NOT promote a model. Promotion is an explicit,
audited operation (`promote()`) that also demotes the current active model.

Layout on disk:
    ml/registry/store/
        registry.json                  # authoritative index
        <model_version>/
            scorecard.json             # weights + intercept
            training_report.json       # metrics + calibration + fairness
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from pathlib import Path
from typing import Any, Literal

PromotionStatus = Literal["candidate", "validated", "active", "retired"]

DEFAULT_STORE = Path(__file__).parent / "store"


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ModelRecord:
    model_version: str
    feature_version: str
    model_type: str
    training_dataset: dict[str, Any]         # DatasetInfo.to_dict
    training_dataset_hash: str
    trained_at: str                          # ISO8601 UTC
    metrics: dict[str, Any]
    fairness: dict[str, Any]
    artifact_path: str                       # relative to store root
    artifact_hash: str
    promotion_status: PromotionStatus = "candidate"
    limitations: list[str] = field(default_factory=list)
    code_version: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    def __init__(self, store: str | Path | None = None) -> None:
        self.store = Path(store) if store else DEFAULT_STORE
        self.store.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store / "registry.json"
        if not self.index_path.exists():
            self._write_index([])

    # ---------- index ----------
    def _read_index(self) -> list[dict[str, Any]]:
        with open(self.index_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_index(self, records: list[dict[str, Any]]) -> None:
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, sort_keys=True)

    # ---------- register ----------
    def register(
        self,
        *,
        scorecard,                            # LogisticScorecard
        training_report,                      # TrainingReport
        dataset_info,                         # DatasetInfo
        fairness_results: list[dict[str, Any]] | None = None,
        model_type: str = "logistic_scorecard_v1",
        code_version: str | None = None,
        notes: list[str] | None = None,
    ) -> ModelRecord:
        version = scorecard.model_version
        model_dir = self.store / version
        model_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = model_dir / "scorecard.json"
        scorecard.save_artifact(artifact_path)
        artifact_hash = _sha256_of_file(artifact_path)

        report_payload = training_report.to_dict() if hasattr(training_report, "to_dict") else dict(training_report)
        if fairness_results:
            report_payload["fairness"] = fairness_results
        with open(model_dir / "training_report.json", "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2, sort_keys=True, default=str)

        # Dataset hash = sha256(sorted json of dataset info + row count/schema).
        dataset_dict = asdict(dataset_info) if hasattr(dataset_info, "__dataclass_fields__") else dict(dataset_info)
        dataset_hash = hashlib.sha256(
            json.dumps(dataset_dict, sort_keys=True, default=str).encode()
        ).hexdigest()[:32]

        metrics = {
            "auc": report_payload.get("auc"),
            "gini": report_payload.get("gini"),
            "ks": report_payload.get("ks"),
            "brier": report_payload.get("brier"),
            "n_train": report_payload.get("n_train"),
            "n_val": report_payload.get("n_val"),
            "calibration_bins": report_payload.get("calibration_bins", []),
        }
        record = ModelRecord(
            model_version=version,
            feature_version=scorecard.feature_version,
            model_type=model_type,
            training_dataset=dataset_dict,
            training_dataset_hash=dataset_hash,
            trained_at=datetime.now(UTC).isoformat(),
            metrics=metrics,
            fairness={"results": fairness_results or []},
            artifact_path=str(artifact_path.relative_to(self.store)).replace("\\", "/"),
            artifact_hash=artifact_hash,
            promotion_status="candidate",
            limitations=list(dataset_dict.get("limitations", []))
                + list(report_payload.get("notes", [])),
            code_version=code_version,
            notes=notes or [],
        )

        # Upsert
        records = self._read_index()
        records = [r for r in records if r["model_version"] != version]
        records.append(record.to_dict())
        self._write_index(records)
        return record

    # ---------- retrieval ----------
    def list_models(self) -> list[ModelRecord]:
        return [ModelRecord(**r) for r in self._read_index()]

    def get(self, model_version: str) -> ModelRecord | None:
        for r in self._read_index():
            if r["model_version"] == model_version:
                return ModelRecord(**r)
        return None

    def get_active(self) -> ModelRecord | None:
        actives = [r for r in self._read_index() if r["promotion_status"] == "active"]
        if not actives:
            return None
        # If somehow multiple, pick most recently trained.
        actives.sort(key=lambda r: r["trained_at"], reverse=True)
        return ModelRecord(**actives[0])

    def artifact_path(self, model_version: str) -> Path | None:
        rec = self.get(model_version)
        if not rec:
            return None
        return self.store / rec.artifact_path

    # ---------- promotion ----------
    def promote(self, model_version: str, to_status: PromotionStatus) -> ModelRecord:
        if to_status not in ("candidate", "validated", "active", "retired"):
            raise ValueError(f"Invalid promotion status: {to_status}")
        records = self._read_index()
        target = next((r for r in records if r["model_version"] == model_version), None)
        if target is None:
            raise KeyError(f"Model {model_version} not in registry")

        # Enforce a simple progression rather than allowing skipping.
        current = target["promotion_status"]
        allowed = {
            "candidate": {"candidate", "validated", "retired"},
            "validated": {"validated", "active", "retired"},
            "active":    {"active", "retired"},
            "retired":   {"retired"},
        }
        if to_status not in allowed[current]:
            raise ValueError(f"Illegal transition {current} -> {to_status} for {model_version}")

        # If promoting to active, demote the current active to 'retired'.
        if to_status == "active":
            for r in records:
                if r["promotion_status"] == "active" and r["model_version"] != model_version:
                    r["promotion_status"] = "retired"

        target["promotion_status"] = to_status
        self._write_index(records)
        return ModelRecord(**target)

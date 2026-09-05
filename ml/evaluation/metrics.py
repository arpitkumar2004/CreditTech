"""Evaluation metrics — P3.3 (predictive) and P3.4 (fairness).

Fairness policy (per P3 brief):
    * Only report metrics — DO NOT invent a threshold. If the project has not
      ratified a tolerance, results are informational and marked as pending
      governance decision.
    * Model input features are never inspected for group membership. Group
      attributes come in as a separate `sensitive` DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DemographicParityResult:
    attribute: str
    threshold: float
    groups: dict[str, dict[str, float]] = field(default_factory=dict)
    max_disparity: float = 0.0
    reference_group: str | None = None
    reference_rate: float | None = None
    ratified_tolerance: float | None = None      # None = pending governance
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attribute": self.attribute,
            "threshold": self.threshold,
            "groups": self.groups,
            "max_disparity": self.max_disparity,
            "reference_group": self.reference_group,
            "reference_rate": self.reference_rate,
            "ratified_tolerance": self.ratified_tolerance,
            "status": "pending_governance" if self.ratified_tolerance is None else "measured",
            "limitations": self.limitations,
        }


def demographic_parity(
    y_prob,
    sensitive_attribute,
    *,
    threshold: float = 0.5,
    attribute_name: str = "attribute",
    min_group_size: int = 30,
) -> DemographicParityResult:
    """Approval-rate disparity across groups.

    approval_rate(g) = P(y_prob >= threshold | group == g)
    max_disparity = max_g |approval_rate(g) - approval_rate(reference)|

    Reference group is the group with the largest sample. Groups below
    `min_group_size` are reported but flagged as low-confidence.
    """
    import numpy as np
    import pandas as pd

    y_prob = np.asarray(y_prob, dtype=float)
    s = pd.Series(sensitive_attribute).reset_index(drop=True)
    if len(y_prob) != len(s):
        raise ValueError("y_prob and sensitive_attribute length mismatch")

    approved = (y_prob >= threshold).astype(int)
    groups: dict[str, dict[str, float]] = {}
    low_conf: list[str] = []
    for g in sorted(s.unique().tolist()):
        mask = (s == g).to_numpy()
        n = int(mask.sum())
        if n == 0:
            continue
        rate = float(approved[mask].mean())
        groups[str(g)] = {"n": float(n), "approval_rate": rate}
        if n < min_group_size:
            low_conf.append(str(g))

    reference = max(groups.items(), key=lambda kv: kv[1]["n"])[0] if groups else None
    ref_rate = groups[reference]["approval_rate"] if reference else None
    max_disp = 0.0
    if reference is not None:
        max_disp = max(abs(v["approval_rate"] - ref_rate) for v in groups.values())

    limitations = [
        "computed on proxy/synthetic data — sample sizes and generator biases limit interpretation",
        "no ratified fairness tolerance yet — threshold decision pending governance",
    ]
    if low_conf:
        limitations.append(f"low-confidence groups (n < {min_group_size}): {', '.join(low_conf)}")

    return DemographicParityResult(
        attribute=attribute_name,
        threshold=threshold,
        groups=groups,
        max_disparity=float(max_disp),
        reference_group=reference,
        reference_rate=ref_rate,
        ratified_tolerance=None,
        limitations=limitations,
    )


def evaluate_predictions(y_true, y_prob) -> dict[str, float]:
    """Standard predictive metrics: AUC, Gini, Brier."""
    import numpy as np
    from sklearn.metrics import brier_score_loss, roc_auc_score

    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    if len(np.unique(y_true)) < 2:
        return {"auc": float("nan"), "gini": float("nan"), "brier": float("nan")}
    auc = float(roc_auc_score(y_true, y_prob))
    return {"auc": auc, "gini": 2 * auc - 1, "brier": float(brier_score_loss(y_true, y_prob))}

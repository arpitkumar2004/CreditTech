"""SHAP explainability for the CreditTech logistic scorecard.

For a linear/logistic model the exact Shapley contribution of feature i is:

    phi_i = w_i * (x_i - E[x_i])

with reference E[x_i] taken from the training-set feature means (preferred),
falling back to a domain-tuned prior for the pre-trained default scorecard.

We compute exact Shapley values in closed form rather than pulling in the
`shap` package — the two are numerically identical for this model class.
"""

from __future__ import annotations

from typing import Any

from ml.training.scorecard import LogisticScorecard

# Domain-tuned prior means (used only when no trained-model reference is present)
DEFAULT_REFERENCE_VALUES: dict[str, float] = {
    "shg_repayment_rate": 90.0,
    "shg_meeting_attendance_pct": 80.0,
    "shg_savings_consistency": 0.5,
    "shg_membership_years": 2.0,
    "shg_grade": 0.6,
    "utility_payment_ontime_pct": 90.0,
    "upi_transaction_regularity": 0.4,
    "estimated_crop_income_kharif": 35000.0,
    "estimated_crop_income_rabi": 40000.0,
    "income_stability_cv": 0.5,
    "monthly_avg_credit_inflow": 6000.0,
    "pm_kisan_regularity": 0.8,
    "shg_cumulative_savings": 4000.0,
    "bank_balance_avg_6m": 5000.0,
    "asset_score": 0.4,
    "land_holding_acres": 2.0,
    "irrigation_access": 0.5,
    "land_quality_ndvi_avg": 0.5,
    "ndvi_trend_2season": 0.0,
    "rainfall_deviation_pct": 0.0,
    "crop_insurance_enrolled": 0.5,
}


class ScorecardSHAPExplainer:
    """Computes exact Shapley contributions for the LogisticScorecard.

    The explainer is deterministic: for a given (features, reference, weights)
    it returns the same ordered list. Unknown features and non-coercible values
    are skipped safely — never raised — so scoring cannot crash on a stray field.
    """

    def __init__(
        self,
        scorecard: LogisticScorecard,
        reference_values: dict[str, float] | None = None,
    ) -> None:
        self.scorecard = scorecard
        # Prefer the trained model's feature means (loaded via registry); fall
        # back to the domain prior; ignore anything not in the scorecard weights.
        self.reference_values: dict[str, float] = {
            k: float(v)
            for k, v in (reference_values or DEFAULT_REFERENCE_VALUES).items()
            if k in scorecard.weights
        }

    def compute_shap_values(self, features: dict[str, Any]) -> list[dict[str, Any]]:
        if hasattr(self.scorecard, "compute_shap_values") and not isinstance(self.scorecard, LogisticScorecard):
            return self.scorecard.compute_shap_values(features)
        contributions: list[dict[str, Any]] = []
        for feature, val in features.items():
            if feature not in self.scorecard.weights:
                continue
            v = self.scorecard._coerce(feature, val)
            if v is None:
                continue
            ref = self.reference_values.get(feature, 0.0)
            coeff = self.scorecard.weights[feature]
            shap_val = float(coeff) * (float(v) - float(ref))
            contributions.append({
                "feature": feature,
                "value": float(v),
                "shap_value": shap_val,
            })
        # Deterministic tie-break: |shap| desc, then feature name asc.
        contributions.sort(key=lambda x: (-abs(x["shap_value"]), x["feature"]))
        return contributions

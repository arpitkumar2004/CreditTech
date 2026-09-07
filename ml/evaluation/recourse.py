"""Actionable Recourse and Counterfactual Explanation Engine for CreditTech.

Under the RBI Fair Practices Code and Basel II/III consumer credit guidelines,
rejected or borderline thin-file borrowers have a right to actionable explanations.
Rather than merely citing immutable negative drivers (e.g. "Your landholding is only 0.5 acres"),
this module computes the minimal, realistic behavioral changes required to elevate
a borrower's score from MODERATE/REJECT (< 650) to APPROVE (>= 650).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RecourseAction:
    feature_name: str
    current_value: float
    target_value: float
    projected_score_impact: float
    guidance_en: str
    guidance_hi: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecoursePlan:
    eligible: bool
    current_score: int
    target_score: int
    projected_score: int
    pathways: list[RecourseAction]

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "current_score": self.current_score,
            "target_score": self.target_score,
            "projected_score": self.projected_score,
            "pathways": [p.to_dict() for p in self.pathways],
        }


# Strict boundary: non-actionable features that must NEVER be suggested as recourse
NON_ACTIONABLE_FEATURES: frozenset[str] = frozenset({
    "land_holding_acres",
    "land_quality_ndvi_avg",
    "ndvi_trend_2season",
    "rainfall_deviation_pct",
    "irrigation_access",
    "shg_membership_years",
    "estimated_crop_income_kharif",
    "estimated_crop_income_rabi",
    "asset_score",
    "income_stability_cv",
    "village_id",
    "gender",
    "landholding_band",
    "agro_climatic_zone",
})


class CounterfactualRecourseEngine:
    """Computes actionable counterfactual recourse pathways for borrowers."""

    def __init__(self, scorecard: Any) -> None:
        self.scorecard = scorecard

    def _get_score_900(self, features: dict[str, Any]) -> int:
        p = self.scorecard.predict_probability(features)
        _, s_900 = self.scorecard.calibrate_score(p)
        return int(s_900)

    def generate_recourse(
        self,
        features: dict[str, Any],
        target_score: int = 650,
        max_pathways: int = 4,
    ) -> dict[str, Any]:
        """Generates minimal behavioral recourse pathways to reach target approval score."""
        current_score = self._get_score_900(features)
        if current_score >= target_score:
            return RecoursePlan(
                eligible=False,
                current_score=current_score,
                target_score=target_score,
                projected_score=current_score,
                pathways=[],
            ).to_dict()

        # Define candidate actionable feature perturbations with domain-realistic upper bounds
        perturbed = dict(features)
        candidate_improvements: list[tuple[str, float, float, str, str]] = []

        # 1. SHG Meeting Attendance
        curr_att = float(features.get("shg_meeting_attendance_pct", 0.0) or 0.0)
        if curr_att < 95.0:
            target_att = min(100.0, max(85.0, curr_att + 25.0))
            candidate_improvements.append((
                "shg_meeting_attendance_pct",
                curr_att,
                target_att,
                f"Increase monthly SHG meeting attendance to {target_att:.0f}% over the next 3 months.",
                f"आगामी 3 महीनों में स्वयं सहायता समूह (SHG) की बैठक उपस्थिति को बढ़ाकर {target_att:.0f}% करें।",
            ))

        # 2. SHG Savings Consistency
        curr_sav = float(features.get("shg_savings_consistency", 0.0) or 0.0)
        if curr_sav < 0.90:
            target_sav = min(1.0, max(0.75, curr_sav + 0.35))
            candidate_improvements.append((
                "shg_savings_consistency",
                curr_sav,
                target_sav,
                "Maintain continuous monthly savings deposits in SHG without interruptions.",
                "स्वयं सहायता समूह (SHG) में बिना किसी रुकावट के लगातार मासिक बचत जमा बनाए रखें।",
            ))

        # 3. Crop Insurance Enrollment
        curr_ins = bool(features.get("crop_insurance_enrolled", False))
        if not curr_ins:
            candidate_improvements.append((
                "crop_insurance_enrolled",
                0.0,
                1.0,
                "Enroll in PMFBY (Pradhan Mantri Fasal Bima Yojana) crop insurance for the upcoming sowing season.",
                "आगामी बुवाई के मौसम के लिए प्रधानमंत्री फसल बीमा योजना (PMFBY) में नामांकन करें।",
            ))

        # 4. Utility Payment Timeliness
        curr_util = float(features.get("utility_payment_ontime_pct", 0.0) or 0.0)
        if curr_util < 95.0:
            target_util = min(100.0, max(90.0, curr_util + 25.0))
            candidate_improvements.append((
                "utility_payment_ontime_pct",
                curr_util,
                target_util,
                f"Ensure electricity and utility bills are consistently paid on time (target: {target_util:.0f}%).",
                f"बिजली और अन्य उपयोगिता बिलों का समय पर लगातार भुगतान (लक्ष्य: {target_util:.0f}%) सुनिश्चित करें।",
            ))

        # 5. SHG Repayment Rate
        curr_repay = float(features.get("shg_repayment_rate", 0.0) or 0.0)
        if curr_repay < 0.95:
            target_repay = min(1.0, max(0.90, curr_repay + 0.20))
            candidate_improvements.append((
                "shg_repayment_rate",
                curr_repay,
                target_repay,
                f"Clear existing internal SHG loan arrears to achieve {int(target_repay * 100)}% on-time repayment.",
                f"आंतरिक SHG ऋण की किश्तों का समय पर {int(target_repay * 100)}% भुगतान सुनिश्चित करें।",
            ))

        # 6. UPI Transaction Regularity
        curr_upi = float(features.get("upi_transaction_regularity", 0.0) or 0.0)
        if curr_upi < 0.70:
            target_upi = min(1.0, curr_upi + 0.35)
            candidate_improvements.append((
                "upi_transaction_regularity",
                curr_upi,
                target_upi,
                "Adopt digital UPI payments for agricultural inputs and market transactions.",
                "कृषि आदानों और दैनिक बाजार लेन-देन के लिए डिजिटल यूपीआई (UPI) का नियमित उपयोग करें।",
            ))

        # 7. PM-Kisan Regularity
        curr_pmk = float(features.get("pm_kisan_regularity", 0.0) or 0.0)
        if curr_pmk < 0.90:
            candidate_improvements.append((
                "pm_kisan_regularity",
                curr_pmk,
                1.0,
                "Complete PM-Kisan portal e-KYC to ensure uninterrupted quarterly benefit transfers.",
                "त्रैमासिक लाभ राशि में निरंतरता हेतु पीएम-किसान पोर्टल पर ई-केवाईसी (e-KYC) पूर्ण करें।",
            ))

        # Greedily evaluate individual gains
        evaluated_actions: list[tuple[float, RecourseAction, dict[str, Any]]] = []
        for feat, c_val, t_val, en_text, hi_text in candidate_improvements:
            test_feat = dict(perturbed)
            test_feat[feat] = t_val
            new_s = self._get_score_900(test_feat)
            gain = new_s - current_score
            if gain > 0:
                action = RecourseAction(
                    feature_name=feat,
                    current_value=round(c_val, 2),
                    target_value=round(t_val, 2),
                    projected_score_impact=gain,
                    guidance_en=en_text,
                    guidance_hi=hi_text,
                )
                evaluated_actions.append((gain, action, test_feat))

        # Sort by impact descending
        evaluated_actions.sort(key=lambda x: -x[0])

        chosen_pathways: list[RecourseAction] = []
        accumulated_features = dict(features)
        running_score = current_score

        for gain, action, _ in evaluated_actions:
            if len(chosen_pathways) >= max_pathways:
                break
            # Apply improvement cumulatively
            test_accum = dict(accumulated_features)
            test_accum[action.feature_name] = action.target_value
            new_running_score = self._get_score_900(test_accum)
            if new_running_score > running_score:
                action.projected_score_impact = new_running_score - running_score
                chosen_pathways.append(action)
                accumulated_features = test_accum
                running_score = new_running_score

            if running_score >= target_score:
                break

        return RecoursePlan(
            eligible=True,
            current_score=current_score,
            target_score=target_score,
            projected_score=running_score,
            pathways=chosen_pathways,
        ).to_dict()

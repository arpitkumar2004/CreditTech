"""Explainability Service rendering SHAP outputs into localized reason codes."""

from typing import Any

from services.core.shared.logging import get_logger

logger = get_logger("explainability.service")


class ExplainabilityService:
    """Renders SHAP feature impact values into human-readable, bilingual reason codes."""

    # Bilingual templates mapping feature + impact direction to localized descriptions
    # Matches phase 0 shap_reason_code_templates.md specification
    TEMPLATES = {
        "shg_repayment_rate": {
            "POSITIVE": {
                "en": "Excellent SHG loan repayment history ({value}%)",
                "hi": "उत्कृष्ट SHG ऋण चुकौती इतिहास ({value}%)",
            },
            "NEGATIVE": {
                "en": "SHG loan repayment rate below average ({value}%)",
                "hi": "उ SHG ऋण चुकौती दर औसत से कम ({value}%)",
            },
        },
        "shg_meeting_attendance_pct": {
            "POSITIVE": {
                "en": "Regular SHG meeting attendance ({value}%)",
                "hi": "नियमित SHG बैठक उपस्थिति ({value}%)",
            },
            "NEGATIVE": {
                "en": "Low SHG meeting attendance ({value}%)",
                "hi": "कम SHG बैठक उपस्थिति ({value}%)",
            },
        },
        "shg_savings_consistency": {
            "POSITIVE": {
                "en": "Consistent monthly SHG savings deposits",
                "hi": "नियमित मासिक SHG बचत जमा",
            },
            "NEGATIVE": {
                "en": "Irregular SHG savings pattern",
                "hi": "अनियमित SHG बचत पैटर्न",
            },
        },
        "shg_membership_years": {
            "POSITIVE": {
                "en": "Long SHG membership ({value} years)",
                "hi": "लंबी SHG सदस्यता ({value} वर्ष)",
            },
        },
        "utility_payment_ontime_pct": {
            "POSITIVE": {
                "en": "Good utility bill payment record ({value}%)",
                "hi": "अच्छा बिल भुगतान रिकॉर्ड ({value}%)",
            },
            "NEGATIVE": {
                "en": "Frequent late utility payments ({value}%)",
                "hi": "बार-बार देर से बिल भुगतान ({value}%)",
            },
        },
        "income_stability_cv": {
            "POSITIVE": {
                "en": "Stable monthly income pattern",
                "hi": "स्थिर मासिक आय पैटर्न",
            },
            "NEGATIVE": {
                "en": "Volatile income — high seasonal variation",
                "hi": "अस्थिर आय — उच्च मौसमी उतार-चढ़ाव",
            },
        },
        "pm_kisan_regularity": {
            "POSITIVE": {
                "en": "Receives PM-KISAN direct benefit transfers regularly",
                "hi": "नियमित रूप से PM-KISAN लाभ प्राप्त",
            },
        },
        "shg_cumulative_savings": {
            "POSITIVE": {
                "en": "Strong cumulative SHG savings (₹{value})",
                "hi": "मजबूत संचयी SHG बचत (₹{value})",
            },
        },
        "bank_balance_avg_6m": {
            "POSITIVE": {
                "en": "Healthy average bank balance (₹{value})",
                "hi": "स्वस्थ औसत बैंक शेष (₹{value})",
            },
            "NEGATIVE": {
                "en": "Low average bank balance (₹{value})",
                "hi": "कम औसत बैंक शेष (₹{value})",
            },
        },
        "asset_score": {
            "POSITIVE": {
                "en": "Good asset base (land, livestock, or equipment)",
                "hi": "अच्छा संपत्ति आधार (भूमि, पशुधन, उपकरण)",
            },
        },
        "land_holding_acres": {
            "POSITIVE": {
                "en": "Adequate cultivable land ({value} acres)",
                "hi": "पर्याप्त कृषि योग्य भूमि ({value} एकड़)",
            },
        },
        "irrigation_access": {
            "POSITIVE": {
                "en": "Access to irrigation infrastructure",
                "hi": "सिंचाई सुविधा उपलब्ध",
            },
            "NEGATIVE": {
                "en": "No irrigation — rain-dependent farming",
                "hi": "सिंचाई नहीं — वर्षा निर्भर खेती",
            },
        },
        "land_quality_ndvi_avg": {
            "POSITIVE": {
                "en": "Good crop health on land (satellite verified)",
                "hi": "भूमि पर अच्छी फसल स्वास्थ्य (उपग्रह सत्यापित)",
            },
        },
        "ndvi_trend_2season": {
            "POSITIVE": {
                "en": "Improving crop health trend",
                "hi": "फसल स्वास्थ्य में सुधार की प्रवृत्ति",
            },
            "NEGATIVE": {
                "en": "Declining crop health trend",
                "hi": "फसल स्वास्थ्य में गिरावट की प्रवृत्ति",
            },
        },
        "rainfall_deviation_pct": {
            "NEGATIVE": {
                "en": "Below-normal rainfall in area ({value}% deviation)",
                "hi": "आपके क्षेत्र में सामान्य से कम वर्षा ({value}% विचलन)",
            },
        },
        "crop_insurance_enrolled": {
            "POSITIVE": {
                "en": "Enrolled in PMFBY crop insurance",
                "hi": "PMFBY फसल बीमा में नामांकित",
            },
        },
        # Added in P3.8 template final pass — cover every feature the v1 model uses.
        "shg_grade": {
            "POSITIVE": {
                "en": "High NABARD SHG grade (A/B)",
                "hi": "उच्च NABARD SHG ग्रेड (A/B)",
            },
            "NEGATIVE": {
                "en": "Low NABARD SHG grade",
                "hi": "निम्न NABARD SHG ग्रेड",
            },
        },
        "estimated_crop_income_kharif": {
            "POSITIVE": {
                "en": "Healthy estimated Kharif crop income (₹{value})",
                "hi": "अनुमानित खरीफ फसल आय (₹{value})",
            },
        },
        "estimated_crop_income_rabi": {
            "POSITIVE": {
                "en": "Healthy estimated Rabi crop income (₹{value})",
                "hi": "अनुमानित रबी फसल आय (₹{value})",
            },
        },
        "monthly_avg_credit_inflow": {
            "POSITIVE": {
                "en": "Steady monthly credit inflow (₹{value})",
                "hi": "नियमित मासिक क्रेडिट प्रवाह (₹{value})",
            },
            "NEGATIVE": {
                "en": "Low monthly credit inflow (₹{value})",
                "hi": "कम मासिक क्रेडिट प्रवाह (₹{value})",
            },
        },
    }

    def render_reason_codes(self, shap_values: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        """Maps computed SHAP contributions to localized templates.

        Returns top 'limit' reason codes with rendered English and Hindi texts.
        """
        reason_codes = []
        rank = 1

        for item in shap_values:
            if rank > limit:
                break

            feature = item["feature"]
            shap_val = item["shap_value"]
            val = item["value"]
            direction = "POSITIVE" if shap_val >= 0 else "NEGATIVE"

            # Check if template exists for this feature and direction
            feature_templates = self.TEMPLATES.get(feature)
            if not feature_templates or direction not in feature_templates:
                continue  # Skip features without mapped templates

            template = feature_templates[direction]

            # Format numbers to look cleaner
            formatted_val = val
            if isinstance(val, float):
                formatted_val = f"{val:.1f}"

            rendered_en = template["en"].format(value=formatted_val)
            rendered_hi = template["hi"].format(value=formatted_val)

            reason_codes.append({
                "rank": rank,
                "feature_name": feature,
                "direction": direction,
                "shap_value": shap_val,
                "localized_text_en": rendered_en,
                "localized_text_hi": rendered_hi,
            })
            rank += 1

        return reason_codes

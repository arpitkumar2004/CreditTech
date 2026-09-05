# SHAP Reason-Code Template Library

**Phase 0 Deliverable — Final pass completed as part of Phase 3 exit gate**
**Last Updated:** 2026-09-03
**Language ratification:** Hindi and English wording below is DRAFT-FINAL for
pilot v1. Wording marked with a ⚠️ tag is **pending governance ratification**
before public release. Do not remove that marker without an approver sign-off.

## Purpose
Human-readable explanations for SHAP-driven reason codes in English and Hindi.

## Templates by Feature

### Character (Repayment & Discipline)
| Feature | Direction | English | Hindi |
|---------|-----------|---------|-------|
| shg_repayment_rate | POSITIVE | Excellent SHG loan repayment history ({value}%) | उत्कृष्ट SHG ऋण चुकौती इतिहास ({value}%) |
| shg_repayment_rate | NEGATIVE | SHG loan repayment rate below average ({value}%) | SHG ऋण चुकौती दर औसत से कम ({value}%) |
| shg_meeting_attendance_pct | POSITIVE | Regular SHG meeting attendance ({value}%) | नियमित SHG बैठक उपस्थिति ({value}%) |
| shg_meeting_attendance_pct | NEGATIVE | Low SHG meeting attendance ({value}%) | कम SHG बैठक उपस्थिति ({value}%) |
| shg_savings_consistency | POSITIVE | Consistent monthly SHG savings deposits | नियमित मासिक SHG बचत जमा |
| shg_savings_consistency | NEGATIVE | Irregular SHG savings pattern | अनियमित SHG बचत पैटर्न |
| shg_membership_years | POSITIVE | Long SHG membership ({value} years) | लंबी SHG सदस्यता ({value} वर्ष) |
| utility_payment_ontime_pct | POSITIVE | Good utility bill payment record ({value}%) | अच्छा बिल भुगतान रिकॉर्ड ({value}%) |
| utility_payment_ontime_pct | NEGATIVE | Frequent late utility payments | बार-बार देर से बिल भुगतान |
| shg_grade | POSITIVE | High NABARD SHG grade (grade A/B) | उच्च NABARD SHG ग्रेड (A/B) |
| shg_grade | NEGATIVE | ⚠️ Low NABARD SHG grade | ⚠️ निम्न NABARD SHG ग्रेड |
| upi_transaction_regularity | POSITIVE | Consistent monthly UPI activity | नियमित मासिक UPI गतिविधि |
| upi_transaction_regularity | NEGATIVE | Irregular UPI transaction pattern | अनियमित UPI लेनदेन पैटर्न |

### Capacity (Income & Cash Flow)
| Feature | Direction | English | Hindi |
|---------|-----------|---------|-------|
| income_stability_cv | POSITIVE | Stable monthly income pattern | स्थिर मासिक आय पैटर्न |
| income_stability_cv | NEGATIVE | Volatile income — high seasonal variation | अस्थिर आय — उच्च मौसमी उतार-चढ़ाव |
| pm_kisan_beneficiary | POSITIVE | Receives PM-KISAN direct benefit transfers | PM-KISAN प्रत्यक्ष लाभ हस्तांतरण प्राप्त |
| pm_kisan_regularity | POSITIVE | Receives PM-KISAN direct benefit transfers regularly | नियमित रूप से PM-KISAN लाभ प्राप्त |
| estimated_crop_income_kharif | POSITIVE | Healthy estimated Kharif crop income (₹{value}) | अनुमानित खरीफ फसल आय (₹{value}) |
| estimated_crop_income_rabi | POSITIVE | Healthy estimated Rabi crop income (₹{value}) | अनुमानित रबी फसल आय (₹{value}) |
| monthly_avg_credit_inflow | POSITIVE | Steady monthly credit inflow (₹{value}) | नियमित मासिक क्रेडिट प्रवाह (₹{value}) |
| monthly_avg_credit_inflow | NEGATIVE | Low monthly credit inflow (₹{value}) | कम मासिक क्रेडिट प्रवाह (₹{value}) |
| diversification_index | POSITIVE | Multiple income sources (diversified livelihood) | अनेक आय स्रोत (विविध आजीविका) |
| diversification_index | NEGATIVE | Single income source (concentration risk) | एकल आय स्रोत (एकाग्रता जोखिम) |

### Capital (Assets & Savings)
| Feature | Direction | English | Hindi |
|---------|-----------|---------|-------|
| shg_cumulative_savings | POSITIVE | Strong cumulative SHG savings (₹{value}) | मजबूत संचयी SHG बचत (₹{value}) |
| bank_balance_avg_6m | POSITIVE | Healthy average bank balance | स्वस्थ औसत बैंक शेष |
| bank_balance_avg_6m | NEGATIVE | Low average bank balance | कम औसत बैंक शेष |
| asset_score | POSITIVE | Good asset base (land + livestock + equipment) | अच्छा संपत्ति आधार (भूमि + पशुधन + उपकरण) |
| kcc_holder | POSITIVE | Active Kisan Credit Card holder | सक्रिय किसान क्रेडिट कार्ड धारक |

### Collateral (Land & Physical)
| Feature | Direction | English | Hindi |
|---------|-----------|---------|-------|
| land_holding_acres | POSITIVE | Adequate cultivable land ({value} acres) | पर्याप्त कृषि योग्य भूमि ({value} एकड़) |
| irrigation_access | POSITIVE | Access to irrigation infrastructure | सिंचाई सुविधा उपलब्ध |
| irrigation_access | NEGATIVE | No irrigation — rain-dependent farming | सिंचाई नहीं — वर्षा निर्भर खेती |
| land_quality_ndvi_avg | POSITIVE | Good crop health on land (satellite verified) | भूमि पर अच्छी फसल स्वास्थ्य (उपग्रह सत्यापित) |

### Conditions (Environmental)
| Feature | Direction | English | Hindi |
|---------|-----------|---------|-------|
| ndvi_trend_2season | POSITIVE | Improving crop health trend | फसल स्वास्थ्य में सुधार की प्रवृत्ति |
| ndvi_trend_2season | NEGATIVE | Declining crop health trend | फसल स्वास्थ्य में गिरावट की प्रवृत्ति |
| rainfall_deviation_pct | NEGATIVE | Below-normal rainfall in your area | आपके क्षेत्र में सामान्य से कम वर्षा |
| crop_insurance_enrolled | POSITIVE | Enrolled in PMFBY crop insurance | PMFBY फसल बीमा में नामांकित |

## Rendering Rules
1. Show top 5 reason codes per score (3 positive + 2 negative, or vice versa)
2. Sort by absolute SHAP value (descending)
3. Insert `{value}` from actual feature values
4. Display in borrower's preferred language
5. No PII, no protected attributes, no monitored-only fields
   (`gender`, `village_id`, `landholding_band`, `site_type`, `agro_climatic_zone`)
   may appear in a rendered reason code, even indirectly.
6. Directionality must match SHAP sign. If a feature has only a POSITIVE template
   but SHAP produces a NEGATIVE contribution, the code is suppressed rather than
   inverted mechanically — inverting text without linguistic review risks
   misleading causal claims.

## Coverage vs. active feature set

The active v1 model (registered at `ml/registry/store/v1.0.0-logistic/`) uses
the feature set declared in `ml/features/schema.py::MODEL_FEATURES`. As of the
P3 gate, every model feature has at least one template (positive or negative);
some directions are single-sided by design because the opposite direction has
no defensible plain-language explanation yet and will be added when governance
ratifies the language.

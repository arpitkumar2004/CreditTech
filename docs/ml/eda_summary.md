# CreditTech — Exploratory Data Analysis & Target Profiling Report

- **Sample Size**: 5,000 borrowers
- **Empirical Default Rate**: 19.08%
- **Unique Pilot Villages**: 15
- **Agro-Climatic Zones**: 3

## Feature Correlations with Repayment

| Feature Name | 5-Cs Rail | Correlation with Repayment | Missingness Rate |
| :--- | :--- | :--- | :--- |
| `shg_repayment_rate` | CHARACTER | `+0.2119` | 0.0% |
| `shg_meeting_attendance_pct` | CHARACTER | `+0.0824` | 0.0% |
| `shg_savings_consistency` | CHARACTER | `-0.1860` | 0.0% |
| `shg_membership_years` | CHARACTER | `+0.1039` | 0.0% |
| `shg_grade` | CHARACTER | `+0.1165` | 0.0% |
| `utility_payment_ontime_pct` | CHARACTER | `+0.0489` | 0.0% |
| `upi_transaction_regularity` | CHARACTER | `-0.0953` | 0.0% |
| `estimated_crop_income_kharif` | CAPACITY | `+0.0241` | 0.0% |
| `estimated_crop_income_rabi` | CAPACITY | `+0.0327` | 0.0% |
| `income_stability_cv` | CAPACITY | `-0.2342` | 0.0% |
| `monthly_avg_credit_inflow` | CAPACITY | `+0.0303` | 0.0% |
| `pm_kisan_regularity` | CAPACITY | `+0.0491` | 0.0% |
| `shg_cumulative_savings` | CAPITAL | `+0.0152` | 0.0% |
| `bank_balance_avg_6m` | CAPITAL | `+0.0452` | 0.0% |
| `asset_score` | CAPITAL | `+0.0743` | 0.0% |
| `land_holding_acres` | COLLATERAL | `+0.0601` | 0.0% |
| `irrigation_access` | COLLATERAL | `+0.1161` | 0.0% |
| `land_quality_ndvi_avg` | COLLATERAL | `+0.0686` | 0.0% |
| `ndvi_trend_2season` | CONDITIONS | `+0.0430` | 0.0% |
| `rainfall_deviation_pct` | CONDITIONS | `-0.0406` | 0.0% |
| `crop_insurance_enrolled` | CONDITIONS | `+0.0549` | 0.0% |

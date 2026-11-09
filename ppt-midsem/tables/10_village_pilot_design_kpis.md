# Table 10: Initial 4–5 Village Pilot Design, Site Profiles & Evaluation KPIs

### 10.1 Stratified Agro-Climatic Pilot Cohort (5 Representative Sites)

| Site Designation | Representative Geography | Cropping Pattern & Economic Archetype | Infrastructure & Connectivity Floor | Target Sample | Primary Hypothesis Tested in Pilot |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Site A: Irrigated High-KCC** | Western Uttar Pradesh / Hanumangarh (Rajasthan) | Canal-irrigated cotton, wheat, sugarcane; high commercialization; active mandi trade. | 4G mobile coverage; high KCC density; digitized state land records. | **200 Borrowers** | Whether alternative scoring improves **turnaround speed (&lt; 1 hr)** and credit limit adequacy for existing KCC holders. |
| **Site B: Rainfed Climate-Exposed** | Marathwada (Maharashtra) / Jhabua (Madhya Pradesh) | Rainfed soybean, cotton, coarse millets; high exposure to monsoon dry spells. | Moderate 4G; moderate land digitization; active microfinance branches. | **200 Borrowers** | Value of **Sentinel-2 NDVI &amp; IMD drought risk** in separating idiosyncratic farm distress from regional covariate weather shocks. |
| **Site C: SHG-Dense Southern Model** | Krishna District (Andhra Pradesh) / Warangal (Telangana) | Paddy, horticulture, dairy; highly organized women's self-help groups under SERP/MEPMA. | Reliable 4G/fiber; 100% e-Shakti digitised SHG ledgers; PACS branches. | **250 Borrowers** | Predictive power of **group thrift &amp; peer social collateral** in under-writing individual micro-enterprise graduation loans. |
| **Site D: Allied-Activity / Dairy** | Anand / Mehsana (Gujarat) / Coastal Odisha | Dairy cattle rearing, smallholder fisheries; non-seasonal daily/weekly cashflow. | Good 4G connectivity; automated milk collection centers (AMCC). | **200 Borrowers** | Modeling **high-frequency non-crop cashflows** (daily milk pouring data) to predict debt-service capacity without land collateral. |
| **Site E: Low-Bandwidth / Tribal** | Ranchi / Khunti (Jharkhand) / Bastar (Chhattisgarh) | Forest produce, smallholder pulses; fragmented land inheritance; oral sharecropping. | Weak/intermittent 2G/4G connectivity; low bank branch density. | **150 Borrowers** | Field stress-testing of **Graceful Degradation** architecture and assisted Bank Sakhi offline PWA tablet onboarding. |
| **Total Pilot Scope** | **5 Gram Panchayats across 5 States** | **Multi-Agro-Climatic Diversity** | **Varied Connectivity Stack** | **1,000 Total Borrowers** | **9–12 Month Duration (Full Kharif–Rabi Agricultural Cycle)** |

---

### 10.2 Quantitative Evaluation KPIs & Target Benchmarks

| Evaluation KPI | Baseline Metric (As-Is Status Quo) | Pilot Target (CreditTech) | Verification Instrument & Data Source |
| :--- | :--- | :--- | :--- |
| **1. Median Turnaround Time (TAT)** | **10 to 15 business days** (traditional branch appraisal) | **&lt; 1 hour** (application to credit score dispatch) | Automated server timestamp logs (`application_created` to `score_dispatched`). |
| **2. Approval Rate Uplift for Thin-File Borrowers** | Standard bank rejection rate: **60–70%** (CIBIL -1) | **+20% to +30% uplift** in formal approvals | Comparative approval rate on thin-file cohort at partner Regulated Entity. |
| **3. Gender Parity in Approvals** | Rural formal credit gender gap of **&gt; 35%** | Parity gap narrowed by **$\ge 50\%$** (DIR $\ge 0.80$) | M5 Fairness Engine demographic audit reports across male and female applicants. |
| **4. Portfolio-at-Risk (PAR90)** | Agricultural banking sector GNPA benchmark: **6.2%** (RBI 2024) | **$\le 2.0\%$** at 90 days past due | Partner bank loan ledger feeds collected via M7 Loan Lifecycle Module. |
| **5. Explainability Comprehension Rate** | **0%** (borrowers never receive structured reasons) | **$\ge 80\%$** of rejected/approved borrowers can correctly restate score drivers | Field survey of 200 random applicants conducted by independent academic team. |
| **6. Resilience Under Partial Data Outage** | **0%** (system halts if single document is missing) | **$\ge 90\%$** of applicants receive valid confidence-weighted score with 1 rail down | Ingestion telemetry tracking partial-data scoring during API timeout events. |

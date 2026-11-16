# `ppt-midsem` — Mid-Semester Academic Defense Presentation Assets

This directory contains the complete, dedicated asset package created specifically for your **Mid-Semester Academic Defense / Evaluation Committee Review** for **CreditTech: Alternative Credit Scoring for Rural Financial Inclusion**.

It directly addresses the 14 requirements requested by your evaluation committee:
1. ❑ Problem & Village-Level Need Assessment [based on secondary data]
2. ❑ Stakeholder & Institutional Mapping
3. ❑ Existing System (As-Is)
4. ❑ Proposed System (To-Be)
5. ❑ Complete System Architecture
6. ❑ Data Architecture & Data Sources
7. ❑ Technology Stack
8. ❑ API/DPI & Institutional Integration Framework
9. ❑ Functional Modules
10. ❑ User Journey / Process Flow
11. ❑ Security, Privacy & Regulatory Framework
12. ❑ Initial 4–5 Village Pilot Design
13. ❑ Preliminary Cost & Resource Requirements
14. ❑ Literature, Policy & Real-world Case Evidence

---

## Folder Structure & Asset Map

```
d:\CreditTech\ppt-midsem\
├── CreditTech_MidSem_Academic_Presentation.pptx <-- Master Constitution-Compliant 16-Slide Deck (with embedded figures & Inter typography)
├── CreditTech_MidSem_Presentation.pptx          <-- Base presentation deck
├── constitution_ppt.md                         <-- The Master Constitution specifying all slide rules & style
├── INSTRUCTIONS_ACADEMIC_PPT.md                 <-- Master Guide: How to build & defend an academic-level PPT
├── SLIDE_DECK_CONTENT_AND_SCRIPTS.md            <-- Slide-by-slide text, bullet points & verbatim speaker scripts
├── COMMITTEE_DEFENSE_CHEATSHEET.md              <-- 2-page antidote sheet to tough professor grilling & formulas
├── generate_midsem_pptx.py                      <-- Standalone Python script to regenerate/customize the .pptx deck
│
├── diagrams/                            <-- 7 Clean, high-resolution vector SVG diagrams
│   ├── 01_as_is_workflow.svg            <-- As-Is linear, paper-heavy bureau failure workflow
│   ├── 02_to_be_workflow.svg            <-- To-Be consent-based multi-rail alternative scoring workflow
│   ├── 03_system_architecture_5layers.svg <-- 5-Layer Modular Monolith reference architecture
│   ├── 04_dpi_integration_hub.svg       <-- Orchestration hub connecting AA, ULI, OCEN, and Regulated Lenders
│   ├── 05_borrower_user_journey.svg     <-- 4-Stage borrower journey with SLAs (<5 min, <3 min, same-day)
│   ├── 06_stakeholder_mapping.svg       <-- 4-Quadrant institutional ecosystem mapping
│   └── 07_pilot_village_matrix.svg      <-- 5 Stratified agro-climatic site archetypes and evaluation KPIs
│
└── tables/                              <-- 12 Structured academic markdown tables ready for slides
    ├── 01_secondary_data_need_assessment.md  <-- Findex '25, RBI FI-Index, NAFIS '22, SIDBI '25 benchmarks
    ├── 02_stakeholder_matrix.md              <-- Table 2.1 Multi-stakeholder roles & legal interlock
    ├── 03_as_is_vs_to_be.md                  <-- Table 5.1 Comparative analysis across 6 dimensions
    ├── 04_data_architecture_and_sources.md   <-- Table 7.1 Ingestion streams & cryptographic PII segregation
    ├── 05_technology_stack_justification.md  <-- Table 8.1 Tech stack selection & Architecture Decision Records
    ├── 06_dpi_and_institutional_integration.md <-- Table 9.1 DPI rails (AA, ULI, OCEN, DPDP)
    ├── 07_functional_modules_m1_m9.md       <-- Table 10.1 Functional specifications for M1 through M9
    ├── 08_user_journey_sla.md                <-- Table 11.1 Process flows, systems-of-record & target SLAs
    ├── 09_security_and_regulatory_matrix.md  <-- Table 12.1 RBI DLG, DPDP 2023, and fairness gates
    ├── 10_village_pilot_design_kpis.md       <-- Table 13.1, 13.2 & 13.3 5-Site pilot design & 6 KPIs
    ├── 11_cost_and_resource_requirements.md  <-- Table 14.1 Itemized budget (₹1.85–2.90 Cr) & in-kind inputs
    └── 12_literature_and_case_evidence.md    <-- Table 3.1 Literature synthesis, cases & stated research gap
```

---

## How to Use These Assets

### 1. View / Present the Generated Deck
Open [`CreditTech_MidSem_Presentation.pptx`](file:///d:/CreditTech/ppt-midsem/CreditTech_MidSem_Presentation.pptx) directly in Microsoft PowerPoint, Google Slides, or Keynote.
- **Layout:** 16:9 Widescreen.
- **Theme:** Academic Navy & Blue Palette (`#0A192F` Deep Navy, `#1E40AF` Royal Blue, `#F0F4F8` Ice Blue, `#FFFFFF` Crisp White).
- **Embedded Speaker Notes:** Every slide already contains complete, word-for-word spoken defense scripts!

### 2. Read the Academic Presentation Guidelines
Review [`INSTRUCTIONS_ACADEMIC_PPT.md`](file:///d:/CreditTech/ppt-midsem/INSTRUCTIONS_ACADEMIC_PPT.md) before stepping into the defense room. It covers:
- The 4 pillars of academic evaluation vs VC hype.
- Pacing rules (30–45s per architecture slide, 60–90s on pilot and literature).
- Verbal transition phrases connecting problem $\rightarrow$ architecture $\rightarrow$ pilot $\rightarrow$ literature.
- 6-point slide quality checklist.

### 3. Practice with the Verbatim Scripts
Read through [`SLIDE_DECK_CONTENT_AND_SCRIPTS.md`](file:///d:/CreditTech/ppt-midsem/SLIDE_DECK_CONTENT_AND_SCRIPTS.md). It gives you the exact narration to say slide-by-slide so you never pause or read bullet points off the screen.

### 4. Keep the Defense Cheatsheet Handy
Print or open [`COMMITTEE_DEFENSE_CHEATSHEET.md`](file:///d:/CreditTech/ppt-midsem/COMMITTEE_DEFENSE_CHEATSHEET.md). It contains:
- 6 Antidotes to tough professor questions (why alternative data, why WoE scorecard, covariate drought handling, spatial autocorrelation, DLG 5% cap, why monolith).
- Key formula reference (WoE, IV, PSI, DIR, Laplace smoothing).
- Live command line demonstration steps (`simulate_pilot.py`).

### 5. Re-generate or Customize Slides Anytime
If you modify slide text or parameters, run:
```powershell
.venv\Scripts\python ppt-midsem\generate_midsem_pptx.py
```
It will instantly update `CreditTech_MidSem_Presentation.pptx`.

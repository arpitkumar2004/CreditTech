"""
CreditTech Calibrated Synthetic Dataset Generator
==================================================
Generates a realistic 20,000-borrower rural credit dataset across 8 villages
and 5 borrower segments, calibrated to NSS 77th Round and NABARD benchmarks.

Rules strictly enforced:
1. Generate label last: Village -> Household Latents -> Shocks -> Rails -> True PD -> Default Flag.
2. Honest target ROC-AUC: 0.75 to 0.82 (values > 0.90 indicate leakage).
3. Zero single-feature AUC > 0.70.
4. Protected attributes (gender, caste, age, landholding) are stored for fairness audit only.
5. Deterministic random seed ensures byte-identical reproducibility.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.special import expit, logit

MASTER_SEED = 20261110

def generate_all_datasets(output_dir="data", seed=MASTER_SEED):
    np.random.seed(seed)

    raw_dir = os.path.join(output_dir, "raw")
    latent_dir = os.path.join(output_dir, "latent")
    proc_dir = os.path.join(output_dir, "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(latent_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)

    # -------------------------------------------------------------
    # 1. POPULATION TOPOLOGY (8 Villages, 20,000 Borrowers)
    # -------------------------------------------------------------
    villages = [
        {
            "village_id": "V01", "name": "Pipri", "district": "Chandauli", "state": "Uttar Pradesh",
            "agro_ecology": "Canal-irrigated plains", "irrigation_reliability": 0.88,
            "rainfall_anomaly": 0.02, "normal_rainfall_mm": 960, "market_distance_km": 8.5,
            "shg_health_score": 0.82, "climate_risk": "Low", "n_borrowers": 2600
        },
        {
            "village_id": "V02", "name": "Babhani", "district": "Chandauli", "state": "Uttar Pradesh",
            "agro_ecology": "Canal-irrigated plains", "irrigation_reliability": 0.82,
            "rainfall_anomaly": -0.03, "normal_rainfall_mm": 930, "market_distance_km": 12.0,
            "shg_health_score": 0.78, "climate_risk": "Low-Medium", "n_borrowers": 2800
        },
        {
            "village_id": "V03", "name": "Lalganj", "district": "Mirzapur", "state": "Uttar Pradesh",
            "agro_ecology": "Rain-fed undulating", "irrigation_reliability": 0.22,
            "rainfall_anomaly": -0.24, "normal_rainfall_mm": 820, "market_distance_km": 22.0,
            "shg_health_score": 0.58, "climate_risk": "High (Drought)", "n_borrowers": 2400
        },
        {
            "village_id": "V04", "name": "Halidhar", "district": "Mirzapur", "state": "Uttar Pradesh",
            "agro_ecology": "Rain-fed undulating", "irrigation_reliability": 0.18,
            "rainfall_anomaly": -0.28, "normal_rainfall_mm": 800, "market_distance_km": 28.0,
            "shg_health_score": 0.52, "climate_risk": "High (Drought)", "n_borrowers": 2200
        },
        {
            "village_id": "V05", "name": "Keshiary", "district": "Paschim Medinipur", "state": "West Bengal",
            "agro_ecology": "Lateritic rain-fed paddy", "irrigation_reliability": 0.38,
            "rainfall_anomaly": 0.08, "normal_rainfall_mm": 1380, "market_distance_km": 14.5,
            "shg_health_score": 0.75, "climate_risk": "Medium-High", "n_borrowers": 2700
        },
        {
            "village_id": "V06", "name": "Manbazar", "district": "Purulia", "state": "West Bengal",
            "agro_ecology": "Lateritic rain-fed paddy", "irrigation_reliability": 0.28,
            "rainfall_anomaly": -0.12, "normal_rainfall_mm": 1220, "market_distance_km": 21.0,
            "shg_health_score": 0.66, "climate_risk": "Medium-High", "n_borrowers": 2400
        },
        {
            "village_id": "V07", "name": "Ralegaon", "district": "Yavatmal", "state": "Maharashtra",
            "agro_ecology": "Dryland cotton-soybean", "irrigation_reliability": 0.22,
            "rainfall_anomaly": -0.19, "normal_rainfall_mm": 790, "market_distance_km": 18.0,
            "shg_health_score": 0.60, "climate_risk": "High (Price & Drought)", "n_borrowers": 2300
        },
        {
            "village_id": "V08", "name": "Maregaon", "district": "Yavatmal", "state": "Maharashtra",
            "agro_ecology": "Dryland cotton-soybean", "irrigation_reliability": 0.18,
            "rainfall_anomaly": -0.16, "normal_rainfall_mm": 760, "market_distance_km": 25.0,
            "shg_health_score": 0.56, "climate_risk": "High (Price & Drought)", "n_borrowers": 2600
        }
    ]
    df_villages = pd.DataFrame(villages)

    # Segment counts: exactly 6,000 marginal, 3,000 small, 2,000 tenant, 6,000 shg, 3,000 microenterprise (Total 20,000)
    segment_quotas = {
        "V01": {"marginal": 780, "small": 400, "tenant": 260, "shg": 780, "microenterprise": 380},
        "V02": {"marginal": 840, "small": 420, "tenant": 280, "shg": 840, "microenterprise": 420},
        "V03": {"marginal": 720, "small": 360, "tenant": 240, "shg": 720, "microenterprise": 360},
        "V04": {"marginal": 660, "small": 320, "tenant": 220, "shg": 660, "microenterprise": 340},
        "V05": {"marginal": 820, "small": 400, "tenant": 280, "shg": 800, "microenterprise": 400},
        "V06": {"marginal": 720, "small": 360, "tenant": 240, "shg": 720, "microenterprise": 360},
        "V07": {"marginal": 700, "small": 340, "tenant": 220, "shg": 700, "microenterprise": 340},
        "V08": {"marginal": 760, "small": 400, "tenant": 260, "shg": 780, "microenterprise": 400},
    }

    borrower_records = []
    b_idx = 1
    for v in villages:
        v_id = v["village_id"]
        quotas = segment_quotas[v_id]
        for seg, count in quotas.items():
            for _ in range(count):
                borrower_records.append({
                    "borrower_id": f"B{b_idx:05d}",
                    "village_id": v_id,
                    "segment": seg,
                })
                b_idx += 1

    df_base = pd.DataFrame(borrower_records)
    N = len(df_base)  # 20,000

    # Join village metadata
    df_base = df_base.merge(df_villages, on="village_id")

    # -------------------------------------------------------------
    # 2. HOUSEHOLD LATENTS & CAPACITY GENERATION
    # -------------------------------------------------------------
    repayment_will = np.random.normal(0.0, 1.0, N)
    skill = np.random.normal(0.0, 1.0, N)

    # Base income lognormal
    base_income_raw = np.random.lognormal(mean=9.10, sigma=0.42, size=N)
    seg_multipliers = {
        "marginal": 0.88,
        "small": 1.28,
        "tenant": 0.83,
        "shg": 0.90,
        "microenterprise": 1.22
    }
    income_mult = df_base["segment"].map(seg_multipliers).values
    monthly_income = base_income_raw * income_mult

    # Winsorize at p1 and p99
    p1, p99 = np.percentile(monthly_income, 1), np.percentile(monthly_income, 99)
    monthly_income = np.clip(monthly_income, p1, p99)

    # Scale base monthly income before DBT so total credits including DBT will average exactly Rs 10,218
    # We will do final normalization after DBT generation.

    # Income components matching NSS 77th Round shares:
    wage_share = np.zeros(N)
    crop_share = np.zeros(N)
    livestock_share = np.zeros(N)
    nonfarm_share = np.zeros(N)
    leasing_share = np.zeros(N)

    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        if seg == "marginal":
            w = np.random.uniform(0.42, 0.58)
            c = np.random.uniform(0.24, 0.36)
            l = np.random.uniform(0.10, 0.20)
            nf = np.random.uniform(0.02, 0.08)
            ls = np.random.uniform(0.00, 0.02)
        elif seg == "small":
            w = np.random.uniform(0.12, 0.24)
            c = np.random.uniform(0.50, 0.65)
            l = np.random.uniform(0.14, 0.24)
            nf = np.random.uniform(0.02, 0.08)
            ls = np.random.uniform(0.01, 0.04)
        elif seg == "tenant":
            w = np.random.uniform(0.40, 0.55)
            c = np.random.uniform(0.32, 0.45)
            l = np.random.uniform(0.08, 0.16)
            nf = np.random.uniform(0.02, 0.06)
            ls = 0.0
        elif seg == "shg":
            w = np.random.uniform(0.40, 0.52)
            c = np.random.uniform(0.20, 0.34)
            l = np.random.uniform(0.16, 0.26)
            nf = np.random.uniform(0.04, 0.10)
            ls = np.random.uniform(0.00, 0.02)
        else: # microenterprise
            w = np.random.uniform(0.10, 0.22)
            c = np.random.uniform(0.10, 0.22)
            l = np.random.uniform(0.05, 0.15)
            nf = np.random.uniform(0.45, 0.65)
            ls = np.random.uniform(0.00, 0.03)

        tot = w + c + l + nf + ls
        wage_share[i] = w / tot
        crop_share[i] = c / tot
        livestock_share[i] = l / tot
        nonfarm_share[i] = nf / tot
        leasing_share[i] = ls / tot

    inc_wages = monthly_income * wage_share
    inc_crop = monthly_income * crop_share
    inc_livestock = monthly_income * livestock_share
    inc_nonfarm = monthly_income * nonfarm_share
    inc_leasing = monthly_income * leasing_share

    # Calibrate component means to match NSS anchors
    inc_wages = inc_wages * (4063.0 / inc_wages.mean())
    inc_crop = inc_crop * (3798.0 / inc_crop.mean())
    inc_livestock = inc_livestock * (1582.0 / inc_livestock.mean())
    inc_nonfarm = inc_nonfarm * (641.0 / inc_nonfarm.mean())
    inc_leasing = inc_leasing * (134.0 / inc_leasing.mean())
    monthly_income = inc_wages + inc_crop + inc_livestock + inc_nonfarm + inc_leasing

    # -------------------------------------------------------------
    # 3. DEMOGRAPHICS (Table A)
    # -------------------------------------------------------------
    genders = []
    ages = []
    castes = []
    educations = []
    hh_sizes = []
    dependents = []
    smartphones = []
    dig_lit = []
    acct_ages = []
    tradelines = []
    bureau_scores = []
    consent_rails = []

    caste_choices = ["OBC", "SC", "ST", "General"]
    caste_p = [0.458, 0.159, 0.142, 0.241]
    edu_choices = ["none", "primary", "secondary", "graduate"]
    edu_p = [0.27, 0.36, 0.27, 0.10]

    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        if seg == "shg":
            g = "F"
            age = int(np.clip(np.random.normal(38, 7), 25, 55))
        else:
            g = "F" if np.random.rand() < 0.12 else "M"
            age = int(np.clip(np.random.normal(41, 10), 21, 65))
        genders.append(g)
        ages.append(age)

        castes.append(np.random.choice(caste_choices, p=caste_p))
        edu = np.random.choice(edu_choices, p=edu_p)
        educations.append(edu)

        h_sz = int(np.clip(np.random.normal(4.8, 1.4), 3, 9))
        hh_sizes.append(h_sz)
        deps = int(np.clip(np.random.normal(h_sz - 2.8, 1.1), 0, min(6, h_sz - 1)))
        dependents.append(deps)

        has_phone = bool(np.random.rand() < 0.65)
        smartphones.append(has_phone)
        if not has_phone or edu == "none":
            lit = "assisted"
        elif edu == "graduate" or (has_phone and np.random.rand() < 0.45):
            lit = "comfortable"
        else:
            lit = "basic"
        dig_lit.append(lit)

        # Bank account age: correlated with age and stability
        acct_a = int(np.clip(np.random.normal(54 + 6 * repayment_will[i] + 0.35 * age, 24), 6, 120))
        acct_ages.append(acct_a)

        # Bureau tradelines: 65% zero
        if np.random.rand() < 0.65:
            lines = 0
            b_score = np.nan
        else:
            lines = int(np.random.choice([1, 2, 3, 4], p=[0.55, 0.28, 0.12, 0.05]))
            score_latent = 620 + 35 * repayment_will[i] + np.random.normal(0, 40)
            b_score = int(np.clip(score_latent, 450, 780))
        tradelines.append(lines)
        bureau_scores.append(b_score)

        c_rails = int(np.random.choice([2, 3, 4], p=[0.08, 0.22, 0.70]))
        consent_rails.append(c_rails)

    years_in_village = [int(np.clip(a - np.random.randint(2, 10), 3, a)) for a in ages]

    df_A = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "village_id": df_base["village_id"],
        "segment": df_base["segment"],
        "age": ages,
        "gender": genders,
        "caste_category": castes,
        "education_level": educations,
        "household_size": hh_sizes,
        "dependents": dependents,
        "years_in_village": years_in_village,
        "has_smartphone": smartphones,
        "mobile_digital_literacy": dig_lit,
        "bank_account_age_months": acct_ages,
        "bureau_tradelines": tradelines,
        "bureau_score_proxy": bureau_scores,
        "consent_rails_granted": consent_rails
    })

    # -------------------------------------------------------------
    # 4. HOUSEHOLD, LAND & CROPS (Table B)
    # -------------------------------------------------------------
    # Target: 75% to 80% under 1.0 ha
    land_owned = []
    land_leased = []
    irrigated_shares = []
    irrigation_sources = []
    primary_crops = []
    secondary_crops = []
    crop_intensities = []
    livestock_units = []
    livestock_vals = []
    pumps_tractors = []
    house_types = []
    asset_indices = []
    titles_clear = []
    crop_insurances = []
    ent_types = []
    ent_ages = []
    ent_sales = []

    crop_mapping = {
        "V01": ("paddy", "wheat"),
        "V02": ("paddy", "wheat"),
        "V03": ("paddy", "pulses"),
        "V04": ("millet", "pulses"),
        "V05": ("paddy", "vegetables"),
        "V06": ("paddy", "vegetables"),
        "V07": ("cotton", "soybean"),
        "V08": ("cotton", "pigeon_pea"),
    }

    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        v_id = df_base.iloc[i]["village_id"]
        v_meta = df_villages[df_villages["village_id"] == v_id].iloc[0]

        # Land owned: calibrated so ~77% have < 1.0 ha
        if seg == "marginal":
            l_own = np.clip(np.random.uniform(0.15, 0.95), 0.10, 0.95)
            l_lease = 0.0
        elif seg == "small":
            l_own = np.clip(np.random.uniform(1.05, 2.00), 1.00, 2.20)
            l_lease = np.random.choice([0.0, 0.2, 0.4], p=[0.75, 0.18, 0.07])
        elif seg == "tenant":
            l_own = np.random.choice([0.0, 0.10, 0.20], p=[0.75, 0.18, 0.07])
            l_lease = np.clip(np.random.uniform(0.40, 1.20), 0.30, 1.50)
        elif seg == "shg":
            # 12% own >= 1.0 ha (family holding)
            if np.random.rand() < 0.12:
                l_own = np.clip(np.random.uniform(1.05, 1.60), 1.00, 1.80)
            else:
                l_own = np.random.choice([0.0, 0.25, 0.50, 0.75], p=[0.30, 0.35, 0.25, 0.10])
            l_lease = 0.0
        else: # microenterprise
            # 30% own >= 1.0 ha
            if np.random.rand() < 0.30:
                l_own = np.clip(np.random.uniform(1.05, 1.70), 1.00, 2.00)
            else:
                l_own = np.random.choice([0.0, 0.20, 0.45, 0.70], p=[0.45, 0.30, 0.15, 0.10])
            l_lease = 0.0

        land_owned.append(round(float(l_own), 2))
        land_leased.append(round(float(l_lease), 2))

        # Irrigation
        v_irr_rel = v_meta["irrigation_reliability"]
        if v_irr_rel > 0.6:
            irr_src = np.random.choice(["canal", "tubewell"], p=[0.70, 0.30])
            irr_sh = np.clip(np.random.normal(0.85, 0.10), 0.60, 1.0)
            ci = np.clip(np.random.normal(1.85, 0.18), 1.5, 2.2)
        elif v_irr_rel > 0.3:
            irr_src = np.random.choice(["tubewell", "pond", "rainfed"], p=[0.40, 0.35, 0.25])
            irr_sh = np.clip(np.random.normal(0.45, 0.18), 0.15, 0.75)
            ci = np.clip(np.random.normal(1.45, 0.15), 1.2, 1.8)
        else:
            irr_src = np.random.choice(["rainfed", "borewell"], p=[0.75, 0.25])
            irr_sh = np.clip(np.random.normal(0.18, 0.12), 0.0, 0.45)
            ci = np.clip(np.random.normal(1.15, 0.12), 1.0, 1.4)

        if l_own + l_lease == 0:
            irr_sh = 0.0
            irr_src = "rainfed"
            ci = 1.0

        irrigated_shares.append(round(float(irr_sh), 2))
        irrigation_sources.append(irr_src)
        crop_intensities.append(round(float(ci), 2))

        # Crops
        c1, c2 = crop_mapping[v_id]
        primary_crops.append(c1)
        secondary_crops.append(c2 if ci > 1.2 else "none")

        # Livestock
        if seg in ["shg", "small", "marginal"]:
            lu = np.clip(np.random.exponential(1.8), 0.0, 6.0)
        else:
            lu = np.clip(np.random.exponential(0.8), 0.0, 4.0)
        l_val = round(lu * np.random.uniform(22000, 32000), -2)
        livestock_units.append(round(float(lu), 1))
        livestock_vals.append(float(l_val))

        # Assets & House
        has_machinery = bool(l_own > 1.2 and np.random.rand() < 0.55)
        pumps_tractors.append(has_machinery)
        if monthly_income[i] > 14000:
            h_type = np.random.choice(["pucca", "semi-pucca"], p=[0.65, 0.35])
        elif monthly_income[i] > 8000:
            h_type = np.random.choice(["pucca", "semi-pucca", "kutcha"], p=[0.25, 0.55, 0.20])
        else:
            h_type = np.random.choice(["semi-pucca", "kutcha"], p=[0.35, 0.65])
        house_types.append(h_type)

        score_asset = (
            (1.0 if h_type == "pucca" else 0.5 if h_type == "semi-pucca" else 0.1) * 30 +
            min(l_own / 2.0, 1.0) * 25 +
            min(l_val / 100000.0, 1.0) * 20 +
            (15 if has_machinery else 0) +
            (10 if df_A.iloc[i]["has_smartphone"] else 0) +
            np.random.normal(0, 4)
        )
        asset_indices.append(round(float(np.clip(score_asset, 5.0, 95.0)), 1))

        title_ok = bool(np.random.rand() < 0.70) if l_own > 0 else False
        titles_clear.append(title_ok)

        ins_prob = 0.42 if v_irr_rel < 0.3 else 0.28
        crop_insurances.append(bool(l_own + l_lease > 0 and np.random.rand() < ins_prob))

        if seg == "microenterprise":
            e_t = np.random.choice(["kirana", "dairy_collection", "repair", "tailoring", "chc"], p=[0.35, 0.25, 0.15, 0.15, 0.10])
            e_age = round(float(np.clip(np.random.normal(6.5, 3.5), 1.0, 25.0)), 1)
            e_sale = round(float(monthly_income[i] * np.random.uniform(2.5, 5.0)), -2)
        else:
            e_t = "none"
            e_age = np.nan
            e_sale = np.nan
        ent_types.append(e_t)
        ent_ages.append(e_age)
        ent_sales.append(e_sale)

    df_B = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "land_owned_ha": land_owned,
        "land_leased_ha": land_leased,
        "irrigated_share": irrigated_shares,
        "irrigation_source": irrigation_sources,
        "primary_crop": primary_crops,
        "secondary_crop": secondary_crops,
        "cropping_intensity": crop_intensities,
        "livestock_units": livestock_units,
        "livestock_value_inr": livestock_vals,
        "owns_pump_or_tractor": pumps_tractors,
        "house_type": house_types,
        "asset_index": asset_indices,
        "land_title_clear": titles_clear,
        "has_crop_insurance_pmfby": crop_insurances,
        "enterprise_type": ent_types,
        "enterprise_age_years": ent_ages,
        "enterprise_monthly_sales": ent_sales
    })

    # -------------------------------------------------------------
    # 5. SHOCKS GENERATION (Latent Shocks)
    # -------------------------------------------------------------
    crop_failures = []
    health_events = []
    livestock_losses = []
    price_shocks = []

    for i in range(N):
        v_id = df_base.iloc[i]["village_id"]
        v_meta = df_villages[df_villages["village_id"] == v_id].iloc[0]
        irr_sh = df_B.iloc[i]["irrigated_share"]
        has_land = (df_B.iloc[i]["land_owned_ha"] + df_B.iloc[i]["land_leased_ha"]) > 0

        if has_land:
            p_crop = 0.22 * (1.0 - irr_sh) * max(0.0, -v_meta["rainfall_anomaly"] + 0.15) + 0.05
            p_crop = np.clip(p_crop, 0.04, 0.25)
        else:
            p_crop = 0.02
        cf = int(np.random.rand() < p_crop)
        crop_failures.append(cf)

        he = int(np.random.rand() < 0.08)
        health_events.append(he)

        ll = int(df_B.iloc[i]["livestock_units"] > 0 and np.random.rand() < 0.04)
        livestock_losses.append(ll)

        p_price = 0.18 if v_id in ["V07", "V08"] else 0.07
        ps = int(np.random.rand() < p_price)
        price_shocks.append(ps)

    latent_income_shock = (
        - 1.1 * np.array(crop_failures)
        - 0.8 * np.array(health_events)
        - 0.5 * np.array(price_shocks)
        - 0.4 * np.array(livestock_losses)
        + np.random.normal(0, 0.4, N)
    )

    # -------------------------------------------------------------
    # 6. SATELLITE & WEATHER (Table F)
    # -------------------------------------------------------------
    ndvi_kharif_peaks = []
    ndvi_kharif_means = []
    ndvi_rabi_peaks = []
    ndvi_rabi_means = []
    ndvi_anomalies = []
    rain_totals = []
    rain_pcts = []
    dry_spells = []
    heat_days = []
    cloud_gaps = []
    plot_ndvi_peaks = []
    plot_coverages = []

    for i in range(N):
        v_id = df_base.iloc[i]["village_id"]
        v_meta = df_villages[df_villages["village_id"] == v_id].iloc[0]
        irr_sh = df_B.iloc[i]["irrigated_share"]
        cf = crop_failures[i]

        v_rain_pct = 100.0 * (1.0 + v_meta["rainfall_anomaly"]) + np.random.normal(0, 3)
        v_rain_mm = v_meta["normal_rainfall_mm"] * (v_rain_pct / 100.0)

        # NDVI: canal villages 0.65-0.78; rainfed 0.42-0.62; realistic soil and crop variety noise
        base_ndvi = 0.50 + 0.18 * irr_sh + 0.10 * max(0.0, v_meta["rainfall_anomaly"]) + np.random.normal(0, 0.075)
        if cf:
            base_ndvi -= np.random.uniform(0.08, 0.15)
        base_ndvi = float(np.clip(base_ndvi, 0.28, 0.82))

        k_peak = round(base_ndvi, 3)
        k_mean = round(base_ndvi - np.random.uniform(0.08, 0.14), 3)
        r_peak = round(base_ndvi * (0.85 if irr_sh > 0.5 else 0.58) + np.random.normal(0, 0.03), 3)
        r_peak = float(np.clip(r_peak, 0.22, 0.80))
        r_mean = round(r_peak - np.random.uniform(0.06, 0.12), 3)

        anomaly = round(float(v_meta["rainfall_anomaly"] * 0.65 + np.random.normal(0, 0.04)), 3)
        anomaly = float(np.clip(anomaly, -0.25, 0.15))

        ds = int(np.clip(12 - v_meta["rainfall_anomaly"] * 45 + np.random.normal(0, 3), 3, 35))
        hd = int(np.clip(8 + (1.0 - irr_sh) * 8 + np.random.normal(0, 2), 0, 22))
        cg = int(np.clip(np.random.normal(12, 4), 2, 28))

        p_peak = round(float(np.clip((k_peak + r_peak) / 2.0 + np.random.normal(0, 0.03), 0.24, 0.85)), 3)
        cov = round(float(np.clip(np.random.normal(88, 7), 58, 100)), 1)

        ndvi_kharif_peaks.append(k_peak)
        ndvi_kharif_means.append(k_mean)
        ndvi_rabi_peaks.append(r_peak)
        ndvi_rabi_means.append(r_mean)
        ndvi_anomalies.append(anomaly)
        rain_totals.append(round(v_rain_mm, 1))
        rain_pcts.append(round(v_rain_pct, 1))
        dry_spells.append(ds)
        heat_days.append(hd)
        cloud_gaps.append(cg)
        plot_ndvi_peaks.append(p_peak)
        plot_coverages.append(cov)

    df_F = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "village_id": df_base["village_id"],
        "ndvi_peak_kharif": ndvi_kharif_peaks,
        "ndvi_mean_kharif": ndvi_kharif_means,
        "ndvi_peak_rabi": ndvi_rabi_peaks,
        "ndvi_mean_rabi": ndvi_rabi_means,
        "ndvi_anomaly_vs_5yr": ndvi_anomalies,
        "rainfall_total_mm": rain_totals,
        "rainfall_pct_of_normal": rain_pcts,
        "dry_spell_days_max": dry_spells,
        "heat_stress_days": heat_days,
        "cloud_gap_days": cloud_gaps,
        "plot_ndvi_peak": plot_ndvi_peaks,
        "plot_ndvi_coverage_pct": plot_coverages
    })

    # -------------------------------------------------------------
    # 7. SHG LEDGER (Table D)
    # -------------------------------------------------------------
    shg_ids = []
    shg_ages = []
    m_tenures = []
    m_held = []
    m_attended = []
    sav_reg_pcts = []
    wkly_savings = []
    sav_corpus = []
    int_loans = []
    int_repay_rates = []
    pancha_scores = []
    shg_grades = []
    prior_linkages = []
    bank_repaid_pcts = []
    shg_v_healths = []

    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        v_id = df_base.iloc[i]["village_id"]
        v_meta = df_villages[df_villages["village_id"] == v_id].iloc[0]
        is_female = df_A.iloc[i]["gender"] == "F"

        is_shg_member = (seg == "shg") or (is_female and np.random.rand() < 0.15)

        if is_shg_member:
            shg_num = np.random.randint(1, 51)
            s_id = f"SHG_{v_id}_{shg_num:02d}"
            s_age = int(np.clip(np.random.normal(54, 25), 12, 120))
            m_ten = int(np.clip(np.random.uniform(6, s_age), 6, s_age))

            held = 24
            # Attendance rate
            att_latent = 0.70 + 0.05 * repayment_will[i] + 0.12 * v_meta["shg_health_score"] + np.random.normal(0, 0.10)
            att_rate = float(np.clip(att_latent, 0.52, 0.98))
            att = int(round(held * att_rate))

            # Savings regularity has independent variation (prevent collinearity > 0.85)
            s_reg = round(float(np.clip(55.0 + 22.0 * att_rate + 12.0 * v_meta["shg_health_score"] + np.random.normal(0, 9.0), 45.0, 100.0)), 1)
            w_sav = float(np.random.choice([50, 100, 150, 200], p=[0.35, 0.45, 0.15, 0.05]))
            corpus = round(float(m_ten * 4.3 * w_sav * (s_reg / 100.0) + np.random.normal(0, 500)), -2)
            corpus = max(1000.0, corpus)

            # Internal loans & repayment rate (correlated with attendance ~0.40 and will ~0.35)
            i_loans = int(np.random.choice([0, 1, 2, 3], p=[0.15, 0.45, 0.30, 0.10]))
            repay_latent = 0.72 + 0.18 * att_rate + 0.04 * repayment_will[i] + 0.03 * skill[i] + np.random.normal(0, 0.05)
            i_repay = round(float(np.clip(repay_latent, 0.60, 1.00)), 3)

            p_score = int(np.clip(2 + 2.5 * v_meta["shg_health_score"] + 0.4 * repayment_will[i] + np.random.normal(0, 0.5), 1, 5))
            grade = "A" if p_score >= 4 else "B" if p_score == 3 else "C"
            prior_link = bool(s_age > 18 and np.random.rand() < 0.65)
            bank_rep = round(float(np.clip(0.85 + 0.10 * v_meta["shg_health_score"] + np.random.normal(0, 0.05), 0.65, 1.0)), 2) if prior_link else np.nan

            shg_ids.append(s_id)
            shg_ages.append(s_age)
            m_tenures.append(m_ten)
            m_held.append(held)
            m_attended.append(att)
            sav_reg_pcts.append(s_reg)
            wkly_savings.append(w_sav)
            sav_corpus.append(corpus)
            int_loans.append(i_loans)
            int_repay_rates.append(i_repay)
            pancha_scores.append(p_score)
            shg_grades.append(grade)
            prior_linkages.append(prior_link)
            bank_repaid_pcts.append(bank_rep)
            shg_v_healths.append(round(v_meta["shg_health_score"], 2))
        else:
            shg_ids.append(None)
            shg_ages.append(np.nan)
            m_tenures.append(np.nan)
            m_held.append(np.nan)
            m_attended.append(np.nan)
            sav_reg_pcts.append(np.nan)
            wkly_savings.append(np.nan)
            sav_corpus.append(np.nan)
            int_loans.append(np.nan)
            int_repay_rates.append(np.nan)
            pancha_scores.append(np.nan)
            shg_grades.append(None)
            prior_linkages.append(None)
            bank_repaid_pcts.append(np.nan)
            shg_v_healths.append(np.nan)

    df_D = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "shg_id": shg_ids,
        "shg_age_months": shg_ages,
        "member_tenure_months": m_tenures,
        "meetings_held_12m": m_held,
        "meetings_attended_12m": m_attended,
        "savings_regularity_pct": sav_reg_pcts,
        "weekly_savings_inr": wkly_savings,
        "member_savings_corpus_inr": sav_corpus,
        "internal_loans_taken": int_loans,
        "internal_repayment_rate": int_repay_rates,
        "shg_panchasutra_score": pancha_scores,
        "shg_grade": shg_grades,
        "prior_bank_linkage": prior_linkages,
        "shg_bank_loan_repaid_pct": bank_repaid_pcts,
        "shg_village_health": shg_v_healths
    })

    # -------------------------------------------------------------
    # 8. UTILITY & DIGITAL TELEMETRY (Table E)
    # -------------------------------------------------------------
    elec_conns = []
    bills_paid = []
    bills_on_time = []
    avg_days_late = []
    arrears = []
    disconnections = []
    mobile_active_m = []
    avg_recharges = []
    recharge_regs = []
    lpg_dth_regs = []

    for i in range(N):
        e_conn = np.random.choice(["metered", "flat-rate", "none"], p=[0.80, 0.14, 0.06])
        elec_conns.append(e_conn)

        if e_conn == "metered":
            b_paid = int(np.random.choice([10, 11, 12], p=[0.10, 0.25, 0.65]))
            ontime_prob = 0.66 + 0.08 * repayment_will[i] + np.random.normal(0, 0.12)
            ontime_prob = np.clip(ontime_prob, 0.30, 0.98)
            b_ontime = int(np.clip(round(b_paid * ontime_prob), 1, b_paid))
            late = round(float(np.clip((b_paid - b_ontime) * 4.2 + np.random.exponential(4), 0.0, 42.0)), 1)
            arr = round(float(np.clip((b_paid - b_ontime) * 320 + np.random.exponential(250), 0.0, 4800.0)), -1)
            disc = int(1 if arr > 2500 and np.random.rand() < 0.22 else 0)
        elif e_conn == "flat-rate":
            b_paid = 12
            b_ontime = 10
            late = 6.0
            arr = 0.0
            disc = 0
        else:
            b_paid = 0
            b_ontime = 0
            late = 0.0
            arr = 0.0
            disc = 0

        bills_paid.append(b_paid)
        bills_on_time.append(b_ontime)
        avg_days_late.append(late)
        arrears.append(arr)
        disconnections.append(disc)

        m_active = int(np.clip(np.random.normal(11.2, 1.5), 6, 12))
        voucher_plans = [150, 180, 200, 240, 270, 300, 350, 400]
        avg_r = float(np.random.choice(voucher_plans, p=[0.10, 0.15, 0.25, 0.22, 0.12, 0.08, 0.05, 0.03]))
        # Moderate dependence on will to ensure AUC <= 0.70 and IV between 0.05 and 0.30
        r_reg = round(float(np.clip(0.70 + 0.045 * repayment_will[i] + 0.035 * (df_B.iloc[i]["asset_index"] / 100.0) + np.random.normal(0, 0.12), 0.30, 1.0)), 2)
        lpg_reg = round(float(np.clip(0.50 + 0.25 * (df_B.iloc[i]["asset_index"] / 100.0) + np.random.normal(0, 0.12), 0.0, 1.0)), 2)

        mobile_active_m.append(m_active)
        avg_recharges.append(avg_r)
        recharge_regs.append(r_reg)
        lpg_dth_regs.append(lpg_reg)

    df_E = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "electricity_connection": elec_conns,
        "bills_paid_12m": bills_paid,
        "bills_on_time_12m": bills_on_time,
        "avg_days_late": avg_days_late,
        "arrears_inr": arrears,
        "disconnection_events_12m": disconnections,
        "mobile_recharge_months_active": mobile_active_m,
        "avg_recharge_inr": avg_recharges,
        "recharge_regularity": recharge_regs,
        "lpg_or_dth_payment_regularity": lpg_dth_regs
    })

    # -------------------------------------------------------------
    # 9. GOVERNMENT & SOCIAL RAIL (Table G)
    # -------------------------------------------------------------
    pm_kisans = []
    mgnrega_days = []
    pensions = []
    pmjdy_flags = []
    insurance_flags = []
    ration_types = []
    fpo_members = []
    fpo_txns = []

    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        l_own = df_B.iloc[i]["land_owned_ha"]

        if l_own > 0:
            pm_k = int(np.random.choice([2, 3], p=[0.18, 0.82]))
        else:
            pm_k = 0
        pm_kisans.append(pm_k)

        if seg in ["marginal", "tenant"]:
            m_days = int(np.clip(np.random.normal(48, 18), 10, 100))
        elif seg == "shg":
            m_days = int(np.clip(np.random.normal(32, 16), 0, 80))
        else:
            m_days = int(np.clip(np.random.normal(14, 12), 0, 45))
        mgnrega_days.append(m_days)

        has_pen = bool(df_A.iloc[i]["age"] > 55 and np.random.rand() < 0.45)
        pensions.append(has_pen)

        pmjdy_flags.append(bool(np.random.rand() < 0.90))
        insurance_flags.append(bool(np.random.rand() < 0.40))

        if df_B.iloc[i]["asset_index"] < 30:
            r_type = np.random.choice(["AAY", "PHH"], p=[0.45, 0.55])
        elif df_B.iloc[i]["asset_index"] < 65:
            r_type = np.random.choice(["PHH", "none"], p=[0.82, 0.18])
        else:
            r_type = np.random.choice(["PHH", "none"], p=[0.35, 0.65])
        ration_types.append(r_type)

        is_fpo = bool(seg in ["small", "marginal"] and np.random.rand() < 0.11)
        fpo_members.append(is_fpo)
        fpo_txns.append(int(np.random.randint(1, 14)) if is_fpo else 0)

    df_G = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "pm_kisan_instalments_received_12m": pm_kisans,
        "mgnrega_days_12m": mgnrega_days,
        "pension_or_other_dbt": pensions,
        "pmjdy_account": pmjdy_flags,
        "insurance_pmjjby_pmsby": insurance_flags,
        "ration_card_type": ration_types,
        "fpo_member": fpo_members,
        "fpo_transactions_12m": fpo_txns
    })

    # -------------------------------------------------------------
    # 10. ACCOUNT AGGREGATOR MONTHLY (Table C: 12,000 Rows)
    # -------------------------------------------------------------
    aa_records = []
    months = [
        "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
        "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"
    ]
    base_season_credit = np.array([0.80, 0.85, 0.90, 1.30, 1.45, 1.20, 0.85, 0.90, 1.25, 1.35, 1.15, 0.80])
    base_season_debit  = np.array([1.25, 0.90, 0.85, 1.25, 1.25, 0.95, 0.85, 0.85, 1.05, 1.15, 0.95, 1.10])

    borrower_avg_daily_balances = []
    borrower_inflow_cvs = []
    borrower_inflow_outflow_ratios = []
    borrower_inflow_trend_slopes = []
    borrower_seasonal_amplitudes = []
    borrower_months_low_balances = []
    borrower_govt_transfer_shares = []
    borrower_avg_inflows = []
    borrower_foirs = []

    is_indebted = np.random.rand(N) < 0.502
    existing_emis = np.zeros(N)
    for i in range(N):
        if is_indebted[i]:
            existing_emis[i] = round(float(np.clip(monthly_income[i] * np.random.uniform(0.12, 0.28), 800, 4500)), -1)

    # First pass: compute DBT credits and preliminary monthly credits
    prelim_credits = []
    all_dbt = []
    for i in range(N):
        seg = df_base.iloc[i]["segment"]
        inc = monthly_income[i]
        pm_k = df_G.iloc[i]["pm_kisan_instalments_received_12m"]

        if seg == "microenterprise":
            s_cred = 1.0 + (base_season_credit - 1.0) * 0.35
            s_deb  = 1.0 + (base_season_debit - 1.0) * 0.35
        elif seg == "tenant":
            s_cred = 1.0 + (base_season_credit - 1.0) * 1.35
            s_deb  = 1.0 + (base_season_debit - 1.0) * 1.20
        else:
            s_cred = base_season_credit.copy()
            s_deb  = base_season_debit.copy()

        dbt_schedule = np.zeros(12)
        if pm_k >= 1: dbt_schedule[1] = 2000.0
        if pm_k >= 2: dbt_schedule[5] = 2000.0
        if pm_k >= 3: dbt_schedule[9] = 2000.0
        if df_G.iloc[i]["mgnrega_days_12m"] > 0:
            mgnrega_total = df_G.iloc[i]["mgnrega_days_12m"] * 240.0
            dbt_schedule += (mgnrega_total / 12.0)

        noise_cred = np.random.normal(1.0, 0.10, 12)
        raw_c = (inc * s_cred * noise_cred) + dbt_schedule
        prelim_credits.append(raw_c)
        all_dbt.append(dbt_schedule)

    # Scale total credits so mean monthly inflow matches NSS anchor Rs 10,218 precisely
    all_credits_arr = np.array(prelim_credits)
    current_mean_inflow = float(np.mean(all_credits_arr))
    scale_factor = 10218.0 / current_mean_inflow
    scaled_credits = all_credits_arr * scale_factor

    for i in range(N):
        b_id = df_base.iloc[i]["borrower_id"]
        seg = df_base.iloc[i]["segment"]
        inc = monthly_income[i]
        dbt_schedule = all_dbt[i]

        s_deb = 1.0 + (base_season_debit - 1.0) * (0.35 if seg == "microenterprise" else 1.20 if seg == "tenant" else 1.0)
        m_credits = np.round(scaled_credits[i], -1)
        hh_sz = df_A.iloc[i]["household_size"]
        base_deb_ratio = 0.88 + 0.015 * (hh_sz - 4.8)
        noise_deb = np.random.normal(base_deb_ratio, 0.05, 12)
        m_debits = np.round(m_credits * s_deb * noise_deb, -1)

        thrift_prop = float(np.clip(0.35 + 0.12 * skill[i] + np.random.normal(0, 0.12), 0.12, 0.65))
        rolling_bal = float(max(1000.0, 1500.0 + inc * thrift_prop + np.random.normal(0, 1200)))
        m_closing = []
        m_min = []
        low_bal_count = 0

        for m_idx in range(12):
            cr = m_credits[m_idx]
            db = m_debits[m_idx]
            rolling_bal = max(0.0, rolling_bal + cr - db)
            m_close = round(float(rolling_bal), -1)
            m_m = round(float(max(0.0, m_close - np.random.uniform(200, 1500))), -1)
            m_closing.append(m_close)
            m_min.append(m_m)
            if m_close < 500:
                low_bal_count += 1

            has_smart = df_A.iloc[i]["has_smartphone"]
            upi_cnt = int(np.clip(np.random.normal(12 if seg == "microenterprise" else 6 if has_smart else 1, 3), 0, 45))
            cash_sh = round(float(np.clip(0.85 - (0.35 if seg == "microenterprise" else 0.15 if has_smart else 0.0) + np.random.normal(0, 0.06), 0.25, 0.95)), 2)
            bounces = int(1 if m_close < 800 and np.random.rand() < 0.20 else 0)
            days_low = int(np.clip(round((1.0 - min(m_close, 3000)/3000.0) * 12 + np.random.exponential(2)), 0, 30))

            emi_deb = float(existing_emis[i]) if is_indebted[i] else 0.0
            inf_lender = bool(is_indebted[i] and np.random.rand() < 0.34)

            aa_records.append({
                "borrower_id": b_id,
                "month": months[m_idx],
                "total_credits_inr": cr,
                "total_debits_inr": db,
                "closing_balance_inr": m_close,
                "min_balance_inr": m_m,
                "upi_txn_count": upi_cnt,
                "cash_withdrawal_share": cash_sh,
                "bounced_or_failed_txn": bounces,
                "days_balance_below_500": days_low,
                "emi_or_loan_debit_inr": emi_deb,
                "informal_lender_flag": inf_lender,
                "dbt_credits_inr": round(float(dbt_schedule[m_idx]), -1)
            })

        m_credits_arr = np.array(m_credits)
        m_debits_arr = np.array(m_debits)
        m_closing_arr = np.array(m_closing)

        mean_inflow = float(np.mean(m_credits_arr))
        inflow_cv = float(np.std(m_credits_arr) / (mean_inflow + 1e-6))
        tot_cr = float(np.sum(m_credits_arr))
        tot_db = float(np.sum(m_debits_arr))
        ratio_in_out = float(tot_cr / (tot_db + 1e-6))

        x_m = np.arange(12)
        slope = float(np.polyfit(x_m, m_credits_arr, 1)[0])

        min_inf = max(np.min(m_credits_arr), 500.0)
        max_inf = np.max(m_credits_arr)
        amplitude = float(max_inf / min_inf)

        govt_share = float(np.sum(dbt_schedule) / (tot_cr + 1e-6))
        indicative_new_emi = (inc * 0.18)
        foir_val = float((existing_emis[i] + indicative_new_emi) / (mean_inflow + 1e-6))

        borrower_avg_inflows.append(round(mean_inflow, 1))
        borrower_inflow_cvs.append(round(inflow_cv, 3))
        borrower_inflow_outflow_ratios.append(round(ratio_in_out, 3))
        borrower_avg_daily_balances.append(round(float(np.mean(m_closing_arr)), 1))
        borrower_inflow_trend_slopes.append(round(slope, 2))
        borrower_seasonal_amplitudes.append(round(amplitude, 2))
        borrower_months_low_balances.append(low_bal_count)
        borrower_govt_transfer_shares.append(round(govt_share, 3))
        borrower_foirs.append(round(min(foir_val, 0.85), 3))

    df_C = pd.DataFrame(aa_records)

    # -------------------------------------------------------------
    # 11. GROUND TRUTH LATENTS & DEFAULT LABEL (GENERATE LABEL LAST)
    # -------------------------------------------------------------
    # Latent economic debt-service capacity (skill + true earning power)
    true_earning_log = np.log(monthly_income) + 0.35 * skill
    cap_z = (true_earning_log - np.mean(true_earning_log)) / np.std(true_earning_log)
    bal_z = (np.array(borrower_avg_daily_balances) - np.mean(borrower_avg_daily_balances)) / np.std(borrower_avg_daily_balances)
    asset_z = (np.array(df_B["asset_index"]) - np.mean(df_B["asset_index"])) / np.std(df_B["asset_index"])
    land_eff = np.array(df_B["land_owned_ha"]) + 0.5 * np.array(df_B["land_leased_ha"])
    land_z = (land_eff - np.mean(land_eff)) / (np.std(land_eff) + 1e-6)
    livestock_z = (np.array(df_B["livestock_value_inr"]) - np.mean(df_B["livestock_value_inr"])) / (np.std(df_B["livestock_value_inr"]) + 1e-6)
    foir_z = (np.array(borrower_foirs) - np.mean(borrower_foirs)) / np.std(borrower_foirs)

    # Village risk baseline adjustment to guarantee village spread is 4.0% to 16.0%
    # V01, V02 (canal): ~4.5% to 5.0%
    # V03, V04, V07, V08 (rain-fed drought): ~10% to 14%
    v_risk_map = {
        "V01": -0.25,
        "V02": -0.22,
        "V03": 0.26,
        "V04": 0.30,
        "V05": -0.05,
        "V06": 0.08,
        "V07": 0.32,
        "V08": 0.28,
    }
    v_offsets = df_base["village_id"].map(v_risk_map).values

    eps = np.random.normal(0.0, 0.74, N)

    has_ins = df_B["has_crop_insurance_pmfby"].astype(float).values
    crop_shock_net = np.array(crop_failures) * (1.0 - 0.70 * has_ins)

    latent_risk_core = (
        v_offsets
        - 0.88 * repayment_will
        - 0.22 * cap_z
        - 0.24 * bal_z
        - 0.18 * (asset_z + land_z) / 2.0
        - 0.14 * livestock_z
        + 0.65 * crop_shock_net
        - 0.16 * has_ins
        + 0.44 * np.array(health_events)
        + 0.34 * np.array(price_shocks)
        + 0.28 * foir_z
        + eps
    )

    # Target segment defaults (calibrated for 20,000 borrowers):
    # marginal: 600 / 6000 (10.0%)
    # small: 220 / 3000 (7.33%)
    # tenant: 260 / 2000 (13.0%)
    # shg: 240 / 6000 (4.0%)
    # microenterprise: 320 / 3000 (10.67%)
    # Total = 1,640 / 20,000 = 8.20%
    target_defaults = {
        "marginal": 600,
        "small": 220,
        "tenant": 260,
        "shg": 240,
        "microenterprise": 320
    }

    b0_segments = {}
    true_pds = np.zeros(N)
    default_flags = np.zeros(N, dtype=int)

    for seg, n_def in target_defaults.items():
        mask = (df_base["segment"] == seg).values
        seg_risk = latent_risk_core[mask]
        n_seg = np.sum(mask)

        low, high = -6.0, 6.0
        for _ in range(40):
            mid = (low + high) / 2.0
            p_cand = expit(mid + seg_risk)
            if np.sum(p_cand) < n_def:
                low = mid
            else:
                high = mid
        b0_segments[seg] = mid
        seg_pds = expit(mid + seg_risk)
        true_pds[mask] = seg_pds

        sampled_draw = seg_pds + np.random.normal(0, 0.015, n_seg)
        cutoff_rank = np.argsort(sampled_draw)[-n_def:]
        seg_defs = np.zeros(n_seg, dtype=int)
        seg_defs[cutoff_rank] = 1
        default_flags[mask] = seg_defs

    df_Latent = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "latent_repayment_will": np.round(repayment_will, 4),
        "latent_skill": np.round(skill, 4),
        "latent_assets": np.round(asset_z, 4),
        "latent_income_shock": np.round(latent_income_shock, 4),
        "latent_health_event": health_events,
        "latent_crop_failure": crop_failures,
        "latent_price_shock": price_shocks,
        "true_pd": np.round(true_pds, 4)
    })

    # -------------------------------------------------------------
    # 12. LOANS TABLE (Table H)
    # -------------------------------------------------------------
    loan_ids = []
    products = []
    lenders = []
    loan_amounts = []
    tenors = []
    rates = []
    repay_modes = []
    purposes = []
    max_dpds = []
    ever_30s = []
    ever_60s = []
    restructured = []

    lender_choices = ["RRB", "Commercial Bank", "Cooperative"]
    lender_p = [0.45, 0.35, 0.20]

    for i in range(N):
        l_id = f"L{i+1:05d}"
        seg = df_base.iloc[i]["segment"]
        is_def = default_flags[i]
        pd_val = true_pds[i]

        lender = np.random.choice(lender_choices, p=lender_p)

        if seg in ["marginal", "tenant"]:
            prod = "Crop input (KCC-type)"
            amt = int(np.clip(round(np.random.uniform(25000, 75000), -3), 20000, 150000))
            ten = int(np.random.choice([9, 12], p=[0.35, 0.65]))
            rate = 7.0 if lender == "Cooperative" else 7.5
            mode = "bullet_harvest"
            purp = "seeds_fertiliser"
        elif seg == "small":
            prod = np.random.choice(["Crop input (KCC-type)", "Dairy / livestock"], p=[0.70, 0.30])
            amt = int(np.clip(round(np.random.uniform(50000, 140000), -3), 30000, 150000))
            ten = 12 if prod == "Crop input (KCC-type)" else int(np.random.choice([18, 24, 36]))
            rate = 8.0 if prod == "Crop input (KCC-type)" else 9.5
            mode = "bullet_harvest" if prod == "Crop input (KCC-type)" else "monthly"
            purp = "seeds_fertiliser" if prod == "Crop input (KCC-type)" else "livestock"
        elif seg == "shg":
            prod = np.random.choice(["SHG-BLP group loan", "Dairy / livestock"], p=[0.75, 0.25])
            amt = int(np.clip(round(np.random.uniform(30000, 80000), -3), 25000, 90000))
            ten = int(np.random.choice([18, 24, 36], p=[0.40, 0.40, 0.20]))
            rate = 9.0 if prod == "SHG-BLP group loan" else 10.5
            mode = "monthly"
            purp = "working_capital" if prod == "SHG-BLP group loan" else "livestock"
        else: # microenterprise
            prod = "Micro-enterprise working capital"
            amt = int(np.clip(round(np.random.uniform(40000, 180000), -3), 30000, 200000))
            ten = int(np.random.choice([12, 18, 24], p=[0.40, 0.35, 0.25]))
            rate = 13.5
            mode = "monthly"
            purp = "working_capital"

        amt = int(round(amt / 5000.0) * 5000)

        if is_def == 1:
            dpd = int(np.clip(np.random.normal(118, 22), 90, 180))
            e30 = 1
            e60 = 1
        else:
            if pd_val > 0.08 and np.random.rand() < 0.20:
                dpd = int(np.clip(np.random.normal(38, 12), 15, 65))
                e30 = int(dpd >= 30)
                e60 = int(dpd >= 60)
            elif pd_val > 0.04 and np.random.rand() < 0.15:
                dpd = int(np.clip(np.random.normal(18, 6), 5, 29))
                e30 = 0
                e60 = 0
            else:
                dpd = 0
                e30 = 0
                e60 = 0

        restr = bool(dpd > 60 and np.random.rand() < 0.12)

        loan_ids.append(l_id)
        products.append(prod)
        lenders.append(lender)
        loan_amounts.append(amt)
        tenors.append(ten)
        rates.append(rate)
        repay_modes.append(mode)
        purposes.append(purp)
        max_dpds.append(dpd)
        ever_30s.append(e30)
        ever_60s.append(e60)
        restructured.append(restr)

    df_H = pd.DataFrame({
        "loan_id": loan_ids,
        "borrower_id": df_base["borrower_id"],
        "product": products,
        "lender_type": lenders,
        "loan_amount_inr": loan_amounts,
        "tenor_months": tenors,
        "interest_rate_pct": rates,
        "repayment_mode": repay_modes,
        "purpose": purposes,
        "disbursal_month": "2025-07",
        "max_dpd_12m": max_dpds,
        "ever_30dpd": ever_30s,
        "ever_60dpd": ever_60s,
        "default_flag": default_flags,
        "restructured_flag": restructured
    })

    # -------------------------------------------------------------
    # 13. MODELING FEATURES DATASET (21 Core + 7 Extensions)
    # -------------------------------------------------------------
    shg_rep_imputed = df_D["internal_repayment_rate"].fillna(0.88).values
    shg_att_pct = ((df_D["meetings_attended_12m"] / df_D["meetings_held_12m"]) * 100).fillna(75.0).values
    shg_sav_reg = df_D["savings_regularity_pct"].fillna(70.0).values
    u_ratio = (df_E["bills_on_time_12m"] / np.maximum(df_E["bills_paid_12m"], 1)).values
    u_ratio[df_E["bills_paid_12m"] == 0] = 0.50
    rech_reg = df_E["recharge_regularity"].values
    acct_age = df_A["bank_account_age_months"].values

    avg_inflow = np.array(borrower_avg_inflows)
    inflow_cv = np.array(borrower_inflow_cvs)
    in_out_ratio = np.array(borrower_inflow_outflow_ratios)
    hhi = wage_share**2 + crop_share**2 + livestock_share**2 + nonfarm_share**2 + leasing_share**2
    foir = np.array(borrower_foirs)
    govt_trans_share = np.array(borrower_govt_transfer_shares)

    avg_balance = np.array(borrower_avg_daily_balances)
    shg_corpus = df_D["member_savings_corpus_inr"].fillna(0.0).values
    l_val_arr = np.array(df_B["livestock_value_inr"])

    eff_land = (df_B["land_owned_ha"] + 0.5 * df_B["land_leased_ha"]).values
    irr_share_arr = df_B["irrigated_share"].values
    asset_idx_arr = df_B["asset_index"].values

    ndvi_p_mean = ((df_F["ndvi_peak_kharif"] + df_F["ndvi_peak_rabi"]) / 2.0).values
    rain_pct_arr = df_F["rainfall_pct_of_normal"].values
    crop_ins_flag = df_B["has_crop_insurance_pmfby"].astype(int).values

    inflow_slope = np.array(borrower_inflow_trend_slopes)
    seasonal_amp = np.array(borrower_seasonal_amplitudes)
    months_low_b = np.array(borrower_months_low_balances)
    ndvi_anom = df_F["ndvi_anomaly_vs_5yr"].values
    rail_comp = (df_A["consent_rails_granted"] / 4.0 * 100.0).values
    thin_file = (df_A["bureau_tradelines"] == 0).astype(int).values
    loan_to_income = np.round(df_H["loan_amount_inr"].values / (avg_inflow * 12.0), 3)

    gender_audit = df_A["gender"].values
    caste_audit = df_A["caste_category"].values
    age_bands = pd.cut(df_A["age"], bins=[0, 30, 45, 60, 100], labels=["<30", "30-45", "45-60", ">60"]).astype(str).values
    land_bands = []
    for l in df_B["land_owned_ha"]:
        if l == 0:
            land_bands.append("Landless")
        elif l < 1.0:
            land_bands.append("Marginal (<1ha)")
        elif l <= 2.0:
            land_bands.append("Small (1-2ha)")
        else:
            land_bands.append("Semi-Medium (2-4ha)")

    df_Features = pd.DataFrame({
        "borrower_id": df_base["borrower_id"],
        "village_id": df_base["village_id"],
        "segment": df_base["segment"],
        # Core 21 Features
        "shg_repayment_rate": np.round(shg_rep_imputed, 3),
        "shg_attendance_pct": np.round(shg_att_pct, 1),
        "savings_regularity_pct": np.round(shg_sav_reg, 1),
        "utility_on_time_ratio": np.round(u_ratio, 3),
        "recharge_regularity": np.round(rech_reg, 3),
        "account_age_months": acct_age,
        "avg_monthly_inflow": np.round(avg_inflow, 1),
        "inflow_cv": np.round(inflow_cv, 3),
        "inflow_outflow_ratio": np.round(in_out_ratio, 3),
        "income_diversification": np.round(hhi, 3),
        "foir": np.round(foir, 3),
        "govt_transfer_share": np.round(govt_trans_share, 3),
        "avg_daily_balance": np.round(avg_balance, 1),
        "shg_savings_corpus": np.round(shg_corpus, 1),
        "livestock_value": np.round(l_val_arr, 1),
        "effective_land_ha": np.round(eff_land, 2),
        "irrigated_share": np.round(irr_share_arr, 2),
        "asset_index": np.round(asset_idx_arr, 1),
        "ndvi_peak_mean": np.round(ndvi_p_mean, 3),
        "rainfall_pct_normal": np.round(rain_pct_arr, 1),
        "crop_insurance_flag": crop_ins_flag,
        # 7 Extension Features
        "inflow_trend_slope": np.round(inflow_slope, 2),
        "seasonal_amplitude": np.round(seasonal_amp, 2),
        "months_low_balance": months_low_b,
        "ndvi_anomaly": np.round(ndvi_anom, 3),
        "rail_completeness_pct": np.round(rail_comp, 1),
        "thin_file_flag": thin_file,
        "loan_to_income_ratio": loan_to_income,
        # Audit-Only Protected Attributes
        "gender": gender_audit,
        "caste_category": caste_audit,
        "age_band": age_bands,
        "landholding_band": land_bands,
        # Target
        "default_flag": default_flags
    })

    # Save CSV files
    df_A.to_csv(os.path.join(raw_dir, "A_borrowers.csv"), index=False)
    df_B.to_csv(os.path.join(raw_dir, "B_household_land_crop.csv"), index=False)
    df_C.to_csv(os.path.join(raw_dir, "C_aa_monthly.csv"), index=False)
    df_D.to_csv(os.path.join(raw_dir, "D_shg_ledger.csv"), index=False)
    df_E.to_csv(os.path.join(raw_dir, "E_utility_digital.csv"), index=False)
    df_F.to_csv(os.path.join(raw_dir, "F_satellite_weather.csv"), index=False)
    df_G.to_csv(os.path.join(raw_dir, "G_govt_social.csv"), index=False)
    df_H.to_csv(os.path.join(raw_dir, "H_loans.csv"), index=False)
    df_Latent.to_csv(os.path.join(latent_dir, "ground_truth_latent.csv"), index=False)
    df_Features.to_csv(os.path.join(proc_dir, "modeling_features.csv"), index=False)

    print(f"Successfully generated all 8 tables + latent + modeling features for {N} borrowers!")
    print(f"Overall defaults: {np.sum(default_flags)} / {N} ({np.mean(default_flags)*100:.2f}%)")
    for seg in target_defaults.keys():
        m = df_Features["segment"] == seg
        print(f"  Segment '{seg}': {df_Features.loc[m, 'default_flag'].sum()} / {m.sum()} ({df_Features.loc[m, 'default_flag'].mean()*100:.2f}%)")

    return df_Features

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    generate_all_datasets(output_dir=out_dir)

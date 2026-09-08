"""Seed script for CreditTech Early Adopter MVP Cohort.

Populates realistic early adopter cohorts:
- 15 Pilot Villages across 3 Agro-Climatic Zones
- Partner Regulated Entities: State Bank of India (RE-SBI-01), Baroda Rajasthan Kshetriya Gramin Bank (RRB-BRKGB-01), NABARD
- Bank Sakhi Field Agent Network (6 agents across village clusters)
- 50 Early Adopter Borrowers (Women SHG micro-entrepreneurs & Small/Marginal farmers)
- DPDP Consent Records with SHA-256 cryptographic hash-chains
- 4-Rail Feature Snapshots (AA, Geospatial, SHG/FPO, Bureau)
- Calibrated Credit Scores with confidence bounds & bilingual SHAP ReasonCodes
- Multi-Tenant Loan Applications & Immutable Officer Decision Logs

Usage:
    python -m scripts.seed_early_adopters
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from sqlalchemy import select
from services.core.config import get_settings
from services.core.database import async_session_factory, engine, init_db
from services.core.shared.models import (
    Borrower,
    ConsentAuditLog,
    ConsentRecord,
    FeatureSnapshot,
    Grievance,
    GrievanceAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    ReasonCode,
    RepaymentRecord,
    Score,
    Village,
)
from services.core.shared.test_personas import (
    BORROWER_RADHIKA_ID,
    VILLAGE_ALPHA_ID,
    VILLAGE_ALPHA_NAME,
    VILLAGE_BETA_ID,
    VILLAGE_BETA_NAME,
)

settings = get_settings()

# ──────────────────────────────────────────────────────────────
# Deterministic Pilot Geography (15+ Villages across 3 Zones)
# ──────────────────────────────────────────────────────────────
PILOT_VILLAGES = [
    # Canal-Irrigated Plains (North-West Rajasthan & Eastern UP)
    {
        "id": VILLAGE_ALPHA_ID,
        "name": VILLAGE_ALPHA_NAME,
        "site_type": "CANAL_IRRIGATED",
        "state": "Uttar Pradesh",
        "district": "Chandauli",
        "block": "Chahaniya",
        "agro_climatic_zone": "Middle Gangetic Plain (Zone IV)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111101"),
        "name": "Sadulshahar Rural",
        "site_type": "CANAL_IRRIGATED",
        "state": "Rajasthan",
        "district": "Sri Ganganagar",
        "block": "Sadulshahar",
        "agro_climatic_zone": "Trans-Gangetic Plains (Zone VI)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111102"),
        "name": "Padampur Canal Cluster",
        "site_type": "CANAL_IRRIGATED",
        "state": "Rajasthan",
        "district": "Sri Ganganagar",
        "block": "Padampur",
        "agro_climatic_zone": "Trans-Gangetic Plains (Zone VI)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111103"),
        "name": "Pilibanga Mandi",
        "site_type": "CANAL_IRRIGATED",
        "state": "Rajasthan",
        "district": "Hanumangarh",
        "block": "Pilibanga",
        "agro_climatic_zone": "Trans-Gangetic Plains (Zone VI)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111104"),
        "name": "Rawatsar Nohar",
        "site_type": "CANAL_IRRIGATED",
        "state": "Rajasthan",
        "district": "Hanumangarh",
        "block": "Rawatsar",
        "agro_climatic_zone": "Trans-Gangetic Plains (Zone VI)",
    },

    # Rain-fed Vindhyan & Plateau Zones
    {
        "id": VILLAGE_BETA_ID,
        "name": VILLAGE_BETA_NAME,
        "site_type": "RAIN_FED",
        "state": "Uttar Pradesh",
        "district": "Mirzapur",
        "block": "Narayanpur",
        "agro_climatic_zone": "Vindhyan Hills & Plateau (Zone VII)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111105"),
        "name": "Robertsganj Dehat",
        "site_type": "RAIN_FED",
        "state": "Uttar Pradesh",
        "district": "Sonbhadra",
        "block": "Robertsganj",
        "agro_climatic_zone": "Vindhyan Hills & Plateau (Zone VII)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111106"),
        "name": "Dudhi Tribal Belt",
        "site_type": "RAIN_FED",
        "state": "Uttar Pradesh",
        "district": "Sonbhadra",
        "block": "Dudhi",
        "agro_climatic_zone": "Vindhyan Hills & Plateau (Zone VII)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111107"),
        "name": "Chunar Khurd",
        "site_type": "RAIN_FED",
        "state": "Uttar Pradesh",
        "district": "Mirzapur",
        "block": "Chunar",
        "agro_climatic_zone": "Vindhyan Hills & Plateau (Zone VII)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111108"),
        "name": "Talbehat Plateau",
        "site_type": "RAIN_FED",
        "state": "Uttar Pradesh",
        "district": "Lalitpur",
        "block": "Talbehat",
        "agro_climatic_zone": "Bundelkhand Agro-Ecological Subregion",
    },

    # Semi-Arid Hills & Arid Western Rajasthan
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111109"),
        "name": "Chohtan Thar",
        "site_type": "ARID_DRYLAND",
        "state": "Rajasthan",
        "district": "Barmer",
        "block": "Chohtan",
        "agro_climatic_zone": "Western Dry Region (Zone XIV)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111110"),
        "name": "Baytu Sandstone",
        "site_type": "ARID_DRYLAND",
        "state": "Rajasthan",
        "district": "Barmer",
        "block": "Baytu",
        "agro_climatic_zone": "Western Dry Region (Zone XIV)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111111"),
        "name": "Bhinmal Pastoral",
        "site_type": "SEMI_ARID",
        "state": "Rajasthan",
        "district": "Jalore",
        "block": "Bhinmal",
        "agro_climatic_zone": "Transitional Plain of Luni Basin (Zone II-B)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111112"),
        "name": "Osian Desert Oasis",
        "site_type": "ARID_DRYLAND",
        "state": "Rajasthan",
        "district": "Jodhpur",
        "block": "Osian",
        "agro_climatic_zone": "Western Dry Region (Zone XIV)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111113"),
        "name": "Hindoli Hills",
        "site_type": "SEMI_ARID",
        "state": "Rajasthan",
        "district": "Bundi",
        "block": "Hindoli",
        "agro_climatic_zone": "South-Eastern Humid Plain (Zone V)",
    },
    {
        "id": uuid.UUID("a1111111-1111-4111-8111-111111111114"),
        "name": "Atru Agricultural Hub",
        "site_type": "SEMI_ARID",
        "state": "Rajasthan",
        "district": "Baran",
        "block": "Atru",
        "agro_climatic_zone": "South-Eastern Humid Plain (Zone V)",
    },
]

# Partner Regulated Entities (REs) for Multi-Tenant Testing
PARTNER_RES = [
    {"id": "RE-SBI-01", "name": "State Bank of India (Lead Rural Partner)", "share": 0.50},
    {"id": "RRB-BRKGB-01", "name": "Baroda Rajasthan Kshetriya Gramin Bank", "share": 0.45},
    {"id": "NABARD-AUDIT-01", "name": "NABARD Pilot Monitoring Authority", "share": 0.05},
]

# Bank Sakhi Field Network
BANK_SAKHIS = [
    {"id": "SAKHI-001", "name": "Sunita Devi", "zone": "Chandauli Plains", "phone": "9876543201"},
    {"id": "SAKHI-002", "name": "Anita Bai", "zone": "Mirzapur Hills", "phone": "9876543202"},
    {"id": "SAKHI-003", "name": "Manju Kanwar", "zone": "Sri Ganganagar Canal", "phone": "9876543203"},
    {"id": "SAKHI-004", "name": "Santosh Meena", "zone": "Barmer Desert", "phone": "9876543204"},
    {"id": "SAKHI-005", "name": "Rekha Yadav", "zone": "Sonbhadra Plateau", "phone": "9876543205"},
    {"id": "SAKHI-006", "name": "Gayatri Rathore", "zone": "Jodhpur & Jalore", "phone": "9876543206"},
]

# 50 Early Adopter Profiles (Synthetic, realistic, grounded in Indian rural economy)
EARLY_ADOPTER_PROFILES = [
    # 1-15: Dairy Micro-enterprises & Livestock (Women SHGs)
    {"name": "Kamla Devi", "gender": "F", "age": 36, "land": "LANDLESS", "purpose": "DAIRY_PURCHASE", "amt": 50000, "inflow": 16500, "shg_rate": 0.98, "savings": 14000, "years": 4, "bureau_loans": 0},
    {"name": "Pooja Gurjar", "gender": "F", "age": 31, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 60000, "inflow": 19000, "shg_rate": 0.95, "savings": 18500, "years": 5, "bureau_loans": 1},
    {"name": "Santosh Sharma", "gender": "F", "age": 42, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 45000, "inflow": 14200, "shg_rate": 0.96, "savings": 12000, "years": 3, "bureau_loans": 0},
    {"name": "Bhagwati Bai", "gender": "F", "age": 39, "land": "LANDLESS", "purpose": "DAIRY_PURCHASE", "amt": 55000, "inflow": 17800, "shg_rate": 0.92, "savings": 15500, "years": 4, "bureau_loans": 1},
    {"name": "Kailash Kanwar", "gender": "F", "age": 28, "land": "SMALL", "purpose": "DAIRY_PURCHASE", "amt": 75000, "inflow": 22000, "shg_rate": 0.99, "savings": 22000, "years": 6, "bureau_loans": 1},
    {"name": "Geeta Devi", "gender": "F", "age": 45, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 40000, "inflow": 12500, "shg_rate": 0.88, "savings": 9500, "years": 2, "bureau_loans": 0},
    {"name": "Laxmi Prajapat", "gender": "F", "age": 34, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 50000, "inflow": 15600, "shg_rate": 0.94, "savings": 13200, "years": 3, "bureau_loans": 0},
    {"name": "Suman Chaudhary", "gender": "F", "age": 33, "land": "SMALL", "purpose": "DAIRY_PURCHASE", "amt": 80000, "inflow": 26000, "shg_rate": 0.97, "savings": 27000, "years": 5, "bureau_loans": 1},
    {"name": "Guddi Yadav", "gender": "F", "age": 37, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 50000, "inflow": 16000, "shg_rate": 0.91, "savings": 11000, "years": 3, "bureau_loans": 0},
    {"name": "Parvati Meena", "gender": "F", "age": 41, "land": "SMALL", "purpose": "DAIRY_PURCHASE", "amt": 65000, "inflow": 21000, "shg_rate": 0.96, "savings": 19000, "years": 4, "bureau_loans": 1},
    {"name": "Munni Devi", "gender": "F", "age": 50, "land": "LANDLESS", "purpose": "DAIRY_PURCHASE", "amt": 35000, "inflow": 11500, "shg_rate": 0.85, "savings": 8000, "years": 2, "bureau_loans": 0},
    {"name": "Saroj Verma", "gender": "F", "age": 29, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 55000, "inflow": 18200, "shg_rate": 0.95, "savings": 16000, "years": 4, "bureau_loans": 0},
    {"name": "Manju Vishwakarma", "gender": "F", "age": 35, "land": "LANDLESS", "purpose": "DAIRY_PURCHASE", "amt": 45000, "inflow": 14000, "shg_rate": 0.93, "savings": 12500, "years": 3, "bureau_loans": 0},
    {"name": "Kiran Rathore", "gender": "F", "age": 32, "land": "SMALL", "purpose": "DAIRY_PURCHASE", "amt": 70000, "inflow": 23500, "shg_rate": 0.98, "savings": 24000, "years": 5, "bureau_loans": 1},
    {"name": "Pushpa Bai", "gender": "F", "age": 46, "land": "MARGINAL", "purpose": "DAIRY_PURCHASE", "amt": 50000, "inflow": 15000, "shg_rate": 0.90, "savings": 10500, "years": 3, "bureau_loans": 1},

    # 16-30: Village Kirana, Tailoring & Micro-Retail
    {"name": "Sharda Devi", "gender": "F", "age": 40, "land": "LANDLESS", "purpose": "KIRANA_EXPANSION", "amt": 60000, "inflow": 28000, "shg_rate": 0.96, "savings": 21000, "years": 5, "bureau_loans": 1},
    {"name": "Asha Kumari", "gender": "F", "age": 27, "land": "LANDLESS", "purpose": "TAILORING_MACHINE", "amt": 35000, "inflow": 13500, "shg_rate": 0.99, "savings": 14500, "years": 3, "bureau_loans": 0},
    {"name": "Premila Saini", "gender": "F", "age": 38, "land": "MARGINAL", "purpose": "KIRANA_EXPANSION", "amt": 80000, "inflow": 32000, "shg_rate": 0.97, "savings": 31000, "years": 6, "bureau_loans": 1},
    {"name": "Urmila Devi", "gender": "F", "age": 44, "land": "LANDLESS", "purpose": "HANDICRAFTS_STOCK", "amt": 40000, "inflow": 15000, "shg_rate": 0.92, "savings": 12000, "years": 3, "bureau_loans": 0},
    {"name": "Anita Kumawat", "gender": "F", "age": 30, "land": "MARGINAL", "purpose": "TAILORING_MACHINE", "amt": 45000, "inflow": 16500, "shg_rate": 0.95, "savings": 15000, "years": 4, "bureau_loans": 0},
    {"name": "Chanda Bai", "gender": "F", "age": 35, "land": "LANDLESS", "purpose": "KIRANA_EXPANSION", "amt": 50000, "inflow": 21000, "shg_rate": 0.94, "savings": 17000, "years": 4, "bureau_loans": 1},
    {"name": "Basanti Devi", "gender": "F", "age": 48, "land": "MARGINAL", "purpose": "FLOUR_MILL_EXPANSION", "amt": 90000, "inflow": 35000, "shg_rate": 0.98, "savings": 38000, "years": 7, "bureau_loans": 2},
    {"name": "Tara Meena", "gender": "F", "age": 26, "land": "LANDLESS", "purpose": "BEAUTY_PARLOUR_KITS", "amt": 30000, "inflow": 12000, "shg_rate": 0.90, "savings": 8500, "years": 2, "bureau_loans": 0},
    {"name": "Vimla Jat", "gender": "F", "age": 37, "land": "SMALL", "purpose": "KIRANA_EXPANSION", "amt": 75000, "inflow": 29000, "shg_rate": 0.96, "savings": 26000, "years": 5, "bureau_loans": 1},
    {"name": "Kavita Maurya", "gender": "F", "age": 32, "land": "LANDLESS", "purpose": "TAILORING_MACHINE", "amt": 40000, "inflow": 14500, "shg_rate": 0.93, "savings": 13000, "years": 3, "bureau_loans": 0},
    {"name": "Sunita Rawat", "gender": "F", "age": 43, "land": "MARGINAL", "purpose": "KIRANA_EXPANSION", "amt": 65000, "inflow": 24000, "shg_rate": 0.89, "savings": 16000, "years": 4, "bureau_loans": 1},
    {"name": "Rekha Bano", "gender": "F", "age": 29, "land": "LANDLESS", "purpose": "EMBROIDERY_ZARI", "amt": 35000, "inflow": 14000, "shg_rate": 0.97, "savings": 15000, "years": 3, "bureau_loans": 0},
    {"name": "Dropadi Devi", "gender": "F", "age": 52, "land": "MARGINAL", "purpose": "POTTERY_EQUIPMENT", "amt": 40000, "inflow": 13000, "shg_rate": 0.86, "savings": 9000, "years": 3, "bureau_loans": 0},
    {"name": "Maya Rajput", "gender": "F", "age": 34, "land": "MARGINAL", "purpose": "KIRANA_EXPANSION", "amt": 55000, "inflow": 22000, "shg_rate": 0.95, "savings": 19500, "years": 4, "bureau_loans": 1},
    {"name": "Nisha Khatun", "gender": "F", "age": 31, "land": "LANDLESS", "purpose": "FOOTWEAR_STALL", "amt": 45000, "inflow": 17500, "shg_rate": 0.93, "savings": 14000, "years": 3, "bureau_loans": 0},

    # 31-50: Smallholder & Marginal Farmers (Wheat, Mustard, Cotton, Pulses, Solar Pumps)
    {"name": "Ramesh Chandra", "gender": "M", "age": 46, "land": "SMALL", "purpose": "CROP_INPUTS_WHEAT", "amt": 60000, "inflow": 24000, "shg_rate": 0.95, "savings": 22000, "years": 5, "bureau_loans": 1},
    {"name": "Surendra Singh", "gender": "M", "age": 39, "land": "MARGINAL", "purpose": "CROP_INPUTS_MUSTARD", "amt": 45000, "inflow": 18000, "shg_rate": 0.92, "savings": 15000, "years": 3, "bureau_loans": 1},
    {"name": "Om Prakash", "gender": "M", "age": 54, "land": "SEMI_MEDIUM", "purpose": "SOLAR_DRIP_IRRIGATION", "amt": 120000, "inflow": 42000, "shg_rate": 0.98, "savings": 45000, "years": 7, "bureau_loans": 2},
    {"name": "Kalu Ram", "gender": "M", "age": 43, "land": "MARGINAL", "purpose": "CROP_INPUTS_BAJRA", "amt": 35000, "inflow": 13000, "shg_rate": 0.88, "savings": 9500, "years": 2, "bureau_loans": 0},
    {"name": "Mohan Lal", "gender": "M", "age": 48, "land": "SMALL", "purpose": "CROP_INPUTS_COTTON", "amt": 70000, "inflow": 29000, "shg_rate": 0.94, "savings": 26000, "years": 5, "bureau_loans": 1},
    {"name": "Dinesh Kumar", "gender": "M", "age": 33, "land": "MARGINAL", "purpose": "VEGETABLE_GREENHOUSE", "amt": 50000, "inflow": 20000, "shg_rate": 0.96, "savings": 18000, "years": 4, "bureau_loans": 0},
    {"name": "Bhagwan Sahay", "gender": "M", "age": 51, "land": "SMALL", "purpose": "CROP_INPUTS_PULSES", "amt": 55000, "inflow": 21000, "shg_rate": 0.91, "savings": 17000, "years": 4, "bureau_loans": 1},
    {"name": "Bhanwar Singh", "gender": "M", "age": 47, "land": "SMALL", "purpose": "TRACTOR_ATTACHMENT", "amt": 85000, "inflow": 33000, "shg_rate": 0.97, "savings": 32000, "years": 6, "bureau_loans": 2},
    {"name": "Gordhan Das", "gender": "M", "age": 56, "land": "MARGINAL", "purpose": "CROP_INPUTS_WHEAT", "amt": 40000, "inflow": 14000, "shg_rate": 0.85, "savings": 10000, "years": 3, "bureau_loans": 0},
    {"name": "Jaswant Singh", "gender": "M", "age": 36, "land": "SMALL", "purpose": "SOLAR_PUMP_SUBSIDY", "amt": 95000, "inflow": 36000, "shg_rate": 0.97, "savings": 35000, "years": 5, "bureau_loans": 1},
    {"name": "Babulal Meena", "gender": "M", "age": 42, "land": "MARGINAL", "purpose": "CROP_INPUTS_MAIZE", "amt": 38000, "inflow": 15500, "shg_rate": 0.93, "savings": 13500, "years": 3, "bureau_loans": 0},
    {"name": "Hari Ram", "gender": "M", "age": 49, "land": "SMALL", "purpose": "CROP_INPUTS_MUSTARD", "amt": 65000, "inflow": 26000, "shg_rate": 0.95, "savings": 24000, "years": 5, "bureau_loans": 1},
    {"name": "Shiv Dayal", "gender": "M", "age": 37, "land": "MARGINAL", "purpose": "DAIRY_FODDER_CHOPPER", "amt": 45000, "inflow": 18500, "shg_rate": 0.94, "savings": 16500, "years": 4, "bureau_loans": 0},
    {"name": "Jagdish Prasad", "gender": "M", "age": 53, "land": "SMALL", "purpose": "CROP_INPUTS_WHEAT", "amt": 60000, "inflow": 23000, "shg_rate": 0.90, "savings": 19000, "years": 4, "bureau_loans": 1},
    {"name": "Madan Lal", "gender": "M", "age": 45, "land": "MARGINAL", "purpose": "BIO_FERTILIZER_INPUTS", "amt": 40000, "inflow": 16000, "shg_rate": 0.92, "savings": 14000, "years": 3, "bureau_loans": 0},
    {"name": "Ramswaroop Jat", "gender": "M", "age": 41, "land": "SMALL", "purpose": "CROP_INPUTS_BARLEY", "amt": 50000, "inflow": 20500, "shg_rate": 0.96, "savings": 21000, "years": 5, "bureau_loans": 1},
    {"name": "Tejpal Gurjar", "gender": "M", "age": 34, "land": "MARGINAL", "purpose": "CROP_INPUTS_MUSTARD", "amt": 42000, "inflow": 17000, "shg_rate": 0.91, "savings": 15000, "years": 3, "bureau_loans": 0},
    {"name": "Mangilal Sharma", "gender": "M", "age": 58, "land": "SEMI_MEDIUM", "purpose": "PIPELINE_IRRIGATION", "amt": 110000, "inflow": 40000, "shg_rate": 0.97, "savings": 42000, "years": 7, "bureau_loans": 2},
    {"name": "Bhairon Singh", "gender": "M", "age": 44, "land": "SMALL", "purpose": "CROP_INPUTS_GUAR", "amt": 55000, "inflow": 21500, "shg_rate": 0.89, "savings": 17500, "years": 4, "bureau_loans": 1},
    {"name": "Chhotu Ram", "gender": "M", "age": 38, "land": "MARGINAL", "purpose": "CROP_INPUTS_WHEAT", "amt": 48000, "inflow": 19000, "shg_rate": 0.93, "savings": 16000, "years": 4, "bureau_loans": 0},
]


def _compute_genesis_hash(borrower_id: uuid.UUID) -> str:
    salt = settings.consent_genesis_salt
    payload = f"GENESIS:{salt}:{borrower_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _compute_consent_hash(
    borrower_id: uuid.UUID,
    purpose: str,
    data_sources: list[str],
    issued_at: datetime,
    expires_at: datetime,
    status: str,
    prev_hash: str,
) -> str:
    payload = json.dumps(
        {
            "borrower_id": str(borrower_id),
            "purpose": purpose,
            "data_sources": sorted(data_sources),
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": status,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def seed_early_adopters() -> None:
    """Idempotently seed the Early Adopter MVP Cohort."""
    print("🚀 Initializing Early Adopter MVP Database Seeding...")
    await init_db()

    now = datetime.now(UTC)
    random.seed(42)  # Deterministic generation

    async with async_session_factory() as db:
        # 1. Upsert Pilot Villages
        print(f"📍 Checking & seeding {len(PILOT_VILLAGES)} pilot villages across 3 agro-climatic zones...")
        village_map = {}
        for v_data in PILOT_VILLAGES:
            existing = await db.get(Village, v_data["id"])
            if not existing:
                village = Village(**v_data)
                db.add(village)
                village_map[v_data["name"]] = v_data["id"]
            else:
                village_map[v_data["name"]] = existing.id
        await db.flush()

        all_village_ids = [v["id"] for v in PILOT_VILLAGES]

        # 2. Check existing early adopters to ensure idempotency
        existing_ea = await db.execute(
            select(Borrower.id).where(Borrower.aadhaar_ref_hash.like("EA_%"))
        )
        existing_ids = set(existing_ea.scalars().all())

        if len(existing_ids) >= len(EARLY_ADOPTER_PROFILES):
            print(f"ℹ️ {len(existing_ids)} Early Adopter profiles already exist in DB. Validating completeness...")
            scores_res = await db.execute(select(Score).where(Score.score <= 100.0))
            low_scores = scores_res.scalars().all()
            if low_scores:
                for sc in low_scores:
                    if sc.confidence_lower > 100.0:
                        sc.score = round(300.0 + (sc.score / 100.0) * 600.0, 1)
                await db.commit()
            app_count = (await db.execute(select(LoanApplication))).scalars().all()
            score_count = (await db.execute(select(Score))).scalars().all()
            print(f"✅ Existing State: {len(existing_ids)} borrowers, {len(score_count)} scores, {len(app_count)} applications.")
            return

        print(f"🌱 Seeding {len(EARLY_ADOPTER_PROFILES)} Early Adopter Borrowers with 4-rail snapshots & scores...")

        borrowers_to_add = []
        consents_to_add = []
        audits_to_add = []
        snapshots_to_add = []
        scores_to_add = []
        reasons_to_add = []
        apps_to_add = []
        decisions_to_add = []
        repayments_to_add = []

        for idx, profile in enumerate(EARLY_ADOPTER_PROFILES, start=1):
            # Deterministic IDs
            b_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-borrower-{idx}")
            if b_uuid in existing_ids:
                continue

            v_id = all_village_ids[idx % len(all_village_ids)]
            assigned_sakhi = BANK_SAKHIS[idx % len(BANK_SAKHIS)]
            re_partner = PARTNER_RES[0] if (idx % 2 == 0) else PARTNER_RES[1]

            # 2a. Borrower record
            aadhaar_hash = f"EA_{hashlib.sha256(f'AADHAAR_EA_{idx:03d}'.encode()).hexdigest()}"
            borrower = Borrower(
                id=b_uuid,
                aadhaar_ref_hash=aadhaar_hash,
                name_encrypted=f"enc:{profile['name']}",
                phone_encrypted=f"enc:98{idx:02d}11{random.randint(1000, 9999)}",
                village_id=v_id,
                gender=profile["gender"],
                age=profile["age"],
                landholding_band=profile["land"],
                language="hi" if idx % 3 != 0 else "raj",
                created_at=now - timedelta(days=random.randint(30, 90)),
            )
            borrowers_to_add.append(borrower)

            # 2b. DPDP Consent Record (Cryptographically Chained)
            c_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-consent-{idx}")
            issued_date = now - timedelta(days=random.randint(15, 45))
            expires_date = issued_date + timedelta(days=365)
            data_sources = ["AA", "SHG_FPO", "GEOSPATIAL", "BUREAU"]
            genesis_hash = _compute_genesis_hash(b_uuid)
            curr_hash = _compute_consent_hash(
                b_uuid, "credit_scoring", data_sources, issued_date, expires_date, "ACTIVE", genesis_hash
            )
            consent = ConsentRecord(
                id=c_uuid,
                borrower_id=b_uuid,
                purpose="credit_scoring",
                consent_mode="bank_sakhi_assisted",
                data_sources=data_sources,
                scope_description_en=f"CreditTech rural appraisal assisted by {assigned_sakhi['name']} ({assigned_sakhi['id']})",
                issued_at=issued_date,
                expires_at=expires_date,
                status="ACTIVE",
                hash_prev=genesis_hash,
                hash_current=curr_hash,
                created_by=f"sakhi:{assigned_sakhi['id']}",
            )
            audit = ConsentAuditLog(
                consent_id=c_uuid,
                action="CREATED",
                actor=f"sakhi:{assigned_sakhi['id']}",
                performed_at=issued_date,
            )
            consents_to_add.extend([consent, audit])

            # 2c. 4-Rail Feature Snapshot
            snap_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-snap-{idx}")
            land_acres = 0.0 if profile["land"] == "LANDLESS" else (1.2 if profile["land"] == "MARGINAL" else 3.2)
            ndvi_val = round(0.40 + (0.35 * (profile["shg_rate"] - 0.70) / 0.30) + random.uniform(-0.05, 0.05), 3)
            rainfall_dev = round(random.uniform(-18.0, 8.0), 1)

            feature_dict = {
                "monthly_avg_credit_inflow": float(profile["inflow"]),
                "shg_repayment_rate": float(profile["shg_rate"]),
                "shg_meeting_attendance_pct": float(round(profile["shg_rate"] * 96.0, 1)),
                "shg_cumulative_savings": float(profile["savings"]),
                "shg_membership_years": int(profile["years"]),
                "utility_payment_ontime_pct": float(round(profile["shg_rate"] * 98.0, 1)),
                "land_holding_acres": land_acres,
                "land_quality_ndvi_avg": ndvi_val,
                "rainfall_deviation_kharif_pct": rainfall_dev,
                "bureau_active_loans_count": int(profile["bureau_loans"]),
                "bureau_overdue_amount": 0.0 if profile["bureau_loans"] == 0 else float(random.choice([0.0, 0.0, 1200.0])),
            }

            snapshot = FeatureSnapshot(
                id=snap_uuid,
                borrower_id=b_uuid,
                feature_version="v1.1.0",
                season_tag="KHARIF",
                sources_used=data_sources,
                features_json=feature_dict,
                computed_at=issued_date + timedelta(days=1),
            )
            snapshots_to_add.append(snapshot)

            # 2d. Calibrated Score Calculation
            # Baseline score derived from cashflow, SHG discipline, and weather stability
            base_score = 450 + (profile["shg_rate"] * 240) + min(120, profile["inflow"] / 300)
            if profile["bureau_loans"] > 1:
                base_score -= 35
            if feature_dict["bureau_overdue_amount"] > 0:
                base_score -= 45
            calibrated_score_900 = float(max(320.0, min(820.0, round(base_score, 1))))
            score_100 = round((calibrated_score_900 - 300.0) / 6.0, 1)

            s_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-score-{idx}")
            score_date = issued_date + timedelta(days=1, hours=2)
            score_rec = Score(
                id=s_uuid,
                borrower_id=b_uuid,
                feature_snapshot_id=snap_uuid,
                model_version="v1.1.0-woe-scorecard",
                score=calibrated_score_900,
                confidence_lower=round(calibrated_score_900 - 28.0, 1),
                confidence_upper=round(calibrated_score_900 + 26.0, 1),
                sources_used=data_sources,
                generated_at=score_date,
            )
            scores_to_add.append(score_rec)

            # 2e. Localized SHAP Reason Codes (Bilingual English / Hindi)
            reasons_to_add.extend([
                ReasonCode(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-reason-{idx}-1"),
                    score_id=s_uuid,
                    rank=1,
                    feature_name="shg_repayment_rate",
                    direction="POSITIVE" if profile["shg_rate"] >= 0.90 else "NEGATIVE",
                    shap_value=round((profile["shg_rate"] - 0.85) * 1.8, 3),
                    localized_text_en=f"SHG repayment punctuality is {int(profile['shg_rate']*100)}%, indicating reliable peer group commitment.",
                    localized_text_hi=f"स्वयं सहायता समूह में ऋण चुकौती की नियमितता {int(profile['shg_rate']*100)}% है, जो अनुशासित साख दर्शाती है।",
                ),
                ReasonCode(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-reason-{idx}-2"),
                    score_id=s_uuid,
                    rank=2,
                    feature_name="monthly_avg_credit_inflow",
                    direction="POSITIVE" if profile["inflow"] >= 15000 else "NEGATIVE",
                    shap_value=round((profile["inflow"] - 15000) / 20000, 3),
                    localized_text_en=f"Monthly digital & cash inflow of ₹{profile['inflow']:,} supports targeted loan debt service.",
                    localized_text_hi=f"मासिक ₹{profile['inflow']:,} का नियमित आय प्रवाह ऋण किस्त भुगतान हेतु पर्याप्त सुरक्षा प्रदान करता है।",
                ),
                ReasonCode(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-reason-{idx}-3"),
                    score_id=s_uuid,
                    rank=3,
                    feature_name="rainfall_deviation_kharif_pct",
                    direction="POSITIVE" if rainfall_dev >= -10.0 else "NEGATIVE",
                    shap_value=round(rainfall_dev / 100.0, 3),
                    localized_text_en=f"Localized Kharif weather deviation ({rainfall_dev}%) assessed against village canal buffer.",
                    localized_text_hi=f"स्थानीय खरीफ वर्षा विचलन ({rainfall_dev}%) ग्राम सिंचाई सुविधा के अनुसार स्थिर है।",
                ),
            ])

            # 2f. Loan Application & Human-In-The-Loop Underwriting
            app_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-app-{idx}")
            tenure = 18 if profile["amt"] <= 50000 else (24 if profile["amt"] <= 80000 else 36)

            # Decision distribution: 65% APPROVED, 20% MORE_INFO_REQUIRED, 15% REJECTED
            if calibrated_score >= 640:
                decision = "APPROVED"
                approved_amt = float(profile["amt"])
                recom = "APPROVE"
                override = False
                ov_reason = None
            elif calibrated_score >= 540:
                decision = "MORE_INFO_REQUIRED" if (idx % 2 == 0) else "APPROVED"
                approved_amt = float(profile["amt"] * 0.85) if decision == "APPROVED" else None
                recom = "REVIEW"
                override = (decision == "APPROVED")
                ov_reason = "Approved based on Bank Sakhi field thrift physical verification" if override else None
            else:
                decision = "REJECTED"
                approved_amt = None
                recom = "REJECT"
                override = False
                ov_reason = "High debt-to-inflow ratio and history of overdue payments"

            app_date = score_date + timedelta(hours=3)
            decision_date = app_date + timedelta(days=1, hours=4)

            loan_app = LoanApplication(
                id=app_uuid,
                borrower_id=b_uuid,
                score_id=s_uuid,
                partner_re_id=re_partner["id"],
                requested_amount=float(profile["amt"]),
                requested_tenure_months=tenure,
                purpose=profile["purpose"],
                officer_decision=decision,
                decided_at=decision_date if decision != "MORE_INFO_REQUIRED" else None,
                override_reason=ov_reason,
                approved_amount=approved_amt,
                created_at=app_date,
                updated_at=decision_date,
            )
            apps_to_add.append(loan_app)

            # Immutable Officer Decision Audit Log
            dec_log = OfficerDecisionLog(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-dec-{idx}"),
                score_id=s_uuid,
                loan_application_id=app_uuid,
                officer_id="OFF-001" if re_partner["id"] == "RE-SBI-01" else "OFF-002",
                decision=decision,
                model_recommendation=recom,
                is_override=override,
                override_reason=ov_reason,
                officer_notes=f"Appraised for {profile['name']} under rural early adopter cohort. Verified by Sakhi {assigned_sakhi['name']}.",
                model_score_at_decision=score_100,
                model_version_at_decision="v1.1.0-woe-scorecard",
                feature_version_at_decision="v1.1.0",
                created_at=decision_date,
            )
            decisions_to_add.append(dec_log)

            # 2g. Consented Repayment Record for Approved Loans
            if decision == "APPROVED":
                repayment = RepaymentRecord(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, f"credit-tech-ea-repay-{idx}"),
                    loan_application_id=app_uuid,
                    period="2026-M07",
                    status="CURRENT" if idx % 10 != 0 else "DPD_1_30",
                    consented_for_retraining=True,
                    recorded_at=decision_date + timedelta(days=25),
                )
                repayments_to_add.append(repayment)

        # Batch insert all records in atomic chunks
        print(f"💾 Committing {len(borrowers_to_add)} borrowers, {len(consents_to_add)} consent/audit records...")
        db.add_all(borrowers_to_add)
        await db.flush()

        db.add_all(consents_to_add)
        db.add_all(snapshots_to_add)
        await db.flush()

        db.add_all(scores_to_add)
        db.add_all(reasons_to_add)
        await db.flush()

        db.add_all(apps_to_add)
        db.add_all(decisions_to_add)
        db.add_all(repayments_to_add)

        # 3. Seed Sample Pilot Grievance with Active SLA
        g_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "credit-tech-ea-grievance-sample")
        existing_g = await db.get(Grievance, g_uuid)
        if not existing_g and borrowers_to_add:
            sample_b = borrowers_to_add[0]
            sample_app = apps_to_add[0]
            grievance = Grievance(
                id=g_uuid,
                borrower_id=sample_b.id,
                score_id=sample_app.score_id,
                loan_application_id=sample_app.id,
                category="DECISION_APPEAL",
                description="Borrower requested re-appraisal of dairy income following cattle immunization certificate submission.",
                status="OPEN",
                sla_hours=168,
                assigned_to="OFF-001",
                created_at=now - timedelta(days=2),
                due_at=now + timedelta(days=5),
            )
            g_audit = GrievanceAuditLog(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, "credit-tech-ea-g-audit-sample"),
                grievance_id=g_uuid,
                from_status=None,
                to_status="OPEN",
                actor="OFF-001",
                note="Grievance received via Bank Sakhi Sunita Devi; SLA clock initialized (168 hrs).",
                performed_at=now - timedelta(days=2),
            )
            db.add_all([grievance, g_audit])

        await db.commit()
        print("✅ Early Adopter MVP Cohort successfully persisted!")
        print(f"   • Villages: {len(PILOT_VILLAGES)}")
        print(f"   • Borrowers Added: {len(borrowers_to_add)}")
        print(f"   • Scores Generated: {len(scores_to_add)}")
        print(f"   • Applications Underwritten: {len(apps_to_add)}")
        print(f"   • Repayments Logged: {len(repayments_to_add)}")


if __name__ == "__main__":
    asyncio.run(seed_early_adopters())

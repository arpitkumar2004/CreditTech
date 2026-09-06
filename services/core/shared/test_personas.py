"""Canonical Permanent Test Personas & Golden Dataset Definitions for CreditTech.

Provides deterministic, immutable identifiers for personas, villages, and security
tripwires across Cluster Alpha (Chandauli) and Cluster Beta (Mirzapur).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class PersonaAccount:
    id: str
    name: str
    role: str
    branch_or_village: str
    description: str
    auth_headers: dict[str, str] = field(default_factory=dict)


# ── Canonical Persona Accounts ─────────────────────────────────────────────

OFFICER_RAJESH = PersonaAccount(
    id="OFF-001",
    name="Rajesh Kumar",
    role="LOAN_OFFICER",
    branch_or_village="Chandauli Rural Branch (Cluster Alpha)",
    description="Branch loan officer underwriting SHG micro-loans and agri-working capital",
    auth_headers={"X-Officer-Id": "OFF-001", "X-Officer-Role": "LOAN_OFFICER"},
)

OFFICER_VIKRAM = PersonaAccount(
    id="OFF-002",
    name="Vikram Singh",
    role="LOAN_OFFICER",
    branch_or_village="Mirzapur Hill Branch (Cluster Beta)",
    description="Branch loan officer reviewing rain-fed and dryland farm applications",
    auth_headers={"X-Officer-Id": "OFF-002", "X-Officer-Role": "LOAN_OFFICER"},
)

SAKHI_SUNITA = PersonaAccount(
    id="SAKHI-001",
    name="Sunita Devi",
    role="BANK_SAKHI",
    branch_or_village="Tara Jivanpur Village (Cluster Alpha)",
    description="Bank Sakhi field agent capturing SHG thrift data and assisting onboarding",
    auth_headers={"X-Officer-Id": "SAKHI-001", "X-Officer-Role": "BANK_SAKHI"},
)

SAKHI_ANITA = PersonaAccount(
    id="SAKHI-002",
    name="Anita Bai",
    role="BANK_SAKHI",
    branch_or_village="Adalhat Village (Cluster Beta)",
    description="Bank Sakhi field agent operating in rain-fed village cluster",
    auth_headers={"X-Officer-Id": "SAKHI-002", "X-Officer-Role": "BANK_SAKHI"},
)

RISK_PRIYA = PersonaAccount(
    id="RISK-001",
    name="Priya Sharma",
    role="RISK_OFFICER",
    branch_or_village="Institutional Head Office",
    description="Credit risk manager auditing demographic & geographic fairness parity",
    auth_headers={"X-Officer-Id": "RISK-001", "X-Officer-Role": "RISK_OFFICER"},
)

ADMIN_AMIT = PersonaAccount(
    id="ADMIN-001",
    name="Amit Verma",
    role="ADMIN",
    branch_or_village="ML Ops & Systems",
    description="MLOps administrator managing model registry, promotion gates & DR",
    auth_headers={"X-Officer-Id": "ADMIN-001", "X-Officer-Role": "ADMIN"},
)

ALL_STAFF_PERSONAS = [
    OFFICER_RAJESH,
    OFFICER_VIKRAM,
    SAKHI_SUNITA,
    SAKHI_ANITA,
    RISK_PRIYA,
    ADMIN_AMIT,
]


# ── Deterministic Permanent Borrowers & Golden Records ─────────────────────

# Cluster Alpha (Chandauli - Canal Irrigated)
VILLAGE_ALPHA_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
VILLAGE_ALPHA_NAME = "Tara Jivanpur"

BORROWER_RADHIKA_ID = uuid.UUID("00000000-0000-0000-0002-000000000001")
BORROWER_RADHIKA_HEADERS = {"X-Borrower-Id": str(BORROWER_RADHIKA_ID)}
SCORE_RADHIKA_ID = uuid.UUID("00000000-0000-0000-0003-000000000001")
APP_RADHIKA_ID = uuid.UUID("00000000-0000-0000-0004-000000000001")
CONSENT_RADHIKA_ID = uuid.UUID("00000000-0000-0000-0005-000000000001")

BORROWER_SITA_ID = uuid.UUID("00000000-0000-0000-0002-000000000002")
BORROWER_SITA_HEADERS = {"X-Borrower-Id": str(BORROWER_SITA_ID)}
SCORE_SITA_ID = uuid.UUID("00000000-0000-0000-0003-000000000002")
APP_SITA_ID = uuid.UUID("00000000-0000-0000-0004-000000000002")
CONSENT_SITA_ID = uuid.UUID("00000000-0000-0000-0005-000000000002")


# Cluster Beta (Mirzapur - Rain-Fed)
VILLAGE_BETA_ID = uuid.UUID("00000000-0000-0000-0001-000000000002")
VILLAGE_BETA_NAME = "Adalhat Dryland"

BORROWER_RAMU_ID = uuid.UUID("00000000-0000-0000-0002-000000000003")
BORROWER_RAMU_HEADERS = {"X-Borrower-Id": str(BORROWER_RAMU_ID)}
SCORE_RAMU_ID = uuid.UUID("00000000-0000-0000-0003-000000000003")
APP_RAMU_ID = uuid.UUID("00000000-0000-0000-0004-000000000003")
CONSENT_RAMU_ID = uuid.UUID("00000000-0000-0000-0005-000000000003")

BORROWER_MEENA_ID = uuid.UUID("00000000-0000-0000-0002-000000000004")
BORROWER_MEENA_HEADERS = {"X-Borrower-Id": str(BORROWER_MEENA_ID)}
SCORE_MEENA_ID = uuid.UUID("00000000-0000-0000-0003-000000000004")
APP_MEENA_ID = uuid.UUID("00000000-0000-0000-0004-000000000004")
CONSENT_MEENA_ID = uuid.UUID("00000000-0000-0000-0005-000000000004")
GRIEVANCE_MEENA_ID = uuid.UUID("00000000-0000-0000-0006-000000000001")


# ── Security & Authorization Tripwires ─────────────────────────────────────

# Trap 1: Isolated borrower for testing horizontal cross-access violation
TRIPWIRE_BORROWER_ID = uuid.UUID("00000000-0000-0000-0009-000000000099")
TRIPWIRE_BORROWER_HEADERS = {"X-Borrower-Id": str(TRIPWIRE_BORROWER_ID)}
TRIPWIRE_SCORE_ID = uuid.UUID("00000000-0000-0000-0009-000000000098")
TRIPWIRE_CONSENT_ID = uuid.UUID("00000000-0000-0000-0009-000000000097")

# Trap 2: Borrower with revoked consent (scoring must be rejected)
TRIPWIRE_REVOKED_BORROWER_ID = uuid.UUID("00000000-0000-0000-0009-000000000088")
TRIPWIRE_REVOKED_CONSENT_ID = uuid.UUID("00000000-0000-0000-0009-000000000087")

# Trap 3: Borrower with expired consent
TRIPWIRE_EXPIRED_BORROWER_ID = uuid.UUID("00000000-0000-0000-0009-000000000077")
TRIPWIRE_EXPIRED_CONSENT_ID = uuid.UUID("00000000-0000-0000-0009-000000000076")

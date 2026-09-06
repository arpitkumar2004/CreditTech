"""Role-based authentication & authorization guards for CreditTech.

Supports explicit persona segregation:
- BORROWER: Access via X-Borrower-Id
- BANK_SAKHI: Field agent (assisted onboarding & data capture)
- LOAN_OFFICER: Branch underwriting & decisioning
- SUPERVISOR: Branch supervisor & review
- RISK_OFFICER: Institutional portfolio risk & fairness audit
- ADMIN / ML_ENGINEER: Model promotion, policy governance, smoke testing
"""

from __future__ import annotations

from typing import Callable
from fastapi import Header, HTTPException, status

KNOWN_OFFICER_ROLES = {
    "BANK_SAKHI",
    "LOAN_OFFICER",
    "SUPERVISOR",
    "RISK_OFFICER",
    "ADMIN",
    "ML_ENGINEER",
}

ALLOWED_ROLES = {"LOAN_OFFICER", "SUPERVISOR", "ADMIN"}


def require_roles(*allowed_roles: str) -> Callable[[str | None, str | None], str]:
    """Generates a FastAPI dependency enforcing specific role permissions.

    - Missing credentials -> 401 Unauthorized
    - Unknown/unrecognized officer role -> 401 Unauthorized
    - Valid officer role but insufficient privileges -> 403 Forbidden
    """
    normalized_allowed = {r.upper() for r in allowed_roles}

    def _role_checker(
        x_officer_id: str | None = Header(default=None, alias="X-Officer-Id"),
        x_officer_role: str | None = Header(default=None, alias="X-Officer-Role"),
    ) -> str:
        if not x_officer_id or not x_officer_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing officer credentials (X-Officer-Id, X-Officer-Role)",
            )
        role_upper = x_officer_role.strip().upper()
        if role_upper not in KNOWN_OFFICER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unrecognized role '{x_officer_role}'",
            )
        if role_upper not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{x_officer_role}' forbidden from accessing this resource",
            )
        return x_officer_id.strip()

    return _role_checker


KNOWN_ROLES = KNOWN_OFFICER_ROLES | {"BORROWER"}

# Backward-compatible general officer dependency
require_officer = require_roles("LOAN_OFFICER", "SUPERVISOR", "ADMIN", "RISK_OFFICER")

# Specialized persona dependencies
require_credit_officer = require_roles("LOAN_OFFICER", "SUPERVISOR", "ADMIN")
require_risk_officer = require_roles("RISK_OFFICER", "ADMIN", "SUPERVISOR")
require_admin = require_roles("ADMIN", "ML_ENGINEER")
require_any_authenticated = require_roles(*KNOWN_OFFICER_ROLES)

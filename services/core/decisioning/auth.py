"""Minimal officer auth guard for the pilot.

Pilot scope (§20 of the planning doc) is 20-50 named loan officers, not a
public API. Full OIDC/SSO integration is a P6 hardening task. For P4 we
require two headers the RE integration is already expected to send:

    X-Officer-Id:   opaque loan-officer identifier
    X-Officer-Role: LOAN_OFFICER (or SUPERVISOR for future expansions)

Requests without both headers, or with a role we do not recognise, are 401.
This is intentionally simple and easy to swap for real SSO later without
changing the DecisioningService signature.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

ALLOWED_ROLES = {"LOAN_OFFICER", "SUPERVISOR"}


def require_officer(
    x_officer_id: str | None = Header(default=None, alias="X-Officer-Id"),
    x_officer_role: str | None = Header(default=None, alias="X-Officer-Role"),
) -> str:
    if not x_officer_id or not x_officer_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing officer credentials (X-Officer-Id, X-Officer-Role)",
        )
    if x_officer_role.upper() not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Role '{x_officer_role}' not authorized for decisioning",
        )
    return x_officer_id.strip()

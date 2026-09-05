"""P5 — Grievance/appeal channel + SLA + audit + authorization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import Borrower, Grievance, Village

OFFICER_HEADERS = {"X-Officer-Id": "off1", "X-Officer-Role": "LOAN_OFFICER"}


@pytest.fixture
async def borrower(db_session: AsyncSession) -> Borrower:
    v = Village(name="V", site_type="X", state="RJ", district="Hanumangarh")
    db_session.add(v)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="c" * 64,
        name_encrypted="e", phone_encrypted="e",
        village_id=v.id, gender="F", age=30, landholding_band="MARGINAL",
    )
    db_session.add(b)
    await db_session.commit()
    return b


@pytest.mark.asyncio
async def test_grievance_creation_starts_sla_clock(
    client: AsyncClient, borrower: Borrower, db_session: AsyncSession
) -> None:
    r = await client.post(
        "/api/v1/grievances/",
        headers={"X-Borrower-Id": str(borrower.id)},
        json={
            "borrower_id": str(borrower.id),
            "category": "SCORE_DISPUTE",
            "description": "I dispute the score of 45 — my SHG history is strong.",
            "sla_hours": 72,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "OPEN"
    assert body["sla_hours"] == 72
    assert body["is_overdue"] is False
    # Persisted row should have a due_at ~72h after created_at
    g = (await db_session.execute(select(Grievance))).scalar_one()
    delta = g.due_at.replace(tzinfo=UTC) - g.created_at.replace(tzinfo=UTC)
    assert 71 <= delta.total_seconds() / 3600 <= 73


@pytest.mark.asyncio
async def test_grievance_requires_borrower_header(
    client: AsyncClient, borrower: Borrower
) -> None:
    r = await client.post(
        "/api/v1/grievances/",
        json={
            "borrower_id": str(borrower.id),
            "category": "SCORE_DISPUTE",
            "description": "no header",
        },
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_grievance_borrower_id_must_match_header(
    client: AsyncClient, borrower: Borrower
) -> None:
    r = await client.post(
        "/api/v1/grievances/",
        headers={"X-Borrower-Id": "00000000-0000-0000-0000-000000000000"},
        json={
            "borrower_id": str(borrower.id),
            "category": "SCORE_DISPUTE",
            "description": "mismatch",
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_grievance_status_transition_and_audit(
    client: AsyncClient, borrower: Borrower
) -> None:
    r = await client.post(
        "/api/v1/grievances/",
        headers={"X-Borrower-Id": str(borrower.id)},
        json={
            "borrower_id": str(borrower.id),
            "category": "DECISION_APPEAL",
            "description": "Please re-review my decision.",
        },
    )
    gid = r.json()["id"]

    # Officer moves OPEN -> IN_REVIEW
    r2 = await client.patch(
        f"/api/v1/grievances/{gid}",
        headers=OFFICER_HEADERS,
        json={"status": "IN_REVIEW", "note": "Assigning to review", "assigned_to": "off1"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "IN_REVIEW"

    # IN_REVIEW -> RESOLVED
    r3 = await client.patch(
        f"/api/v1/grievances/{gid}",
        headers=OFFICER_HEADERS,
        json={"status": "RESOLVED", "resolution_notes": "Updated after re-review"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "RESOLVED"
    assert r3.json()["resolved_at"] is not None

    # Invalid transition: RESOLVED -> IN_REVIEW is not allowed
    r_bad = await client.patch(
        f"/api/v1/grievances/{gid}",
        headers=OFFICER_HEADERS,
        json={"status": "IN_REVIEW"},
    )
    assert r_bad.status_code == 400

    # Audit trail should have 3 rows (OPEN, IN_REVIEW, RESOLVED)
    audit = await client.get(f"/api/v1/grievances/{gid}/audit", headers=OFFICER_HEADERS)
    assert audit.status_code == 200
    entries = audit.json()
    assert [e["to_status"] for e in entries] == ["OPEN", "IN_REVIEW", "RESOLVED"]


@pytest.mark.asyncio
async def test_grievance_sla_overdue_and_auto_escalate(
    client: AsyncClient, borrower: Borrower, db_session: AsyncSession
) -> None:
    # Insert directly with a past due_at so SLA is exceeded
    g = Grievance(
        borrower_id=borrower.id,
        category="DATA_ACCURACY",
        description="Wrong crop area recorded.",
        status="OPEN",
        sla_hours=1,
        due_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db_session.add(g)
    await db_session.commit()

    listed = await client.get(
        "/api/v1/grievances/?overdue_only=true", headers=OFFICER_HEADERS
    )
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]["is_overdue"] is True

    esc = await client.post("/api/v1/grievances/escalate-overdue", headers=OFFICER_HEADERS)
    assert esc.status_code == 200
    assert esc.json()["escalated"] == 1

    # Now escalated, no longer OPEN
    r = await client.get(f"/api/v1/grievances/{g.id}", headers=OFFICER_HEADERS)
    assert r.json()["status"] == "ESCALATED"


@pytest.mark.asyncio
async def test_grievance_list_requires_officer(client: AsyncClient) -> None:
    r = await client.get("/api/v1/grievances/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_borrower_can_view_own_grievance(
    client: AsyncClient, borrower: Borrower
) -> None:
    r = await client.post(
        "/api/v1/grievances/",
        headers={"X-Borrower-Id": str(borrower.id)},
        json={
            "borrower_id": str(borrower.id),
            "category": "CONSENT_ISSUE",
            "description": "Please revoke my previous consent.",
        },
    )
    gid = r.json()["id"]
    # Borrower fetches their own grievance
    r2 = await client.get(
        f"/api/v1/grievances/{gid}", headers={"X-Borrower-Id": str(borrower.id)}
    )
    assert r2.status_code == 200
    # Different borrower cannot access
    r3 = await client.get(
        f"/api/v1/grievances/{gid}",
        headers={"X-Borrower-Id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r3.status_code == 401

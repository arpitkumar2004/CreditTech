"""P4.6 — Officer decisioning API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.core.shared.models import (
    Borrower,
    FeatureSnapshot,
    ReasonCode,
    Score,
    Village,
)

OFFICER_HEADERS = {"X-Officer-Id": "officer_007", "X-Officer-Role": "LOAN_OFFICER"}


@pytest.fixture
async def high_risk_score(db_session: AsyncSession) -> Score:
    """A score whose band is HIGH_RISK -> model recommendation REJECT."""
    village = Village(
        name="V", site_type="RAINFED", state="MP", district="Sehore"
    )
    db_session.add(village)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="a" * 64,
        name_encrypted="enc",
        phone_encrypted="enc",
        village_id=village.id,
        gender="F",
        age=28,
        landholding_band="MARGINAL",
    )
    db_session.add(b)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id,
        feature_version="v1.0.0",
        features_json={"land_holding_acres": 0.3},
        season_tag="KHARIF",
        sources_used=["SHG_FPO"],
    )
    db_session.add(snap)
    await db_session.flush()
    s = Score(
        borrower_id=b.id,
        feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic",
        score=35.0,
        confidence_lower=25.0,
        confidence_upper=45.0,
        sources_used=["SHG_FPO"],
    )
    db_session.add(s)
    await db_session.flush()
    db_session.add(
        ReasonCode(
            score_id=s.id,
            rank=1,
            feature_name="land_holding_acres",
            direction="NEGATIVE",
            shap_value=-0.4,
            localized_text_en="Small landholding limits income capacity",
            localized_text_hi="छोटी भूमि आय क्षमता को सीमित करती है",
        )
    )
    await db_session.flush()
    return s


@pytest.fixture
async def good_score(db_session: AsyncSession) -> Score:
    village = Village(
        name="V2", site_type="IRRIGATED", state="RJ", district="Hanumangarh"
    )
    db_session.add(village)
    await db_session.flush()
    b = Borrower(
        aadhaar_ref_hash="b" * 64,
        name_encrypted="enc",
        phone_encrypted="enc",
        village_id=village.id,
        gender="M",
        age=45,
        landholding_band="SMALL",
    )
    db_session.add(b)
    await db_session.flush()
    snap = FeatureSnapshot(
        borrower_id=b.id,
        feature_version="v1.0.0",
        features_json={"shg_repayment_rate": 0.98},
        season_tag="RABI",
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO"],
    )
    db_session.add(snap)
    await db_session.flush()
    s = Score(
        borrower_id=b.id,
        feature_snapshot_id=snap.id,
        model_version="v1.0.0-logistic",
        score=72.0,
        confidence_lower=65.0,
        confidence_upper=79.0,
        sources_used=["AA", "GEOSPATIAL", "SHG_FPO"],
    )
    db_session.add(s)
    await db_session.flush()
    db_session.add(
        ReasonCode(
            score_id=s.id,
            rank=1,
            feature_name="shg_repayment_rate",
            direction="POSITIVE",
            shap_value=0.15,
            localized_text_en="Strong SHG repayment history",
            localized_text_hi="SHG चुकौती इतिहास मजबूत",
        )
    )
    await db_session.flush()
    return s


# ── review payload ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_review_payload_contains_score_reasons_evidence(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.get(
        f"/api/v1/decision/review/{good_score.id}", headers=OFFICER_HEADERS
    )
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 72.0
    assert body["score_band"] == "GOOD"
    assert body["model_recommendation"] == "APPROVE"
    assert body["model_version"] == "v1.0.0-logistic"
    assert body["feature_version"]  # not empty
    assert body["confidence_lower"] == 65.0 and body["confidence_upper"] == 79.0
    assert body["reason_codes"][0]["localized_text_hi"]
    # sources_used excludes BUREAU -> partial_data must be True.
    assert body["partial_data"] is True
    statuses = {s["source"]: s["available"] for s in body["source_status"]}
    assert statuses["BUREAU"] is False
    assert statuses["AA"] is True


@pytest.mark.asyncio
async def test_review_requires_officer_auth(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.get(f"/api/v1/decision/review/{good_score.id}")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_review_rejects_unknown_role(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.get(
        f"/api/v1/decision/review/{good_score.id}",
        headers={"X-Officer-Id": "x", "X-Officer-Role": "BORROWER"},
    )
    assert r.status_code == 401


# ── decision capture ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_matches_recommendation_no_override(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(good_score.id), "decision": "APPROVED"},
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["decision"] == "APPROVED"
    assert body["model_recommendation"] == "APPROVE"
    assert body["is_override"] is False
    assert body["override_reason"] is None


@pytest.mark.asyncio
async def test_reject_on_good_score_requires_override_reason(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(good_score.id), "decision": "REJECTED"},
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 400
    assert "override_reason" in r.json()["detail"]


@pytest.mark.asyncio
async def test_more_info_is_valid(client: AsyncClient, good_score: Score) -> None:
    r = await client.post(
        "/api/v1/decision/",
        json={
            "score_id": str(good_score.id),
            "decision": "MORE_INFO_REQUIRED",
            "override_reason": "Need updated land record",
        },
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 201
    assert r.json()["is_override"] is True


@pytest.mark.asyncio
async def test_override_reason_rejected_when_matching_recommendation(
    client: AsyncClient, high_risk_score: Score
) -> None:
    # High risk -> REJECT recommendation. Officer also REJECTS -> no override,
    # supplying an override_reason should be an error.
    r = await client.post(
        "/api/v1/decision/",
        json={
            "score_id": str(high_risk_score.id),
            "decision": "REJECTED",
            "override_reason": "shouldn't be here",
        },
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 400
    assert "must be empty" in r.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_decision_rejected(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(good_score.id), "decision": "MAYBE"},
        headers=OFFICER_HEADERS,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_decision_requires_officer_auth(
    client: AsyncClient, good_score: Score
) -> None:
    r = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(good_score.id), "decision": "APPROVED"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_audit_trail_is_append_only(
    client: AsyncClient, good_score: Score
) -> None:
    # Officer records more_info first, then later approves.
    r1 = await client.post(
        "/api/v1/decision/",
        json={
            "score_id": str(good_score.id),
            "decision": "MORE_INFO_REQUIRED",
            "override_reason": "Ask borrower for latest utility bill",
        },
        headers=OFFICER_HEADERS,
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/decision/",
        json={"score_id": str(good_score.id), "decision": "APPROVED"},
        headers=OFFICER_HEADERS,
    )
    assert r2.status_code == 201

    audit = await client.get(
        f"/api/v1/decision/audit/{good_score.id}", headers=OFFICER_HEADERS
    )
    assert audit.status_code == 200
    entries = audit.json()
    assert len(entries) == 2
    assert entries[0]["decision"] == "MORE_INFO_REQUIRED"
    assert entries[1]["decision"] == "APPROVED"
    assert entries[0]["id"] != entries[1]["id"]

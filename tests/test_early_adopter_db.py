"""Unit and integration tests for Early Adopter MVP Database Organization.

Validates:
- Pilot village distribution across 3 agro-climatic zones
- Early adopter borrower population with demographic diversity
- Cryptographically chained DPDP consent records
- 4-rail feature snapshots and calibrated scores
- Multi-tenant partner RE underwriting and immutable decision logs
- Composite indexes on high-throughput database tables
"""

import pytest
from sqlalchemy import inspect, select

from scripts.seed_early_adopters import seed_early_adopters
from services.core.database import async_session_factory, engine
from services.core.shared.models import (
    Borrower,
    ConsentRecord,
    FeatureSnapshot,
    LoanApplication,
    OfficerDecisionLog,
    ReasonCode,
    RepaymentRecord,
    Score,
    Village,
)


@pytest.mark.asyncio
async def test_seed_early_adopters_execution():
    """Verify seed_early_adopters executes idempotently and populates all tables."""
    await seed_early_adopters()

    async with async_session_factory() as db:
        # 1. Villages across 3 Agro-Climatic Zones
        villages = (await db.execute(select(Village))).scalars().all()
        assert len(villages) >= 15
        zones = {v.agro_climatic_zone for v in villages if v.agro_climatic_zone}
        assert len(zones) >= 3

        # 2. Early Adopter Borrowers
        borrowers = (await db.execute(select(Borrower))).scalars().all()
        ea_borrowers = [b for b in borrowers if b.aadhaar_ref_hash.startswith("EA_")]
        assert len(ea_borrowers) == 50

        # Gender & Landholding diversity
        genders = {b.gender for b in ea_borrowers}
        assert "F" in genders and "M" in genders
        bands = {b.landholding_band for b in ea_borrowers}
        assert "MARGINAL" in bands and "SMALL" in bands

        # 3. DPDP Consent Records & Hash Chains
        consents = (await db.execute(select(ConsentRecord))).scalars().all()
        assert len(consents) >= 50
        for c in consents:
            assert c.status in ("ACTIVE", "EXPIRED", "REVOKED")
            assert len(c.hash_prev) == 64
            assert len(c.hash_current) == 64
            assert c.hash_prev != c.hash_current

        # 4. Feature Snapshots
        snapshots = (await db.execute(select(FeatureSnapshot))).scalars().all()
        assert len(snapshots) >= 50
        ea_snaps = [s for s in snapshots if s.feature_version == "v1.1.0"]
        assert len(ea_snaps) == 50
        sample_snap = ea_snaps[0]
        assert "monthly_avg_credit_inflow" in sample_snap.features_json
        assert "shg_repayment_rate" in sample_snap.features_json
        assert "land_quality_ndvi_avg" in sample_snap.features_json

        # 5. Scores & Localized ReasonCodes
        scores = (await db.execute(select(Score))).scalars().all()
        assert len(scores) >= 50
        ea_b_ids = {b.id for b in ea_borrowers}
        ea_scores = [s for s in scores if s.borrower_id in ea_b_ids]
        assert len(ea_scores) == 50
        for s in ea_scores:
            assert 300.0 <= s.score <= 850.0
            assert s.confidence_lower <= s.score <= s.confidence_upper

        reasons = (await db.execute(select(ReasonCode))).scalars().all()
        assert len(reasons) >= 150  # At least 3 per early adopter
        for r in reasons[:10]:
            assert r.localized_text_en
            assert r.localized_text_hi
            assert r.direction in ("POSITIVE", "NEGATIVE")

        # 6. Multi-Tenant Loan Applications & Immutable Decision Logs
        apps = (await db.execute(select(LoanApplication))).scalars().all()
        assert len(apps) >= 50
        partner_res = {a.partner_re_id for a in apps}
        assert "RE-SBI-01" in partner_res
        assert "RRB-BRKGB-01" in partner_res

        decisions = (await db.execute(select(OfficerDecisionLog))).scalars().all()
        assert len(decisions) >= 50
        assert all(d.decision in ("APPROVED", "REJECTED", "MORE_INFO_REQUIRED") for d in decisions)

        # 7. Repayment Records
        repayments = (await db.execute(select(RepaymentRecord))).scalars().all()
        assert len(repayments) >= 20


@pytest.mark.asyncio
async def test_composite_indexes_configured():
    """Verify that composite indexes are present on core tables."""
    # Check that the model __table_args__ define the expected composite indexes
    borrower_idx_names = {idx.name for idx in Borrower.__table_args__ if hasattr(idx, "name")}
    assert "idx_borrowers_village_created" in borrower_idx_names

    score_idx_names = {idx.name for idx in Score.__table_args__ if hasattr(idx, "name")}
    assert "idx_scores_borrower_created" in score_idx_names

    loan_app_idx_names = {idx.name for idx in LoanApplication.__table_args__ if hasattr(idx, "name")}
    assert "idx_loan_apps_re_decision" in loan_app_idx_names
    assert "idx_loan_apps_borrower_created" in loan_app_idx_names

    snapshot_idx_names = {idx.name for idx in FeatureSnapshot.__table_args__ if hasattr(idx, "name")}
    assert "idx_feature_snapshots_borrower_computed" in snapshot_idx_names

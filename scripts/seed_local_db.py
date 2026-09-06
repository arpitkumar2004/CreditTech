"""Script to initialize and seed local SQLite database with realistic data."""

import asyncio
import hashlib
import json
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
from services.core.database import Base, async_session_factory, engine, init_db
from services.core.shared.models import (
    Borrower,
    ConsentAuditLog,
    ConsentRecord,
    FairnessAuditLog,
    FeatureSnapshot,
    Grievance,
    GrievanceAuditLog,
    LoanApplication,
    OfficerDecisionLog,
    ReasonCode,
    Score,
    Village,
)

settings = get_settings()


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


async def seed() -> None:
    print("🌱 Initializing local database schema and triggers...")
    await init_db()

    async with async_session_factory() as db:
        # Check if already seeded
        existing_v = (await db.execute(select(Village))).scalars().first()
        if existing_v is not None:
            print("ℹ️ Database already seeded. Skipping.")
            return

        print("🏡 Seeding pilot village...")
        village = Village(
            id=uuid.uuid4(),
            name="Sangaria Pilot Village",
            site_type="IRRIGATED_COTTON",
            state="Rajasthan",
            district="Hanumangarh",
            block="Sangaria",
        )
        db.add(village)
        await db.flush()

        borrower_specs = [
            {
                "name": "Sunita Devi",
                "phone": "9876543210",
                "gender": "F",
                "age": 34,
                "landholding": "MARGINAL",
                "score_100": 78.4,
                "score_900": 745,
                "band": "GOOD",
                "recommendation": "APPROVE",
                "amount": 50000.0,
                "tenure": 12,
                "purpose": "Kharif Cotton Seeds & Bio-fertilizers",
                "officer_decision": "PENDING",
                "reasons": [
                    ("shg_thrift_regularity_6m", "POS", "Consistent 100% attendance in SHG meetings over 6 months", "पिछले 6 महीनों में एसएचजी बैठकों में 100% नियमित उपस्थिति", 0.35),
                    ("aa_avg_balance_6m", "POS", "Healthy operating account balance with regular UPI inflows", "नियमित यूपीआई लेनदेन के साथ खाते में स्थिर औसत शेष", 0.28),
                    ("ndvi_avg", "POS", "Favorable vegetation index on farm coordinates indicating crop health", "खेत निर्देशांक पर फसल स्वास्थ्य का अच्छा सूचकांक", 0.19),
                    ("pm_kisan_regularity", "POS", "Regular PM-Kisan installment credits verified on Aadhaar account", "आधार खाते में पीएम-किसान किस्त का नियमित क्रेडिट", 0.12),
                ],
            },
            {
                "name": "Ramesh Chandra",
                "phone": "9823456789",
                "gender": "M",
                "age": 42,
                "landholding": "SMALL",
                "score_100": 64.2,
                "score_900": 620,
                "band": "MODERATE",
                "recommendation": "REVIEW",
                "amount": 75000.0,
                "tenure": 24,
                "purpose": "Drip Irrigation Pipe Installation",
                "officer_decision": "PENDING",
                "reasons": [
                    ("aa_avg_balance_6m", "POS", "Regular agricultural income deposits via PACS", "पीएसीएस के माध्यम से नियमित कृषि आय जमा", 0.22),
                    ("shg_thrift_regularity_6m", "POS", "Active member of Kisan Vikas Mandal", "किसान विकास मंडल के सक्रिय सदस्य", 0.15),
                    ("rainfall_dev", "NEG", "Rainfall deviation -18% below seasonal average", "मौसमी औसत से वर्षा में -18% की कमी", -0.25),
                    ("kcc_utilization", "NEG", "KCC credit line utilization above 80%", "केसीसी क्रेडिट लाइन का उपयोग 80% से अधिक", -0.18),
                ],
            },
            {
                "name": "Anita Meena",
                "phone": "9811223344",
                "gender": "F",
                "age": 29,
                "landholding": "LANDLESS",
                "score_100": 82.5,
                "score_900": 780,
                "band": "EXCELLENT",
                "recommendation": "APPROVE",
                "amount": 35000.0,
                "tenure": 12,
                "purpose": "Dairy Animal Purchase (Gir Cow)",
                "officer_decision": "APPROVED",
                "reasons": [
                    ("shg_repayment_rate", "POS", "100% on-time repayment history across 2 previous SHG internal loans", "पिछले 2 आंतरिक ऋणों में 100% समय पर पुनर्भुगतान", 0.42),
                    ("shg_thrift_regularity_6m", "POS", "Exemplary thrift savings record over 3 years", "3 वर्षों में उत्कृष्ट बचत का रिकॉर्ड", 0.31),
                    ("aa_credit_inflow_cv", "POS", "Steady daily dairy cooperative milk sales deposits", "डेयरी सहकारी दूध बिक्री से स्थिर दैनिक आय जमा", 0.24),
                ],
            },
            {
                "name": "Balwant Singh",
                "phone": "9898765432",
                "gender": "M",
                "age": 51,
                "landholding": "MEDIUM",
                "score_100": 41.0,
                "score_900": 490,
                "band": "HIGH_RISK",
                "recommendation": "REJECT",
                "amount": 150000.0,
                "tenure": 36,
                "purpose": "Tractor Attachment Purchase",
                "officer_decision": "REJECTED",
                "reasons": [
                    ("bureau_overdue_loans", "NEG", "Overdue loan reported on CIC bureau file", "सीआईसी ब्यूरो फाइल पर अतिदेय ऋण दर्ज", -0.45),
                    ("ndvi_trend", "NEG", "Negative crop vigor trend detected over previous 2 cycles", "पिछले 2 चक्रों में फसल स्वास्थ्य में गिरावट", -0.28),
                    ("aa_avg_balance_6m", "NEG", "Frequent negative balance and zero savings cushion", "अक्सर न्यूनतम शेष और कम बचत कुशन", -0.22),
                ],
            },
            {
                "name": "Kavita Sharma",
                "phone": "9871122334",
                "gender": "F",
                "age": 38,
                "landholding": "MARGINAL",
                "score_100": 71.0,
                "score_900": 690,
                "band": "GOOD",
                "recommendation": "APPROVE",
                "amount": 40000.0,
                "tenure": 12,
                "purpose": "Organic Mustard Farming Supplies",
                "officer_decision": "APPROVED",
                "reasons": [
                    ("shg_thrift_regularity_6m", "POS", "Active SHG leadership and flawless savings records", "एसएचजी में सक्रिय नेतृत्व और त्रुटिहीन बचत रिकॉर्ड", 0.30),
                    ("ndvi_avg", "POS", "Good vegetation vigor in mustard sowing zone", "सरसों बुवाई क्षेत्र में अच्छा वनस्पति स्वास्थ्य", 0.26),
                    ("pm_kisan_regularity", "POS", "Verified PM-Kisan beneficiary", "सत्यापित पीएम-किसान लाभार्थी", 0.15),
                ],
            },
        ]

        now = datetime.now(UTC)
        print("👥 Seeding borrowers, consents, scores, and applications...")

        for i, spec in enumerate(borrower_specs):
            b_id = uuid.uuid4()
            aadhaar_hash = hashlib.sha256(f"aadhaar_{i}_{spec['phone']}".encode()).hexdigest()
            name_encrypted = spec["name"]
            phone_encrypted = spec["phone"]

            borrower = Borrower(
                id=b_id,
                village_id=village.id,
                aadhaar_ref_hash=aadhaar_hash,
                name_encrypted=name_encrypted,
                phone_encrypted=phone_encrypted,
                gender=spec["gender"],
                age=spec["age"],
                landholding_band=spec["landholding"],
            )
            db.add(borrower)
            await db.flush()

            # Consent record
            gen_hash = _compute_genesis_hash(b_id)
            c_hash = _compute_consent_hash(
                borrower_id=b_id,
                purpose="credit_scoring",
                data_sources=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
                issued_at=now - timedelta(days=5),
                expires_at=now + timedelta(days=360),
                status="ACTIVE",
                prev_hash=gen_hash,
            )
            consent = ConsentRecord(
                id=uuid.uuid4(),
                borrower_id=b_id,
                purpose="credit_scoring",
                consent_mode="bank_sakhi_assisted",
                scope_description_en="Consent to pull AA, geospatial, and SHG data for credit assessment",
                data_sources=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
                status="ACTIVE",
                issued_at=now - timedelta(days=5),
                expires_at=now + timedelta(days=360),
                hash_prev=gen_hash,
                hash_current=c_hash,
                created_by="sakhi:SK-014",
            )
            db.add(consent)

            # Feature Snapshot
            feat_snap = FeatureSnapshot(
                id=uuid.uuid4(),
                borrower_id=b_id,
                feature_version="v1.0.0",
                season_tag="KHARIF",
                sources_used=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
                features_json={
                    "shg_thrift_regularity_6m": 0.95,
                    "shg_meeting_attendance_6m": 0.90,
                    "shg_repayment_rate": 1.0,
                    "aa_avg_balance_6m": 12500.0,
                    "aa_credit_inflow_cv": 0.35,
                    "aa_avg_credit_inflow": 18000.0,
                    "upi_regularity": 0.85,
                    "pm_kisan_regularity": 1.0,
                    "ndvi_avg": 0.68,
                    "ndvi_trend": 0.05,
                    "rainfall_dev": -4.2,
                    "irrigation_detected": True,
                    "bureau_active_loans": 0,
                    "bureau_overdue_loans": 0,
                    "bureau_score": 680,
                },
                computed_at=now - timedelta(hours=6),
            )
            db.add(feat_snap)
            await db.flush()

            # Score
            score_row = Score(
                id=uuid.uuid4(),
                borrower_id=b_id,
                feature_snapshot_id=feat_snap.id,
                score=spec["score_100"],
                confidence_lower=spec["score_100"] - 4.5,
                confidence_upper=spec["score_100"] + 4.5,
                model_version="v1.0.0-logistic",
                sources_used=["AA", "GEOSPATIAL", "SHG_FPO", "BUREAU"],
                generated_at=now - timedelta(hours=5),
            )
            db.add(score_row)
            await db.flush()

            # Reason codes
            for rank, (feat_name, dir_short, en_text, hi_text, shap) in enumerate(spec["reasons"], start=1):
                rc = ReasonCode(
                    id=uuid.uuid4(),
                    score_id=score_row.id,
                    rank=rank,
                    feature_name=feat_name,
                    direction="POSITIVE" if dir_short == "POS" else "NEGATIVE",
                    localized_text_en=en_text,
                    localized_text_hi=hi_text,
                    shap_value=shap,
                )
                db.add(rc)

            # Loan Application
            loan_app = LoanApplication(
                id=uuid.uuid4(),
                borrower_id=b_id,
                score_id=score_row.id,
                partner_re_id="RE-SBI-PILOT-01",
                requested_amount=spec["amount"],
                requested_tenure_months=spec["tenure"],
                purpose=spec["purpose"],
                officer_decision=None if spec["officer_decision"] == "PENDING" else spec["officer_decision"],
                override_reason="Strong local agricultural cooperative backing" if spec["officer_decision"] == "APPROVED" and spec["recommendation"] != "APPROVE" else None,
                decided_at=now - timedelta(hours=1) if spec["officer_decision"] != "PENDING" else None,
            )
            db.add(loan_app)
            await db.flush()

            if spec["officer_decision"] != "PENDING":
                decision_log = OfficerDecisionLog(
                    id=uuid.uuid4(),
                    loan_application_id=loan_app.id,
                    score_id=score_row.id,
                    officer_id="OFF-001",
                    decision=spec["officer_decision"],
                    model_recommendation=spec["recommendation"],
                    is_override=False,
                    override_reason=None,
                    model_score_at_decision=spec["score_100"],
                    model_version_at_decision="v1.0.0-logistic",
                    feature_version_at_decision="v1.0.0",
                    created_at=now - timedelta(hours=1),
                )
                db.add(decision_log)

        # Seed sample Grievance
        print("⚖️ Seeding grievances and audit trail...")
        first_b = (await db.execute(select(Borrower))).scalars().first()
        if first_b:
            grv = Grievance(
                id=uuid.uuid4(),
                borrower_id=first_b.id,
                category="DATA_ACCURACY",
                description="Applicant requested review of PM-Kisan bank credit records following branch IFSC update",
                status="OPEN",
                sla_hours=48,
                due_at=now + timedelta(hours=36),
                created_at=now - timedelta(hours=12),
            )
            db.add(grv)
            await db.flush()

            audit = GrievanceAuditLog(
                id=uuid.uuid4(),
                grievance_id=grv.id,
                from_status="OPEN",
                to_status="OPEN",
                actor="system",
                note="Ticket auto-triaged and assigned to field officer",
                performed_at=now - timedelta(hours=12),
            )
            db.add(audit)

        # Seed Fairness Audit record
        print("📊 Seeding initial fairness audit snapshot...")
        fairness_records = [
            FairnessAuditLog(
                id=uuid.uuid4(),
                period="2026-W35",
                dimension="GENDER",
                group_value="F",
                approval_rate=0.75,
                sample_size=12,
                override_rate=0.08,
                status="OK",
                computed_at=now - timedelta(days=2),
            ),
            FairnessAuditLog(
                id=uuid.uuid4(),
                period="2026-W35",
                dimension="GENDER",
                group_value="M",
                approval_rate=0.72,
                sample_size=18,
                override_rate=0.11,
                status="OK",
                computed_at=now - timedelta(days=2),
            ),
            FairnessAuditLog(
                id=uuid.uuid4(),
                period="2026-W35",
                dimension="LANDHOLDING",
                group_value="MARGINAL",
                approval_rate=0.70,
                sample_size=14,
                override_rate=0.07,
                status="OK",
                computed_at=now - timedelta(days=2),
            ),
            FairnessAuditLog(
                id=uuid.uuid4(),
                period="2026-W35",
                dimension="LANDHOLDING",
                group_value="SMALL",
                approval_rate=0.78,
                sample_size=16,
                override_rate=0.06,
                status="OK",
                computed_at=now - timedelta(days=2),
            ),
        ]
        for fr in fairness_records:
            db.add(fr)

        await db.commit()
        print("✅ Local database successfully seeded with pilot data!")


if __name__ == "__main__":
    asyncio.run(seed())

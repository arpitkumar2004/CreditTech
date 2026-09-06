"""Verify all live API endpoints against seeded credittech.db."""

import asyncio
import json
import sys
from httpx import ASGITransport, AsyncClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.core.main import app

AUTH_HEADERS = {
    "X-Officer-Id": "OFF-001",
    "X-Officer-Role": "LOAN_OFFICER",
}


async def test_live_stack():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("=== 1. Testing GET /api/v1/decision/applications ===")
        res = await client.get("/api/v1/decision/applications", headers=AUTH_HEADERS)
        print(f"Status: {res.status_code}")
        apps = res.json()
        print(f"Applications count: {len(apps)}")
        assert res.status_code == 200 and len(apps) > 0, "Applications list failed"
        first_app = apps[0]
        print(f"First app: {first_app['borrower_name']} ({first_app['village']}) - Score: {first_app['score_900']} ({first_app['band']}) - Rec: {first_app['model_recommendation']}")

        print("\n=== 2. Testing GET /api/v1/decision/applications/{id} ===")
        res_detail = await client.get(f"/api/v1/decision/applications/{first_app['id']}", headers=AUTH_HEADERS)
        print(f"Status: {res_detail.status_code}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        print(f"Review Pack: score={detail['score']}, reason codes={len(detail['reason_codes'])}")
        for rc in detail['reason_codes'][:2]:
            print(f"  - [{rc['direction']}] {rc['feature_name']}: {rc['localized_text_en']}")

        print("\n=== 3. Testing GET /api/v1/dashboard/portfolio ===")
        res_portfolio = await client.get("/api/v1/dashboard/portfolio", headers=AUTH_HEADERS)
        print(f"Status: {res_portfolio.status_code}")
        assert res_portfolio.status_code == 200
        port = res_portfolio.json()
        print(f"Portfolio metrics: borrowers={port['borrowers']}, approved={port['applications_approved']}, pending={port['applications_pending']}, disbursement=INR {port['disbursed_amount_approved']:,.2f}")

        print("\n=== 4. Testing GET /api/v1/dashboard/fairness ===")
        res_fairness = await client.get("/api/v1/dashboard/fairness", headers=AUTH_HEADERS)
        print(f"Status: {res_fairness.status_code}")
        assert res_fairness.status_code == 200
        fair = res_fairness.json()
        print(f"Fairness period: {fair['period']}, rows={len(fair['rows'])}")

        print("\n=== 5. Testing GET /api/v1/grievances/ ===")
        res_grv = await client.get("/api/v1/grievances/", headers=AUTH_HEADERS)
        print(f"Status: {res_grv.status_code}")
        assert res_grv.status_code == 200
        grvs = res_grv.json()
        print(f"Grievances count: {len(grvs)}")
        if grvs:
            print(f"  First grievance: [{grvs[0]['category']}] {grvs[0]['description']} (Status: {grvs[0]['status']})")

        print("\n=== 6. Testing GET /api/v1/admin/models ===")
        res_models = await client.get("/api/v1/admin/models", headers=AUTH_HEADERS)
        print(f"Status: {res_models.status_code}")
        assert res_models.status_code == 200
        models = res_models.json()
        print(f"Models registered: {len(models)}")
        for m in models:
            print(f"  Model {m['model_version']} ({m['promotion_status']}) - AUC: {m['metrics']['auc']}, Gini: {m['metrics']['gini']}")

        print("\n=== 7. Testing POST /api/v1/decision/ (Officer Decision & Override) ===")
        pending_app = next((a for a in apps if a['decision'] == "PENDING"), apps[0])
        score_id = pending_app['score_id']
        decision_payload = {
            "score_id": score_id,
            "decision": "APPROVED",
            "override_reason": "Applicant has demonstrated seasonal repayment track record in local mandi." if pending_app['model_recommendation'] != "APPROVE" else None,
            "officer_notes": "Officer verified land coordinates and village cooperative endorsement.",
        }
        res_dec = await client.post("/api/v1/decision/", json=decision_payload, headers=AUTH_HEADERS)
        print(f"Status: {res_dec.status_code}")
        assert res_dec.status_code == 201
        dec_result = res_dec.json()
        print(f"Recorded decision: {dec_result['decision']} (Override: {dec_result['is_override']}) by {dec_result['officer_id']}")

        print("\n=== 8. Testing GET /api/v1/admin/fairness/manifest ===")
        res_manifest = await client.get("/api/v1/admin/fairness/manifest", headers=AUTH_HEADERS)
        print(f"Status: {res_manifest.status_code}")
        assert res_manifest.status_code == 200
        manifest_data = res_manifest.json()
        print(f"Manifest hash: {manifest_data['manifest_hash'][:16]}..., version: {manifest_data['manifest']['version']}")

        print("\n[SUCCESS] ALL ENDPOINTS RESPONDED WITH LIVE DATA FROM LOCAL SQLite DB!")


if __name__ == "__main__":
    asyncio.run(test_live_stack())

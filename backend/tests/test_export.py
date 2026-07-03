import pytest
from httpx import AsyncClient
from models.mongo_models import get_db

@pytest.mark.anyio
async def test_exports(client: AsyncClient):
    db = await get_db()
    
    # Create workspace
    ws_payload = {"name": "Test Export Workspace"}
    response = await client.post("/api/workspaces", json=ws_payload)
    workspace_id = response.json()["_id"]

    try:
        # Seed dummy score
        await db.bid_scores.insert_one({
            "workspace_id": workspace_id,
            "overall_score": 0.74,
            "win_probability": 0.74,
            "go_no_go": "GO",
            "go_no_go_reasoning": "Reasoning details.",
            "confidence_level": "HIGH",
            "score_breakdown": {
                "compliance_completeness": 80.0,
                "domain_experience_match": 75.0,
                "budget_alignment": 90.0,
                "client_relationship": 50.0,
                "competition_risk": 60.0,
                "technical_complexity_fit": 80.0,
                "timeline_feasibility": 75.0
            },
            "feature_importance": {
                "budget_alignment": 0.25,
                "compliance_score": 0.22,
                "domain_experience_score": 0.20
            }
        })

        # Seed requirement and compliance item
        req_id = "test_req_export"
        await db.requirements.insert_one({
            "_id": req_id,
            "workspace_id": workspace_id,
            "section": "Section 2",
            "requirement_text": "Clause to export.",
            "is_mandatory": True,
            "category": "technical",
            "cluster_id": 0
        })

        await db.compliance_items.insert_one({
            "workspace_id": workspace_id,
            "requirement_id": req_id,
            "status": "pass",
            "final_score": 1.0
        })

        # Seed section
        await db.proposal_sections.insert_one({
            "workspace_id": workspace_id,
            "section_title": "Section Title",
            "ai_draft": "This is AI drafted content.",
            "status": "draft",
            "order_index": 0
        })

        # 1. Test DOCX export
        response = await client.get(f"/api/workspaces/{workspace_id}/export/proposal.docx")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # 2. Test XLSX export
        response = await client.get(f"/api/workspaces/{workspace_id}/export/compliance.xlsx")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # 3. Test PDF export
        response = await client.get(f"/api/workspaces/{workspace_id}/export/scorecard.pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # 4. Test ZIP export
        response = await client.get(f"/api/workspaces/{workspace_id}/export/all.zip")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-zip-compressed"

    finally:
        await db.workspaces.delete_one({"_id": workspace_id})
        await db.bid_scores.delete_many({"workspace_id": workspace_id})
        await db.requirements.delete_many({"workspace_id": workspace_id})
        await db.compliance_items.delete_many({"workspace_id": workspace_id})
        await db.proposal_sections.delete_many({"workspace_id": workspace_id})

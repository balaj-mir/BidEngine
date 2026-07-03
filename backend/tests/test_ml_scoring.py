import pytest
from httpx import AsyncClient
from models.mongo_models import get_db

@pytest.mark.anyio
async def test_ml_scoring_endpoints(client: AsyncClient):
    db = await get_db()
    
    # Create workspace
    ws_payload = {"name": "Test ML Scoring Workspace"}
    response = await client.post("/api/workspaces", json=ws_payload)
    workspace_id = response.json()["_id"]

    try:
        # Seed score record
        score_id = "test_score_123"
        await db.bid_scores.insert_one({
            "_id": score_id,
            "workspace_id": workspace_id,
            "overall_score": 0.76,
            "win_probability": 0.74,
            "go_no_go": "GO",
            "go_no_go_reasoning": "Calibrated score indicates a solid match for technical capabilities and budget alignment.",
            "confidence_level": "HIGH",
            "score_breakdown": {
                "compliance_completeness": 0.82,
                "domain_experience_match": 0.78,
                "budget_alignment: 0.90": 0.90,  # Or standard dictionary keys
                "compliance_completeness": 0.82,
                "domain_experience_match": 0.78,
                "budget_alignment": 0.90,
                "client_relationship": 0.50,
                "competition_risk": 0.60,
                "technical_complexity_fit": 0.80,
                "timeline_feasibility": 0.75
            },
            "feature_importance": {
                "budget_alignment": 0.25,
                "compliance_score": 0.22,
                "domain_experience_score": 0.20
            },
            "model_version": "1.0.0",
            "scored_at": "2026-06-12T18:51:29Z"
        })

        # Test GET /api/workspaces/{id}/score
        response = await client.get(f"/api/workspaces/{workspace_id}/score")
        assert response.status_code == 200
        score_data = response.json()
        assert score_data["_id"] == score_id
        assert score_data["win_probability"] == 0.74
        assert score_data["go_no_go"] == "GO"

        # Test POST /api/workspaces/{id}/score
        # Since MongoDB is mock or live, it should return a calibrated score structure
        response = await client.post(f"/api/workspaces/{workspace_id}/score")
        assert response.status_code == 200
        recal_data = response.json()
        assert "win_probability" in recal_data
        assert "go_no_go" in recal_data

        # Test POST /api/workspaces/{id}/score/simulate
        sim_payload = {
            "compliance_score": 95.0,
            "competitor_count": 1,
            "certifications_met": True
        }
        response = await client.post(f"/api/workspaces/{workspace_id}/score/simulate", json=sim_payload)
        assert response.status_code == 200
        sim_data = response.json()
        assert "win_probability" in sim_data
        assert "go_no_go" in sim_data
        assert "[Simulation Sandbox]" in sim_data["go_no_go_reasoning"]

    finally:
        await db.workspaces.delete_one({"_id": workspace_id})
        await db.bid_scores.delete_many({"workspace_id": workspace_id})
        await db.requirements.delete_many({"workspace_id": workspace_id})
        await db.capability_matches.delete_many({"workspace_id": workspace_id})

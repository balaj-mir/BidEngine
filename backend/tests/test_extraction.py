import pytest
from httpx import AsyncClient
from models.mongo_models import get_db

@pytest.mark.anyio
async def test_requirements_and_compliance(client: AsyncClient):
    db = await get_db()
    
    # Create a dummy workspace
    ws_payload = {"name": "Test Requirements Workspace"}
    response = await client.post("/api/workspaces", json=ws_payload)
    workspace_id = response.json()["_id"]

    try:
        # Seed a dummy requirement
        req_id = "test_req_123"
        await db.requirements.insert_one({
            "_id": req_id,
            "workspace_id": workspace_id,
            "section": "Section 1",
            "requirement_text": "The bidder must have ISO 27001 certification.",
            "is_mandatory": True,
            "category": "certification",
            "cluster_id": 1
        })

        # Seed a dummy compliance item
        comp_id = "test_comp_123"
        from datetime import datetime
        await db.compliance_items.insert_one({
            "_id": comp_id,
            "workspace_id": workspace_id,
            "requirement_id": req_id,
            "status": "partial",
            "final_score": 0.5,
            "notes": "Initial state",
            "gap_description": "ISO 27001 certificate is not present in capabilities.",
            "recommendation": "Acquire ISO 27001 or partner with certified subcontractor.",
            "ai_reasoning": "No mention of ISO 27001 in current capability library.",
            "assigned_to": None,
            "resolved_at": None,
            "created_at": datetime.utcnow()
        })

        # Test listing requirements
        response = await client.get(f"/api/workspaces/{workspace_id}/requirements")
        assert response.status_code == 200
        reqs = response.json()
        assert len(reqs) == 1
        assert reqs[0]["_id"] == req_id

        # Test compliance report fetching
        response = await client.get(f"/api/workspaces/{workspace_id}/compliance")
        assert response.status_code == 200
        report = response.json()
        assert len(report) == 1
        assert report[0]["_id"] == comp_id

        # Test manual override submission
        override_payload = {
            "status": "pass",
            "notes": "Approved after manual reference check"
        }
        response = await client.put(
            f"/api/workspaces/{workspace_id}/compliance/{comp_id}", 
            json=override_payload
        )
        assert response.status_code == 200
        assert "message" in response.json()

        # Verify the update succeeded
        response = await client.get(f"/api/workspaces/{workspace_id}/compliance")
        assert response.status_code == 200
        report = response.json()
        assert report[0]["status"] == "pass"
        assert report[0]["notes"] == "Approved after manual reference check"

    finally:
        # Clean up database records
        await db.workspaces.delete_one({"_id": workspace_id})
        await db.requirements.delete_many({"workspace_id": workspace_id})
        await db.compliance_items.delete_many({"workspace_id": workspace_id})

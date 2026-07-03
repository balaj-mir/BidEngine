import pytest
from httpx import AsyncClient
from models.mongo_models import get_db

@pytest.mark.anyio
async def test_rag_matches(client: AsyncClient):
    db = await get_db()
    
    # Create workspace
    ws_payload = {"name": "Test RAG Workspace"}
    response = await client.post("/api/workspaces", json=ws_payload)
    workspace_id = response.json()["_id"]

    try:
        # Seed requirement and capability record
        req_id = "test_req_123"
        cap_id = "test_cap_123"
        await db.requirements.insert_one({
            "_id": req_id,
            "workspace_id": workspace_id,
            "requirement_text": "Sample Requirement",
            "is_mandatory": True,
            "category": "technical",
            "section": "General"
        })
        await db.capability_records.insert_one({
            "_id": cap_id,
            "title": "Tax Digitization System",
            "description": "Developed tax portal."
        })

        # Seed a match
        match_id = "test_match_123"
        await db.capability_matches.insert_one({
            "_id": match_id,
            "workspace_id": workspace_id,
            "requirement_id": req_id,
            "capability_id": cap_id,
            "semantic_score": 0.85,
            "bm25_score": 12.5,
            "rerank_score": 0.91,
            "final_score": 0.88,
            "match_evidence": "Found similar past Tax digitization project from 2024.",
            "match_method": "hybrid",
            "is_approved": None
        })

        # Test list matches
        response = await client.get(f"/api/workspaces/{workspace_id}/matches")
        assert response.status_code == 200
        matches = response.json()
        assert len(matches) == 1
        assert matches[0]["requirement_id"] == req_id
        assert len(matches[0]["matches"]) == 1
        assert matches[0]["matches"][0]["_id"] == match_id

        # Test approve match
        approve_payload = {"is_approved": True}
        response = await client.put(
            f"/api/workspaces/{workspace_id}/matches/{match_id}/approve", 
            json=approve_payload
        )
        assert response.status_code == 200
        assert "message" in response.json()

        # Test reject match
        reject_payload = {"is_approved": False}
        response = await client.put(
            f"/api/workspaces/{workspace_id}/matches/{match_id}/approve", 
            json=reject_payload
        )
        assert response.status_code == 200
        assert "message" in response.json()

    finally:
        await db.workspaces.delete_one({"_id": workspace_id})
        await db.capability_matches.delete_many({"workspace_id": workspace_id})
        await db.requirements.delete_many({"workspace_id": workspace_id})
        await db.capability_records.delete_many({"_id": cap_id})

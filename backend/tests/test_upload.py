import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_workspace_lifecycle(client: AsyncClient):
    # 1. Create workspace
    payload = {"name": "Test Ingestion Workspace"}
    response = await client.post("/api/workspaces", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Test Ingestion Workspace"
    assert "status" in data
    assert data["status"] == "uploaded"
    workspace_id = data["_id"]

    # 2. Get workspace
    response = await client.get(f"/api/workspaces/{workspace_id}")
    assert response.status_code == 200
    assert response.json()["_id"] == workspace_id

    # 3. List workspaces
    response = await client.get("/api/workspaces")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) > 0
    assert any(w["_id"] == workspace_id for w in workspaces)

    # 4. Delete workspace
    response = await client.delete(f"/api/workspaces/{workspace_id}")
    assert response.status_code == 200
    
    # 5. Verify deleted
    response = await client.get(f"/api/workspaces/{workspace_id}")
    assert response.status_code == 404

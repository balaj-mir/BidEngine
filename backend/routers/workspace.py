import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from bson import ObjectId

# DB and Schema imports
from models.mongo_models import get_db, User, Workspace
from models.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    WorkspaceCreateRequest, WorkspaceResponse
)
from routers.auth_utils import (
    get_password_hash, verify_password, create_access_token, get_current_user_id
)

logger = logging.getLogger("bidengine.workspace")
router = APIRouter(prefix="", tags=["workspaces"])

# ----------------- Auth Endpoints -----------------

@router.post("/auth/register", response_model=TokenResponse)
async def register(req: UserRegisterRequest, db=Depends(get_db)):
    # Check if user already exists
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(req.password)
    user_data = {
        "email": req.email,
        "hashed_password": hashed_password,
        "name": req.name,
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)

    access_token = create_access_token(data={"sub": user_id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": req.email, "name": req.name}
    }

@router.post("/auth/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db=Depends(get_db)):
    user = await db.users.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": user["email"], "name": user["name"]}
    }

@router.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    if user_id == "demo_user_id":
        return {"id": "demo_user_id", "email": "demo@bidengine.ai", "name": "Demo User"}
    
    user = await db.users.find_one({"_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user["_id"]), "email": user["email"], "name": user["name"]}

# ----------------- Workspace CRUD -----------------

@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    cursor = db.workspaces.find({"created_by": user_id})
    workspaces = await cursor.to_list(100)
    
    response_list = []
    for w in workspaces:
        w_id = str(w["_id"])
        
        # Count related elements
        req_count = await db.requirements.count_documents({"workspace_id": w_id})
        match_count = await db.capability_matches.count_documents({"workspace_id": w_id})
        section_count = await db.proposal_sections.count_documents({"workspace_id": w_id})
        
        # Fetch latest bid score
        latest_score = await db.bid_scores.find_one({"workspace_id": w_id}, sort=[("scored_at", -1)])
        if latest_score:
            latest_score["_id"] = str(latest_score["_id"])

        response_list.append({
            "_id": w_id,
            "name": w["name"],
            "rfp_filename": w.get("rfp_filename"),
            "status": w["status"],
            "error_message": w.get("error_message"),
            "created_at": w["created_at"],
            "updated_at": w["updated_at"],
            "requirements_count": req_count,
            "matches_count": match_count,
            "sections_count": section_count,
            "latest_score": latest_score
        })
    return response_list

@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(req: WorkspaceCreateRequest, user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    ws_data = {
        "name": req.name,
        "rfp_filename": None,
        "rfp_text": None,
        "rfp_pages": [],
        "rfp_metadata": {},
        "status": "uploaded",
        "error_message": None,
        "created_by": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "pipeline_log": [
            {"timestamp": datetime.utcnow(), "stage": "creation", "message": "Workspace initialized."}
        ]
    }
    result = await db.workspaces.insert_one(ws_data)
    ws_id = str(result.inserted_id)
    
    return {
        "_id": ws_id,
        "name": req.name,
        "status": "uploaded",
        "created_at": ws_data["created_at"],
        "updated_at": ws_data["updated_at"],
        "requirements_count": 0,
        "matches_count": 0,
        "sections_count": 0,
        "latest_score": None
    }

@router.get("/workspaces/{id}", response_model=WorkspaceResponse)
async def get_workspace(id: str, user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    w = await db.workspaces.find_one({"_id": ObjectId(id) if ObjectId.is_valid(id) else id})
    if not w:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    w_id = str(w["_id"])
    req_count = await db.requirements.count_documents({"workspace_id": w_id})
    match_count = await db.capability_matches.count_documents({"workspace_id": w_id})
    section_count = await db.proposal_sections.count_documents({"workspace_id": w_id})
    
    latest_score = await db.bid_scores.find_one({"workspace_id": w_id}, sort=[("scored_at", -1)])
    if latest_score:
        latest_score["_id"] = str(latest_score["_id"])

    return {
        "_id": w_id,
        "name": w["name"],
        "rfp_filename": w.get("rfp_filename"),
        "status": w["status"],
        "error_message": w.get("error_message"),
        "created_at": w["created_at"],
        "updated_at": w["updated_at"],
        "requirements_count": req_count,
        "matches_count": match_count,
        "sections_count": section_count,
        "latest_score": latest_score
    }

@router.get("/workspaces/{id}/requirements")
async def list_workspace_requirements(id: str, db=Depends(get_db)):
    """Fetch the list of extracted requirements for a workspace"""
    cursor = db.requirements.find({"workspace_id": id})
    requirements = await cursor.to_list(1000)
    for r in requirements:
        r["_id"] = str(r["_id"])
    return requirements

@router.put("/workspaces/{id}/requirements/{req_id}")
async def update_requirement(id: str, req_id: str, req: Dict[str, Any], db=Depends(get_db)):
    """Update an extracted requirement"""
    oid = ObjectId(req_id) if ObjectId.is_valid(req_id) else req_id
    update_data = {k: v for k, v in req.items() if k not in ["_id", "workspace_id", "created_at"]}
    if not update_data:
        return {"message": "No data to update"}
        
    result = await db.requirements.update_one(
        {"_id": oid, "workspace_id": id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"message": "Requirement updated successfully"}

@router.delete("/workspaces/{id}/requirements/{req_id}")
async def delete_requirement(id: str, req_id: str, db=Depends(get_db)):
    """Delete an extracted requirement"""
    oid = ObjectId(req_id) if ObjectId.is_valid(req_id) else req_id
    result = await db.requirements.delete_one({"_id": oid, "workspace_id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"message": "Requirement deleted successfully"}

@router.delete("/workspaces/{id}")
async def delete_workspace(id: str, user_id: str = Depends(get_current_user_id), db=Depends(get_db)):
    # Cascade delete all related files
    oid = ObjectId(id) if ObjectId.is_valid(id) else id
    
    await db.workspaces.delete_one({"_id": oid})
    await db.requirements.delete_many({"workspace_id": id})
    await db.capability_matches.delete_many({"workspace_id": id})
    await db.proposal_sections.delete_many({"workspace_id": id})
    await db.compliance_items.delete_many({"workspace_id": id})
    await db.bid_scores.delete_many({"workspace_id": id})
    
    return {"message": "Workspace deleted successfully"}

@router.get("/workspaces/{id}/status/stream")
async def stream_workspace_status(id: str, db=Depends(get_db)):
    """SSE endpoint streaming pipeline log updates to client"""
    async def log_generator():
        last_count = 0
        w_id = ObjectId(id) if ObjectId.is_valid(id) else id
        
        while True:
            w = await db.workspaces.find_one({"_id": w_id})
            if not w:
                yield "event: error\ndata: Workspace not found\n\n"
                break
                
            logs = w.get("pipeline_log", [])
            status = w.get("status", "uploaded")
            
            if len(logs) > last_count:
                new_logs = logs[last_count:]
                for log in new_logs:
                    # Format payload
                    payload = {
                        "timestamp": log["timestamp"].isoformat() if isinstance(log["timestamp"], datetime) else str(log["timestamp"]),
                        "stage": log["stage"],
                        "message": log["message"],
                        "status": status
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                last_count = len(logs)

            if status in ["complete", "error"]:
                # Yield final state and close
                yield f"data: {json.dumps({'status': status, 'message': 'Pipeline finished', 'stage': 'finished'})}\n\n"
                break
                
            await asyncio.sleep(1.0)

    return StreamingResponse(log_generator(), media_type="text/event-stream")

import json

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
from bson import ObjectId

# DB and Schema imports
from models.mongo_models import get_db, CapabilityRecord
from models.schemas import (
    CapabilityMatchResponse, MatchApproveRequest, CapabilityRecordCreate
)
from routers.auth_utils import get_current_user_id

logger = logging.getLogger("bidengine.match")
router = APIRouter(prefix="", tags=["matching"])

@router.get("/workspaces/{id}/matches")
async def list_workspace_matches(id: str, db=Depends(get_db)):
    """Returns requirements with best matches grouped together"""
    req_cursor = db.requirements.find({"workspace_id": id})
    requirements = await req_cursor.to_list(200)

    match_cursor = db.capability_matches.find({"workspace_id": id})
    matches = await match_cursor.to_list(1000)

    result = []
    for req in requirements:
        req_id = str(req["_id"])
        
        # Filter matches for this requirement
        req_matches = [m for m in matches if str(m["requirement_id"]) == req_id]
        
        # Sort matches by final score desc
        req_matches.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        
        # Fetch detailed capability info for matched items
        detailed_matches = []
        for m in req_matches:
            cap_id = m["capability_id"]
            cap = await db.capability_records.find_one({"_id": cap_id})
            
            m_copy = dict(m)
            m_copy["_id"] = str(m_copy["_id"])
            m_copy["capability_detail"] = cap
            detailed_matches.append(m_copy)

        # Highlight best match (first after sorting)
        best_match = detailed_matches[0] if detailed_matches else None

        result.append({
            "requirement_id": req_id,
            "section": req.get("section", "General"),
            "requirement_text": req.get("requirement_text", ""),
            "is_mandatory": req.get("is_mandatory", False),
            "category": req.get("category", "other"),
            "source_page": req.get("source_page"),
            "matches": detailed_matches,
            "best_match": best_match
        })
    return result

@router.post("/workspaces/{id}/match/run")
async def run_matching(id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """Trigger the Celery background matching task (or fallback to background thread)"""
    try:
        from workers.celery_app import match_capabilities_task
        match_capabilities_task.delay(id)
        logger.info("Enqueued matching task via Celery.")
    except Exception as e:
        logger.warning(f"Failed to enqueue Celery matching task: {e}. Running fallback thread.")
        # Fallback
        from routers.upload import run_extraction_fallback
        background_tasks.add_task(run_extraction_fallback, id)

    return {"status": "processing", "message": "Matching run triggered."}

@router.put("/workspaces/{id}/matches/{match_id}/approve")
async def approve_match(id: str, match_id: str, req: MatchApproveRequest, db=Depends(get_db)):
    """Allows human overlay to approve/reject specific RAG capability evidence matches"""
    mid = ObjectId(match_id) if ObjectId.is_valid(match_id) else match_id
    
    result = await db.capability_matches.update_one(
        {"_id": mid},
        {"$set": {"is_approved": req.is_approved}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Match record not found")
        
    return {"message": "Match approval status updated successfully"}

@router.put("/workspaces/{id}/matches/{match_id}/override")
async def override_match(id: str, match_id: str, req: Dict[str, str], db=Depends(get_db)):
    """Allows human overlay to manually swap out the capability evidence (HitL RAG)"""
    new_cap_id = req.get("capability_id")
    if not new_cap_id:
        raise HTTPException(status_code=400, detail="Missing capability_id")

    mid = ObjectId(match_id) if ObjectId.is_valid(match_id) else match_id
    
    # Verify capability exists
    cap = await db.capability_records.find_one({"_id": new_cap_id})
    if not cap:
        raise HTTPException(status_code=404, detail="New Capability not found")

    result = await db.capability_matches.update_one(
        {"_id": mid},
        {
            "$set": {
                "capability_id": new_cap_id,
                "match_evidence": cap.get("description", "")[:500],
                "match_method": "manual_override",
                "is_approved": True
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Match record not found")
        
    return {"message": "Capability match overridden successfully"}

# ----------------- Capability Library -----------------

@router.post("/capability-library", response_model=CapabilityRecordCreate)
async def add_capability(req: CapabilityRecordCreate, db=Depends(get_db)):
    """Adds a new reference project / capability record to the database"""
    # Check if duplicate id
    existing = await db.capability_records.find_one({"_id": req.id})
    if existing:
        raise HTTPException(status_code=400, detail="Capability record with this ID already exists.")

    cap_data = req.model_dump(by_alias=True)
    cap_data["created_at"] = datetime.utcnow()
    
    await db.capability_records.insert_one(cap_data)
    
    # Ingest the new record into BM25 and vector stores
    try:
        from services.hybrid_rag_engine import HybridRAGEngine
        rag = HybridRAGEngine()
        rag.ingest_capability_library([cap_data])
    except Exception as e:
        logger.error(f"Failed to index capability record: {e}")

    return req

@router.get("/capability-library")
async def list_capabilities(
    sector: Optional[str] = None,
    client_type: Optional[str] = None,
    search: Optional[str] = None,
    db=Depends(get_db)
):
    """Lists capability library entries with search filters"""
    query = {}
    if sector:
        query["sector"] = sector
    if client_type:
        query["client_type"] = client_type
    if search:
        # Text query search
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"keywords": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.capability_records.find(query)
    records = await cursor.to_list(100)
    return records

@router.post("/capability-library/reindex")
async def reindex_capability_library(background_tasks: BackgroundTasks, db=Depends(get_db)):
    """Trigger background re-indexing of all capability records in vector and lexical store"""
    async def _reindex():
        try:
            cursor = db.capability_records.find({})
            records = await cursor.to_list(1000)
            
            from services.hybrid_rag_engine import HybridRAGEngine
            rag = HybridRAGEngine()
            rag.ingest_capability_library(records)
            logger.info("Successfully re-indexed capability library.")
        except Exception as e:
            logger.error(f"Re-indexing failed: {e}")

    background_tasks.add_task(_reindex)
    return {"message": "Re-indexing triggered successfully."}

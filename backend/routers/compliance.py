import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from bson import ObjectId

# DB and Schema imports
from models.mongo_models import get_db, ComplianceItem
from models.schemas import (
    ComplianceItemResponse, ComplianceOverrideRequest, ComplianceNoteRequest
)
from services.compliance_engine import ComplianceEngine

logger = logging.getLogger("bidengine.compliance")
router = APIRouter(prefix="", tags=["compliance"])

@router.get("/workspaces/{id}/compliance", response_model=List[ComplianceItemResponse])
async def get_compliance_report(id: str, db=Depends(get_db)):
    """Returns the full compliance checklist items with requirement texts attached"""
    cursor = db.compliance_items.find({"workspace_id": id})
    items = await cursor.to_list(200)

    result = []
    for item in items:
        # Load requirement details
        req_id = item.get("requirement_id")
        req = await db.requirements.find_one({"_id": ObjectId(req_id) if ObjectId.is_valid(req_id) else req_id})
        
        item_copy = dict(item)
        item_copy["_id"] = str(item_copy["_id"])
        item_copy["requirement_text"] = req.get("requirement_text", "") if req else "Requirement text clause"
        result.append(item_copy)

    return result

@router.post("/workspaces/{id}/compliance/generate")
async def regenerate_compliance_report(id: str, db=Depends(get_db)):
    """Triggers recalculation and updates compliance status matrix database records"""
    engine = ComplianceEngine()
    summary = await engine.generate_report(id)
    return summary

@router.put("/workspaces/{id}/compliance/{item_id}")
async def override_compliance_status(
    id: str, 
    item_id: str, 
    req: ComplianceOverrideRequest, 
    db=Depends(get_db)
):
    """Allows manual human overlay overrides of automated compliance matrix classifications"""
    iid = ObjectId(item_id) if ObjectId.is_valid(item_id) else item_id
    
    update_doc = {
        "status": req.status,
        "resolved_at": datetime.utcnow() if req.status == "pass" else None
    }
    if req.notes:
        update_doc["notes"] = req.notes

    result = await db.compliance_items.update_one(
        {"_id": iid},
        {"$set": update_doc}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Compliance item not found")
        
    return {"message": "Compliance override applied successfully."}

@router.get("/workspaces/{id}/compliance/summary")
async def get_compliance_summary(id: str, db=Depends(get_db)):
    """Returns compliance stats: counts of pass, partial, fail, pending and final overall score"""
    cursor = db.compliance_items.find({"workspace_id": id})
    items = await cursor.to_list(500)
    
    if not items:
        return {"pass": 0, "partial": 0, "fail": 0, "pending": 0, "score": 0.0}

    pass_cnt = sum(1 for i in items if i["status"] == "pass")
    part_cnt = sum(1 for i in items if i["status"] == "partial")
    fail_cnt = sum(1 for i in items if i["status"] == "fail")
    pend_cnt = sum(1 for i in items if i["status"] == "pending")

    overall_score = (pass_cnt + part_cnt * 0.5) / len(items) * 100

    return {
        "pass": pass_cnt,
        "partial": part_cnt,
        "fail": fail_cnt,
        "pending": pend_cnt,
        "score": overall_score
    }

@router.post("/workspaces/{id}/compliance/{item_id}/note")
async def add_compliance_note(id: str, item_id: str, req: ComplianceNoteRequest, db=Depends(get_db)):
    iid = ObjectId(item_id) if ObjectId.is_valid(item_id) else item_id
    
    result = await db.compliance_items.update_one(
        {"_id": iid},
        {"$set": {"notes": req.notes}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Compliance item not found")
        
    return {"message": "Compliance note saved successfully."}

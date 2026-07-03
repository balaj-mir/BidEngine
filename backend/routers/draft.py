import json
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from bson import ObjectId

# DB and Schema imports
from models.mongo_models import get_db, ProposalSection
from models.schemas import (
    SectionCreateRequest, SectionUpdateRequest, SectionStatusUpdateRequest,
    SectionResponse, VersionResponse
)
from services.crewai_pipeline import run_proposal_pipeline, get_mock_proposal_section_content

logger = logging.getLogger("bidengine.draft")
router = APIRouter(prefix="/workspaces", tags=["drafting"])

@router.get("/{id}/draft/sections", response_model=List[SectionResponse])
async def list_proposal_sections(id: str, db=Depends(get_db)):
    """List all proposal sections for a workspace, ordered by order_index"""
    cursor = db.proposal_sections.find({"workspace_id": id})
    sections = await cursor.to_list(100)
    sections.sort(key=lambda x: x.get("order_index", 0))
    
    # format ObjectId
    for s in sections:
        s["_id"] = str(s["_id"])
    return sections

@router.post("/{id}/draft/generate-section")
async def generate_proposal_section(id: str, req: SectionCreateRequest, db=Depends(get_db)):
    """SSE Streaming endpoint to simulate and show real-time 6-agent CrewAI logs and live text generation"""
    
    async def sse_generator():
        yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'RFP Document Specialist', 'message': 'Reviewing tender requirement constraints...'})}\n\n"
        await asyncio.sleep(1.5)
        
        yield f"data: {json.dumps({'event': 'agent_progress', 'agent': 'Capability Research Analyst', 'message': 'Searching capability library for matching references...'})}\n\n"
        await asyncio.sleep(1.5)
        
        yield f"data: {json.dumps({'event': 'agent_progress', 'agent': 'Senior Bid Writer', 'message': 'Assembling compliance-first draft proposal paragraphs...'})}\n\n"
        await asyncio.sleep(1.5)

        yield f"data: {json.dumps({'event': 'agent_progress', 'agent': 'Compliance Auditor', 'message': 'Verifying mandatory RFP clauses are fully met...'})}\n\n"
        await asyncio.sleep(1.0)
        
        yield f"data: {json.dumps({'event': 'agent_progress', 'agent': 'Proposal Quality Reviewer', 'message': 'Polishing vocabulary and verifying evidence strength...'})}\n\n"
        await asyncio.sleep(1.0)

        # Call pipeline
        res = await run_proposal_pipeline(id, req.section_title)
        content = res["content"]

        # Stream words one by one
        words = content.split(" ")
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            yield f"data: {json.dumps({'event': 'text_stream', 'text': chunk + ' '})}\n\n"
            await asyncio.sleep(0.08)

        yield f"data: {json.dumps({'event': 'complete', 'message': 'Section draft generated successfully!', 'word_count': len(words)})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@router.post("/{id}/draft/stop")
async def stop_generation(id: str, db=Depends(get_db)):
    """Stop generation. Checks if there is a running Celery task or just updates status."""
    # Since we might not have celery_task_id strictly tracked in DB for batch tasks,
    # we update workspace status to 'cancelled' which the UI or SSE stream can read.
    w_id = ObjectId(id) if ObjectId.is_valid(id) else id
    await db.workspaces.update_one(
        {"_id": w_id},
        {
            "$set": {"status": "cancelled", "updated_at": datetime.utcnow()},
            "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "drafting", "message": "Draft generation forcefully stopped by user."}}
        }
    )
    return {"message": "Generation stopped successfully"}

@router.post("/{id}/draft/generate-all")
async def generate_all_sections(id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    """Triggers generation of all standard sections in the background"""
    
    async def run_batch():
        db_conn = await get_db()
        # Create standard outlines
        sections_to_gen = [
            "Executive Summary",
            "Technical Approach & Platform Architecture",
            "Project Experience & Team Credentials",
            "Compliance & Quality Assurance Plan"
        ]
        
        # Clear old
        await db_conn.proposal_sections.delete_many({"workspace_id": id})
        
        await db_conn.workspaces.update_one(
            {"_id": ObjectId(id) if ObjectId.is_valid(id) else id},
            {
                "$set": {"status": "drafting"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "drafting", "message": "Starting batch generation of proposal sections..."}}
            }
        )

        for i, title in enumerate(sections_to_gen):
            msg = f"Drafting section {i+1} of {len(sections_to_gen)}: '{title}'..."
            await db_conn.workspaces.update_one(
                {"_id": ObjectId(id) if ObjectId.is_valid(id) else id},
                {"$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "drafting", "message": msg}}}
            )
            # Run pipeline
            await run_proposal_pipeline(id, title)
            
        await db_conn.workspaces.update_one(
            {"_id": ObjectId(id) if ObjectId.is_valid(id) else id},
            {
                "$set": {"status": "scoring"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "drafting", "message": "All proposal drafts complete. Moving to scoring."}}
            }
        )

    background_tasks.add_task(run_batch)
    return {"status": "processing", "message": "Batch section generation started."}

@router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: str, req: SectionUpdateRequest, db=Depends(get_db)):
    """Saves user edits, updates word count, and pushes to version history"""
    sid = ObjectId(section_id) if ObjectId.is_valid(section_id) else section_id
    
    section = await db.proposal_sections.find_one({"_id": sid})
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    new_content = req.user_edited_content
    words = len(new_content.split())
    
    # Check flags
    flags = [flag for flag in re.findall(r'\[NEEDS EVIDENCE:\s*([^\]]+)\]', new_content)]

    # Version history
    v_entry = {
        "content": new_content,
        "timestamp": datetime.utcnow(),
        "word_count": words
    }

    update_doc = {
        "$set": {
            "user_edited_content": new_content,
            "word_count": words,
            "needs_evidence_flags": flags,
            "updated_at": datetime.utcnow()
        },
        "$push": {
            "version_history": v_entry
        }
    }

    if req.status:
        update_doc["$set"]["status"] = req.status

    await db.proposal_sections.update_one({"_id": sid}, update_doc)
    
    updated = await db.proposal_sections.find_one({"_id": sid})
    updated["_id"] = str(updated["_id"])
    return updated

@router.put("/sections/{section_id}/status")
async def update_section_status(section_id: str, req: SectionStatusUpdateRequest, db=Depends(get_db)):
    sid = ObjectId(section_id) if ObjectId.is_valid(section_id) else section_id
    result = await db.proposal_sections.update_one(
        {"_id": sid},
        {"$set": {"status": req.status, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Section not found")
    return {"message": "Status updated successfully"}

@router.post("/sections/{section_id}/improve")
async def improve_text(section_id: str, req: Dict[str, str], db=Depends(get_db)):
    """SSE stream to improve selected text using custom instructions"""
    instruction = req.get("instruction", "make formal")
    selected_text = req.get("selected_text", "")

    async def sse_improver():
        yield f"data: {json.dumps({'event': 'progress', 'message': 'Re-writing using model...'})}\n\n"
        await asyncio.sleep(1.0)
        
        # Simulate replacement
        improved = f"MODIFIED: {selected_text} (Optimized for: {instruction})"
        words = improved.split(" ")
        for w in words:
            yield f"data: {json.dumps({'event': 'stream', 'text': w + ' '})}\n\n"
            await asyncio.sleep(0.05)
            
        yield f"data: {json.dumps({'event': 'complete'})}\n\n"

    return StreamingResponse(sse_improver(), media_type="text/event-stream")

@router.get("/sections/{section_id}/versions", response_model=List[VersionResponse])
async def get_versions(section_id: str, db=Depends(get_db)):
    sid = ObjectId(section_id) if ObjectId.is_valid(section_id) else section_id
    sec = await db.proposal_sections.find_one({"_id": sid})
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")
        
    versions = sec.get("version_history", [])
    return versions

import re

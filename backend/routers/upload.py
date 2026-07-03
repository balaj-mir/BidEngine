import os
import shutil
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, status
from bson import ObjectId

# DB and Service imports
from models.mongo_models import get_db
from services.document_parser import DocumentParser

logger = logging.getLogger("bidengine.upload")
router = APIRouter(prefix="/workspaces", tags=["upload"])

@router.post("/{workspace_id}/upload")
async def upload_rfp(
    workspace_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    # 1. Validate extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.docx']:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported file format. Only PDF and DOCX are allowed."
        )

    # 2. Check size (max 50MB)
    max_size = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=413, # Payload Too Large
            detail="File size exceeds the 50MB limit."
        )

    # 3. Check Magic Bytes
    # PDF starts with %PDF (0x25 0x50 0x44 0x46)
    # DOCX is a zip file, starting with PK (0x50 0x4B)
    if ext == '.pdf' and not content.startswith(b'%PDF'):
        raise HTTPException(status_code=400, detail="Corrupted PDF file structure detected.")
    if ext == '.docx' and not content.startswith(b'PK'):
        raise HTTPException(status_code=400, detail="Corrupted DOCX file structure detected.")

    # 4. Save file to temporary directory
    target_dir = f"D:\\bid-engine\\backend\\data\\sample_rfps\\{workspace_id}"
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # 5. Retrieve Workspace
    w_id = ObjectId(workspace_id) if ObjectId.is_valid(workspace_id) else workspace_id
    workspace = await db.workspaces.find_one({"_id": w_id})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 6. Parse Document
    try:
        parser = DocumentParser()
        parsed = parser.parse(filepath)
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        # clean up file
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"Failed to process document: {str(e)}")

    # 7. Save parsed data to workspace
    await db.workspaces.update_one(
        {"_id": w_id},
        {
            "$set": {
                "rfp_filename": filename,
                "rfp_text": parsed["full_text"],
                "rfp_pages": parsed["pages"],
                "rfp_metadata": parsed["metadata"],
                "status": "uploaded",
                "updated_at": datetime.utcnow()
            },
            "$push": {
                "pipeline_log": {
                    "timestamp": datetime.utcnow(),
                    "stage": "upload",
                    "message": f"File '{filename}' uploaded successfully. Parsed {parsed['metadata']['page_count']} pages."
                }
            }
        }
    )

    # 8. Trigger Celery Task or Fallback to FastAPI Background Tasks (if Celery fails)
    try:
        from workers.celery_app import extract_requirements_task
        extract_requirements_task.delay(workspace_id)
        logger.info("Enqueued requirement extraction via Celery.")
    except Exception as e:
        logger.warning(f"Failed to enqueue Celery task: {e}. Executing fallback background thread.")
        # Fallback async run
        background_tasks.add_task(run_extraction_fallback, workspace_id)

    return {
        "workspace_id": workspace_id,
        "filename": filename,
        "page_count": parsed["metadata"]["page_count"],
        "is_scanned": parsed["metadata"]["is_scanned"],
        "status": "processing"
    }

async def run_extraction_fallback(workspace_id: str):
    """Fallback runner if Redis/Celery is offline"""
    logger.info(f"Running fallback extraction thread for {workspace_id}")
    from services.ner_extractor import NERExtractor
    from services.hybrid_rag_engine import HybridRAGEngine
    from services.compliance_engine import ComplianceEngine
    db = await get_db()
    w_id = ObjectId(workspace_id) if ObjectId.is_valid(workspace_id) else workspace_id
    
    try:
        # Step 1: Extract requirements
        workspace = await db.workspaces.find_one({"_id": w_id})
        await db.workspaces.update_one(
            {"_id": w_id},
            {
                "$set": {"status": "extracting"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "extraction", "message": "[Fallback Mode] Starting requirement extraction..."}}
            }
        )
        
        enable_masking = workspace.get("enable_privacy_masking", False)
        extractor = NERExtractor()
        extracted = extractor.extract_requirements(workspace_id, workspace["rfp_pages"], enable_masking=enable_masking)
        
        if extracted:
            await db.requirements.delete_many({"workspace_id": workspace_id})
            await db.requirements.insert_many(extracted)
            
        await db.workspaces.update_one(
            {"_id": w_id},
            {
                "$set": {"status": "extracted"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "extraction", "message": f"[Fallback Mode] Extracted {len(extracted)} clauses."}}
            }
        )
        
        # Step 2: Match capabilities
        await db.workspaces.update_one(
            {"_id": w_id},
            {
                "$set": {"status": "matching"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "matching", "message": "[Fallback Mode] Starting capability matching..."}}
            }
        )
        
        cap_cursor = db.capability_records.find({})
        caps = await cap_cursor.to_list(1000)
        
        rag = HybridRAGEngine()
        rag.ingest_capability_library(caps)
        
        req_cursor = db.requirements.find({"workspace_id": workspace_id})
        reqs = await req_cursor.to_list(500)
        
        all_matches = []
        for req in reqs:
            req_id = str(req["_id"])
            matches = rag.match_requirement(req["requirement_text"], top_k=5)
            for m in matches:
                all_matches.append({
                    "workspace_id": workspace_id,
                    "requirement_id": req_id,
                    "capability_id": str(m["capability"].get("id", m["capability"].get("_id"))),
                    "semantic_score": m["semantic_score"],
                    "bm25_score": m["bm25_score"],
                    "rerank_score": m["rerank_score"],
                    "final_score": m["final_score"],
                    "match_evidence": m["capability"].get("description", "")[:500],
                    "match_method": m["match_method"],
                    "is_approved": None,
                    "created_at": datetime.utcnow()
                })
                
        await db.capability_matches.delete_many({"workspace_id": workspace_id})
        if all_matches:
            await db.capability_matches.insert_many(all_matches)
            
        # Step 3: Compliance scoring
        comp_eng = ComplianceEngine()
        summary = await comp_eng.generate_report(workspace_id)
        
        await db.workspaces.update_one(
            {"_id": w_id},
            {
                "$set": {"status": "complete"},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "complete", "message": f"[Fallback Mode] Pipeline completed! Compliance: {summary['overall_compliance_score']:.1f}%"}}
            }
        )
        
    except Exception as e:
        logger.error(f"Fallback pipeline failed: {e}")
        await db.workspaces.update_one(
            {"_id": w_id},
            {
                "$set": {"status": "error", "error_message": str(e)},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "error", "message": f"[Fallback Mode] Error: {str(e)}"}}
            }
        )

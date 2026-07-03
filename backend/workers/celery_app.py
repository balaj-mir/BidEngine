import os
import asyncio
import logging
from celery import Celery

logger = logging.getLogger("bidengine.celery")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "bidengine_workers",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 min limit
)

# ----------------- Celery Tasks -----------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def extract_requirements_task(self, workspace_id: str):
    """Celery task to run requirement extraction on uploaded RFP"""
    logger.info(f"Starting async requirement extraction for workspace {workspace_id}")
    
    # Import inside task to prevent circular import issues
    from services.ner_extractor import NERExtractor
    from models.mongo_models import get_db
    from bson import ObjectId
    
    # Run async function in synchronous Celery task
    async def _run():
        db = await get_db()
        workspace = await db.workspaces.find_one({"_id": ObjectId(workspace_id) if ObjectId.is_valid(workspace_id) else workspace_id})
        if not workspace:
            raise ValueError("Workspace not found")

        # Update status
        await db.workspaces.update_one(
            {"_id": workspace["_id"]},
            {
                "$set": {"status": "extracting", "updated_at": datetime.utcnow()},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "extraction", "message": "Initiating spaCy + LLM hybrid requirement extraction..."}}
            }
        )

        try:
            enable_masking = workspace.get("enable_privacy_masking", False)
            extractor = NERExtractor()
            extracted_reqs = extractor.extract_requirements(workspace_id, workspace.get("rfp_pages", []), enable_masking=enable_masking)
            
            # Save extracted requirements
            if extracted_reqs:
                await db.requirements.delete_many({"workspace_id": workspace_id})
                await db.requirements.insert_many(extracted_reqs)
                logger.info(f"Extracted and saved {len(extracted_reqs)} requirements.")
            
            # Update workspace status
            msg = f"Requirement extraction complete. Found {len(extracted_reqs)} distinct requirements."
            await db.workspaces.update_one(
                {"_id": workspace["_id"]},
                {
                    "$set": {"status": "extracted", "updated_at": datetime.utcnow()},
                    "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "extraction", "message": msg}}
                }
            )

            # Auto trigger next step: Capability Matching
            match_capabilities_task.delay(workspace_id)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            await db.workspaces.update_one(
                {"_id": workspace["_id"]},
                {
                    "$set": {"status": "error", "error_message": str(e), "updated_at": datetime.utcnow()},
                    "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "error", "message": f"Extraction error: {str(e)}"}}
                }
            )
            raise e

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_run(), loop)
            future.result()
        else:
            asyncio.run(_run())
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            pass

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def match_capabilities_task(self, workspace_id: str):
    """Celery task to run hybrid matching of capabilities against requirements"""
    logger.info(f"Starting async capability matching for workspace {workspace_id}")
    
    from services.hybrid_rag_engine import HybridRAGEngine
    from services.compliance_engine import ComplianceEngine
    from models.mongo_models import get_db
    from bson import ObjectId

    async def _run():
        db = await get_db()
        workspace = await db.workspaces.find_one({"_id": ObjectId(workspace_id) if ObjectId.is_valid(workspace_id) else workspace_id})
        if not workspace:
            raise ValueError("Workspace not found")

        await db.workspaces.update_one(
            {"_id": workspace["_id"]},
            {
                "$set": {"status": "matching", "updated_at": datetime.utcnow()},
                "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "matching", "message": "Querying capability library using Hybrid RAG (BM25 + ChromaDB + CrossEncoder Reranking)..."}}
            }
        )

        try:
            # Load capabilities to ensure they are ingested
            cap_cursor = db.capability_records.find({})
            capabilities = await cap_cursor.to_list(1000)
            
            # 1. Ingest capabilities to index
            rag = HybridRAGEngine()
            rag.ingest_capability_library(capabilities)

            # 2. Match each requirement
            req_cursor = db.requirements.find({"workspace_id": workspace_id})
            requirements = await req_cursor.to_list(500)
            
            all_matches = []
            for req in requirements:
                req_id = str(req["_id"])
                req_text = req.get("requirement_text", "")
                
                matches = rag.match_requirement(req_text, top_k=5)
                for m in matches:
                    cap = m["capability"]
                    all_matches.append({
                        "workspace_id": workspace_id,
                        "requirement_id": req_id,
                        "capability_id": str(cap.get("id", cap.get("_id"))),
                        "semantic_score": m["semantic_score"],
                        "bm25_score": m["bm25_score"],
                        "rerank_score": m["rerank_score"],
                        "final_score": m["final_score"],
                        "match_evidence": cap.get("description", "")[:500],
                        "match_method": m["match_method"],
                        "is_approved": None,
                        "created_at": datetime.utcnow()
                    })

            # Save matches
            await db.capability_matches.delete_many({"workspace_id": workspace_id})
            if all_matches:
                await db.capability_matches.insert_many(all_matches)

            # 3. Generate Compliance Report
            comp_eng = ComplianceEngine()
            summary = await comp_eng.generate_report(workspace_id)

            msg = f"Matching complete. Processed {len(requirements)} clauses. Compliance score: {summary['overall_compliance_score']:.1f}%"
            await db.workspaces.update_one(
                {"_id": workspace["_id"]},
                {
                    "$set": {"status": "matched", "updated_at": datetime.utcnow()},
                    "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "matching", "message": msg}}
                }
            )

        except Exception as e:
            logger.error(f"Capability matching failed: {e}")
            await db.workspaces.update_one(
                {"_id": workspace["_id"]},
                {
                    "$set": {"status": "error", "error_message": str(e), "updated_at": datetime.utcnow()},
                    "$push": {"pipeline_log": {"timestamp": datetime.utcnow(), "stage": "error", "message": f"Matching error: {str(e)}"}}
                }
            )
            raise e

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_run(), loop)
            future.result()
        else:
            asyncio.run(_run())
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            pass

from datetime import datetime

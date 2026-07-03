import os
import sys
import asyncio
import logging
from datetime import datetime

# Add backend to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.mongo_models import get_db, init_db_connection
from routers.auth_utils import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo_workspace")

async def main():
    logger.info("Initializing demo workspace seeding...")
    init_db_connection()
    db = await get_db()

    # 1. Create or Find Demo User
    demo_email = "demo@bidengine.ai"
    user = await db.users.find_one({"email": demo_email})
    if not user:
        hashed_password = get_password_hash("Demo@1234")
        user_data = {
            "email": demo_email,
            "hashed_password": hashed_password,
            "name": "Demo User",
            "created_at": datetime.utcnow()
        }
        res = await db.users.insert_one(user_data)
        user_id = str(res.inserted_id)
        logger.info(f"Created demo user with ID: {user_id}")
    else:
        user_id = str(user["_id"])
        logger.info(f"Found existing demo user with ID: {user_id}")

    # 2. Check and Clear Old Workspace
    ws_name = "FBR Tax Digitization RFP"
    old_ws = await db.workspaces.find_one({"created_by": user_id, "name": ws_name})
    if old_ws:
        ws_id = str(old_ws["_id"])
        logger.info(f"Clearing existing workspace {ws_id} to avoid duplicates...")
        await db.workspaces.delete_one({"_id": old_ws["_id"]})
        await db.requirements.delete_many({"workspace_id": ws_id})
        await db.capability_matches.delete_many({"workspace_id": ws_id})
        await db.proposal_sections.delete_many({"workspace_id": ws_id})
        await db.compliance_items.delete_many({"workspace_id": ws_id})
        await db.bid_scores.delete_many({"workspace_id": ws_id})

    # 3. Create New Workspace
    ws_data = {
        "name": ws_name,
        "rfp_filename": "fbr_tax_digitization_rfp.pdf",
        "rfp_text": "Federal Board of Revenue (FBR) request for proposal for Tax System Digitization, covering secure databases, ISO certifications, and mobile tax applications.",
        "rfp_pages": [
            {"page_num": 1, "text": "RFP Title: FBR Tax Digitization Tenders. Section I: Technical Specifications.", "tables": []},
            {"page_num": 2, "text": "Section II: Compliance Clauses. The vendor must be ISO 27001 certified.", "tables": []}
        ],
        "rfp_metadata": {"page_count": 2, "file_size": 24500, "is_scanned": False},
        "status": "complete",
        "error_message": None,
        "created_by": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "pipeline_log": [
            {"timestamp": datetime.utcnow(), "stage": "creation", "message": "Workspace initialized."},
            {"timestamp": datetime.utcnow(), "stage": "extraction", "message": "Extracted 47 requirements from document."},
            {"timestamp": datetime.utcnow(), "stage": "matching", "message": "Completed hybrid RAG search matching."},
            {"timestamp": datetime.utcnow(), "stage": "drafting", "message": "Orchestrated CrewAI 6-agent proposal generation."},
            {"timestamp": datetime.utcnow(), "stage": "scoring", "message": "Completed win probability prediction (Calibrated Random Forest)."},
            {"timestamp": datetime.utcnow(), "stage": "finished", "message": "Workspace generation complete."}
        ]
    }
    res = await db.workspaces.insert_one(ws_data)
    ws_id = str(res.inserted_id)
    logger.info(f"Created demo workspace with ID: {ws_id}")

    # 4. Seed 47 Requirements
    # 23 mandatory, 8 deadlines, 5 clusters
    req_ids = []
    requirements_data = []
    for i in range(1, 48):
        # 23 mandatory: first 23 are mandatory
        is_mand = (i <= 23)
        # 8 with deadlines: 8 requirements have specific deadlines
        deadline = "2026-12-31" if (i <= 8) else None
        # distributed across 5 clusters
        cluster_id = (i % 5)
        # categories
        category = "technical" if i <= 15 else "certification" if i <= 25 else "deadline" if i <= 30 else "financial" if i <= 35 else "legal" if i <= 40 else "experience" if i <= 45 else "other"
        
        req = {
            "workspace_id": ws_id,
            "section": f"Section {1 + (i // 10)}",
            "requirement_text": f"The contractor must fulfill requirement standard number {i} regarding {category} specifications.",
            "is_mandatory": is_mand,
            "category": category,
            "source_page": 1 + (i % 3),
            "deadline_date": deadline,
            "evaluation_weight": float(random_weight(i)),
            "cluster_id": cluster_id,
            "compliance_keywords": ["must"] if is_mand else ["should"],
            "created_at": datetime.utcnow()
        }
        requirements_data.append(req)

    res_reqs = await db.requirements.insert_many(requirements_data)
    req_ids = [str(rid) for rid in res_reqs.inserted_ids]
    logger.info(f"Seeded {len(req_ids)} requirements.")

    # Fetch some capability records from DB to link in matches
    capabilities = await db.capability_records.find().to_list(50)
    if not capabilities:
        logger.warning("No capability records found! Seeding dummy capability record first...")
        dummy_cap = {
            "_id": "cap_001",
            "title": "Tax System Deployment",
            "description": "Completed tax portal deployment",
            "sector": "IT Services",
            "client_type": "Government",
            "year_completed": 2023,
            "contract_value": 15000000.0,
            "currency": "PKR",
            "duration_months": 12,
            "certifications": ["ISO 27001"],
            "team_size": 10,
            "keywords": ["tax", "government"],
            "outcome": "Success",
            "created_at": datetime.utcnow()
        }
        await db.capability_records.insert_one(dummy_cap)
        capabilities = [dummy_cap]

    # 5. Seed Exactly 43 matches
    matches_data = []
    # 43 capability matches
    for idx in range(43):
        req_id = req_ids[idx]
        cap = capabilities[idx % len(capabilities)]
        cap_id = cap["_id"]
        
        # We want:
        # - 38 PASS status (score >= 0.78, e.g. 0.85)
        # - 5 PARTIAL status (score = 0.65)
        # (This totals 43 matches)
        score = 0.85 if idx < 38 else 0.65
        
        match_item = {
            "workspace_id": ws_id,
            "requirement_id": req_id,
            "capability_id": cap_id,
            "semantic_score": score - 0.05,
            "bm25_score": score + 0.03,
            "rerank_score": (score * 20.0) - 10.0,
            "final_score": score,
            "match_evidence": f"Matched previous project {cap['title']} which implements the specific digitized tax functionalities.",
            "match_method": "hybrid",
            "is_approved": True,
            "created_at": datetime.utcnow()
        }
        matches_data.append(match_item)
        
    await db.capability_matches.insert_many(matches_data)
    logger.info("Seeded 43 capability matches.")

    # 6. Seed Exactly 9 Proposal Sections
    sections_data = []
    section_titles = [
        "Executive Summary",
        "Technical Architecture",
        "Security Framework",
        "Compliance Strategy",
        "Project Plan & Deadlines",
        "Financial Bid & Commercials",
        "Legal & Regulatory Alignment",
        "Organizational Capabilities",
        "Appendix: Support Protocols"
    ]
    for idx, title in enumerate(section_titles):
        draft_content = f"### {title.upper()}\n\nThis section outlines our strategy for the {title}. We have matched 38 requirements to complete this phase. "
        if idx == 3: # Compliance Strategy
            # Include Needs Evidence flags
            draft_content += "\n[NEEDS EVIDENCE: Upload ISO 27001 certificate] [NEEDS EVIDENCE: FBR NTN document]"
            
        sections_data.append({
            "workspace_id": ws_id,
            "section_title": title,
            "ai_draft": draft_content,
            "user_edited_content": None,
            "status": "draft" if idx != 0 else "approved",
            "word_count": len(draft_content.split()),
            "needs_evidence_flags": ["Upload ISO 27001 certificate", "FBR NTN document"] if idx == 3 else [],
            "agent_log": {"generated_at": str(datetime.utcnow()), "method": "crewai"},
            "order_index": idx,
            "version_history": [{"content": draft_content, "timestamp": datetime.utcnow(), "word_count": len(draft_content.split())}],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    await db.proposal_sections.insert_many(sections_data)
    logger.info("Seeded 9 proposal sections.")

    # 7. Seed Exactly 38 PASS, 6 PARTIAL, 3 FAIL Compliance Matrix Items
    compliance_items = []
    
    # 38 PASS items
    for idx in range(38):
        req_id = req_ids[idx]
        compliance_items.append({
            "workspace_id": ws_id,
            "requirement_id": req_id,
            "status": "pass",
            "final_score": 0.85,
            "gap_description": "None. Fully satisfied.",
            "recommendation": "No action required.",
            "ai_reasoning": "Requirement satisfies capability library credentials.",
            "assigned_to": "Bid Manager",
            "notes": "",
            "resolved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        })
        
    # 6 PARTIAL items
    for idx in range(38, 44):
        req_id = req_ids[idx]
        compliance_items.append({
            "workspace_id": ws_id,
            "requirement_id": req_id,
            "status": "partial",
            "final_score": 0.65,
            "gap_description": "Matched project lacks exact scale parameters.",
            "recommendation": "Provide details of another contract with contract value above PKR 100M.",
            "ai_reasoning": "Capability matched partially. Missing scale evidence.",
            "assigned_to": "Compliance Lead",
            "notes": "",
            "resolved_at": None,
            "created_at": datetime.utcnow()
        })

    # 3 FAIL items
    for idx in range(44, 47):
        req_id = req_ids[idx]
        compliance_items.append({
            "workspace_id": ws_id,
            "requirement_id": req_id,
            "status": "fail",
            "final_score": 0.0,
            "gap_description": "No direct matches found in capability library.",
            "recommendation": "Upload new certifications or capability records matching the clause.",
            "ai_reasoning": "No relevant experience found.",
            "assigned_to": "Subject Matter Expert",
            "notes": "",
            "resolved_at": None,
            "created_at": datetime.utcnow()
        })

    await db.compliance_items.insert_many(compliance_items)
    logger.info("Seeded compliance matrix: 38 PASS, 6 PARTIAL, 3 FAIL (Overall 82%).")

    # 8. Seed Win Probability Score (74% GO decision)
    score_breakdown = {
        "compliance_completeness": 82.0,
        "domain_experience_match": 75.0,
        "budget_alignment": 80.0,
        "client_relationship": 70.0,
        "competition_risk": 60.0,
        "technical_complexity_fit": 85.0,
        "timeline_feasibility": 75.0
    }
    feature_importance = {
        "compliance_score": 0.25,
        "domain_experience_score": 0.20,
        "budget_alignment": 0.15,
        "past_relationship_with_client": 0.10,
        "competitor_count": 0.10,
        "submission_quality_score": 0.10,
        "timeline_days": 0.10
    }
    bid_score = {
        "workspace_id": ws_id,
        "overall_score": 74.0,
        "win_probability": 0.74,
        "go_no_go": "GO",
        "go_no_go_reasoning": "The RandomForest win prediction engine recommends a GO decision due to high compliance alignment (82%) and solid past performance history with the client.",
        "confidence_level": "HIGH",
        "score_breakdown": score_breakdown,
        "feature_importance": feature_importance,
        "model_version": "1.0.0",
        "scored_at": datetime.utcnow()
    }
    await db.bid_scores.insert_one(bid_score)
    logger.info("Seeded win probability score (74% GO).")
    
    logger.info("Successfully seeded demo workspace FBR Tax Digitization RFP!")

def random_weight(i):
    # Returns a mock weightage for RFP requirements
    import random
    random.seed(i)
    return random.choice([5.0, 10.0, 15.0, 20.0])

if __name__ == "__main__":
    asyncio.run(main())

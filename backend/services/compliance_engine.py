import os
import re
import httpx
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

# DB imports
from models.mongo_models import get_db, Requirement, CapabilityMatch, ProposalSection, ComplianceItem

logger = logging.getLogger("bidengine.compliance")

class ComplianceEngine:
    def __init__(self):
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load encoder in ComplianceEngine: {e}")
            self.encoder = None

        self.api_key = os.getenv("GEMINI_API_KEY", "")

    async def generate_report(self, workspace_id: str) -> Dict[str, Any]:
        """Generates a full compliance matrix report for a workspace"""
        db = await get_db()
        
        # 1. Fetch requirements
        req_cursor = db.requirements.find({"workspace_id": workspace_id})
        requirements = await req_cursor.to_list(100)
        
        # 2. Fetch matches
        match_cursor = db.capability_matches.find({"workspace_id": workspace_id})
        matches = await match_cursor.to_list(500)
        
        # 3. Fetch proposal sections
        sec_cursor = db.proposal_sections.find({"workspace_id": workspace_id})
        sections = await sec_cursor.to_list(100)
        
        # Aggregate proposal text
        proposal_text = " ".join([s.get("user_edited_content") or s.get("ai_draft") or "" for s in sections])

        compliance_items = []
        
        for req in requirements:
            req_id = str(req["_id"])
            req_text = req.get("requirement_text", "")
            
            # Find best match for this requirement
            req_matches = [m for m in matches if str(m["requirement_id"]) == req_id]
            best_match = None
            if req_matches:
                # Get match with highest final score
                req_matches.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
                best_match = req_matches[0]

            score = best_match.get("final_score", 0.0) if best_match else 0.0
            
            # Classify status based on score thresholds
            if score >= 0.78:
                status = "pass"
            elif score >= 0.52:
                status = "partial"
            else:
                status = "fail"

            # Check if requirement is actually addressed in proposal text
            proposal_addressed = True
            if sections and req_text:
                proposal_addressed = self.check_requirement_in_proposal(req_text, proposal_text)
                
                # Demote if evidence exists but draft is missing it
                if not proposal_addressed and status == "pass":
                    status = "partial"

            # Generate reasoning and recommendations
            gap_desc = None
            recom = None
            ai_reasoning = ""

            if status == "pass" and best_match:
                cap_id = best_match.get("capability_id")
                # Find capability title
                cap = await db.capability_records.find_one({"_id": cap_id})
                cap_title = cap.get("title", "Capability") if cap else "Capability"
                ai_reasoning = f"Requirement fully satisfied. Matched library project: '{cap_title}' with {int(score * 100)}% confidence."
                if not proposal_addressed:
                    ai_reasoning += " [Note: Evidence found in capability library, but not yet explicitly incorporated in proposal text.]"
                    gap_desc = "Evidence found in library but not explicitly written in the proposal draft."
                    recom = "Update the proposal section to explicitly reference the FBR ERP or similar projects."
            else:
                # Call LLM or use static generator for gaps
                ai_reasoning = await self.generate_gap_reasoning(req_text, best_match, status)
                gap_desc = ai_reasoning
                recom = self.get_recommendation(req.get("category", "other"), status)

            compliance_items.append({
                "workspace_id": workspace_id,
                "requirement_id": req_id,
                "status": status,
                "final_score": float(score),
                "gap_description": gap_desc,
                "recommendation": recom,
                "ai_reasoning": ai_reasoning,
                "assigned_to": "Bid Manager",
                "notes": "",
                "resolved_at": datetime.utcnow() if status == "pass" else None,
                "created_at": datetime.utcnow()
            })

        # Insert compliance items to DB, removing stale records first
        await db.compliance_items.delete_many({"workspace_id": workspace_id})
        if compliance_items:
            await db.compliance_items.insert_many(compliance_items)

        # Calculate counts
        pass_cnt = sum(1 for i in compliance_items if i["status"] == "pass")
        part_cnt = sum(1 for i in compliance_items if i["status"] == "partial")
        fail_cnt = sum(1 for i in compliance_items if i["status"] == "fail")
        
        overall_score = (pass_cnt + part_cnt * 0.5) / len(compliance_items) * 100 if compliance_items else 0.0

        return {
            "overall_compliance_score": overall_score,
            "pass_count": pass_cnt,
            "partial_count": part_cnt,
            "fail_count": fail_cnt,
            "total_count": len(compliance_items),
            "generated_at": str(datetime.utcnow())
        }

    async def generate_gap_reasoning(self, req_text: str, best_match: Optional[Dict[str, Any]], status: str) -> str:
        """Call Gemini to explain the compliance gap in 2 sentences"""
        evidence_text = best_match.get("match_evidence", "") if best_match else "None found"
        
        prompt = f"""Given the following requirement from a tender document:
Requirement: "{req_text}"
Best evidence found in capability library: "{evidence_text}"
Compliance status: "{status.upper()}"

Explain in exactly two concise sentences why this is a compliance gap and what specific evidence or project experience is needed to resolve this gap. Return ONLY the explanation.
"""
        if not self.api_key:
            # Static mock gap explanations for demo
            if "ISO 27001" in req_text or "certification" in req_text:
                return "The company library contains general information-security descriptions, but lacks a valid, uploaded ISO 27001 certificate artifact. To resolve this, upload a current ISO 27001 PDF under certifications."
            elif "SAP" in req_text or "ERP" in req_text:
                return "The best matched project is a custom web portal which does not satisfy the specific requirement for SAP S/4HANA implementation experience. We need to reference a completed SAP ERP deployment project."
            else:
                return f"No direct match found in the capability library for the required scope of work. We need to document a previous reference project that covers this requirement."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    return text.strip()
        except Exception as e:
            logger.error(f"Failed to generate gap reasoning via Gemini: {e}")
            
        return "A gap was identified because the current proposal does not present sufficient capability evidence for this clause. Please provide details of past projects matching these requirements."

    def check_requirement_in_proposal(self, req_text: str, proposal_text: str) -> bool:
        """Cross-checks if the proposal draft text semantically contains the requirement"""
        if not self.encoder or not proposal_text:
            return True # Fail-safe, don't penalize if model load failed

        try:
            # Segment proposal text into paragraphs
            paragraphs = [p.strip() for p in proposal_text.split("\n") if len(p.strip()) > 30]
            if not paragraphs:
                return False

            req_emb = self.encoder.encode([req_text])[0]
            prop_embs = self.encoder.encode(paragraphs)

            # Cosine similarities
            norms_req = np.linalg.norm(req_emb)
            norms_prop = np.linalg.norm(prop_embs, axis=1)
            
            dots = np.dot(prop_embs, req_emb)
            sims = dots / (norms_prop * norms_req + 1e-9)

            max_sim = float(np.max(sims))
            return max_sim >= 0.65
        except Exception as e:
            logger.error(f"Semantic cross-check failed: {e}")
            return True

    def get_recommendation(self, category: str, status: str) -> str:
        if status == "pass":
            return "No action required."
            
        recommendations = {
            "technical": "Provide detailed system blueprints, API document references, or partner support SLAs.",
            "financial": "Supply audited financial balance sheets from last 3 fiscal years or PKR bank guarantees.",
            "legal": "Attach standard company registration documents, tax registration (NTN), and non-blacklisting affidavits.",
            "experience": "Reference another government or enterprise project showing similar contract value and scope.",
            "deadline": "Adjust proposed project timeline milestones to match the RFP's target completion dates.",
            "certification": "Provide a PDF copy of ISO 27001, CMMI Level 3, or relevant manufacturer partner letters.",
            "other": "Review compliance details and coordinate with the subject matter expert to provide supporting evidence."
        }
        return recommendations.get(category, recommendations["other"])

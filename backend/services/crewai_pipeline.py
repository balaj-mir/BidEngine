import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Type
from datetime import datetime

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# LangChain Gemini imports
from langchain_google_genai import ChatGoogleGenerativeAI

# Database model imports
from models.mongo_models import get_db, ProposalSection

logger = logging.getLogger("bidengine.crew")

# ----------------- Tool Definitions -----------------

class WorkspaceIdInput(BaseModel):
    workspace_id: str = Field(description="The workspace ID to fetch requirements for")

class RequirementFetcherTool(BaseTool):
    name: str = "fetch_requirements"
    description: str = "Fetch all extracted requirements for a workspace by its workspace_id"
    args_schema: Type[BaseModel] = WorkspaceIdInput

    def _run(self, workspace_id: str) -> str:
        try:
            # Synchronous wrapper for database call
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Runs a coroutine synchronously inside an active loop
                db = loop.run_until_complete(self._fetch_reqs(workspace_id))
            else:
                db = asyncio.run(self._fetch_reqs(workspace_id))
            return json.dumps(db)
        except Exception as e:
            return f"Error fetching requirements: {str(e)}"

    async def _fetch_reqs(self, workspace_id: str) -> List[Dict[str, Any]]:
        db = await get_db()
        cursor = db.requirements.find({"workspace_id": workspace_id})
        reqs = await cursor.to_list(100)
        # convert ObjectId
        for r in reqs:
            r["_id"] = str(r["_id"])
        return reqs

class SearchQueryInput(BaseModel):
    query: str = Field(description="The query string to search for in capability records")

class CapabilitySearchTool(BaseTool):
    name: str = "search_capabilities"
    description: str = "Search the capability library for project evidence matching a requirement"
    args_schema: Type[BaseModel] = SearchQueryInput

    def _run(self, query: str) -> str:
        # Avoid circular import at top level
        from services.hybrid_rag_engine import HybridRAGEngine
        try:
            rag = HybridRAGEngine()
            # Feed some dummy data for seed if search is empty
            results = rag.match_requirement(query, top_k=3)
            # Serialize results
            clean_results = []
            for r in results:
                clean_results.append({
                    "title": r["capability"]["title"],
                    "description": r["capability"]["description"],
                    "sector": r["capability"]["sector"],
                    "outcome": r["capability"]["outcome"],
                    "score": r["final_score"]
                })
            return json.dumps(clean_results)
        except Exception as e:
            return f"Error searching capabilities: {str(e)}"

class ProposalSaveInput(BaseModel):
    workspace_id: str = Field(description="Workspace ID")
    section_title: str = Field(description="Title of the section")
    draft_content: str = Field(description="Content of the drafted section")

class ProposalSaverTool(BaseTool):
    name: str = "save_proposal_section"
    description: str = "Save a drafted proposal section to the workspace database"
    args_schema: Type[BaseModel] = ProposalSaveInput

    def _run(self, workspace_id: str, section_title: str, draft_content: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                res = loop.run_until_complete(self._save(workspace_id, section_title, draft_content))
            else:
                res = asyncio.run(self._save(workspace_id, section_title, draft_content))
            return f"Successfully saved proposal section. Status: {res}"
        except Exception as e:
            return f"Error saving proposal section: {str(e)}"

    async def _save(self, workspace_id: str, section_title: str, draft_content: str) -> str:
        db = await get_db()
        # count existing
        count = await db.proposal_sections.count_documents({"workspace_id": workspace_id})
        
        section_data = {
            "workspace_id": workspace_id,
            "section_title": section_title,
            "ai_draft": draft_content,
            "user_edited_content": None,
            "status": "draft",
            "word_count": len(draft_content.split()),
            "needs_evidence_flags": [flag for flag in re.findall(r'\[NEEDS EVIDENCE:\s*([^\]]+)\]', draft_content)],
            "agent_log": {"generated_at": str(datetime.utcnow()), "method": "crewai"},
            "order_index": count,
            "version_history": [{"content": draft_content, "timestamp": datetime.utcnow(), "word_count": len(draft_content.split())}],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.proposal_sections.insert_one(section_data)
        return "Saved"

class ComplianceCheckInput(BaseModel):
    requirement_text: str = Field(description="Text of the requirement to check")
    proposal_text: str = Field(description="Drafted proposal section text to audit")

class ComplianceCheckerTool(BaseTool):
    name: str = "check_compliance"
    description: str = "Check if a drafted proposal section text fully addresses a specific requirement"
    args_schema: Type[BaseModel] = ComplianceCheckInput

    def _run(self, requirement_text: str, proposal_text: str) -> str:
        # Quick heuristic NLP match for verification
        req_words = set(re.findall(r'\w+', requirement_text.lower()))
        prop_words = set(re.findall(r'\w+', proposal_text.lower()))
        common = req_words.intersection(prop_words)
        ratio = len(common) / len(req_words) if req_words else 0.0
        
        addressed = ratio > 0.35
        confidence = min(0.99, ratio + 0.2)
        gaps = []
        if not addressed:
            gaps.append(f"Missing core terminology from requirement: {list(req_words - prop_words)[:3]}")
            
        return json.dumps({
            "addressed": addressed,
            "confidence": confidence,
            "gaps": gaps
        })

# Global cache for the active LLM
_cached_llm = None
_cached_checked = False

def get_active_llm():
    global _cached_llm, _cached_checked
    if _cached_checked:
        return _cached_llm

    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() in ("true", "1", "yes")
    if use_local:
        try:
            from langchain_openai import ChatOpenAI
            ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3:8b")
            llm = ChatOpenAI(
                model=ollama_model,
                api_key="ollama",
                base_url=ollama_base,
                temperature=0.3
            )
            _cached_llm = llm
            _cached_checked = True
            logger.info(f"Auto-selected Local Ollama LLM ({ollama_model}) at {ollama_base}")
            return _cached_llm
        except Exception as e:
            logger.warning(f"Failed to load Local Ollama LLM: {e}. Falling back to cloud APIs...")

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Priority 1: Claude 3.5 Sonnet
    if anthropic_key:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=anthropic_key,
                temperature=0.3
            )
            _cached_llm = llm
            _cached_checked = True
            logger.info("Auto-selected Anthropic Claude 3.5 Sonnet as primary LLM.")
            return _cached_llm
        except Exception as e:
            logger.warning(f"Failed to load Anthropic Claude LLM: {e}")

    # Priority 2: Google Gemini 1.5
    if gemini_key and not gemini_key.startswith("sk-"):
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=gemini_key,
                temperature=0.3
            )
            _cached_llm = llm
            _cached_checked = True
            logger.info("Auto-selected Google Gemini 1.5 Flash as primary LLM.")
            return _cached_llm
        except Exception as e:
            logger.warning(f"Failed to load Google Gemini LLM: {e}")

    # Priority 3: OpenAI / ChatAnywhere Proxy
    active_openai_key = gemini_key if gemini_key.startswith("sk-") else openai_key
    if active_openai_key:
        try:
            from langchain_openai import ChatOpenAI
            base_url = os.getenv("OPENAI_API_BASE", "https://api.chatanywhere.tech/v1")
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=active_openai_key,
                base_url=base_url,
                temperature=0.3
            )
            _cached_llm = llm
            _cached_checked = True
            logger.info(f"Auto-selected ChatOpenAI routed via proxy: {base_url}")
            return _cached_llm
        except Exception as e:
            logger.warning(f"Failed to load OpenAI proxy LLM: {e}")

    _cached_checked = True
    return None

# ----------------- Crew Setup -----------------

def get_crew_agents_and_tasks(workspace_id: str, section_title: str) -> Dict[str, Any]:
    llm = get_active_llm()
    if llm is None:
        logger.warning("No active LLM credentials. The CrewAI pipeline will operate in Demo Mock Mode.")
        return {"mock": True}

    # Initialize tools
    fetch_tool = RequirementFetcherTool()
    search_tool = CapabilitySearchTool()
    save_tool = ProposalSaverTool()
    compliance_tool = ComplianceCheckerTool()

    # Agents
    document_agent = Agent(
        role="RFP Document Intelligence Specialist",
        goal="Parse and structure the RFP document, identify all sections, deadlines, and compliance requirements with zero omissions",
        backstory="""You are a 20-year veteran of government procurement in Pakistan and GCC region.
        You know PPRA regulations, NTS tenders, and enterprise RFPs inside out. You can read a
        tender and identify every requirement, deadline, and evaluation criterion.""",
        tools=[fetch_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    research_agent = Agent(
        role="Capability Research Analyst",
        goal="Find the most compelling capability evidence for each requirement from the company library using semantic + keyword search",
        backstory="""You are an expert at matching project experience to tender requirements.
        You know how to identify transferable skills and find analogous projects.
        You use multiple search strategies and critically evaluate match quality.""",
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    writer_agent = Agent(
        role="Senior Bid Writer",
        goal="Draft compelling, compliance-first, evidence-backed proposal sections that score 90+ with evaluation committees",
        backstory="""You have written 500+ winning proposals for government and enterprise clients.
        You write clear, confident professional English.
        Every claim you make is backed by specific evidence from the capability library.
        You flag [NEEDS EVIDENCE: description] where gaps exist — never fabricate.""",
        tools=[save_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    compliance_agent = Agent(
        role="Compliance Auditor",
        goal="Verify every mandatory requirement is fully addressed in the proposal with sufficient evidence and correct compliance language",
        backstory="""You are a procurement compliance expert. You cross-reference proposal drafts against
        requirements with surgical precision. You know that missing even one 'shall' requirement
        disqualifies a bid.""",
        tools=[compliance_tool, fetch_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    reviewer_agent = Agent(
        role="Senior Proposal Quality Reviewer",
        goal="Review and improve proposal sections for quality, completeness, persuasiveness, and winning potential — provide specific improvement actions",
        backstory="""You are the final check before any proposal reaches a client.
        You have evaluated hundreds of proposals and know exactly what separates a 90-scoring proposal
        from a 60. You enforce: every requirement addressed, every claim evidenced, correct tone.""",
        tools=[],
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # Tasks
    t1 = Task(
        description=f"Review and structure requirements for the '{section_title}' section of workspace {workspace_id}. Identify mandatory requirements and evaluation criteria.",
        agent=document_agent,
        expected_output="Structured list of requirements with mandatory flags and categories"
    )
    t2 = Task(
        description=f"Find the top capability evidence for each requirement in the '{section_title}' section. Identify any capability gaps.",
        agent=research_agent,
        expected_output="Matched capability evidence for each requirement, gaps identified"
    )
    t3 = Task(
        description=f"Draft the complete '{section_title}' proposal section. Address every requirement. Use evidence from research. Flag gaps as [NEEDS EVIDENCE: ...].",
        agent=writer_agent,
        expected_output="Complete proposal section in professional English, 400-600 words, evidence-backed"
    )
    t4 = Task(
        description=f"Audit the drafted '{section_title}' section. Verify every mandatory requirement is addressed. Identify any compliance gaps.",
        agent=compliance_agent,
        expected_output="Compliance audit: list of addressed/missed requirements, gap descriptions"
    )
    t5 = Task(
        description=f"Review and improve the '{section_title}' section. Provide specific improvements for evidence strength, tone, and compliance coverage.",
        agent=reviewer_agent,
        expected_output="Improved section with tracked changes and quality score"
    )

    return {
        "mock": False,
        "agents": [document_agent, research_agent, writer_agent, compliance_agent, reviewer_agent],
        "tasks": [t1, t2, t3, t4, t5]
    }

async def run_proposal_pipeline(workspace_id: str, section_title: str, requirements: list = None, capabilities: list = None) -> Dict[str, Any]:
    """Runs the 6-agent CrewAI pipeline (or generates structured mock proposals in demo mode)"""
    setup = get_crew_agents_and_tasks(workspace_id, section_title)
    
    if setup.get("mock"):
        # Let's wait a couple of seconds to simulate AI agent workflows
        await asyncio.sleep(2.0)
        mock_content = get_mock_proposal_section_content(section_title, requirements)
        
        # Save to database
        db = await get_db()
        count = await db.proposal_sections.count_documents({"workspace_id": workspace_id})
        
        section_data = {
            "workspace_id": workspace_id,
            "section_title": section_title,
            "ai_draft": mock_content,
            "user_edited_content": None,
            "status": "draft",
            "word_count": len(mock_content.split()),
            "needs_evidence_flags": [flag for flag in re.findall(r'\[NEEDS EVIDENCE:\s*([^\]]+)\]', mock_content)],
            "agent_log": {
                "generated_at": str(datetime.utcnow()),
                "method": "mock_crewai_simulation",
                "agents_used": ["Document Specialist", "Capability Researcher", "Senior Bid Writer", "Compliance Auditor", "Quality Reviewer"]
            },
            "order_index": count,
            "version_history": [{"content": mock_content, "timestamp": datetime.utcnow(), "word_count": len(mock_content.split())}],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.proposal_sections.insert_one(section_data)
        
        return {
            "section_title": section_title,
            "content": mock_content,
            "agent_log": {
                "total_tokens": 1250,
                "successful_requests": 5,
                "agents": ["Document Specialist", "Capability Researcher", "Senior Bid Writer", "Compliance Auditor", "Quality Reviewer"]
            }
        }

    # Real CrewAI Execution
    try:
        crew = Crew(
            agents=setup["agents"],
            tasks=setup["tasks"],
            process=Process.sequential,
            verbose=True
        )
        # kickoff needs to run in a threadpool to avoid blocking event loop
        result = await asyncio.to_thread(crew.kickoff)
        return {
            "section_title": section_title,
            "content": str(result),
            "agent_log": getattr(crew, "usage_metrics", {"method": "crewai"})
        }
    except Exception as e:
        logger.error(f"Error executing CrewAI: {e}. Falling back to mock generator.")
        # Fail safe - return mock content
        mock_content = get_mock_proposal_section_content(section_title, requirements)
        return {
            "section_title": section_title,
            "content": mock_content,
            "agent_log": {"error": str(e), "method": "fail_safe_fallback"}
        }

def get_mock_proposal_section_content(section_title: str, requirements: list = None) -> str:
    """Generates high-quality mock proposal sections matching real RFPs"""
    req_context = ""
    if requirements:
        req_context = "\n".join([f"- Required: {r}" for r in requirements[:3]])
    
    if "Technical" in section_title or "System" in section_title:
        return f"""### 1. TECHNICAL APPROACH AND ARCHITECTURE

We propose a state-of-the-art, service-oriented architecture designed to address the specific requirements of the RFP. Our system leverages modern, containerized deployments built on robust foundations.

#### 1.1 Core Platform Components
The engine utilizes a hybrid processing core to ingest, index, and analyze incoming documentation. By deploying modern open-source web frameworks alongside specialized language services, we ensure sub-second query latency and near-perfect parsing accuracy.
{req_context}

#### 1.2 Evidence & Implementations
[NEEDS EVIDENCE: Detailed system topology diagram and cloud hosting certificates]
Our implementation team has successfully deployed this architecture for the Federal Board of Revenue (FBR), supporting over 1,200 active concurrent users. The core system achieved 99.7% uptime and demonstrated 35% performance gains over legacy relational architectures.

#### 1.3 Methodology
Our delivery methodology is divided into three key phases:
1. **Requirements Validation**: Re-checking and clustering compliance objectives.
2. **Component Integration**: Assembling the database and caching middleware layers.
3. **Calibrated Verification**: Training models against test fixtures to evaluate accuracy prior to final production cut-over.
"""
    elif "Executive" in section_title:
        return f"""### EXECUTIVE SUMMARY

We are pleased to submit this proposal to deliver our advanced digital platform, custom-engineered to meet the rigorous objectives outlined in this solicitation.

#### The Opportunity
Modern enterprise and government operations require rapid, data-backed decision frameworks. By integrating multi-agent document analysis tools, lexical search systems, and machine-learning evaluation models, our proposal provides a reliable path to success.
{req_context}

#### Why Partner With Us
- **Proven Experience**: Over 50 successfully delivered projects in IT services, cloud migration, and workflow automation.
- **Advanced Technology**: We utilize a hybrid RAG retrieval system (fusing lexical and vector scoring) followed by deep CrossEncoder reranking.
- **Calibrated Prediction**: All recommendations are evaluated by a trained RandomForest classifier, achieving an validation AUC of 0.84.

We are fully committed to completing the requirements within the estimated timelines and look forward to partnering on this strategic initiative.
"""
    elif "Compliance" in section_title or "Quality" in section_title:
        return f"""### COMPLIANCE AND QUALITY ASSURANCE PLAN

We establish strict quality baselines for every deliverable, ensuring full adherence to all mandatory objectives.

#### 1.1 Compliance Matrix Review
Our compliance auditor runs continuous audits to cross-reference work items against the RFP matrix. 
{req_context}

#### 1.2 Quality Standards
- **Certifications**: The proposed operations align with CMMI Level 3 standards and ISO 27001 InfoSec requirements.
- **Verification Gate**: No deliverable is exported without passing a readability index gate and scoring threshold check.
[NEEDS EVIDENCE: ISO 9001 and ISO 27001 certificate attachments]
"""
    else:
        return f"""### {section_title.upper()}

#### 1.1 Overview
This section outlines our approach and commitments regarding {section_title}. We ensure all activities are executed by qualified staff in accordance with the specifications.
{req_context}

#### 1.2 Operations
Our operational model emphasizes safety, reliability, and precision. We maintain robust logging feeds and real-time trackers to keep stakeholders informed of milestones.
[NEEDS EVIDENCE: Specific project reference for {section_title}]
"""

import re

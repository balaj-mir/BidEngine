from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

# Auth Schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Workspace Schemas
class WorkspaceCreateRequest(BaseModel):
    name: str

class PipelineLogSchema(BaseModel):
    timestamp: datetime
    stage: str
    message: str

class WorkspaceResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    rfp_filename: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requirements_count: int = 0
    matches_count: int = 0
    sections_count: int = 0
    latest_score: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

# Requirement Schemas
class RequirementResponse(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    section: str
    requirement_text: str
    is_mandatory: bool
    category: str
    source_page: Optional[int]
    deadline_date: Optional[str]
    evaluation_weight: Optional[float]
    cluster_id: Optional[int]
    compliance_keywords: List[str]
    created_at: datetime

    class Config:
        populate_by_name = True

# Capability Record Schemas
class CapabilityRecordCreate(BaseModel):
    id: str = Field(alias="_id")  # e.g., cap_001
    title: str
    description: str
    sector: str
    client_type: str
    year_completed: int
    contract_value: float
    currency: str = "PKR"
    duration_months: int
    certifications: List[str]
    team_size: int
    keywords: List[str]
    outcome: str
    client_reference_available: bool = False

    class Config:
        populate_by_name = True

# Capability Match Schemas
class CapabilityMatchResponse(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    requirement_id: str
    capability_id: str
    semantic_score: float
    bm25_score: float
    rerank_score: float
    final_score: float
    match_evidence: str
    match_method: str
    is_approved: Optional[bool]
    created_at: datetime
    capability_detail: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

class MatchApproveRequest(BaseModel):
    is_approved: bool

# Proposal Section Schemas
class SectionCreateRequest(BaseModel):
    section_title: str
    section_type: Optional[str] = None

class SectionUpdateRequest(BaseModel):
    user_edited_content: str
    status: Optional[Literal['draft', 'reviewed', 'approved']] = None

class SectionStatusUpdateRequest(BaseModel):
    status: Literal['draft', 'reviewed', 'approved']

class SectionResponse(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    section_title: str
    ai_draft: str
    user_edited_content: Optional[str]
    status: str
    word_count: int
    needs_evidence_flags: List[str]
    agent_log: Dict[str, Any]
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class VersionResponse(BaseModel):
    content: str
    timestamp: datetime
    word_count: int

# Compliance Schemas
class ComplianceItemResponse(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    requirement_id: str
    requirement_text: Optional[str] = None
    status: str
    final_score: float
    gap_description: Optional[str]
    recommendation: Optional[str]
    ai_reasoning: Optional[str]
    assigned_to: Optional[str]
    notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        populate_by_name = True

class ComplianceOverrideRequest(BaseModel):
    status: Literal['pass', 'partial', 'fail', 'pending']
    notes: Optional[str] = None

class ComplianceNoteRequest(BaseModel):
    notes: str

# Score Schemas
class ScoreBreakdownSchema(BaseModel):
    compliance_completeness: float
    domain_experience_match: float
    budget_alignment: float
    client_relationship: float
    competition_risk: float
    technical_complexity_fit: float
    timeline_feasibility: float

class BidScoreResponse(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    overall_score: float
    win_probability: float
    go_no_go: str
    go_no_go_reasoning: Optional[str]
    confidence_level: str
    score_breakdown: ScoreBreakdownSchema
    feature_importance: Dict[str, float]
    model_version: str
    scored_at: datetime

    class Config:
        populate_by_name = True

class ScoreSimulationRequest(BaseModel):
    compliance_score: Optional[float] = None
    domain_experience_score: Optional[float] = None
    budget_alignment: Optional[float] = None
    competitor_count: Optional[int] = None
    certifications_met: Optional[bool] = None
    contract_value: Optional[float] = None
    incumbent_present: Optional[bool] = None
    timeline_days: Optional[int] = None

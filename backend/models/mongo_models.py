import os
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, BeforeValidator, TypeAdapter
from typing_extensions import Annotated
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Configure logger
logger = logging.getLogger("bidengine.db")
logging.basicConfig(level=logging.INFO)

# PyObjectId type for handling MongoDB ObjectIds
def validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]

# ----------------- database helper / client -----------------
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/bidengine")

class MockCollection:
    """Mock asynchronous MongoDB collection for zero-crash fallback when DB is missing"""
    def __init__(self, name: str):
        self.name = name
        self._data: Dict[str, Dict[str, Any]] = {}
        logger.warning(f"Using MockCollection for '{name}'")

    async def insert_one(self, document: Dict[str, Any], *args, **kwargs):
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = str(ObjectId())
        elif isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        self._data[doc["_id"]] = doc
        class Result:
            inserted_id = doc["_id"]
        return Result()

    async def insert_many(self, documents: List[Dict[str, Any]], *args, **kwargs):
        _inserted_ids = []
        for doc in documents:
            if "_id" not in doc:
                doc["_id"] = str(ObjectId())
            elif isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])
            self._data[doc["_id"]] = doc
            _inserted_ids.append(doc["_id"])
        class Result:
            def __init__(self, ids):
                self.inserted_ids = ids
        return Result(_inserted_ids)

    async def find_one(self, filter: Dict[str, Any] = None, *args, **kwargs) -> Optional[Dict[str, Any]]:
        # Extremely basic query filter matcher
        for doc in self._data.values():
            match = True
            for k, v in filter.items():
                if k == "_id" or k == "id":
                    val = str(doc.get("_id"))
                    if val != str(v):
                        match = False
                        break
                else:
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                return dict(doc)
        return None

    def find(self, filter: Dict[str, Any] = None, *args, **kwargs):
        filter = filter or {}
        class MockCursor:
            def __init__(self, data, filt):
                self.results = []
                for doc in data.values():
                    match = True
                    for k, v in filt.items():
                        if k == "_id" or k == "id":
                            val = str(doc.get("_id"))
                            if val != str(v):
                                match = False
                                break
                        elif k.endswith("$in") or (isinstance(v, dict) and "$in" in v):
                            # Handle simple $in
                            in_list = v.get("$in") if isinstance(v, dict) else []
                            if doc.get(k.replace(".$in", "")) not in in_list:
                                match = False
                                break
                        else:
                            if doc.get(k) != v:
                                match = False
                                break
                    if match:
                        self.results.append(dict(doc))
                self.index = 0

            def sort(self, key, direction=-1):
                # Simple sort implementation
                reverse = True if direction == -1 else False
                self.results.sort(key=lambda x: x.get(key, ""), reverse=reverse)
                return self

            def limit(self, count):
                self.results = self.results[:count]
                return self

            async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
                if length is not None:
                    return self.results[:length]
                return self.results

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.results):
                    raise StopAsyncIteration
                res = self.results[self.index]
                self.index += 1
                return res

        return MockCursor(self._data, filter)

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any], upsert: bool = False, *args, **kwargs):
        doc = await self.find_one(filter)
        if not doc:
            if upsert:
                doc = {}
                for k, v in filter.items():
                    if not k.startswith("$"):
                        doc[k] = v
                if "_id" not in doc:
                    doc["_id"] = str(ObjectId())
                self._data[doc["_id"]] = doc
            else:
                class UpdateResult:
                    matched_count = 0
                    modified_count = 0
                return UpdateResult()

        # Handle basic $set operator
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        # Handle basic $push operator
        if "$push" in update:
            for k, v in update["$push"].items():
                if k not in doc or not isinstance(doc[k], list):
                    doc[k] = []
                doc[k].append(v)

        self._data[doc["_id"]] = doc
        class UpdateResult:
            matched_count = 1
            modified_count = 1
        return UpdateResult()

    async def delete_one(self, filter: Dict[str, Any], *args, **kwargs):
        doc = await self.find_one(filter)
        if doc:
            self._data.pop(doc["_id"])
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

    async def delete_many(self, filter: Dict[str, Any], *args, **kwargs):
        cursor = self.find(filter)
        results = await cursor.to_list()
        deleted = 0
        for r in results:
            self._data.pop(r["_id"])
            deleted += 1
        class DeleteResult:
            deleted_count = deleted
        return DeleteResult()

    async def count_documents(self, filter: Dict[str, Any], *args, **kwargs) -> int:
        cursor = self.find(filter)
        results = await cursor.to_list()
        return len(results)

class MockDatabase:
    """Mock MongoDB database for zero-crash fallback"""
    def __init__(self):
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]

    def __getattr__(self, name: str) -> MockCollection:
        return self[name]

# Global DB client variables
db_client = None
db = None
is_mock_db = False

def init_db_connection():
    global db_client, db, is_mock_db
    try:
        from pymongo import MongoClient
        # Synchronous ping to force exception if DB is down
        sync_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=1500)
        sync_client.admin.command('ping')
        
        # 1.5 seconds timeout for quick fallback if DB is not running
        db_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=1500)
        db = db_client.get_default_database()
        is_mock_db = False
        logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}. Falling back to MockDatabase.")
        db = MockDatabase()
        is_mock_db = True

# Initialize right away
init_db_connection()

async def get_db():
    return db

# ----------------- DB Models -----------------

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: str
    hashed_password: str
    name: str
    role: Literal['manager', 'sme', 'admin'] = 'manager'
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class PipelineLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str
    message: str
    token_usage: Optional[int] = 0
    estimated_cost_usd: Optional[float] = 0.0

class Workspace(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    rfp_filename: Optional[str] = None
    rfp_text: Optional[str] = None
    rfp_pages: List[Dict[str, Any]] = Field(default_factory=list)  # [{"page_num": int, "text": str, "tables": List[str]}]
    rfp_metadata: Dict[str, Any] = Field(default_factory=dict)
    status: Literal['uploaded', 'extracting', 'extracted', 'matching', 'drafting', 'scoring', 'complete', 'error'] = 'uploaded'
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_log: List[PipelineLogEntry] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class Requirement(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    workspace_id: str
    section: str
    requirement_text: str
    is_mandatory: bool = False
    category: Literal['technical', 'financial', 'legal', 'experience', 'deadline', 'certification', 'other'] = 'other'
    source_page: Optional[int] = None
    deadline_date: Optional[str] = None
    evaluation_weight: Optional[float] = None
    cluster_id: Optional[int] = None
    compliance_keywords: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class CapabilityRecord(BaseModel):
    id: str = Field(alias="_id")  # User-controlled IDs like cap_001
    title: str
    description: str
    sector: str
    client_type: str
    year_completed: int
    contract_value: float
    currency: str = "PKR"
    duration_months: int
    certifications: List[str] = Field(default_factory=list)
    team_size: int
    keywords: List[str] = Field(default_factory=list)
    outcome: str
    client_reference_available: bool = False
    embedding_id: Optional[str] = None
    bm25_doc_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class CompetitorIntelligence(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    competitor_name: str
    win_rate: float
    typical_pricing_tier: Literal['LOW', 'MEDIUM', 'HIGH']
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class CapabilityMatch(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    workspace_id: str
    requirement_id: str
    capability_id: str
    semantic_score: float
    bm25_score: float
    rerank_score: float
    final_score: float
    match_evidence: str
    match_method: Literal['semantic', 'bm25', 'hybrid'] = 'hybrid'
    is_approved: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class VersionHistoryEntry(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    word_count: int

class ProposalSection(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    workspace_id: str
    section_title: str
    ai_draft: str
    user_edited_content: Optional[str] = None
    status: Literal['draft', 'reviewed', 'approved'] = 'draft'
    word_count: int = 0
    needs_evidence_flags: List[str] = Field(default_factory=list)
    agent_log: Dict[str, Any] = Field(default_factory=dict)
    order_index: int = 0
    version_history: List[VersionHistoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class ComplianceItem(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    workspace_id: str
    requirement_id: str
    status: Literal['pass', 'partial', 'fail', 'pending'] = 'pending'
    final_score: float = 0.0
    gap_description: Optional[str] = None
    recommendation: Optional[str] = None
    ai_reasoning: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

class ScoreBreakdown(BaseModel):
    compliance_completeness: float
    domain_experience_match: float
    budget_alignment: float
    client_relationship: float
    competition_risk: float
    technical_complexity_fit: float
    timeline_feasibility: float

class BidScore(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    workspace_id: str
    overall_score: float
    win_probability: float
    go_no_go: Literal['GO', 'CONDITIONAL', 'NO-GO']
    go_no_go_reasoning: Optional[str] = None
    confidence_level: Literal['HIGH', 'MEDIUM', 'LOW']
    score_breakdown: ScoreBreakdown
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "1.0.0"
    scored_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }

# ----------------- DB Indexes -----------------
async def create_indexes():
    """Create indexes if we are not on a mock database"""
    if is_mock_db:
        return
    try:
        await db.users.create_index("email", unique=True)
        await db.workspaces.create_index("created_by")
        await db.requirements.create_index("workspace_id")
        await db.capability_records.create_index("sector")
        await db.capability_matches.create_index("workspace_id")
        await db.proposal_sections.create_index([("workspace_id", 1), ("order_index", 1)])
        await db.compliance_items.create_index("workspace_id")
        await db.bid_scores.create_index("workspace_id")
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.error(f"Could not create MongoDB indexes: {e}")

# Run async index creation
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(create_indexes())
    else:
        loop.run_until_complete(create_indexes())
except Exception:
    pass

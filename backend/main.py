import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Database and Model initialization
from models.mongo_models import init_db_connection, is_mock_db

# Import routers
from routers import workspace, upload, match, draft, compliance, score, export, auth

# Configure logger
logger = logging.getLogger("bidengine.main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

ml_model_loaded = False
chroma_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ml_model_loaded, chroma_ready
    logger.info("Starting up BidEngine AI backend...")
    
    # 1. Initialize MongoDB connection
    init_db_connection()
    
    # 2. Check if trained ML model exists (optional - may require heavy deps)
    try:
        from services.ml_win_scorer import MLWinScorer
        scorer = MLWinScorer()
        if os.path.exists(scorer.model_path):
            try:
                scorer.predict({"compliance_score": 50, "domain_experience_score": 50})
                ml_model_loaded = True
                logger.info("ML Scorer RandomForest model successfully loaded.")
            except Exception as e:
                logger.error(f"Failed to load ML model during startup: {e}")
                ml_model_loaded = False
        else:
            logger.warning("No pre-trained ML model pkl found. Will train model on seed or run in heuristic fallback mode.")
            ml_model_loaded = False
    except Exception as e:
        logger.warning(f"ML Win Scorer unavailable (missing deps): {e}")
        ml_model_loaded = False

    # 3. Check ChromaDB vector store connection (optional - may require heavy deps)
    try:
        from services.hybrid_rag_engine import HybridRAGEngine
        try:
            rag = HybridRAGEngine()
            # check if collection is accessible
            if rag.collection is not None:
                chroma_ready = True
                logger.info("ChromaDB vector store is ready.")
            else:
                chroma_ready = False
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB connection on startup: {e}")
            chroma_ready = False
    except Exception as e:
        logger.warning(f"Hybrid RAG Engine unavailable (missing deps): {e}")
        chroma_ready = False

    yield
    
    logger.info("Shutting down BidEngine AI backend...")

app = FastAPI(
    title="BidEngine AI",
    description="AI-Powered Bid & Proposal Response Engine API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api prefix
app.include_router(workspace.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(match.router, prefix="/api")
app.include_router(draft.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")
app.include_router(score.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# ----------------- Health and Exception Handlers -----------------

@app.get("/health")
async def health_check():
    from services.ml_win_scorer import MLWinScorer
    scorer = MLWinScorer()
    has_pkl = os.path.exists(scorer.model_path)
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "ml_model_loaded": ml_model_loaded or has_pkl,
        "chroma_ready": chroma_ready,
        "database": "mock" if is_mock_db else "mongodb"
    }

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Resource not found", "code": "NOT_FOUND"}
    )

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "code": "VALIDATION_ERROR"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.exception("Internal Server Error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred", "code": "SERVER_ERROR"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

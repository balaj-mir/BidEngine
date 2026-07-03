import os
import sys
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

# Mock motor and other heavy modules before importing main to avoid timeouts and ModuleNotFoundErrors
from unittest.mock import MagicMock
mock_motor_client = MagicMock(side_effect=Exception("Forced mock database fallback"))
sys.modules['motor'] = MagicMock()
sys.modules['motor.motor_asyncio'] = MagicMock()
sys.modules['motor.motor_asyncio'].AsyncIOMotorClient = mock_motor_client
sys.modules['fitz'] = MagicMock()
sys.modules['docx'] = MagicMock()
sys.modules['docx.shared'] = MagicMock()
sys.modules['docx.enum'] = MagicMock()
sys.modules['docx.enum.text'] = MagicMock()
sys.modules['docx.enum.table'] = MagicMock()
sys.modules['docx.oxml'] = MagicMock()
sys.modules['docx.oxml.ns'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['rank_bm25'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['numpy'] = MagicMock()
mock_joblib = MagicMock()
mock_joblib.load.side_effect = Exception("Forced mock joblib load failure")
sys.modules['joblib'] = mock_joblib
sys.modules['spacy'] = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.lib.colors'] = MagicMock()
sys.modules['reportlab.lib.units'] = MagicMock()
sys.modules['reportlab.platypus'] = MagicMock()
sys.modules['reportlab.lib.styles'] = MagicMock()
sys.modules['reportlab.graphics'] = MagicMock()
sys.modules['reportlab.graphics.shapes'] = MagicMock()
sys.modules['reportlab.graphics.charts'] = MagicMock()
sys.modules['reportlab.graphics.charts.piecharts'] = MagicMock()
sys.modules['reportlab.graphics.charts.barcharts'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()
sys.modules['openpyxl.styles'] = MagicMock()
sys.modules['openpyxl.utils'] = MagicMock()
sys.modules['celery'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['crewai'] = MagicMock()
sys.modules['crewai.tools'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.ensemble'] = MagicMock()
sys.modules['sklearn.model_selection'] = MagicMock()
sys.modules['sklearn.preprocessing'] = MagicMock()
sys.modules['sklearn.calibration'] = MagicMock()
sys.modules['sklearn.metrics'] = MagicMock()

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.mongo_models import get_db, init_db_connection

@pytest.fixture(scope="session")
def event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    # Initialize connection which falls back to MockDatabase if offline
    init_db_connection()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

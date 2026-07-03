import io
import zipfile
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from routers.auth_utils import get_current_user_id

# DB and Service imports
from models.mongo_models import get_db
from services.export_service import ExportService

logger = logging.getLogger("bidengine.export")
router = APIRouter(prefix="/workspaces", tags=["exports"])

@router.get("/{id}/export/proposal.docx")
async def export_proposal_docx(id: str, db=Depends(get_db)):
    try:
        exporter = ExportService()
        docx_bytes = await exporter.export_proposal_docx(id)
        
        file_stream = io.BytesIO(docx_bytes)
        filename = f"proposal_response_{id}.docx"
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Failed to export DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export proposal: {str(e)}")

@router.get("/{id}/export/compliance.xlsx")
async def export_compliance_xlsx(id: str, db=Depends(get_db)):
    try:
        exporter = ExportService()
        xlsx_bytes = await exporter.export_compliance_xlsx(id)
        
        file_stream = io.BytesIO(xlsx_bytes)
        filename = f"compliance_matrix_{id}.xlsx"
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Failed to export XLSX: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export compliance matrix: {str(e)}")

@router.get("/{id}/export/scorecard.pdf")
async def export_scorecard_pdf(id: str, db=Depends(get_db)):
    try:
        exporter = ExportService()
        pdf_bytes = await exporter.export_scorecard_pdf(id)
        
        file_stream = io.BytesIO(pdf_bytes)
        filename = f"go_nogo_scorecard_{id}.pdf"
        
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export scorecard: {str(e)}")

@router.get("/{id}/export/all.zip")
async def export_all_zip(id: str, db=Depends(get_db)):
    try:
        exporter = ExportService()
        
        docx_bytes = await exporter.export_proposal_docx(id)
        xlsx_bytes = await exporter.export_compliance_xlsx(id)
        pdf_bytes = await exporter.export_scorecard_pdf(id)
        
        # Zip files together in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("proposal_response.docx", docx_bytes)
            zip_file.writestr("compliance_matrix.xlsx", xlsx_bytes)
            zip_file.writestr("go_nogo_scorecard.pdf", pdf_bytes)
            
        zip_buffer.seek(0)
        filename = f"bid_bundle_{id}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Failed to export zip bundle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export zip bundle: {str(e)}")

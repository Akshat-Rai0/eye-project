# Defines HTTP endpoints for document-related operations (upload, list, delete).
from fastapi import APIRouter, UploadFile, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.services.document_services import upload_document
from app.services.ai_service import process_document_ai

router = APIRouter()

@router.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Upload a document and trigger AI processing in the background.
    
    Flow:
    1. Upload and save document to DB (fast, returns immediately)
    2. Queue AI processing as background task (runs after response sent)
    3. Background task creates its own DB session to avoid conflicts
    """
    # Step 1: Upload document synchronously
    doc = await upload_document(file, session)
    
    # Step 2: Queue AI processing (runs AFTER response is sent)
    # Note: We pass doc.id, not the entire doc object or session
    background_tasks.add_task(process_document_ai, doc.id)
    
    # Step 3: Return immediately to client
    return {
        "id": doc.id,
        "filename": doc.filename,
        "message": "Upload successful. AI processing started in background."
    }
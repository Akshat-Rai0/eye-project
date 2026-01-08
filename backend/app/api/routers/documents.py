from fastapi import APIRouter, UploadFile, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

# Import your models and schemas
from app.db.database import get_session
from app.models.document import Document
from app.schemas.document_schemas import DocumentOut # Ensure this matches your file name
from app.services.document_services import upload_document
from app.services.ai_service import process_document_ai

router = APIRouter()

@router.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    # Step 1: Upload and save to DB
    doc = await upload_document(file, session)
    
    # Step 2: Queue AI (Pass only the ID)
    background_tasks.add_task(process_document_ai, doc.id)
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "message": "Upload successful. AI processing started in background."
    }

@router.get("/search", response_model=List[DocumentOut])
async def search_documents(
    tag: Optional[str] = Query(None, description="Filter by a specific YOLO tag"),
    q: Optional[str] = Query(None, description="Search keyword in Moondream caption"),
    limit: int = 20,
    session: AsyncSession = Depends(get_session) # Fixed name to 'session' and used 'get_session'
):
    query = select(Document)

    # 1. Filter by YOLO Tags (Postgres ARRAY logic)
    if tag:
        # Postgres 'ANY' syntax for SQLAlchemy
        query = query.filter(Document.tags.any(tag))

    # 2. Search in Caption (Case-insensitive)
    if q:
        query = query.filter(Document.caption.ilike(f"%{q}%"))

    result = await session.execute(query.limit(limit))
    return result.scalars().all()
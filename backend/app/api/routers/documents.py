from fastapi import APIRouter, UploadFile, Depends, BackgroundTasks, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, text
from typing import List, Optional
from uuid import UUID
from pathlib import Path
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

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    doc = await upload_document(file, session)
    background_tasks.add_task(process_document_ai, doc.id)
    return {"id": doc.id, "message": "Processing started..."}

@router.get("", response_model=List[DocumentOut])
async def list_documents(
    limit: int = Query(100, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all documents.
    Returns a list of all documents with their IDs, filenames, tags, and captions.
    Useful for finding document IDs.
    """
    result = await session.execute(
        select(Document).limit(limit).offset(offset)
    )
    documents = result.scalars().all()
    return documents

@router.get("/search", response_model=List[DocumentOut])
async def search_documents(
    tag: Optional[str] = Query(None, description="Filter by a specific YOLO tag"),
    q: Optional[str] = Query(None, description="Search keyword in Moondream caption"),
    limit: int = 20,
    session: AsyncSession = Depends(get_session) # Fixed name to 'session' and used 'get_session'
):
    query = select(Document)

    # 1. Filter by YOLO Tags (JSON array search)
    if tag:
        # For JSON columns, we need to use JSON functions
        # SQLite: Use json_each to check if tag exists in the JSON array
        # PostgreSQL: Can use JSON operators, but this works for both
        # Using a cross-database approach: check if the JSON array contains the exact tag
        # We search for the tag as a JSON string value (with quotes) to avoid partial matches
        # This matches patterns like: ["animal", "cat"] or ["cat", "animal"]
        query = query.filter(
            cast(Document.tags, String).like(f'%"{tag}"%')
        )

    # 2. Search in Caption (Case-insensitive)
    if q:
        query = query.filter(Document.caption.ilike(f"%{q}%"))

    result = await session.execute(query.limit(limit))
    
    return result.scalars().all()

@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a document by its ID.
    Returns the document with all its details including tags and caption.
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    return doc
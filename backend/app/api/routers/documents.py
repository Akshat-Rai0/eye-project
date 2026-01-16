from fastapi import APIRouter, UploadFile, Depends, BackgroundTasks, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, String
from typing import List, Optional
from uuid import UUID
from pathlib import Path

# Import your models and schemas
from app.db.database import get_session
from app.models.document import Document
from app.schemas.document_schemas import DocumentOut 
from app.services.document_services import upload_document
from app.services.ai_service import process_document_ai
from app.services.graph_service import calculate_2d_projection

router = APIRouter()

@router.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Upload an image, save to disk, and trigger background AI processing.
    """
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 1. Save file and create DB record
    doc = await upload_document(file, session)
    
    # 2. Trigger AI processing (YOLO + Moondream) in the background
    background_tasks.add_task(process_document_ai, doc.id)
    
    return {"id": doc.id, "message": "Upload successful. AI processing started."}

@router.get("", response_model=List[DocumentOut])
async def list_documents(
    limit: int = Query(100, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all documents.
    """
    result = await session.execute(
        select(Document).order_by(Document.id.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()

@router.get("/search", response_model=List[DocumentOut])
async def search_documents(
    q: str = Query(..., description="The keyword to search for in tags or captions"),
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    """
    Unified Search: Looks for the keyword 'q' in:
    1. The tags list (YOLO + Moondream keywords)
    2. The full text caption
    3. The filename
    """
    search_term = q.lower()
    wildcard_term = f"%{search_term}%"

    # We use 'or_' to match the term in ANY of these places
    statement = select(Document).where(
        or_(
            # Search inside the JSON tags array
            # cast to String is a safe way to check JSON in SQLite/Postgres
            cast(Document.tags, String).ilike(wildcard_term),
            
            # Search in the long Moondream caption
            Document.caption.ilike(wildcard_term),
            
            # Search in the original filename
            Document.filename.ilike(wildcard_term)
        )
    ).limit(limit)

    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/graph")
async def get_image_graph(session: AsyncSession = Depends(get_session)):
    """
    Generate a force-directed graph of images based on their embeddings.
    Returns nodes (images) and links (connections between similar images).
    """
    # 1. Fetch all documents with embeddings
    result = await session.execute(
        select(Document).where(Document.embedding != None)
    )
    docs = result.scalars().all()
    
    if not docs:
        return {"nodes": [], "links": []}

    # 2. Project embeddings to 2D coordinates
    embeddings = [d.embedding for d in docs]
    coords = calculate_2d_projection(embeddings)

    # 3. Build Nodes
    nodes = []
    for i, doc in enumerate(docs):
        nodes.append({
            "id": str(doc.id),
            "x": coords[i][0],
            "y": coords[i][1],
            "img": f"http://localhost:8000/data/{doc.relative_path}",
            "caption": doc.caption,
            "tags": doc.tags
        })

    # 4. Build Links (Connect images if they share 2+ tags)
    links = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            shared = set(nodes[i]["tags"]) & set(nodes[j]["tags"])
            if len(shared) >= 2:
                links.append({
                    "source": nodes[i]["id"], 
                    "target": nodes[j]["id"]
                })

    return {"nodes": nodes, "links": links}

@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific document by ID.
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc
@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a document and its associated file.
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        file_path = get_document_absolute_path(doc.relative_path)
        if file_path.exists():
            file_path.unlink()
            print(f"✅ Deleted file: {file_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not delete file: {e}")
    
    await session.delete(doc)
    await session.commit()
    
    return {"message": "Document deleted successfully", "id": document_id}
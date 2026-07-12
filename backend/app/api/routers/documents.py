from fastapi import APIRouter, UploadFile, Depends, BackgroundTasks, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, String
from typing import List, Optional
from uuid import UUID
from pathlib import Path
from app.core.config import settings

from app.db.database import get_session
from app.models.document import Document
from app.schemas.document_schemas import DocumentOut, DocumentUpdate

from app.services.ai_service import process_document_ai_async
from app.services.graph_service import calculate_2d_projection
from app.services.document_services import upload_document, get_document_absolute_path

router = APIRouter()


@router.patch("/{document_id}/tags", response_model=DocumentOut)
async def update_tags(
    document_id: UUID,
    update_data: DocumentUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Append new tags to a document.
    """
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if update_data.tags:
        current_tags = list(doc.tags) if doc.tags else []
        for tag in update_data.tags:
            if tag not in current_tags:
                current_tags.append(tag)
        doc.tags = current_tags

    await session.commit()
    await session.refresh(doc)
    return doc


@router.post("/upload")
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    if settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail="Upload disabled in demo mode — this is a read-only showcase."
        )

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    doc = await upload_document(file, session)
    background_tasks.add_task(process_document_ai_async, doc.id)

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

    statement = select(Document).where(
        or_(
            cast(Document.tags, String).ilike(wildcard_term),
            Document.caption.ilike(wildcard_term),
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
    result = await session.execute(
        select(Document).where(Document.embedding != None)
    )
    docs = result.scalars().all()

    if not docs:
        return {"nodes": [], "links": []}

    embeddings = [d.embedding for d in docs]
    coords = calculate_2d_projection(embeddings)

    nodes = []
    for i, doc in enumerate(docs):
        nodes.append({
            "id": str(doc.id),
            "x": coords[i][0],
            "y": coords[i][1],
            "img": f"{settings.PUBLIC_BASE_URL}/data/{doc.relative_path}",
            "caption": doc.caption,
            "tags": doc.tags
        })

    links = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            shared = set(nodes[i]["tags"]) & set(nodes[j]["tags"])
            if len(shared) >= 3:
                links.append({
                    "source": nodes[i]["id"],
                    "target": nodes[j]["id"]
                })

    return {"nodes": nodes, "links": links}


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
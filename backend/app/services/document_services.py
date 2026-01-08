# Document upload and management services
from pathlib import Path
from uuid import uuid4
import hashlib
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document
from app.core.config import get_data_base_path


async def upload_document(file: UploadFile, session: AsyncSession) -> Document:
    """
    Upload a document, save it to disk, and create a database record.
    Prevents duplicate uploads by checking content hash.
    """
    # Read file content
    content = await file.read()
    
    # Calculate SHA256 hash
    content_hash = hashlib.sha256(content).hexdigest()
    
    # Check if document with this hash already exists
    result = await session.execute(
        select(Document).where(Document.content_hash == content_hash)
    )
    existing_doc = result.scalar_one_or_none()
    
    if existing_doc:
        # If it exists in DB, we return it so the AI can process it 
        # (even if it was previously failed/interrupted)
        await file.seek(0)
        return existing_doc
    
    # Generate unique filename using first 16 chars of hash
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{content_hash[:16]}{file_ext}"
    
    # --- CONSISTENT PATHING ---
    # We store "inbound/filename.jpg" in the DB
    relative_path = f"inbound/{unique_filename}"
    
    # We save to "backend/data/inbound/filename.jpg"
    data_base_path = get_data_base_path()
    absolute_path = data_base_path / relative_path
    
    # Ensure directory exists (creates data/inbound/)
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file to disk
    with open(absolute_path, "wb") as f:
        f.write(content)
    
    # Create database record
    doc = Document(
        filename=file.filename,
        relative_path=relative_path, # Saves as "inbound/82c29f3..."
        content_hash=content_hash,
        tags=[],
        caption=None
    )
    
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    
    return doc


def get_document_absolute_path(relative_path: str) -> Path:
    """
    Convert relative path from DB to absolute path.
    Matches the logic used in upload_document.
    """
    data_base_path = get_data_base_path()
    return data_base_path / relative_path
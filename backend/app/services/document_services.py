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
    
    if existing_doc:
        # Duplicate found - check if file exists at the path stored in DB
        existing_absolute_path = get_document_absolute_path(existing_doc.relative_path)
        
        if not existing_absolute_path.exists():
            # File is missing - save it using the calculated path (based on hash)
            print(f"⚠️  Duplicate hash found but file missing at {existing_absolute_path}")
            print(f"    Saving file to {absolute_path}")
            with open(absolute_path, "wb") as f:
                f.write(content)
            # Update the relative_path to match the hash-based filename
            existing_doc.relative_path = relative_path
            await session.commit()
            await session.refresh(existing_doc)
        else:
            # File exists, just return existing document
            await file.seek(0)
        
        return existing_doc
    
    # No duplicate - save file and create new record
    print(f"📁 Saving new file to {absolute_path}")
    with open(absolute_path, "wb") as f:
        f.write(content)
    
    # Verify file was saved
    if not absolute_path.exists():
        raise HTTPException(status_code=500, detail=f"Failed to save file to {absolute_path}")
    
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
    
    print(f"✅ Created document record: {doc.id}, path: {doc.relative_path}")
    return doc


def get_document_absolute_path(relative_path: str) -> Path:
    """
    Convert relative path from DB to absolute path.
    Matches the logic used in upload_document.
    """
    data_base_path = get_data_base_path()
    return data_base_path / relative_path
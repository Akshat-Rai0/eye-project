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
    
    Args:
        file: The uploaded file
        session: Database session
        
    Returns:
        The created or existing Document record
    """
    # Read file content
    content = await file.read()
    
    # Calculate SHA256 hash of file content
    content_hash = hashlib.sha256(content).hexdigest()
    
    # Check if document with this hash already exists
    result = await session.execute(
        select(Document).where(Document.content_hash == content_hash)
    )
    existing_doc = result.scalar_one_or_none()
    
    if existing_doc:
        # Duplicate found - return existing document
        # Reset file pointer for potential future use
        await file.seek(0)
        return existing_doc
    
    # No duplicate - proceed with upload
    # Generate unique filename using hash (first 16 chars for readability)
    file_ext = Path(file.filename).suffix
    unique_filename = f"{content_hash[:16]}{file_ext}"
    
    # Create relative path (e.g., "inbound/hash.jpg")
    relative_path = f"inbound/{unique_filename}"
    
    # Get absolute path for saving
    data_base_path = get_data_base_path()
    absolute_path = data_base_path / relative_path
    
    # Ensure directory exists
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file to disk
    with open(absolute_path, "wb") as f:
        f.write(content)
    
    # Create database record with relative path and hash
    doc = Document(
        filename=file.filename,
        relative_path=relative_path,
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
    Convert a relative path from database to absolute path for file access.
    
    Args:
        relative_path: Relative path stored in database (e.g., "inbound/uuid.jpg")
        
    Returns:
        Absolute path to the file
    """
    data_base_path = get_data_base_path()
    return data_base_path / relative_path

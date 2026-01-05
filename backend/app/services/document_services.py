# Document upload and management services
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.core.config import get_data_base_path


async def upload_document(file: UploadFile, session: AsyncSession) -> Document:
    """
    Upload a document, save it to disk, and create a database record.
    Stores relative path in database for portability.
    
    Args:
        file: The uploaded file
        session: Database session
        
    Returns:
        The created Document record
    """
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid4()}{file_ext}"
    
    # Create relative path (e.g., "inbound/uuid.jpg")
    relative_path = f"inbound/{unique_filename}"
    
    # Get absolute path for saving
    data_base_path = get_data_base_path()
    absolute_path = data_base_path / relative_path
    
    # Ensure directory exists
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file to disk
    with open(absolute_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create database record with relative path
    doc = Document(
        filename=file.filename,
        relative_path=relative_path,
        tags=None,
        description=None
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

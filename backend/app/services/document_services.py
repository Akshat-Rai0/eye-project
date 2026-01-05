#Implements business logic such as hashing, deduplication, and persistence.
import hashlib
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.document import Document

async def upload_document(
    file: UploadFile,
    session: AsyncSession,
):
    hasher = hashlib.sha256()

    while chunk := await file.read(1024 * 1024):
        hasher.update(chunk)

    content_hash = hasher.hexdigest()

    doc = Document(
        filename=file.filename,
        content_hash=content_hash,
    )

    session.add(doc)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate document")

    return doc
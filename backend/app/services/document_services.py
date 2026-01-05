#Implements business logic such as hashing, deduplication, and persistence.
import hashlib
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.document import Document
INBOUND_DIR = Path("data/images/inbound")
INBOUND_DIR.mkdir(parents=True, exist_ok=True)
async def upload_document(
    file: UploadFile,
    session: AsyncSession,
):
    hasher = hashlib.sha256()

    # 1. Hash the file
    while chunk := await file.read(1024 * 1024):
        hasher.update(chunk)

    content_hash = hasher.hexdigest()

    # 2. RESET FILE POINTER (mandatory)
    await file.seek(0)

    # 3. Persist file to disk
    file_path = INBOUND_DIR / f"{content_hash}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Persist metadata to DB
    doc = Document(
        filename=file.filename,
        content_hash=content_hash,
        path=str(file_path),
    )

    session.add(doc)

    try:
        await session.commit()
        await session.refresh(doc)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate document")

    return doc
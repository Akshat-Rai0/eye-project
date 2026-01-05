#takes the input of file format 
#Defines HTTP endpoints for document-related operations (upload, list, delete).
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.services.document_services import upload_document

router = APIRouter()

@router.post("/upload")
async def upload(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    return await upload_document(file, session)
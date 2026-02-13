# Defines Pydantic models for request/response validation and serialization.
# this tells the structure in which the data will be stored in database 
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class DocumentOut(BaseModel):
    id: UUID
    filename: str
    relative_path: str
    tags: List[str]
    caption: Optional[str] = None
    processing_progress: int = 0

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    tags: Optional[List[str]] = None
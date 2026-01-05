# Defines Pydantic models for request/response validation and serialization.
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class DocumentOut(BaseModel):
    id: UUID
    filename: str
    relative_path: str
    content_hash: Optional[str] = None
    tags: Optional[List[str]] = None
    caption: Optional[str] = None

    class Config:
        from_attributes = True
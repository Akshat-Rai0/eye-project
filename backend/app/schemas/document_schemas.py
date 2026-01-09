# Defines Pydantic models for request/response validation and serialization.
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class DocumentOut(BaseModel):
    id: UUID
    filename: str
    relative_path: str
    tags: List[str]
    caption: Optional[str] = None

    class Config:
        from_attributes = True
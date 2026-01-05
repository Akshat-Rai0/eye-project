# tells the postgres the format to store data into 
# UUID : filename 
#Defines Pydantic models for request/response validation and serialization.
from pydantic import BaseModel
from uuid import UUID

class DocumentOut(BaseModel):
    id: UUID
    filename: str

    class Config:
        from_attributes = True
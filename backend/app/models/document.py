# Defines the SQLAlchemy Document model for database storage
from sqlalchemy import Column, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String, nullable=False)
    # Store relative path (e.g., "inbound/hash.jpg") instead of absolute path
    relative_path = Column(String, nullable=False)
    # AI-generated tags from YOLO detection
    tags = Column(ARRAY(String), nullable=True, default=list)
    # AI-generated description/caption from Moondream
    description = Column(Text, nullable=True)

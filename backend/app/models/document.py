# this tells how the data moves between client and db
from datetime import datetime
from typing import List, Optional
from uuid import uuid4, UUID

from sqlalchemy import String, JSON, text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)

    # AI Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    caption: Mapped[Optional[str]] = mapped_column(String)
    
    # Embedding: 
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)

    # Audit Timestamps 
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Processing Status (0-100)
    processing_progress: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    
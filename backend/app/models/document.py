# Defines the SQLAlchemy Document model for database storage
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    # Store relative path (e.g., "inbound/hash.jpg") instead of absolute path
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    # SHA256 hash of file content for duplicate detection
    # Note: nullable=True allows existing records, but new uploads will always have a hash
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True, unique=True, index=True)
    # AI-generated tags from YOLO detection (using JSON for SQLite/PostgreSQL compatibility)
    tags: Mapped[list[str]] = mapped_column(JSON, default=[], nullable=False)
    # AI-generated caption from Moondream
    caption: Mapped[str | None] = mapped_column(String, nullable=True)

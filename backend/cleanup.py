"""
Cleanup script to empty the database and remove uploaded files.
Run from backend directory: python cleanup.py
"""
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings, get_data_base_path
from app.models.document import Document

def get_sync_url(url: str) -> str:
    """Convert async database URL to sync URL."""
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://")
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url

def main():
    print("🧹 Starting cleanup...")
    
    # 1. Clear database
    print("\n📊 Clearing database...")
    sync_url = get_sync_url(settings.DATABASE_URL)
    engine = create_engine(sync_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        # Delete all documents
        count = session.query(Document).count()
        if count > 0:
            session.query(Document).delete()
            session.commit()
            print(f"   ✅ Deleted {count} document(s) from database")
        else:
            print("   ℹ️  Database is already empty")
    
    # 2. Remove uploaded files
    print("\n📁 Removing uploaded files...")
    data_base_path = get_data_base_path()
    
    # Remove files from inbound directory
    inbound_dir = data_base_path / "inbound"
    if inbound_dir.exists():
        files_removed = 0
        for file_path in inbound_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
                files_removed += 1
        if files_removed > 0:
            print(f"   ✅ Removed {files_removed} file(s) from {inbound_dir}")
        else:
            print(f"   ℹ️  No files found in {inbound_dir}")
    
    # Also check old images/inbound location
    old_inbound_dir = data_base_path / "images" / "inbound"
    if old_inbound_dir.exists():
        files_removed = 0
        for file_path in old_inbound_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
                files_removed += 1
        if files_removed > 0:
            print(f"   ✅ Removed {files_removed} file(s) from {old_inbound_dir}")
    
    # Remove thumbnails
    thumbnails_dir = data_base_path / "thumbnails"
    if thumbnails_dir.exists():
        files_removed = 0
        for file_path in thumbnails_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
                files_removed += 1
        if files_removed > 0:
            print(f"   ✅ Removed {files_removed} thumbnail(s)")
    
    # 3. Remove unwanted files
    print("\n🗑️  Removing unwanted files...")
    backend_dir = Path(__file__).parent
    
    unwanted_files = [
        backend_dir / "fix_file_paths.py",
    ]
    
    for file_path in unwanted_files:
        if file_path.exists():
            file_path.unlink()
            print(f"   ✅ Removed {file_path.name}")
    
    print("\n✅ Cleanup complete!")
    print("   Database is empty")
    print("   All uploaded files have been removed")
    print("   Unwanted files have been deleted")

if __name__ == "__main__":
    main()

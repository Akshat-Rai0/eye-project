"""
Migration script to fix file path mismatches between database and filesystem.
Run this from the backend directory: python fix_file_paths.py
"""
import os
from pathlib import Path
import shutil
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
    print("🔧 Starting path migration...")
    
    # Setup database connection
    sync_url = get_sync_url(settings.DATABASE_URL)
    engine = create_engine(sync_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    data_base_path = get_data_base_path()
    print(f"📁 Data base path: {data_base_path}")
    
    # Ensure correct directory structure exists
    inbound_dir = data_base_path / "inbound"
    inbound_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Ensured directory exists: {inbound_dir}")
    
    with SessionLocal() as session:
        # Get all documents
        documents = session.query(Document).all()
        print(f"📊 Found {len(documents)} documents in database")
        
        fixed_count = 0
        error_count = 0
        
        for doc in documents:
            old_path = data_base_path / doc.relative_path
            
            # Check if file exists at recorded location
            if old_path.exists():
                print(f"✅ {doc.filename}: File exists at {doc.relative_path}")
                continue
            
            # Check if file exists in old images/inbound location
            old_images_path = data_base_path / "images" / "inbound" / Path(doc.relative_path).name
            
            if old_images_path.exists():
                # File exists in old location, move it to new location
                new_relative_path = f"inbound/{Path(doc.relative_path).name}"
                new_absolute_path = data_base_path / new_relative_path
                
                print(f"🔄 Moving {doc.filename}")
                print(f"   From: {old_images_path}")
                print(f"   To: {new_absolute_path}")
                
                # Move the file
                shutil.move(str(old_images_path), str(new_absolute_path))
                
                # Update database record
                doc.relative_path = new_relative_path
                fixed_count += 1
            else:
                # File doesn't exist anywhere
                print(f"❌ {doc.filename}: File not found at either location")
                print(f"   Expected: {old_path}")
                print(f"   Or: {old_images_path}")
                error_count += 1
        
        # Commit all changes
        if fixed_count > 0:
            session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} file path(s)")
        
        if error_count > 0:
            print(f"⚠️  {error_count} file(s) could not be found")
        
        if fixed_count == 0 and error_count == 0:
            print("\n✅ All files are already in the correct location!")
    
    # Check if old images/inbound directory is now empty and can be removed
    old_images_inbound = data_base_path / "images" / "inbound"
    if old_images_inbound.exists():
        remaining_files = list(old_images_inbound.iterdir())
        if not remaining_files:
            print(f"\n🗑️  Old directory {old_images_inbound} is empty and can be removed")
            print("   Run: rm -rf backend/data/images")
        else:
            print(f"\n⚠️  Old directory {old_images_inbound} still contains {len(remaining_files)} file(s)")
    
    print("\n🎉 Migration complete!")

if __name__ == "__main__":
    main()
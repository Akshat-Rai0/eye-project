from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# --- ASYNC SETUP (For FastAPI Endpoints) ---
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

# --- SYNC SETUP (For AI Background Worker) ---
def get_sync_database_url() -> str:
    """Convert async database URL to sync URL for background threads."""
    url = settings.DATABASE_URL
    
    # Remove PostgreSQL async drivers
    url = url.replace("+asyncpg", "").replace("+psycopg", "")
    
    # Remove SQLite async driver (Critical for avoiding MissingGreenlet error)
    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")
        
    return url

sync_engine = create_engine(
    get_sync_database_url(),
    echo=False,  # Set to True if you want to see SQL logs for the worker
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
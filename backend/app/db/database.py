#Creates the database engine and provides async database sessions.
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

# Async engine and session for FastAPI endpoints
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

# Synchronous engine and session for background workers (AI processing)
# This avoids asyncio.run() conflicts when running CPU-bound ML models
def get_sync_database_url() -> str:
    """Convert async database URL to sync URL."""
    url = settings.DATABASE_URL
    # Remove async drivers
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    elif "+psycopg" in url:
        url = url.replace("+psycopg", "")
    # Ensure postgresql:// (not postgresql+asyncpg://)
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    elif url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://")
    return url

sync_engine = create_engine(
    get_sync_database_url(),
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
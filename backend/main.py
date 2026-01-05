# Starts the FastAPI application and registers all API routers.
from fastapi import FastAPI
from app.db.database import engine
from app.db.base import Base
from app.api.router import api_router

app = FastAPI(title="EYE")

# Register API routes
app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
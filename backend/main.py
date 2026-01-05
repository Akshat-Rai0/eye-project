# Starts the FastAPI application and registers all API routers.
from fastapi import FastAPI
from app.db.database import engine, Base

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
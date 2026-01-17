# Starts the FastAPI application and registers all API routers.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db.database import engine
from app.db.base import Base
from app.api.router import api_router
from app.core.config import get_data_base_path

app = FastAPI(title="EYE")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # More permissive for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Register API routes from backend/app/api/routers/documents.py
app.include_router(api_router)

# Mount static files directory to serve images
data_base_path = get_data_base_path()
app.mount("/data", StaticFiles(directory=str(data_base_path)), name="data")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
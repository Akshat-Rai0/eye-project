# Starts the FastAPI application and registers all API routers.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.db.database import engine
from app.db.base import Base
from app.api.router import api_router
from app.core.config import get_data_base_path

app = FastAPI(title="EYE")

# Enable CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://eye-project-nine.vercel.app",
    "https://eye-project-git-main-akshatrai.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes from backend/app/api/routers/documents.py
app.include_router(api_router)

# Mount static files directory to serve images
data_base_path = get_data_base_path()
app.mount("/data", StaticFiles(directory=str(data_base_path)), name="data")

# Serve frontend static files
frontend_dist_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="frontend")
else:
    @app.get("/")
    async def read_root():
        return {"message": "Frontend not built. Please run 'npm run build' in the frontend directory."}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
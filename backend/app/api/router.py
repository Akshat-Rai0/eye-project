# Aggregates and mounts all feature routers into the main app.
from fastapi import APIRouter
from app.api.routers import documents

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
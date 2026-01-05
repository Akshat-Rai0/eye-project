# Starts the FastAPI application and registers all API routers.
from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="EYE")

app.include_router(api_router)
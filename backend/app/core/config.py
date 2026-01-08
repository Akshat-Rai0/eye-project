#loads and validates environment-based application settings.
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    # Changed from "data/images" to "data" to match your service logic
    DATA_BASE_DIR: str = "data" 

    class Config:
        env_file = ".env"

settings = Settings()

# Get absolute path to data directory (relative to backend directory)
def get_data_base_path() -> Path:
    """Returns the absolute path to the data base directory."""
    backend_dir = Path(__file__).parent.parent.parent  # Go up from core/ to backend/
    absolute_path = (backend_dir / settings.DATA_BASE_DIR).resolve()
    return absolute_path
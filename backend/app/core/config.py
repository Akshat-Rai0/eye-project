#loads and validates environment-based application settings.
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    # Base directory for storing uploaded files (relative to project root)
    # Default: data/images (relative to backend directory)
    DATA_BASE_DIR: str = "data/images"

    class Config:
        env_file = ".env"

settings = Settings()

# Get absolute path to data directory (relative to backend directory)
def get_data_base_path() -> Path:
    """Returns the absolute path to the data base directory."""
    backend_dir = Path(__file__).parent.parent.parent  # Go up from core/ to backend/
    return backend_dir / settings.DATA_BASE_DIR
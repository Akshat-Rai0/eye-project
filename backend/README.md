# EYE Backend

A FastAPI-based backend for document management with AI-powered image analysis using YOLOv11 and Moondream2.

## Features

- **Document Management**: Upload, retrieve, and manage documents with images
- **AI Image Analysis**: 
  - Object detection using YOLOv11
  - Visual question answering with Moondream2
- **Database**: SQLite with async support (SQLAlchemy + Alembic migrations)
- **REST API**: FastAPI with automatic OpenAPI documentation
- **CORS Support**: Configured for frontend integration

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Database**: SQLite (async) with SQLAlchemy 2.0
- **Computer Vision**: 
  - YOLOv11 (Ultralytics)
  - Moondream2 (Hugging Face Transformers)
  - OpenCV
- **ML Framework**: PyTorch 2.0+
- **Migrations**: Alembic

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── router.py           # Main API router
│   │   └── routers/
│   │       └── documents.py    # Document endpoints
│   ├── core/
│   │   └── config.py           # Configuration & settings
│   ├── db/
│   │   ├── database.py         # Database connection
│   │   └── base.py             # SQLAlchemy base
│   ├── models/
│   │   └── document.py         # Database models
│   ├── schemas/
│   │   └── document_schemas.py # Pydantic schemas
│   └── services/
│       ├── ai_service.py       # AI/ML services
│       └── document_services.py # Business logic
├── alembic/                    # Database migrations
├── data/                       # Uploaded files storage
├── .env                        # Environment variables
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── start.sh                    # Startup script
├── yolo11n.pt                  # YOLO model weights
└── eye.db                      # SQLite database
```

## Setup

### Prerequisites

- Python 3.8+
- macOS with Homebrew (for the current setup script)

### Installation

1. **Clone the repository** and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the backend directory:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./eye.db
   DATA_BASE_DIR=data
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

## Running the Application

### Using the start script (macOS):
```bash
chmod +x start.sh
./start.sh
```

### Manual start:
```bash
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Documents

- `POST /api/documents/` - Upload a new document with image
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}` - Get document by ID
- `DELETE /api/documents/{id}` - Delete document

### AI Services

- **Object Detection**: Automatically runs YOLO on uploaded images
- **Visual QA**: Ask questions about document images

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Development

### Project Architecture

- **API Layer**: FastAPI routers handle HTTP requests/responses
- **Service Layer**: Business logic and AI operations
- **Data Layer**: SQLAlchemy models and database operations
- **Schemas**: Pydantic models for validation and serialization

### Adding New Features

1. Define database models in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add API endpoints in `app/api/routers/`
5. Create and run migrations with Alembic

## Configuration

Key settings in `app/core/config.py`:
- `DATABASE_URL`: Database connection string
- `DATA_BASE_DIR`: Directory for uploaded files

## Notes

- The application uses async/await for database operations
- YOLO model weights are loaded on demand
- Static files are served from the `/data` endpoint
- CORS is configured for `http://localhost:5173` (frontend)

## Troubleshooting

### Library Loading Issues (macOS)
If you encounter library loading errors, ensure `DYLD_LIBRARY_PATH` is set:
```bash
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
```

### Database Issues
Reset the database:
```bash
rm eye.db
alembic upgrade head
```

## License

[Add your license here]

# AI processing worker that runs in background threads
# Uses its own DB session to avoid FastAPI request session conflicts

from pathlib import Path
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path
import asyncio


def process_document_ai(doc_id: int):
    """
    Background worker for AI processing (YOLO + Moondream).
    Runs in a separate thread via FastAPI's BackgroundTasks.
    This is a pure synchronous function - BackgroundTasks handles threading.
    Uses asyncio.run() to handle async database operations without event loop conflicts.
    
    Args:
        doc_id: The document ID to process
    """
    # BackgroundTasks runs this in a separate thread, so asyncio.run() is safe
    # This prevents event loop conflicts when running blocking ML models
    asyncio.run(_process_document_async(doc_id))


async def _process_document_async(doc_id: int):
    """
    Internal async function that handles the actual AI processing.
    Creates its own database session independent of the HTTP request.
    """
    # 1. Create a NEW session (not the one from the HTTP request)
    async with AsyncSessionLocal() as session:
        # 2. Fetch the document from DB
        result = await session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            print(f"Document {doc_id} not found")
            return
        
        print(f"Processing document {doc_id}: {doc.filename}")
        
        # 3. Get absolute path from relative path stored in DB
        image_path = get_document_absolute_path(doc.relative_path)
        
        # 4. Run AI models (placeholder for now)
        # TODO: Add YOLO detection
        # detections = run_yolo(str(image_path))
        
        # TODO: Add Moondream captioning
        # caption = run_moondream(str(image_path))
        
        # 5. Update the document with AI results
        # doc.tags = detections  # Now we have the tags column!
        # doc.description = caption  # Now we have the description column!
        
        # For now, set placeholder values to test the columns work
        # Remove these when you implement the actual AI models
        if doc.tags is None:
            doc.tags = []
        if doc.description is None:
            doc.description = ""
        
        # 6. Commit changes
        await session.commit()
        
        print(f"Finished processing document {doc_id}")


# Placeholder functions for AI models (implement later)
def run_yolo(image_path: str):
    """Run YOLO object detection on the image"""
    # from ultralytics import YOLO
    # model = YOLO('yolov11n.pt')
    # results = model(image_path)
    # return parse_detections(results)
    pass


def run_moondream(image_path: str):
    """Run Moondream captioning on the image"""
    # import ollama
    # response = ollama.chat(model='moondream', messages=[...])
    # return response['message']['content']
    pass


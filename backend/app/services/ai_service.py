# AI processing worker that runs in background threads
# Uses synchronous database session to avoid asyncio conflicts with CPU-bound ML models

from pathlib import Path
from uuid import UUID
from sqlalchemy import select
from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path


def process_document_ai(doc_id: UUID):
    """
    Background worker for AI processing (YOLO + Moondream).
    Runs in a separate thread via FastAPI's BackgroundTasks.
    Uses synchronous database operations to avoid event loop conflicts
    when running CPU-bound ML models (YOLO).
    
    Args:
        doc_id: The document ID to process
    """
    # 1. Create a NEW synchronous session (not the async one from HTTP request)
    with SessionLocal() as session:
        # 2. Fetch the document from DB
        doc = session.query(Document).filter(Document.id == doc_id).first()
        
        if not doc:
            print(f"Document {doc_id} not found")
            return
        
        print(f"Processing document {doc_id}: {doc.filename}")
        
        # 3. Get absolute path from relative path stored in DB
        image_path = get_document_absolute_path(doc.relative_path)
        
        # Verify file exists
        if not image_path.exists():
            print(f"Error: Image file not found at {image_path}")
            return
        
        # 4. Run AI models (placeholder for now)
        # TODO: Add YOLO detection
        # detections = run_yolo(str(image_path))
        
        # TODO: Add Moondream captioning
        # caption = run_moondream(str(image_path))
        
        # 5. Update the document with AI results
        # doc.tags = detections  # Now we have the tags column!
        # doc.caption = caption  # Now we have the caption column!
        
        # For now, set placeholder values to test the columns work
        # Remove these when you implement the actual AI models
        if not doc.tags:
            doc.tags = []
        if doc.caption is None:
            doc.caption = ""
        
        # 6. Commit changes
        session.commit()
        
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


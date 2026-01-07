import torch
from pathlib import Path
from uuid import UUID
from PIL import Image
from sqlalchemy.orm import Session
from ultralytics import YOLO
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path

# --- GLOBAL MODEL LOADING (Loads once on startup) ---
# These stay in your M4's memory.
print("Loading YOLOv11...")
yolo_model = YOLO('yolo11n.pt')

print("Loading Moondream2 (this may take a moment)...")
# Note: Use 'mps' for Mac M4 GPU acceleration
moondream_model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    revision="2025-01-09", # Use latest stable revision
    trust_remote_code=True,
    device_map={"": "mps"} if torch.backends.mps.is_available() else "cpu"
)
moondream_tokenizer = AutoTokenizer.from_pretrained("vikhyatk/moondream2")


def process_document_ai(doc_id: UUID):
    """
    Background worker for AI processing. Runs in a separate thread.
    """
    # Create a fresh sync session for this thread
    with SessionLocal() as session:
        doc = session.query(Document).filter(Document.id == doc_id).first()
        
        if not doc:
            print(f"Document {doc_id} not found")
            return
        
        image_path = get_document_absolute_path(doc.relative_path)
        
        if not image_path.exists():
            print(f"Error: Image file not found at {image_path}")
            return

        try:
            # 1. Run YOLO (Object Detection)
            tags = run_yolo(str(image_path))
            doc.tags = tags
            
            # 2. Run Moondream (Captioning)
            caption = run_moondream(str(image_path))
            doc.caption = caption

            # 3. Save results
            session.commit()
            print(f"Successfully processed {doc.filename}")
            
        except Exception as e:
            session.rollback()
            print(f"AI Processing failed for {doc_id}: {str(e)}")


def run_yolo(image_path: str) -> list[str]:
    """Runs YOLO using the global model and returns unique tags."""
    # Run on MPS (Mac GPU)
    results = yolo_model.predict(source=image_path, device="mps", conf=0.25, verbose=False)
    
    # Extract unique class names using a set comprehension
    names = yolo_model.names
    detected_classes = {names[int(box.cls[0])] for result in results for box in result.boxes}
    
    return list(detected_classes)


def run_moondream(image_path: str) -> str:
    """Runs Moondream using the global model and returns a caption."""
    image = Image.open(image_path)
    
    # Encode image
    enc_image = moondream_model.encode_image(image)
    
    # Generate caption
    caption = moondream_model.answer_question(enc_image, "Describe this image in one sentence.", moondream_tokenizer)
    
    return caption
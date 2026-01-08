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


# --- GLOBAL MODEL LOADING ---
print("Loading Moondream2...")
moondream_model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    revision="2025-01-09",
    trust_remote_code=True,
    device_map={"": "mps"} if torch.backends.mps.is_available() else "cpu"
).to("mps") # Explicitly move to MPS for M4 stability

moondream_tokenizer = AutoTokenizer.from_pretrained(
    "vikhyatk/moondream2", 
    trust_remote_code=True # Added for consistency
)

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


# --- RUN MOONDREAM ---
def run_moondream(image_path: str) -> str:
    with Image.open(image_path) as image: # Wrap in 'with' to auto-close file
        enc_image = moondream_model.encode_image(image)
        caption = moondream_model.answer_question(
            enc_image, 
            "Describe this image in two sentences.", 
            moondream_tokenizer
        )
    return caption
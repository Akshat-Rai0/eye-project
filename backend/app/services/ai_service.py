import torch
from pathlib import Path
from uuid import UUID
from PIL import Image
from ultralytics import YOLO
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path

# --- GLOBAL MODEL LOADING (Runs on startup) ---
print("Loading YOLOv11...")
yolo_model = YOLO('yolo11l.pt')

print("Loading Moondream2 (Optimizing for M4 MPS)...")
device = "mps" if torch.backends.mps.is_available() else "cpu"
moondream_model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    revision="2025-01-09",
    trust_remote_code=True,
    device_map={"": device}
).to(device) 

moondream_tokenizer = AutoTokenizer.from_pretrained(
    "vikhyatk/moondream2", 
    trust_remote_code=True
)

def process_document_ai(doc_id: UUID):
    """
    Synchronous background worker. 
    Uses the Sync SessionLocal and runs in a separate thread.
    """
    with SessionLocal() as session:
        # Use Standard Sync Query
        doc = session.query(Document).filter(Document.id == doc_id).first()
        
        if not doc:
            print(f"❌ Error: Document {doc_id} not found in database.")
            return
        
        image_path = get_document_absolute_path(doc.relative_path)
        
        print(f"🔍 Looking for file at: {image_path}")
        print(f"   Relative path from DB: {doc.relative_path}")
        print(f"   File exists: {image_path.exists()}")
        
        if not image_path.exists():
            print(f"❌ Error: File not found at {image_path}")
            # Try to find the file in alternative locations
            from app.core.config import get_data_base_path
            data_base = get_data_base_path()
            print(f"   Data base path: {data_base}")
            print(f"   Data base exists: {data_base.exists()}")
            if data_base.exists():
                # List files in inbound directory
                inbound_dir = data_base / "inbound"
                if inbound_dir.exists():
                    files = list(inbound_dir.glob("*"))
                    print(f"   Files in inbound/: {[f.name for f in files[:5]]}")
            return

        try:
            print(f"🧠 AI processing started for: {doc.filename}")
            
            # 1. Run YOLO Object Detection
            tags = run_yolo(str(image_path))
            doc.tags = tags
            
            # 2. Run Moondream Captioning
            caption = run_moondream(str(image_path))
            doc.caption = caption

            # 3. Commit changes to DB
            session.commit()
            print(f"✅ Successfully processed {doc.filename}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ AI Processing failed for {doc.filename}: {str(e)}")

def run_yolo(image_path: str) -> list[str]:
    """Runs YOLO on the M4 GPU and returns unique object names."""
    results = yolo_model.predict(
    source=image_path, 
    device="mps" if torch.backends.mps.is_available() else "cpu",  # Make it conditional
    conf=0.25, 
    verbose=False
)
    
    names = yolo_model.names
    detected_classes = {names[int(box.cls[0])] for result in results for box in result.boxes}
    
    return list(detected_classes)

def run_moondream(image_path: str) -> str:
    """Generates a visual description using Moondream2 on MPS."""
    with Image.open(image_path) as image:
        image = image.convert("RGB") # Ensure compatible format
        enc_image = moondream_model.encode_image(image)
        caption = moondream_model.answer_question(
            enc_image, 
            "Describe this image in two sentences.", 
            moondream_tokenizer
        )
    return caption
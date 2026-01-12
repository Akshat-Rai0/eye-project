import torch
from pathlib import Path
from uuid import UUID
from PIL import Image
from ultralytics import YOLO
from transformers import AutoModelForCausalLM, AutoTokenizer
import open_clip

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path

# --- GLOBAL MODEL LOADING (Runs once on startup) ---
print("Loading YOLOv11m...")
yolo_model = YOLO('yolo11m.pt')

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

# --- CLIP for embeddings ---
print("Loading CLIP for embeddings...")
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32',
    pretrained='openai'
)
clip_model = clip_model.to(device)
clip_model.eval()

def generate_embedding(image_path: Path) -> list[float]:
    """Generate a 512-dimensional embedding for an image using CLIP."""
    try:
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            image_tensor = clip_preprocess(img_rgb).unsqueeze(0).to(device)
            
            with torch.no_grad():
                embedding = clip_model.encode_image(image_tensor)
                # Normalize and convert to list
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                return embedding.cpu().numpy().flatten().tolist()
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None

def process_document_ai(doc_id: UUID):
    """
    Synchronous background worker. 
    Processes image with YOLO and Moondream to extract rich metadata.
    Also generates CLIP embeddings for graph visualization.
    """
    with SessionLocal() as session:
        doc = session.query(Document).filter(Document.id == doc_id).first()
        
        if not doc:
            print(f"❌ Error: Document {doc_id} not found in database.")
            return
        
        image_path = get_document_absolute_path(doc.relative_path)
        
        if not image_path.exists():
            print(f"❌ Error: File not found at {image_path}")
            return

        try:
            print(f"🧠 AI processing started for: {doc.filename}")
            
            # 1. Open and prepare image
            with Image.open(image_path) as img:
                img_rgb = img.convert("RGB")
                
                # 2. Run YOLO Object Detection (Fast)
                yolo_tags = run_yolo(str(image_path))
                
                # 3. Run Moondream Visual Reasoning
                # Encode once to save compute time
                enc_image = moondream_model.encode_image(img_rgb)
                
                # Generate full caption
                caption = moondream_model.answer_question(
                    enc_image, 
                    "Describe this image in two sentences.", 
                    moondream_tokenizer
                )
                
                # Extract AI keywords (solves the giraffe/deer/turkey issues)
                ai_keywords = extract_ai_keywords(enc_image)

                # 4. Merge results
                # Using a set removes duplicates between YOLO and Moondream
                unique_tags = list(set(yolo_tags + ai_keywords))
                
                # 5. Generate embedding for graph visualization
                embedding = generate_embedding(image_path)
                
                # Update DB record
                doc.tags = unique_tags
                doc.caption = caption
                doc.embedding = embedding

            session.commit()
            print(f"✅ Successfully processed {doc.filename}")
            print(f"   Tags: {unique_tags}")
            print(f"   Embedding: {'Generated' if embedding else 'Failed'}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ AI Processing failed for {doc.filename}: {str(e)}")
        
        finally:
            # Clear M4 GPU cache to prevent memory leaks
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

def run_yolo(image_path: str) -> list[str]:
    """Runs YOLOv11m on the M4 GPU."""
    results = yolo_model.predict(
        source=image_path, 
        device="mps" if torch.backends.mps.is_available() else "cpu",
        conf=0.25, 
        verbose=False
    )
    
    names = yolo_model.names
    detected_classes = {names[int(box.cls[0])] for result in results for box in result.boxes}
    return list(detected_classes)

def extract_ai_keywords(enc_image) -> list[str]:
    """Uses Moondream to extract specific, high-accuracy keywords."""
    question = "List the 3 most important objects in this image as a comma separated list of single words."
    
    answer = moondream_model.answer_question(
        enc_image, 
        question, 
        moondream_tokenizer
    )
    
    # Clean the response: lowercase, remove periods, split by comma
    raw_tags = answer.lower().replace(".", "").split(",")
    return [t.strip() for t in raw_tags if t.strip()]
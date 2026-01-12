import torch
from pathlib import Path
from uuid import UUID
from PIL import Image
from ultralytics import YOLO
from transformers import AutoModelForCausalLM, AutoTokenizer
import open_clip
import gc

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path

# --- GLOBAL MODEL LOADING (Runs once on startup) ---
# Check MPS availability
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🔧 Using device: {device}")

# Set memory optimization flags
if device == "mps":
    # Limit MPS memory allocation
    torch.mps.set_per_process_memory_fraction(.95)  # Use max 95% of available memory
    print("✅ MPS memory limited to 95%")

print("Loading YOLOv11n (lightweight)...")
yolo_model = YOLO('yolo11n.pt')

print("Loading Moondream2 (Optimizing for M4 MPS)...")

moondream_model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    revision="2025-01-09",
    trust_remote_code=True,
    torch_dtype=torch.float16 if device == "mps" else torch.float32,  # Use half precision on MPS
    device_map={"": device},
    low_cpu_mem_usage=True  # Reduce RAM usage during loading
).to(device)

#s
moondream_tokenizer = AutoTokenizer.from_pretrained(
    "vikhyatk/moondream2", 
    trust_remote_code=True
)

print("Loading CLIP model for embeddings...")
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
clip_model = clip_model.to(device)
if device == "mps":
    clip_model = clip_model.half()  # Use FP16 for memory efficiency
clip_model.eval()

print(f"✅ All models loaded on {device}")
if device == "mps":
    print("🚀 MPS acceleration enabled for M4")

def process_document_ai(doc_id: UUID):
    """
    Synchronous background worker. 
    Processes image with YOLO and Moondream to extract rich metadata.
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

                # 4. Generate CLIP embedding for semantic similarity
                embedding = generate_clip_embedding(img_rgb)

                # 5. Merge results
                # Using a set removes duplicates between YOLO and Moondream
                unique_tags = list(set(yolo_tags + ai_keywords))
                
                # Update DB record
                doc.tags = unique_tags
                doc.caption = caption
                doc.embedding = embedding

            session.commit()
            print(f"✅ Successfully processed {doc.filename}")
            print(f"   Tags: {unique_tags}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ AI Processing failed for {doc.filename}: {str(e)}")
        
        finally:
            # Aggressive memory cleanup
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            gc.collect()  # Force Python garbage collection

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

def generate_clip_embedding(image: Image.Image) -> list[float]:
    """Generate a 512-dimensional CLIP embedding for semantic similarity."""
    with torch.no_grad():
        # Preprocess and encode image
        image_tensor = clip_preprocess(image).unsqueeze(0).to(device)
        
        # Use FP16 if on MPS
        if device == "mps":
            image_tensor = image_tensor.half()
        
        embedding = clip_model.encode_image(image_tensor)
        
        # Normalize the embedding (important for cosine similarity)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        
        # Convert to list of floats for JSON storage
        return embedding.cpu().float().numpy().flatten().tolist()

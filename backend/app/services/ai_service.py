import torch
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID
from PIL import Image

from app.db.database import SessionLocal
from app.models.document import Document
from app.services.document_services import get_document_absolute_path

from app.core.config import settings

executor = ThreadPoolExecutor(max_workers=3)

# --- GLOBAL MODEL LOADING (Runs once on startup) ---
print("Loading YOLOv11m...")
yolo_model = YOLO('yolo11n.pt')

print("Loading Moondream2 (Optimizing for M4 MPS)...")
device = "mps" if torch.backends.mps.is_available() else "cpu"

moondream_model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    revision="2025-01-09",
    trust_remote_code=True,
    device_map={"": device},
    torch_dtype=torch.float16  # Use FP16 for faster inference
).to(device)

moondream_model.eval()  # Set to evaluation mode

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

def preprocess_image(image_path: Path, max_size=1024):
    """Resize large images before AI processing"""
    img = Image.open(image_path)
    img_rgb = img.convert("RGB")
    
    # Resize if too large
    if max(img_rgb.size) > max_size:
        ratio = max_size / max(img_rgb.size)
        new_size = tuple(int(dim * ratio) for dim in img_rgb.size)
        img_rgb = img_rgb.resize(new_size, Image.Resampling.LANCZOS)
    
    return img_rgb

async def process_document_ai_async(doc_id: UUID):
    """Async wrapper for AI processing"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, process_document_ai, doc_id)

def process_document_ai(doc_id: UUID):
    """
    Synchronous background worker. 
    Processes image with YOLO and Moondream to extract rich metadata.
    Also generates CLIP embeddings for graph visualization.
    """
    start = time.time()
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
            # Step 1: Start (10%)
            doc.processing_progress = 10
            session.commit()
            
            # 1. Image Preprocessing
            img_rgb = preprocess_image(image_path, max_size=1024)
            
            # Step 2: Preprocessing done (20%)
            doc.processing_progress = 20
            session.commit()
            
            # 2. YOLO (fast)
            yolo_tags = run_yolo(str(image_path))
            
            # Step 3: YOLO done (50% - as requested "till 50% till moondream is done")
            # Wait, user said "make it till 50% till moondream is done". 
            # This implies hitting 50% BEFORE or AS Moondream finishes? 
            # Or "YOLO done = 50%, Moondream done = 100%?"
            # Let's interpret: 
            # Pre-Moondream (YOLO done) -> 30-40%
            # Moondream running -> hold
            # Moondream done -> 80-90%
            doc.processing_progress = 40 
            session.commit()
            
            # 3. Moondream - SINGLE CALL with combined prompt
            enc_image = moondream_model.encode_image(img_rgb)
            
            # Combined prompt for efficiency
            combined_prompt = """Provide two things:
1. A 2-sentence description of this image
2. List the 5 most important objects/subjects as comma-separated words

Format your response as:
DESCRIPTION: [your description]
TAGS: [tag1, tag2, tag3, tag4, tag5]"""
            
            response = moondream_model.answer_question(
                enc_image, 
                combined_prompt,
                moondream_tokenizer
            )
            
            # Parse response
            caption = ""
            ai_keywords = []
            
            lines = response.split('\n')
            for line in lines:
                if line.startswith('DESCRIPTION:'):
                    caption = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('TAGS:'):
                    tags_str = line.replace('TAGS:', '').strip()
                    ai_keywords = [t.strip().lower() for t in tags_str.split(',')]
            
            # Fallback if parsing fails
            if not caption:
                caption = response[:200]  # First 200 chars
            if not ai_keywords:
                ai_keywords = extract_ai_keywords(enc_image)  # Use old method as fallback
            
            # Step 4: Moondream done (80%)
            doc.processing_progress = 80
            session.commit()

            # 4. Merge & deduplicate
            unique_tags = list(set(yolo_tags + ai_keywords))
            
            # 5. Generate embedding for graph visualization
            embedding = generate_embedding(image_path)
            
            # Update DB record
            doc.tags = unique_tags[:15]  # Limit to 15 tags max
            doc.caption = caption
            doc.embedding = embedding
            
            # Step 5: Finish (100%)
            doc.processing_progress = 100
            session.commit()

            elapsed = time.time() - start
            print(f"✅ Successfully processed {doc.filename}")
            print(f"   Tags: {unique_tags}")
            print(f"   Embedding: {'Generated' if embedding else 'Failed'}")
            print(f"⏱️  Processed in {elapsed:.2f}s")
            
        except Exception as e:
            session.rollback()
            print(f"❌ AI Processing failed for {doc.filename}: {str(e)}")
            # Optional: Set failure state, e.g., -1? Or just leave as is.
        
        finally:
            # Clear M4 GPU cache to prevent memory leaks
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

def run_yolo(image_path: str) -> list[str]:
    """Runs YOLOv11m with optimizations"""
    results = yolo_model.predict(
        source=image_path, 
        device="mps" if torch.backends.mps.is_available() else "cpu",
        conf=0.35,  # Increased from 0.25 to reduce false positives
        verbose=False,
        half=True,  # Use FP16 for faster inference on M4
        imgsz=640   # Explicit image size (default but ensures consistency)
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


executor = ThreadPoolExecutor(max_workers=3)


# --- GLOBAL MODEL LOADING (Runs once on startup) ---
if not settings.DEMO_MODE:
    from ultralytics import YOLO
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import open_clip

    print("Loading YOLOv11m...")
    yolo_model = YOLO('yolo11n.pt')

    print("Loading Moondream2 (Optimizing for M4 MPS)...")
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    moondream_model = AutoModelForCausalLM.from_pretrained(
        "vikhyatk/moondream2",
        revision="2025-01-09",
        trust_remote_code=True,
        device_map={"": device},
        torch_dtype=torch.float16
    ).to(device)
    moondream_model.eval()

    moondream_tokenizer = AutoTokenizer.from_pretrained(
        "vikhyatk/moondream2",
        trust_remote_code=True
    )

    print("Loading CLIP for embeddings...")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='openai'
    )
    clip_model = clip_model.to(device)
    clip_model.eval()
else:
    print("DEMO_MODE active — skipping AI model loads.")
    yolo_model = None
    moondream_model = None
    moondream_tokenizer = None
    clip_model = None
    clip_preprocess = None
    device = "cpu"
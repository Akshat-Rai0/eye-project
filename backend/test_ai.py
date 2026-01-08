# test_ai.py
import asyncio
from app.services.ai_service import run_yolo, run_moondream
from PIL import Image

def test_local_image(path):
    print("--- Testing YOLO ---")
    tags = run_yolo(path)
    print(f"Detected Tags: {tags}")

    print("\n--- Testing Moondream ---")
    caption = run_moondream(path)
    print(f"Generated Caption: {caption}")

if __name__ == "__main__":
    # Put a path to any real image on your Mac here
    test_path = "backend/data/inbound/test2.jpeg" 
    test_local_image(test_path)
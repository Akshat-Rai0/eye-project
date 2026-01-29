# 👁️ EYE - Intelligent Visual Asset Management

EYE is a sophisticated image management and discovery platform that leverages state-of-the-art AI (YOLO11, Moondream2, and CLIP) to automatically tag, describe, and organize your visual data. It features a unique 3D "Constellation" view that clusters similar images based on their semantic content.

---

## 🛠️ Backend Architecture

The backend is built with **FastAPI**, **SQLAlchemy** (Async), and **PyTorch**, designed to run intensive AI models locally while maintaining a responsive API.

### 📁 File Structure & Purpose

| File | Purpose |
| :--- | :--- |
| `main.py` | The application entry point. Configures FastAPI, handles CORS, mounts static folders for image serving, and registers routers. |
| `app/api/router.py` | Centralized router that aggregates all feature-specific routers (e.g., documents) into a single API tree. |
| `app/api/routers/documents.py` | Defines the REST endpoints for document operations: upload, search, listing, and graph data generation. |
| `app/core/config.py` | Manages environment variables and application settings using Pydantic Settings. Handles path resolution for data storage. |
| `app/db/database.py` | Sets up both **Async** (for web endpoints) and **Sync** (for background AI workers) database engines and session factories. |
| `app/db/base.py` | Contains the SQLAlchemy `DeclarativeBase` used by all database models. |
| `app/models/document.py` | The `Document` database model schema, including fields for AI metadata (tags, captions) and vector embeddings. |
| `app/schemas/document_schemas.py` | Pydantic models for data validation and serialization (DTOs) for the API responses. |
| `app/services/document_services.py` | Low-level file system and database logic for saving files and preventing duplicate uploads via SHA256 hashing. |
| `app/services/ai_service.py` | The "Brain" of the project. Loads and executes YOLO11, Moondream2, and CLIP models for image analysis. |
| `app/services/graph_service.py` | Handles dimensionality reduction (UMAP) to project high-dimensional CLIP embeddings into low-dimensional space for visualization. |
| `cleanup.py` | A utility script to wipe the database and delete all uploaded files for a fresh start. |
| `init_db.py` | A standalone script to initialize the database tables. |

---

---

## 🧠 AI Intelligence Suite

EYE utilizes a multi-layered AI pipeline to extract maximum information from every image. The system is optimized for local execution, specifically taking advantage of Apple Silicon (M4/MPS) for hardware acceleration.

### 🤖 Models Used

| Model | Role | Version / Details |
| :--- | :--- | :--- |
| **YOLO11n** | **Object Detection** | The latest iteration of Ultralytics YOLO. Used for high-speed identification of 80+ standard objects with bounding box logic. |
| **Moondream2** | **Visual Reasoning** | A tiny yet powerful Vision Language Model (VLM). It generates the image captions and identifies complex context that fixed-class detectors miss. |
| **CLIP (ViT-B-32)** | **Semantic Vectorization** | OpenAI's Contrastive Language-Image Pre-training. It converts images into 512-dimensional vectors (embeddings) where visual similarity equals mathematical proximity. |
| **UMAP** | **Dimensionality Reduction** | Not a neural network, but a sophisticated manifold learning algorithm that projects 512D CLIP vectors into 2D/3D space for the Constellation view. |

### 🔄 The AI Processing Pipeline (`process_document_ai`)

When an image is uploaded, the following sequence occurs in the background:

1.  **Preprocessing**: The image is normalized and converted to RGB.
2.  **Object Detection (YOLO)**: The model scans for common objects to generate the first set of tags.
3.  **Visual Captioning (Moondream)**: The model "looks" at the image and describes it in natural language.
4.  **Keyword Extraction**: A second pass with Moondream asks specific questions to extract descriptive nouns and attributes.
5.  **Vector Embedding (CLIP)**: The image is passed through the CLIP encoder to generate its "fingerprint."
6.  **Metadata Merging**: Tags from YOLO and Moondream are de-duplicated and merged into a final list.
7.  **Database Sync**: All generated metadata and the vector embedding are saved to the SQLite/PostgreSQL database.

### ⚙️ Backend Function Documentation

#### `app/api/routers/documents.py`
- `upload()`: Receives a file, saves it to disk via `upload_document`, and spawns a background task for AI processing.
- `list_documents()`: Fetches a paginated list of all processed images.
- `search_documents()`: Implements a unified search across tags, captions, and filenames using case-insensitive partial matching.
- `get_image_graph()`: Retrieves all images with embeddings and calculates their spatial positions and relational links for the 3D view.
- `get_document()`: Retreives full details for a single specific document.

#### `app/services/document_services.py`
- `upload_document()`: Handles the file save process. It calculates a SHA256 hash to prevent duplicates and returns the existing record if found.
- `get_document_absolute_path()`: Helper to resolve a database relative path into a full system path.

#### `app/services/ai_service.py`
- `process_document_ai()`: The main background worker. Orchestrates YOLO, Moondream, and CLIP to populate a document's metadata.
- `run_yolo()`: Executes object detection to find common items (e.g., "dog", "car").
- `extract_ai_keywords()`: Uses Moondream to prompt for specific descriptive keywords that YOLO might miss.
- `generate_embedding()`: Uses CLIP (OpenAI) to generate a 512-dimensional vector representing the "meaning" of the image.

#### `app/services/graph_service.py`
- `calculate_2d_projection()`: Takes high-dimensional embeddings and uses **UMAP** to project them into a normalized coordinate system for the UI.

#### `app/db/database.py`
- `get_session()`: A dependency generator for async database sessions.
- `get_sync_database_url()`: Safely converts async connection strings to sync ones for multi-threaded background processing.

---

## 🎨 Frontend Features

The frontend is a high-performance **React** application built with **Vite** and **Tailwind CSS**, focusing on a premium, cinematic user experience.

- **Dynamic Grid Interface**: A sleek, grayscale-to-color interactive grid for browsing your library.
- **3D Constellation View**: A revolutionary 3D graph visualization powered by `react-force-graph-3d`. It clusters images semantically—images that "look" similar or share meanings are physically closer in space.
- **Intelligent Search**: Real-time filtering that searches through AI-generated captions and tags instantly.
- **Deep Image Inspection**: A detailed modal view showing full-resolution previews, AI-generated transcriptions, and categorical tags.
- **Background AI Polling**: The UI automatically detects when images are being processed and updates the metadata in real-time as the backend finishes its analysis.
- **Seamless Secure Upload**: Drag-and-drop or file selection with automatic hash-based deduplication to keep your library clean.
- **Premium Aesthetics**: A custom-designed dark mode interface with glassmorphism, micro-animations, and high-contrast typography.

import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import fitz  # PyMuPDF

# Load environment variables from .env
load_dotenv()

from backend.ingest import ingest_pdf, update_metadata
from backend.retrieve import retrieve_chunks
from backend.llm import generate_answer

app = FastAPI(title="DocTalk Backend API")

# Configure CORS so Streamlit can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str
    filename: str

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Accepts PDF upload, saves it, records the initial status as processing,
    and launches the ingestion pipeline asynchronously in the background.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    
    # Save file to uploads folder
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
        
    try:
        # Get page count using PyMuPDF
        doc = fitz.open(file_path)
        page_count = len(doc)
    except Exception as e:
        # Cleanup file if invalid PDF
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid PDF file format: {str(e)}")
        
    # Mark status as processing in metadata JSON
    update_metadata(file.filename, page_count, "processing")
    
    # Enqueue ingestion pipeline task
    background_tasks.add_task(ingest_pdf, file_path, file.filename)
    
    return {
        "filename": file.filename,
        "page_count": page_count,
        "status": "processing"
    }

@app.post("/query")
async def query_document(request: QueryRequest):
    """
    Retrieves the top-k chunks from Qdrant via hybrid RRF search,
    passes them to Groq, and returns the grounded answer with citations.
    """
    if not request.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    if not request.question or request.question.strip() == "":
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    # Retrieve top relevant passages
    chunks = retrieve_chunks(request.question, request.filename)
    
    # Generate LLM response grounded in passages
    result = generate_answer(request.question, chunks, request.filename)
    
    return result

@app.get("/documents")
async def get_documents():
    """
    Returns a list of all uploaded and indexed documents.
    """
    qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_store")
    metadata_path = os.path.join(qdrant_path, "metadata.json")
    
    if not os.path.exists(metadata_path):
        return []
        
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        return list(metadata.values())
    except Exception:
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import uuid
import json
import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct, SparseVector

from backend.models_cache import get_dense_model, get_sparse_model

def update_metadata(filename: str, page_count: int, status: str):
    """
    
    Updates the local document catalog metadata JSON file.
    """
    qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_store")
    metadata_path = os.path.join(qdrant_path, "metadata.json")
    os.makedirs(qdrant_path, exist_ok=True)
    
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}
            
    metadata[filename] = {
        "filename": filename,
        "page_count": page_count,
        "status": status
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

def ingest_pdf(file_path: str, filename: str):
    """
    Parses a PDF file, splits it into overlapping token chunks,
    generates dense and sparse embeddings, and uploads them to Qdrant.
    """
    try:
        # 1. Open PDF and extract text
        doc = fitz.open(file_path)
        page_count = len(doc)
        
        # Ensure status is processing at start
        update_metadata(filename, page_count, "processing")
        
        # Load cached models
        dense_model = get_dense_model()
        sparse_model = get_sparse_model()
        tokenizer = dense_model.tokenizer
        
        chunks = []
        
        chunk_size = int(os.getenv("CHUNK_SIZE", 512))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 64))
        
        # 2. Extract page text and tokenize into chunks
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            if not text.strip():
                continue
                
            # Tokenize text using the HuggingFace tokenizer
            tokens = tokenizer.encode(text)
            num_tokens = len(tokens)
            
            if num_tokens <= chunk_size:
                chunk_text = tokenizer.decode(tokens, skip_special_tokens=True)
                chunks.append({
                    "text": chunk_text,
                    "page_number": page_num + 1,
                    "filename": filename
                })
            else:
                start = 0
                while start < num_tokens:
                    end = min(start + chunk_size, num_tokens)
                    chunk_tokens = tokens[start:end]
                    chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                    chunks.append({
                        "text": chunk_text,
                        "page_number": page_num + 1,
                        "filename": filename
                    })
                    if end == num_tokens:
                        break
                    start += chunk_size - chunk_overlap
                    
        if not chunks:
            # If no text was extracted, update status to failed
            update_metadata(filename, page_count, "failed")
            return
            
        # 3. Compute dense embeddings in batch
        texts = [c["text"] for c in chunks]
        dense_vectors = dense_model.encode(texts).tolist()
        
        # 4. Compute sparse embeddings in batch
        sparse_embeddings = list(sparse_model.embed(texts))
        
        # 5. Connect to Qdrant
        qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_store")
        collection_name = os.getenv("COLLECTION_NAME", "doctalk_docs")
        
        client = QdrantClient(path=qdrant_path)
        
        # 6. Ensure Collection exists
        try:
            client.get_collection(collection_name)
        except Exception:
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=len(dense_vectors[0]),
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False
                        )
                    )
                }
            )
            
        # 7. Prepare points
        points = []
        for idx, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            sparse_emb = sparse_embeddings[idx]
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_vectors[idx],
                        "sparse": SparseVector(
                            indices=sparse_emb.indices.tolist(),
                            values=sparse_emb.values.tolist()
                        )
                    },
                    payload={
                        "text": chunk["text"],
                        "page_number": chunk["page_number"],
                        "filename": chunk["filename"]
                    }
                )
            )
            
        # 8. Upsert to Qdrant in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            client.upsert(
                collection_name=collection_name,
                points=points[i:i + batch_size]
            )
            
        # 9. Update status in metadata
        update_metadata(filename, page_count, "indexed")
        
    except Exception as e:
        print(f"Error during ingestion of {filename}: {str(e)}")
        # Try to mark as failed
        try:
            doc = fitz.open(file_path)
            update_metadata(filename, len(doc), "failed")
        except Exception:
            update_metadata(filename, 0, "failed")

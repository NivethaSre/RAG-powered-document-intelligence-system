import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import SparseVector

from backend.models_cache import get_dense_model, get_sparse_model

def retrieve_chunks(question: str, filename: str) -> list:
    """
    Performs hybrid search (dense + sparse) on the specified document
    and fuses results using Reciprocal Rank Fusion (RRF).
    """
    try:
        qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_store")
        collection_name = os.getenv("COLLECTION_NAME", "doctalk_docs")
        top_k = int(os.getenv("TOP_K", 5))
        
        client = QdrantClient(path=qdrant_path)
        
        # Verify collection exists before querying
        try:
            client.get_collection(collection_name)
        except Exception:
            return []
            
        # Load cached models
        dense_model = get_dense_model()
        sparse_model = get_sparse_model()
        
        # Generate query dense embeddings
        dense_query = dense_model.encode(question).tolist()
        
        # Generate query sparse embeddings
        sparse_query_emb = list(sparse_model.embed([question]))[0]
        sparse_query = SparseVector(
            indices=sparse_query_emb.indices.tolist(),
            values=sparse_query_emb.values.tolist()
        )
        
        # Scope search to the target document
        doc_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="filename",
                    match=models.MatchValue(value=filename)
                )
            ]
        )
        
        # Execute hybrid search with RRF fusion
        results = client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_query,
                    using="dense",
                    limit=top_k * 2,
                    filter=doc_filter
                ),
                models.Prefetch(
                    query=sparse_query,
                    using="sparse",
                    limit=top_k * 2,
                    filter=doc_filter
                ),
            ],
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            query_filter=doc_filter,
            limit=top_k
        )
        
        chunks = []
        for point in results.points:
            chunks.append({
                "text": point.payload["text"],
                "page_number": point.payload["page_number"],
                "filename": point.payload["filename"]
            })
            
        return chunks
        
    except Exception as e:
        print(f"Error during retrieval: {str(e)}")
        return []

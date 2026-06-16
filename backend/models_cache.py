import os
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding

_dense_model = None
_sparse_model = None

def get_dense_model():
    """
    Get or load the dense sentence-transformers model.
    """
    global _dense_model
    if _dense_model is None:
        model_name = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
        _dense_model = SentenceTransformer(model_name)
    return _dense_model

def get_sparse_model():
    """
    Get or load the sparse fastembed model (SPLADE).
    """
    global _sparse_model
    if _sparse_model is None:
        # Default SPLADE model supported by fastembed
        _sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
    return _sparse_model

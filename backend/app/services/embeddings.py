from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.core.config import settings

_model_instance: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-loads the SentenceTransformer singleton model."""
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model_instance


def generate_embedding(text: str) -> List[float]:
    """Generates a 384-dimensional dense vector for a given text string."""
    model = get_embedding_model()
    # Normalize embeddings for cosine similarity
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generates dense embedding vectors for a batch of text strings."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()

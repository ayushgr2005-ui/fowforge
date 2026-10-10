from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.core.config import settings

@lru_cache(maxsize=1)
def model():
    return SentenceTransformer(settings.embedding_model)

def embed(texts: list[str]) -> list[list[float]]:
    return model().encode(texts, normalize_embeddings=True).tolist()

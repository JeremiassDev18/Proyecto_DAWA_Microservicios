from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.ml.text_cleaner import clean_text

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.MODEL_NAME)
    return _model


def generate_embedding(text: str) -> list[float]:
    model = _get_model()
    cleaned = clean_text(text)
    return model.encode(cleaned).tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    cleaned = [clean_text(t) for t in texts]
    return model.encode(cleaned).tolist()


def update_embedding_in_db(conn, record_id: int, embedding: list[float]):
    from app.db.queries import update_embedding
    update_embedding(conn, record_id, embedding)

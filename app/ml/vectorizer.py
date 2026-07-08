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




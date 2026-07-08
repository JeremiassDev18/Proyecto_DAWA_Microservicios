from app.core.config import settings
from app.db import queries
from app.ml.vectorizer import generate_embedding
from app.utils.logger import logger

INTENT_CATEGORY_MAP: dict[str, str] = {
    "CONSULTAR_PERFIL": "carreras",
    "BUSCAR_DOCENTE": "docentes",
    "DISPONIBILIDAD_DOCENTE": "docentes",
    "CONTACTAR_DOCENTE": "docentes",
}


def search_documents(conn, query_text: str, limit: int = 3, category: str = None):
    embedding = generate_embedding(query_text)
    return queries.search_documentos(
        conn, embedding, categoria=category, limit=limit
    )


def build_context(documents) -> str:
    if not documents:
        return ""
    parts = []
    for doc in documents:
        parts.append(f"{doc[1]}: {doc[2]}")
    return "\n\n".join(parts)


def respond_with_documents(conn, query_text: str, intent: str = "") -> str | None:
    category = INTENT_CATEGORY_MAP.get(intent) if intent else None
    docs = search_documents(
        conn, query_text,
        limit=settings.RAG_TOP_K,
        category=category,
    )
    if not docs:
        return None

    best = docs[0]
    similarity = float(best[5])
    if similarity < settings.RAG_SIMILARITY_THRESHOLD:
        return None

    context = build_context(docs)
    logger.info(f"RAG: {len(docs)} docs (cat={category}, top_sim={similarity:.3f})")
    return context

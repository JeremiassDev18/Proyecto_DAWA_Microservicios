from app.core.config import settings
from app.db import queries
from app.ml.vectorizer import generate_embedding
from app.utils.logger import logger


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


def respond_with_documents(conn, query_text: str) -> str | None:
    docs = search_documents(
        conn, query_text,
        limit=settings.RAG_TOP_K,
    )
    if not docs:
        return None

    best = docs[0]
    similarity = float(best[5])
    if similarity < settings.RAG_SIMILARITY_THRESHOLD:
        return None

    context = build_context(docs)
    logger.info(f"RAG: {len(docs)} documento(s) encontrados (top sim={similarity:.3f})")
    return context

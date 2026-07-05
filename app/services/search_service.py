from app.db import queries
from app.ml.vectorizer import generate_embedding


def hybrid_search(conn, mensaje: str) -> str | None:
    embedding = generate_embedding(mensaje)
    results = queries.search_hybrid(conn, embedding, mensaje, limit=1)
    if not results:
        return None

    best = results[0]
    if best[4] < 0.5:
        return None

    respuesta = queries.get_respuesta_by_intencion(conn, best[2])
    if not respuesta:
        return None

    queries.increment_veces_usada(conn, respuesta[0])
    return respuesta[1]

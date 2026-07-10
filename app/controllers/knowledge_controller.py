"""
Controlador del Centro de Conocimiento.

Gestiona fragmentos de conocimiento institucional usados por el agente RAG.
Cada entrada genera un embedding con MiniLM para búsqueda semántica.
"""

from typing import Optional

from app.db import queries
from app.ml.vectorizer import generate_embedding


def _row_to_dict(r):
    return {
        "id": r[0],
        "titulo": r[1],
        "contenido": r[2],
        "tags": r[3] or [],
        "activo": r[4],
        "fecha_actualizacion": r[5],
    }


def list_knowledge(conn, texto_query: str = "", tags: list[str] | None = None,
                   activo: Optional[bool] = None):
    rows = queries.query_conocimiento(conn, texto_query, tags, activo)
    return [_row_to_dict(r) for r in rows]


def get_knowledge(conn, id: int):
    row = queries.get_conocimiento_by_id(conn, id)
    return _row_to_dict(row) if row else None


def create_knowledge(conn, titulo: str, contenido: str, tags: list[str] | None = None):
    embedding = generate_embedding(f"{titulo} {contenido}")
    new_id = queries.insert_conocimiento(
        conn, titulo, contenido, embedding, tags or [],
    )
    return get_knowledge(conn, new_id)


def update_knowledge(conn, id: int, titulo: Optional[str] = None,
                     contenido: Optional[str] = None,
                     tags: Optional[list[str]] = None):
    existing = queries.get_conocimiento_by_id(conn, id)
    if not existing:
        return None

    new_titulo = titulo if titulo is not None else existing[1]
    new_contenido = contenido if contenido is not None else existing[2]
    new_tags = tags if tags is not None else (existing[3] or [])

    queries.update_conocimiento(conn, id, new_titulo, new_contenido, new_tags)

    if titulo is not None or contenido is not None:
        embedding = generate_embedding(f"{new_titulo} {new_contenido}")
        queries.update_embedding_conocimiento(conn, id, embedding)

    return get_knowledge(conn, id)


def delete_knowledge(conn, id: int):
    existing = queries.get_conocimiento_by_id(conn, id)
    if not existing:
        return False
    queries.soft_delete_conocimiento(conn, id)
    return True

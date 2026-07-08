from typing import Optional

from app.db import queries
from app.ml.vectorizer import generate_embedding


def _row_to_dict(r):
    return {
        "id": r[0],
        "titulo": r[1],
        "contenido": r[2],
        "categoria": r[3],
        "fuente": r[4],
        "archivo_pdf": r[5],
        "activo": r[6],
        "creado_en": r[7].isoformat() if r[7] else None,
        "actualizado_en": r[8].isoformat() if r[8] else None,
    }


def list_documents(conn, query: str = "", categoria: str = "",
                   activo: Optional[bool] = None):
    rows = queries.query_documentos(conn, query, categoria, activo)
    return [_row_to_dict(r) for r in rows]


def get_document(conn, id: int):
    row = queries.get_documento_by_id(conn, id)
    return _row_to_dict(row) if row else None


def create_document(conn, titulo: str, contenido: str,
                    categoria: str = "", fuente: str = "",
                    archivo_pdf: str = ""):
    embedding = generate_embedding(f"{titulo} {contenido}")
    new_id = queries.insert_documento(
        conn, titulo, contenido, embedding,
        categoria, fuente, archivo_pdf,
    )
    return get_document(conn, new_id)


def update_document(conn, id: int, titulo: Optional[str] = None,
                    contenido: Optional[str] = None,
                    categoria: Optional[str] = None,
                    fuente: Optional[str] = None,
                    archivo_pdf: Optional[str] = None):
    existing = queries.get_documento_by_id(conn, id)
    if not existing:
        return None

    new_titulo = titulo if titulo is not None else existing[1]
    new_contenido = contenido if contenido is not None else existing[2]
    new_categoria = categoria if categoria is not None else (existing[3] or "")
    new_fuente = fuente if fuente is not None else (existing[4] or "")
    new_archivo = archivo_pdf if archivo_pdf is not None else (existing[5] or "")

    queries.update_documento(conn, id, new_titulo, new_contenido,
                             new_categoria, new_fuente, new_archivo)

    if titulo is not None or contenido is not None:
        embedding = generate_embedding(f"{new_titulo} {new_contenido}")
        queries.update_embedding_documento(conn, id, embedding)

    return get_document(conn, id)


def delete_document(conn, id: int):
    existing = queries.get_documento_by_id(conn, id)
    if not existing:
        return False
    queries.soft_delete_documento(conn, id)
    return True

from typing import Optional

from app.db import queries


def get_all(conn, texto_query: str = "", intencion: str = "",
            activo: Optional[bool] = None):
    return queries.query_dataset(conn, texto_query, intencion, activo)


def get_by_id(conn, id: int):
    return queries.get_dataset_by_id(conn, id)


def create(conn, texto: str, id_intencion: int,
           embedding: Optional[list] = None,
           origen: str = "manual") -> int:
    return queries.insert_dataset(conn, texto, id_intencion, embedding, origen)


def update(conn, id: int, texto: str, id_intencion: int):
    queries.update_dataset(conn, id, texto, id_intencion)


def update_embedding(conn, id: int, embedding: list):
    queries.update_embedding(conn, id, embedding)


def delete(conn, id: int):
    queries.soft_delete_dataset(conn, id)


def validate(conn, id: int):
    queries.validate_dataset(conn, id)

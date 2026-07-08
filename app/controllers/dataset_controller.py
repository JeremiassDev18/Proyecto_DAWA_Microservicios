from typing import Optional

from app.db import dataset_repository as repo
from app.db import queries
from app.ml.vectorizer import generate_embedding


def _row_to_dict(r):
    return {
        "id": r[0],
        "texto": r[1],
        "id_intencion": r[2],
        "intencion": r[3],
        "validado": r[4],
        "origen": r[5],
        "activo": r[6],
        "creado_en": r[7],
        "actualizado_en": r[8],
    }


def list_dataset(conn, texto_query: str = "", intencion: str = "",
                 activo: Optional[bool] = None):
    rows = repo.get_all(conn, texto_query, intencion, activo)
    return [_row_to_dict(r) for r in rows]


def get_dataset(conn, id: int):
    row = repo.get_by_id(conn, id)
    return _row_to_dict(row) if row else None


def create_dataset(conn, texto: str, id_intencion: int, origen: str = "manual"):
    embedding = generate_embedding(texto)
    new_id = repo.create(conn, texto, id_intencion, embedding, origen)
    return get_dataset(conn, new_id)


def update_dataset(conn, id: int, texto: Optional[str] = None,
                   id_intencion: Optional[int] = None):
    existing = repo.get_by_id(conn, id)
    if not existing:
        return None
    new_texto = texto if texto is not None else existing[1]
    new_id_intencion = id_intencion if id_intencion is not None else existing[2]
    repo.update(conn, id, new_texto, new_id_intencion)
    if texto is not None and texto != existing[1]:
        embedding = generate_embedding(new_texto)
        repo.update_embedding(conn, id, embedding)
    return get_dataset(conn, id)


def delete_dataset(conn, id: int):
    existing = repo.get_by_id(conn, id)
    if not existing:
        return False
    repo.delete(conn, id)
    return True


def validate_dataset(conn, id: int):
    existing = repo.get_by_id(conn, id)
    if not existing:
        return None
    repo.validate(conn, id)

    from app.db.training_repository import auto_train_if_needed
    trained = auto_train_if_needed(conn)
    if trained:
        from app.utils.logger import logger
        logger.info("Reentrenamiento automático completado.")

    return get_dataset(conn, id)

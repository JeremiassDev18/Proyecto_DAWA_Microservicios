from app.core.config import settings
from app.db import queries


def get_training_data(conn):
    rows = queries.get_activos_validados(conn)
    texts = [r[1] for r in rows]
    labels = [r[3] for r in rows]
    return texts, labels


def save_model_with_metrics(conn, nombre: str, version: str, metrics: dict) -> int:
    model_id = queries.crear_modelo(
        conn, nombre, version,
        accuracy=metrics.get("accuracy", 0.0),
        precision=metrics.get("precision", 0.0),
        recall=metrics.get("recall", 0.0),
        f1_score=metrics.get("f1_score", 0.0),
    )
    queries.set_modelo_activo(conn, model_id)
    return model_id


def record_training_run(conn, modelo_version: str, ejemplos_usados: int,
                        metrics: dict) -> int:
    training_id = queries.iniciar_training(conn, modelo_version)
    queries.completar_training(
        conn, training_id, ejemplos_usados,
        accuracy=metrics.get("accuracy", 0.0),
        precision=metrics.get("precision", 0.0),
        recall=metrics.get("recall", 0.0),
        f1_score=metrics.get("f1_score", 0.0),
        loss=metrics.get("loss", 0.0),
    )
    return training_id


def auto_train_if_needed(conn) -> bool:
    if not settings.AUTO_TRAIN:
        return False
    nuevos = queries.count_nuevos_validados(conn)
    if nuevos < settings.AUTO_TRAIN_THRESHOLD:
        return False

    texts, labels = get_training_data(conn)
    if not texts:
        return False

    from app.services.training_queue import enqueue_training
    task_id = enqueue_training(texts, labels)
    return task_id is not None

import threading
from datetime import datetime
from typing import Optional

from app.utils.logger import logger

_tasks: dict[int, dict] = {}
_counter = [0]
_lock = threading.Lock()
_training_in_progress = False


def _next_id() -> int:
    with _lock:
        _counter[0] += 1
        return _counter[0]


def _run_training(task_id: int, texts: list[str], labels: list[str]):
    from app.db.postgres_client import get_connection, release_connection

    conn = get_connection()
    try:
        from app.ml.setfit_trainer import train_model
        from app.db import queries
        from app.utils.version import next_version
        from app.db.training_repository import save_model_with_metrics, record_training_run

        metrics = train_model(texts, labels)

        from app.ml import predictor as ml_predictor
        from app.ml.setfit_trainer import load_model
        try:
            ml_predictor.set_cached_model(load_model())
            logger.info("Modelo recargado en caché tras entrenamiento")
        except Exception as e:
            logger.error(f"Error al recargar modelo en caché: {e}")

        active = queries.get_modelo_activo(conn)
        prev_version = active[2] if active else None
        version = next_version(prev_version)
        version_str = f"setfit-v{version}"

        save_model_with_metrics(conn, "setfit", version_str, metrics)
        record_training_run(conn, version_str, len(texts), metrics)

        with _lock:
            _tasks[task_id] = {
                "status": "completed",
                "modelo_version": version_str,
                "metricas": metrics,
                "completed_at": datetime.now(),
                "error": None,
            }

        logger.info(f"Training task {task_id} completed: {version_str}")

    except Exception as e:
        logger.error(f"Training task {task_id} failed: {e}")
        with _lock:
            _tasks[task_id] = {
                "status": "failed",
                "modelo_version": "",
                "metricas": {},
                "completed_at": datetime.now(),
                "error": str(e),
            }
    finally:
        global _training_in_progress
        with _lock:
            _training_in_progress = False
        release_connection(conn)


def enqueue_training(texts: list[str], labels: list[str]) -> int | None:
    global _training_in_progress
    with _lock:
        if _training_in_progress:
            logger.warning("Training already in progress, rejecting duplicate")
            return None
        _training_in_progress = True

    task_id = _next_id()
    with _lock:
        _tasks[task_id] = {
            "status": "pending",
            "modelo_version": "",
            "metricas": {},
            "completed_at": None,
            "error": None,
        }

    thread = threading.Thread(
        target=_run_training,
        args=(task_id, texts, labels),
        daemon=True,
    )
    thread.start()
    logger.info(f"Training task {task_id} enqueued ({len(texts)} examples)")
    return task_id


def get_task_status(task_id: int) -> Optional[dict]:
    with _lock:
        return _tasks.get(task_id)

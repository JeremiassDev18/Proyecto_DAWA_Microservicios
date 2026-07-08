import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, get_connection, release_connection
from app.db.training_repository import get_training_data, save_model_with_metrics, record_training_run
from app.db.queries import get_modelo_activo
from app.ml.setfit_trainer import train_model
from app.utils.version import next_version


def main():
    init_pool()
    conn = get_connection()
    try:
        texts, labels = get_training_data(conn)
        if not texts:
            print("No hay datos de entrenamiento validados.")
            return

        print(f"Entrenando con {len(texts)} ejemplos...")
        metrics = train_model(texts, labels)
        print(f"Métricas: {metrics}")

        active = get_modelo_activo(conn)
        version = next_version(active[2] if active else None)
        version_str = f"setfit-v{version}"

        model_id = save_model_with_metrics(conn, "setfit", version_str, metrics)
        record_training_run(conn, version_str, len(texts), metrics)

        print(f"Modelo {version_str} guardado (ID {model_id}).")
    finally:
        release_connection(conn)


if __name__ == "__main__":
    main()

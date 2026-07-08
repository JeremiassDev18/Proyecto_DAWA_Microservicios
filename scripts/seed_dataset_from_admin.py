import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, close_pool
from app.services.admin_sync_service import sync
from app.utils.logger import logger


def main():
    logger.info("Inicializando pool de conexiones...")
    init_pool()

    try:
        logger.info("Sincronizando datos desde administración...")
        stats = sync()

        print("\n" + "=" * 50)
        print("RESULTADO DE SINCRONIZACIÓN")
        print("=" * 50)
        if "error" in stats:
            print(f"  ERROR: {stats['error']}")
        else:
            print(f"  Docentes encontrados:    {stats['docentes_encontrados']}")
            print(f"  Carreras encontradas:     {stats['carreras_encontradas']}")
            print(f"  Facultades encontradas:   {stats['facultades_encontradas']}")
            print(f"  Ejemplos generados:       {stats['ejemplos_generados']}")
            print(f"  Ejemplos insertados:      {stats['ejemplos_insertados']}")
            print(f"  Duplicados omitidos:      {stats['duplicados_omitidos']}")
            print(f"  Documentos RAG:           {stats['documentos_rag_generados']}")
            training = stats.get('training_task_id')
            if training:
                print(f"  Entrenamiento encolado:   task_id={training}")
            else:
                print(f"  Entrenamiento:            no necesario (0 insertados o ya en curso)")
        print("=" * 50 + "\n")

    finally:
        close_pool()
        logger.info("Pool cerrado.")


if __name__ == "__main__":
    main()

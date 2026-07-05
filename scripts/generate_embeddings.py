import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, get_connection, release_connection
from app.db.queries import get_pendientes_embedding, update_embedding, update_embedding_documento
from app.ml.vectorizer import generate_embedding


def _process_dataset(conn):
    rows = get_pendientes_embedding(conn)
    print(f"Generando embeddings para {len(rows)} registros del dataset...")
    for pid, texto in rows:
        emb = generate_embedding(texto)
        update_embedding(conn, pid, emb)
    return len(rows)


def _process_documents(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, contenido FROM documento_base WHERE embedding IS NULL"
        )
        rows = cur.fetchall()
    print(f"Generando embeddings para {len(rows)} documentos...")
    for did, contenido in rows:
        emb = generate_embedding(contenido)
        update_embedding_documento(conn, did, emb)
    return len(rows)


def main():
    init_pool()
    conn = get_connection()
    try:
        ds_count = _process_dataset(conn)
        doc_count = _process_documents(conn)
        print(f"Completado: {ds_count} dataset + {doc_count} documentos.")
    finally:
        release_connection(conn)


if __name__ == "__main__":
    main()

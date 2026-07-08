#!/usr/bin/env python3
"""
Script para generar y guardar embeddings en la columna 'embedding' de chatbot_pregunta.
Ejecutar después de levantar la BD y antes de poner en producción el servicio.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, get_connection, release_connection
from app.db import queries
from app.ml.vectorizer import generate_embedding

def main():
    init_pool()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Obtener todas las preguntas que aún no tienen embedding
            cur.execute("SELECT id, pregunta_texto FROM chatbot_pregunta WHERE embedding IS NULL")
            rows = cur.fetchall()
            print(f"Se encontraron {len(rows)} preguntas sin embedding.")
            for pid, texto in rows:
                print(f"Generando embedding para pregunta ID {pid}...")
                emb = generate_embedding(texto)
                queries.update_embedding(conn, pid, emb)
            print("✅ Todos los embeddings han sido generados y guardados.")
    finally:
        release_connection(conn)

if __name__ == "__main__":
    main()
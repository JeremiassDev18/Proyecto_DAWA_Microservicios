from typing import Generator
from app.db.postgres_client import get_connection, release_connection

def get_db() -> Generator:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.rollback()
        release_connection(conn)   
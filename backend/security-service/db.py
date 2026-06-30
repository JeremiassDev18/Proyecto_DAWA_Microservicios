import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Config

connection_pool = None


def init_db_pool(minconn: int = 1, maxconn: int = 10):
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn,
            maxconn,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
        )
    return connection_pool


def get_connection():
    if connection_pool is None:
        init_db_pool()
    return connection_pool.getconn()


def release_connection(conn):
    if connection_pool and conn is not None:
        connection_pool.putconn(conn)


def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None

        conn.commit()

        return result
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        release_connection(conn)

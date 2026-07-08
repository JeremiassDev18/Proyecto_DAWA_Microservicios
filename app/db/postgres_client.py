from psycopg2.pool import ThreadedConnectionPool
from app.core.config import settings
from pgvector.psycopg2 import register_vector

pool = None


def init_pool(minconn: int = 2, maxconn: int = 10):
    global pool
    pool = ThreadedConnectionPool(minconn, maxconn, settings.DATABASE_URL)


def get_connection():
    global pool
    if pool is None:
        init_pool()
    conn = pool.getconn()
    register_vector(conn)
    return conn


def release_connection(conn):
    global pool
    if pool is None:
        return
    pool.putconn(conn)


def close_pool():
    global pool
    if pool is not None:
        pool.closeall()
        pool = None

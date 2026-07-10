"""
Queries de PostgreSQL para el chatbot-service.

Este módulo contiene únicamente las funciones activas usadas por:
- Gestión de conversaciones y mensajes
- Feedback de usuarios
- Preguntas pendientes
- Centro de conocimiento (RAG)
- Métricas de uso
- Memoria del agente LLM

Código obsoleto de SetFit (dataset, intenciones, respuestas, modelos,
entrenamientos, predicciones) fue eliminado en la migración al agente LLM.
"""

import json
from datetime import datetime
from typing import Any, Optional


# ── chatbot_conversacion ───────────────────────────────────────────────

def create_conversacion(conn, id_usuario: int, nombre_cliente: str = "") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_conversacion (id_usuario, nombre_cliente) "
            "VALUES (%s, %s) RETURNING id",
            (id_usuario, nombre_cliente or None),
        )
        conn.commit()
        return cur.fetchone()[0]


def update_conversacion_nombre(conn, id_conversacion: int, nombre_cliente: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_conversacion SET nombre_cliente = %s WHERE id = %s AND "
            "(nombre_cliente IS NULL OR nombre_cliente = '')",
            (nombre_cliente, id_conversacion),
        )
        conn.commit()


def update_conversacion_estado(conn, id_conversacion: int, activa: bool):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_conversacion SET activa = %s WHERE id = %s",
            (activa, id_conversacion),
        )
        conn.commit()


def get_conversacion(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, id_usuario, activa, iniciado_en, finalizado_en "
            "FROM chatbot_conversacion WHERE id = %s",
            (id_conversacion,),
        )
        return cur.fetchone()


def get_conversaciones_by_usuario(conn, id_usuario: int, limit: int = 20):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, id_usuario, nombre_cliente, activa, iniciado_en, finalizado_en "
            "FROM chatbot_conversacion WHERE id_usuario = %s "
            "ORDER BY iniciado_en DESC LIMIT %s",
            (id_usuario, limit),
        )
        return cur.fetchall()


def delete_old_conversations(conn, id_usuario: int, keep: int = 5) -> int:
    """Elimina conversaciones antiguas dejando solo las `keep` más recientes."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM chatbot_conversacion "
            "WHERE id_usuario = %s AND id NOT IN ("
            "  SELECT id FROM chatbot_conversacion "
            "  WHERE id_usuario = %s ORDER BY iniciado_en DESC LIMIT %s"
            ")",
            (id_usuario, id_usuario, keep),
        )
        conn.commit()
        return cur.rowcount


def cerrar_conversacion(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_conversacion SET activa = FALSE, finalizado_en = NOW() "
            "WHERE id = %s",
            (id_conversacion,),
        )
        conn.commit()


# ── chatbot_mensaje ────────────────────────────────────────────────────

def insert_mensaje(conn, id_conversacion: int, rol: str, contenido: str,
                   tipo_resolucion: str = "estatica") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_mensaje "
            "(id_conversacion, rol, contenido, tipo_resolucion) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (id_conversacion, rol, contenido, tipo_resolucion),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_mensajes_by_conversacion(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, rol, contenido, tipo_resolucion, id_intencion, "
            "confianza_ml, modelo_usado, enviado_en "
            "FROM chatbot_mensaje WHERE id_conversacion = %s "
            "ORDER BY enviado_en",
            (id_conversacion,),
        )
        return cur.fetchall()


def get_mensaje_by_id(conn, id_mensaje: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, id_conversacion, rol, contenido, tipo_resolucion, "
            "id_intencion, confianza_ml, modelo_usado, enviado_en "
            "FROM chatbot_mensaje WHERE id = %s",
            (id_mensaje,),
        )
        return cur.fetchone()


# ── chatbot_feedback ───────────────────────────────────────────────────

def insert_feedback(conn, id_mensaje: int, util: bool) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_feedback (id_mensaje, fue_util) VALUES (%s, %s) RETURNING id",
            (id_mensaje, util),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_feedback_by_mensaje(conn, id_mensaje: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, fue_util, creado_en FROM chatbot_feedback WHERE id_mensaje = %s",
            (id_mensaje,),
        )
        return cur.fetchone()


# ── chatbot_pregunta_pendiente ─────────────────────────────────────────

def insert_pendiente(conn, contenido: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_pregunta_pendiente (contenido) "
            "VALUES (%s) RETURNING id",
            (contenido,),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_pendientes(conn, resuelta: bool = False):
    with conn.cursor() as cur:
        if resuelta:
            cur.execute(
                "SELECT p.id, p.contenido, p.resuelta, p.creado_en "
                "FROM chatbot_pregunta_pendiente p "
                "WHERE p.resuelta = TRUE ORDER BY p.creado_en DESC"
            )
        else:
            cur.execute(
                "SELECT p.id, p.contenido, p.resuelta, p.creado_en "
                "FROM chatbot_pregunta_pendiente p "
                "WHERE p.resuelta = FALSE ORDER BY p.creado_en DESC"
            )
        return cur.fetchall()


def get_pendiente_by_id(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT p.id, p.contenido, p.resuelta, p.creado_en "
            "FROM chatbot_pregunta_pendiente p WHERE p.id = %s",
            (id,),
        )
        return cur.fetchone()


def marcar_pendiente_resuelta(conn, id_pendiente: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_pregunta_pendiente SET resuelta = TRUE WHERE id = %s",
            (id_pendiente,),
        )
        conn.commit()


def resolver_pendiente(conn, id_pendiente: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_pregunta_pendiente SET resuelta = TRUE WHERE id = %s",
            (id_pendiente,),
        )
        conn.commit()


# ── centro_conocimiento (Agentic RAG) ──────────────────────────────────

def get_conocimiento_by_id(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, titulo, contenido, tags, activo, fecha_actualizacion "
            "FROM centro_conocimiento WHERE id = %s",
            (id,),
        )
        return cur.fetchone()


def query_conocimiento(conn, query: str = "", tags: list[str] | None = None,
                       activo: Optional[bool] = None):
    with conn.cursor() as cur:
        sql = (
            "SELECT id, titulo, contenido, tags, activo, fecha_actualizacion "
            "FROM centro_conocimiento WHERE 1=1"
        )
        params: list[Any] = []
        if query:
            sql += " AND (titulo ILIKE %s OR contenido ILIKE %s)"
            params.extend([f"%{query}%", f"%{query}%"])
        if tags:
            sql += " AND tags && %s"
            params.append(tags)
        if activo is not None:
            sql += " AND activo = %s"
            params.append(activo)
        sql += " ORDER BY fecha_actualizacion DESC"
        cur.execute(sql, params)
        return cur.fetchall()


def insert_conocimiento(conn, titulo: str, contenido: str, embedding: list,
                        tags: list[str]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO centro_conocimiento (titulo, contenido, embedding, tags) "
            "VALUES (%s, %s, %s::vector, %s) RETURNING id",
            (titulo, contenido, embedding, tags),
        )
        conn.commit()
        return cur.fetchone()[0]


def update_conocimiento(conn, id: int, titulo: str, contenido: str, tags: list[str]):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE centro_conocimiento SET titulo = %s, contenido = %s, tags = %s, "
            "fecha_actualizacion = NOW() WHERE id = %s",
            (titulo, contenido, tags, id),
        )
        conn.commit()


def update_embedding_conocimiento(conn, id: int, embedding: list):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE centro_conocimiento SET embedding = %s::vector, "
            "fecha_actualizacion = NOW() WHERE id = %s",
            (embedding, id),
        )
        conn.commit()


def soft_delete_conocimiento(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE centro_conocimiento SET activo = FALSE, "
            "fecha_actualizacion = NOW() WHERE id = %s",
            (id,),
        )
        conn.commit()


def search_conocimiento_hibrido(conn, query_text: str, embedding: list,
                                limit: int = 20,
                                vector_weight: float = 0.80,
                                trgm_weight: float = 0.20):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ck.id, ck.titulo, ck.contenido, "
            "(%s * (1 - (ck.embedding <=> %s::vector)) "
            "+ %s * similarity(ck.contenido, %s)) as score "
            "FROM centro_conocimiento ck "
            "WHERE ck.activo = TRUE AND ck.embedding IS NOT NULL "
            "ORDER BY score DESC LIMIT %s",
            (vector_weight, embedding, trgm_weight, query_text, limit),
        )
        return cur.fetchall()


# ── agente_memoria (persistencia del agente LLM) ───────────────────────

def get_agent_memory(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT contexto, resumen, total_mensajes, actualizado_en "
            "FROM agente_memoria WHERE id_conversacion = %s",
            (id_conversacion,),
        )
        return cur.fetchone()


def upsert_agent_memory(conn, id_conversacion: int, contexto: str,
                        resumen: str = "", total_mensajes: int = 0):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO agente_memoria (id_conversacion, contexto, resumen, total_mensajes, actualizado_en) "
            "VALUES (%s, %s, %s, %s, NOW()) "
            "ON CONFLICT (id_conversacion) "
            "DO UPDATE SET contexto = EXCLUDED.contexto, "
            "              resumen = EXCLUDED.resumen, "
            "              total_mensajes = EXCLUDED.total_mensajes, "
            "              actualizado_en = NOW()",
            (id_conversacion, contexto, resumen, total_mensajes),
        )
        conn.commit()


def delete_agent_memory(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM agente_memoria WHERE id_conversacion = %s",
            (id_conversacion,),
        )
        conn.commit()


# ── Resúmenes de bitácoras (worker RabbitMQ) ───────────────────────────

def insert_bitacora_resumen(
    conn,
    solicitud_id: int,
    estudiante_id: int,
    observaciones: str,
    resumen: str,
    temas_detectados: str | None = None,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO bitacora_resumen (solicitud_id, estudiante_id, observaciones, resumen, temas_detectados) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (solicitud_id, estudiante_id, observaciones, resumen, temas_detectados),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_bitacora_resumen_by_solicitud(conn, solicitud_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, solicitud_id, estudiante_id, observaciones, resumen, temas_detectados, generado_en "
            "FROM bitacora_resumen WHERE solicitud_id = %s ORDER BY generado_en DESC LIMIT 1",
            (solicitud_id,),
        )
        return cur.fetchone()


def get_bitacora_resumenes_by_estudiante(conn, estudiante_id: int, limit: int = 20):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, solicitud_id, estudiante_id, observaciones, resumen, temas_detectados, generado_en "
            "FROM bitacora_resumen WHERE estudiante_id = %s ORDER BY generado_en DESC LIMIT %s",
            (estudiante_id, limit),
        )
        return cur.fetchall()


def insert_evento_procesado(conn, evento_id: str, tipo_evento: str, datos: dict):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO worker_evento_procesado (evento_id, tipo_evento, datos) "
            "VALUES (%s, %s, %s) ON CONFLICT (evento_id) DO NOTHING",
            (evento_id, tipo_evento, json.dumps(datos, ensure_ascii=False) if datos else None),
        )
        conn.commit()


def existe_evento_procesado(conn, evento_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM worker_evento_procesado WHERE evento_id = %s LIMIT 1",
            (evento_id,),
        )
        return cur.fetchone() is not None


# ── Métricas de uso ────────────────────────────────────────────────────

def count_conversaciones(conn, activa: Optional[bool] = None) -> int:
    with conn.cursor() as cur:
        if activa is None:
            cur.execute("SELECT COUNT(*) FROM chatbot_conversacion")
        else:
            cur.execute("SELECT COUNT(*) FROM chatbot_conversacion WHERE activa = %s", (activa,))
        return cur.fetchone()[0]


def count_mensajes(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM chatbot_mensaje")
        return cur.fetchone()[0]


def count_pendientes(conn, resuelta: bool = False) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM chatbot_pregunta_pendiente WHERE resuelta = %s",
            (resuelta,),
        )
        return cur.fetchone()[0]


def top_tipos_resolucion(conn, limit: int = 10):
    """
    Ahora agrupa por tipo_resolucion en lugar de intención.
    SetFit fue eliminado, por lo que las intenciones ya no aplican.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tipo_resolucion, COUNT(*) as total "
            "FROM chatbot_mensaje WHERE rol = 'bot' "
            "GROUP BY tipo_resolucion "
            "ORDER BY total DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def resolucion_por_tipo(conn):
    """
    Ahora devuelve conteo por tipo_resolucion (agente, estatica, etc.).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tipo_resolucion, COUNT(*) as total "
            "FROM chatbot_mensaje WHERE rol = 'bot' "
            "GROUP BY tipo_resolucion ORDER BY total DESC"
        )
        return cur.fetchall()


def feedback_summary(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT "
            "  COUNT(*) FILTER (WHERE fue_util = TRUE) as utiles, "
            "  COUNT(*) FILTER (WHERE fue_util = FALSE) as no_utiles, "
            "  COUNT(*) as total "
            "FROM chatbot_feedback"
        )
        return cur.fetchone()


# ── Resúmenes ──────────────────────────────────────────────────────────

def get_conversacion_with_mensajes(conn, id_conversacion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT c.id, c.id_usuario, c.nombre_cliente, "
            "c.iniciado_en, c.finalizado_en, c.activa "
            "FROM chatbot_conversacion c WHERE c.id = %s",
            (id_conversacion,),
        )
        conv = cur.fetchone()
        if not conv:
            return None
        cur.execute(
            "SELECT id, rol, contenido, tipo_resolucion, "
            "id_intencion, confianza_ml, enviado_en "
            "FROM chatbot_mensaje WHERE id_conversacion = %s "
            "ORDER BY enviado_en",
            (id_conversacion,),
        )
        mensajes = cur.fetchall()
        return conv, mensajes


def get_conversaciones_by_date_range(conn, desde, hasta, limit: int = 50):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT c.id, c.id_usuario, c.nombre_cliente, "
            "c.iniciado_en, c.activa "
            "FROM chatbot_conversacion c "
            "WHERE c.iniciado_en BETWEEN %s AND %s "
            "ORDER BY c.iniciado_en DESC LIMIT %s",
            (desde, hasta, limit),
        )
        return cur.fetchall()

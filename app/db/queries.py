from datetime import datetime
from typing import Any, Optional


# ── chatbot_dataset ── query helpers ───────────────────────────────────

def get_dataset_by_id(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion, "
            "cd.validado, cd.origen, cd.activo, cd.creado_en, cd.actualizado_en "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE cd.id = %s",
            (id,),
        )
        return cur.fetchone()


def update_dataset(conn, id: int, texto: str, id_intencion: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_dataset SET texto = %s, id_intencion = %s, "
            "actualizado_en = NOW() WHERE id = %s",
            (texto, id_intencion, id),
        )
        conn.commit()


def soft_delete_dataset(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_dataset SET activo = FALSE, actualizado_en = NOW() "
            "WHERE id = %s",
            (id,),
        )
        conn.commit()


def validate_dataset(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_dataset SET validado = TRUE, actualizado_en = NOW() "
            "WHERE id = %s",
            (id,),
        )
        conn.commit()


def query_dataset(conn, texto_query: str = "", intencion: str = "",
                  activo: Optional[bool] = None):
    with conn.cursor() as cur:
        sql = (
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion, "
            "cd.validado, cd.origen, cd.activo, cd.creado_en, cd.actualizado_en "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE 1=1"
        )
        params = []
        if texto_query:
            sql += " AND cd.texto ILIKE %s"
            params.append(f"%{texto_query}%")
        if intencion:
            sql += " AND ci.nombre = %s"
            params.append(intencion)
        if activo is not None:
            sql += " AND cd.activo = %s"
            params.append(activo)
        sql += " ORDER BY cd.id"
        cur.execute(sql, params)
        return cur.fetchall()


# ── chatbot_intencion ──────────────────────────────────────────────────

def get_all_intenciones(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, descripcion, activo, creado_en "
            "FROM chatbot_intencion ORDER BY nombre"
        )
        return cur.fetchall()


def get_intencion_by_id(conn, id_intencion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, descripcion, activo, creado_en "
            "FROM chatbot_intencion WHERE id = %s",
            (id_intencion,),
        )
        return cur.fetchone()


def get_intencion_by_nombre(conn, nombre: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, descripcion, activo, creado_en "
            "FROM chatbot_intencion WHERE nombre = %s",
            (nombre,),
        )
        return cur.fetchone()


def create_intencion(conn, nombre: str, descripcion: str = "") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_intencion (nombre, descripcion) "
            "VALUES (%s, %s) RETURNING id",
            (nombre, descripcion),
        )
        conn.commit()
        return cur.fetchone()[0]


# ── chatbot_dataset ────────────────────────────────────────────────────

def get_all_dataset(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion, "
            "cd.validado, cd.origen, cd.activo "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "ORDER BY cd.id"
        )
        return cur.fetchall()


def get_activos_validados(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE cd.activo = TRUE AND cd.validado = TRUE"
        )
        return cur.fetchall()


def search_hybrid(conn, embedding, query_text: str, limit: int = 5,
                  vector_weight: float = 0.7, trgm_weight: float = 0.3,
                  threshold: float = 0.25):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion, "
            "(%s * (1 - (cd.embedding <=> %s::vector)) "
            "+ %s * similarity(cd.texto, %s)) as score "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE cd.activo = TRUE AND cd.validado = TRUE "
            "AND (%s * (1 - (cd.embedding <=> %s::vector)) "
            "+ %s * similarity(cd.texto, %s)) >= %s "
            "ORDER BY score DESC LIMIT %s",
            (vector_weight, embedding, trgm_weight, query_text,
             vector_weight, embedding, trgm_weight, query_text,
             threshold, limit),
        )
        return cur.fetchall()


def search_by_embedding(conn, embedding, limit: int = 5, threshold: float = 0.25):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cd.id, cd.texto, cd.id_intencion, ci.nombre as intencion, "
            "1 - (cd.embedding <=> %s::vector) as similarity "
            "FROM chatbot_dataset cd "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE cd.activo = TRUE AND cd.validado = TRUE "
            "AND 1 - (cd.embedding <=> %s::vector) >= %s "
            "ORDER BY similarity DESC LIMIT %s",
            (embedding, embedding, threshold, limit),
        )
        return cur.fetchall()


def insert_dataset(conn, texto: str, id_intencion: int,
                   embedding: Optional[list] = None,
                   origen: str = "manual") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_dataset (texto, id_intencion, embedding, origen) "
            "VALUES (%s, %s, %s::vector, %s) RETURNING id",
            (texto, id_intencion, embedding, origen),
        )
        conn.commit()
        return cur.fetchone()[0]


def update_embedding(conn, record_id: int, embedding: list):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_dataset SET embedding = %s::vector WHERE id = %s",
            (embedding, record_id),
        )
        conn.commit()


def get_pendientes_embedding(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, texto FROM chatbot_dataset WHERE embedding IS NULL"
        )
        return cur.fetchall()


# ── chatbot_respuesta ──────────────────────────────────────────────────

def get_respuesta_by_intencion(conn, id_intencion: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, respuesta_texto, tipo, prioridad, veces_usada "
            "FROM chatbot_respuesta "
            "WHERE id_intencion = %s AND activa = TRUE "
            "ORDER BY prioridad DESC, veces_usada DESC LIMIT 1",
            (id_intencion,),
        )
        return cur.fetchone()


def get_all_respuestas(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT r.id, r.respuesta_texto, r.tipo, r.prioridad, "
            "r.activa, r.veces_usada, i.nombre as intencion "
            "FROM chatbot_respuesta r "
            "JOIN chatbot_intencion i ON r.id_intencion = i.id "
            "ORDER BY i.nombre, r.prioridad DESC"
        )
        return cur.fetchall()


def create_respuesta(conn, id_intencion: int, respuesta_texto: str,
                     tipo: str = "texto", prioridad: int = 1) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_respuesta (id_intencion, respuesta_texto, tipo, prioridad) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (id_intencion, respuesta_texto, tipo, prioridad),
        )
        conn.commit()
        return cur.fetchone()[0]


def increment_veces_usada(conn, id_respuesta: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_respuesta SET veces_usada = veces_usada + 1 WHERE id = %s",
            (id_respuesta,),
        )
        conn.commit()


# ── chatbot_conversacion ───────────────────────────────────────────────

def create_conversacion(conn, id_usuario: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_conversacion (id_usuario) VALUES (%s) RETURNING id",
            (id_usuario,),
        )
        conn.commit()
        return cur.fetchone()[0]


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
            "SELECT id, id_usuario, activa, iniciado_en, finalizado_en "
            "FROM chatbot_conversacion WHERE id_usuario = %s "
            "ORDER BY iniciado_en DESC LIMIT %s",
            (id_usuario, limit),
        )
        return cur.fetchall()


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
                    tipo_resolucion: str = "estatica",
                   id_intencion: Optional[int] = None,
                   confianza_ml: Optional[float] = None,
                   modelo_usado: Optional[str] = None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_mensaje "
            "(id_conversacion, rol, contenido, tipo_resolucion, "
            "id_intencion, confianza_ml, modelo_usado) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (id_conversacion, rol, contenido, tipo_resolucion,
             id_intencion, confianza_ml, modelo_usado),
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
            "FROM chatbot_pregunta_pendiente p "
            "WHERE p.id = %s",
            (id,),
        )
        return cur.fetchone()


def marcar_pendiente_resuelta(conn, id_pendiente: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_pregunta_pendiente "
            "SET resuelta = TRUE WHERE id = %s",
            (id_pendiente,),
        )
        conn.commit()


def resolver_pendiente(conn, id_pendiente: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_pregunta_pendiente "
            "SET resuelta = TRUE WHERE id = %s",
            (id_pendiente,),
        )
        conn.commit()


# ── documento_base (RAG) ───────────────────────────────────────────────

def get_documento_by_id(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, titulo, contenido, categoria, fuente, archivo_pdf, "
            "activo, creado_en, actualizado_en "
            "FROM documento_base WHERE id = %s",
            (id,),
        )
        return cur.fetchone()


def query_documentos(conn, query: str = "", categoria: str = "",
                     activo: Optional[bool] = None):
    with conn.cursor() as cur:
        sql = (
            "SELECT id, titulo, contenido, categoria, fuente, archivo_pdf, "
            "activo, creado_en, actualizado_en "
            "FROM documento_base WHERE 1=1"
        )
        params: list = []
        if query:
            sql += " AND (titulo ILIKE %s OR contenido ILIKE %s)"
            params.extend([f"%{query}%", f"%{query}%"])
        if categoria:
            sql += " AND categoria = %s"
            params.append(categoria)
        if activo is not None:
            sql += " AND activo = %s"
            params.append(activo)
        sql += " ORDER BY titulo"
        cur.execute(sql, params)
        return cur.fetchall()


def insert_documento(conn, titulo: str, contenido: str, embedding: list,
                     categoria: str, fuente: str = "", archivo_pdf: str = "") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO documento_base (titulo, contenido, embedding, categoria, fuente, archivo_pdf) "
            "VALUES (%s, %s, %s::vector, %s, %s, %s) RETURNING id",
            (titulo, contenido, embedding, categoria, fuente, archivo_pdf),
        )
        conn.commit()
        return cur.fetchone()[0]


def update_documento(conn, id: int, titulo: str, contenido: str, categoria: str,
                     fuente: str = "", archivo_pdf: str = ""):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE documento_base SET titulo = %s, contenido = %s, "
            "categoria = %s, fuente = %s, archivo_pdf = %s, actualizado_en = NOW() "
            "WHERE id = %s",
            (titulo, contenido, categoria, fuente, archivo_pdf, id),
        )
        conn.commit()


def update_embedding_documento(conn, id: int, embedding: list):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE documento_base SET embedding = %s::vector, actualizado_en = NOW() "
            "WHERE id = %s",
            (embedding, id),
        )
        conn.commit()


def soft_delete_documento(conn, id: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE documento_base SET activo = FALSE, actualizado_en = NOW() "
            "WHERE id = %s",
            (id,),
        )
        conn.commit()


def search_documentos(conn, embedding, categoria: Optional[str] = None,
                      limit: int = 3):
    with conn.cursor() as cur:
        if categoria:
            cur.execute(
                "SELECT id, titulo, contenido, categoria, fuente, "
                "1 - (embedding <=> %s::vector) as similarity "
                "FROM documento_base "
                "WHERE categoria = %s AND activo = TRUE AND embedding IS NOT NULL "
                "ORDER BY similarity DESC LIMIT %s",
                (embedding, categoria, limit),
            )
        else:
            cur.execute(
                "SELECT id, titulo, contenido, categoria, fuente, "
                "1 - (embedding <=> %s::vector) as similarity "
                "FROM documento_base "
                "WHERE activo = TRUE AND embedding IS NOT NULL "
                "ORDER BY similarity DESC LIMIT %s",
                (embedding, limit),
            )
        return cur.fetchall()


# ── chatbot_prediccion ─────────────────────────────────────────────────

def insert_prediccion(conn, texto_usuario: str, intencion_predicha: str,
                      confianza: float) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_prediccion (texto_usuario, intencion_predicha, confianza) "
            "VALUES (%s, %s, %s) RETURNING id",
            (texto_usuario, intencion_predicha, confianza),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_predicciones(conn, incorrectas: bool = False, limit: int = 100):
    with conn.cursor() as cur:
        if incorrectas:
            cur.execute(
                "SELECT id, texto_usuario, intencion_predicha, confianza, "
                "correcta, fecha "
                "FROM chatbot_prediccion WHERE correcta = FALSE "
                "ORDER BY fecha DESC LIMIT %s",
                (limit,),
            )
        else:
            cur.execute(
                "SELECT id, texto_usuario, intencion_predicha, confianza, "
                "correcta, fecha "
                "FROM chatbot_prediccion ORDER BY fecha DESC LIMIT %s",
                (limit,),
            )
        return cur.fetchall()


def marcar_prediccion_correcta(conn, id_prediccion: int, correcta: bool):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_prediccion SET correcta = %s WHERE id = %s",
            (correcta, id_prediccion),
        )
        conn.commit()


# ── entrenamiento_pendiente ────────────────────────────────────────────

def encolar_entrenamiento(conn, id_dataset: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO entrenamiento_pendiente (id_dataset) VALUES (%s) RETURNING id",
            (id_dataset,),
        )
        conn.commit()
        return cur.fetchone()[0]


def count_pendientes_entrenamiento(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM entrenamiento_pendiente WHERE procesado = FALSE"
        )
        return cur.fetchone()[0]


def get_pendientes_entrenamiento(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ep.id, ep.id_dataset, cd.texto, cd.id_intencion, "
            "ci.nombre as intencion, ep.fecha "
            "FROM entrenamiento_pendiente ep "
            "JOIN chatbot_dataset cd ON ep.id_dataset = cd.id "
            "JOIN chatbot_intencion ci ON cd.id_intencion = ci.id "
            "WHERE ep.procesado = FALSE ORDER BY ep.fecha"
        )
        return cur.fetchall()


def marcar_entrenamiento_procesado(conn, id_pendiente: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE entrenamiento_pendiente SET procesado = TRUE WHERE id = %s",
            (id_pendiente,),
        )
        conn.commit()


# ── modelo_ml ──────────────────────────────────────────────────────────

def crear_modelo(conn, nombre: str, version: str,
                 accuracy: float = 0.0, precision: float = 0.0,
                 recall: float = 0.0, f1_score: float = 0.0) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO modelo_ml (nombre, version, accuracy, precision, recall, f1_score) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (nombre, version, accuracy, precision, recall, f1_score),
        )
        conn.commit()
        return cur.fetchone()[0]


def get_modelo_activo(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, version, accuracy, precision, recall, f1_score, "
            "activo, fecha_entrenamiento "
            "FROM modelo_ml WHERE activo = TRUE LIMIT 1"
        )
        return cur.fetchone()


def set_modelo_activo(conn, id_modelo: int):
    with conn.cursor() as cur:
        cur.execute("UPDATE modelo_ml SET activo = FALSE WHERE activo = TRUE")
        cur.execute("UPDATE modelo_ml SET activo = TRUE WHERE id = %s", (id_modelo,))
        conn.commit()


def get_historial_modelos(conn, limit: int = 10):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, version, accuracy, precision, recall, f1_score, "
            "activo, fecha_entrenamiento "
            "FROM modelo_ml ORDER BY fecha_entrenamiento DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def update_modelo_metrics(conn, id_modelo: int,
                          accuracy: float, precision: float,
                          recall: float, f1_score: float):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE modelo_ml SET accuracy = %s, precision = %s, "
            "recall = %s, f1_score = %s WHERE id = %s",
            (accuracy, precision, recall, f1_score, id_modelo),
        )
        conn.commit()


# ── chatbot_training ───────────────────────────────────────────────────

def iniciar_training(conn, modelo_version: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chatbot_training (modelo_version, estado) "
            "VALUES (%s, 'en_progreso') RETURNING id",
            (modelo_version,),
        )
        conn.commit()
        return cur.fetchone()[0]


def completar_training(conn, id_training: int, ejemplos_usados: int,
                       accuracy: float, precision: float, recall: float,
                       f1_score: float, loss: float = 0.0, estado: str = "completado"):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_training SET estado = %s, ejemplos_usados = %s, "
            "accuracy = %s, precision = %s, recall = %s, f1_score = %s, "
            "loss = %s WHERE id = %s",
            (estado, ejemplos_usados, accuracy, precision, recall,
             f1_score, loss, id_training),
        )
        conn.commit()


def fail_training(conn, id_training: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE chatbot_training SET estado = 'fallido' "
            "WHERE id = %s",
            (id_training,),
        )
        conn.commit()


def get_training_history(conn, limit: int = 20):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, modelo_version, ejemplos_usados, accuracy, precision, "
            "recall, f1_score, loss, estado, fecha "
            "FROM chatbot_training ORDER BY fecha DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


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


def top_intenciones(conn, limit: int = 10):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT i.nombre, COUNT(m.id) as total "
            "FROM chatbot_mensaje m "
            "JOIN chatbot_intencion i ON i.id = m.id_intencion "
            "WHERE m.rol = 'bot' "
            "GROUP BY i.nombre "
            "ORDER BY total DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def resolucion_por_tipo(conn):
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

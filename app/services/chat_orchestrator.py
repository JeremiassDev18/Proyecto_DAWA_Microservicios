from app.db import queries
from app.ml.predictor import predict_with_confidence
from app.services.dispatcher import dispatch
from app.services.response_validator import validar_respuesta
from app.utils.logger import logger


def _resolve_conversation(conn, usuario_id: int,
                          id_conversacion: int | None,
                          nombre_cliente: str = "") -> int:
    if id_conversacion:
        conv = queries.get_conversacion(conn, id_conversacion)
        if not conv:
            conv_id = queries.create_conversacion(conn, usuario_id, nombre_cliente)
            return conv_id
        if nombre_cliente:
            queries.update_conversacion_nombre(conn, id_conversacion, nombre_cliente)
        return id_conversacion

    convs = queries.get_conversaciones_by_usuario(conn, usuario_id, limit=1)
    if convs and convs[0][2]:
        conv_id = convs[0][0]
        if nombre_cliente:
            queries.update_conversacion_nombre(conn, conv_id, nombre_cliente)
        return conv_id

    return queries.create_conversacion(conn, usuario_id, nombre_cliente)


def _classify(mensaje: str) -> tuple[str, float]:
    try:
        return predict_with_confidence(mensaje)
    except FileNotFoundError:
        logger.warning("Modelo no encontrado, usando fallback SIN_INTENCION")
        return "SIN_INTENCION", 0.0
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return "SIN_INTENCION", 0.0


def _get_intencion_id(conn, intent: str):
    row = queries.get_intencion_by_nombre(conn, intent)
    return row[0] if row else None


def process_message(conn, usuario_id: int, mensaje: str,
                    id_conversacion: int | None = None,
                    nombre_cliente: str = "") -> dict:
    conv_id = _resolve_conversation(conn, usuario_id, id_conversacion, nombre_cliente)
    queries.insert_mensaje(conn, conv_id, "usuario", mensaje)

    intent, confidence = _classify(mensaje)
    queries.insert_prediccion(conn, mensaje, intent, confidence)
    result = dispatch(conn, usuario_id, mensaje, intent, confidence)

    valido, motivo = validar_respuesta(result["respuesta"], mensaje, intent)
    if not valido:
        logger.warning(f"Respuesta bloqueada por validación: {motivo}")
        queries.insert_pendiente(conn, mensaje)
        result = {
            "respuesta": ("Lo siento, no pude generar una respuesta adecuada. "
                          "Un administrador revisará tu consulta."),
            "tipo_resolucion": "sin_respuesta",
        }

    intencion_id = _get_intencion_id(conn, intent)
    bot_msg_id = queries.insert_mensaje(
        conn, conv_id, "bot", result["respuesta"], result["tipo_resolucion"],
        id_intencion=intencion_id, confianza_ml=confidence, modelo_usado="setfit",
    )

    return {
        "respuesta": result["respuesta"],
        "intencion": intent,
        "confianza": confidence,
        "tipo_resolucion": result["tipo_resolucion"],
        "id_conversacion": conv_id,
        "id_mensaje": bot_msg_id,
    }

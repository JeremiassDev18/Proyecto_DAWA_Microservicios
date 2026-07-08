from app.core.config import settings
from app.db import queries

from app.ml.vectorizer import generate_embedding
from app.services.handlers.base import IntentHandler
from app.utils.logger import logger


ESCALATION_ENABLED = settings.ESCALATION_ENABLED
CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD


def _save_auto_dataset(conn, mensaje: str, intent: str):
    try:
        id_intencion = queries.get_or_create_intencion(conn, intent,
                                                        f"Auto-creada desde {intent}")
        embedding = generate_embedding(mensaje)
        ds_id = queries.insert_dataset(conn, mensaje, id_intencion,
                                        embedding, origen="auto")
        queries.validate_dataset(conn, ds_id)
    except Exception as e:
        logger.warning(f"No se pudo auto-guardar dataset: {e}")


class FallbackHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        escalation_reason = None
        if ESCALATION_ENABLED and confidence < CONFIDENCE_THRESHOLD:
            escalation_reason = (f"Confianza baja ({confidence:.2f} < "
                                 f"{CONFIDENCE_THRESHOLD})")
        else:
            escalation_reason = "Sin coincidencia en búsqueda híbrida ni RAG"

        queries.insert_pendiente(conn, mensaje)
        _save_auto_dataset(conn, mensaje, intent)

        response_text = (
            f"Lo siento, no pude resolver tu consulta de forma automática "
            f"(motivo: {escalation_reason}). "
            "Un administrador revisará tu pregunta y te responderá pronto."
        )
        logger.info(f"Escalado: motivo={escalation_reason}")

        return {
            "respuesta": response_text,
            "tipo_resolucion": "sin_respuesta",
            "escalation_reason": escalation_reason,
        }

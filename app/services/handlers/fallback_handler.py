from app.core.config import settings
from app.db import queries
from app.services.handlers.base import IntentHandler
from app.utils.logger import logger


ESCALATION_ENABLED = settings.ESCALATION_ENABLED
CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD


class FallbackHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float) -> bool:
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

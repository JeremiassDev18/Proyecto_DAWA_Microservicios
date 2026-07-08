from app.core.config import settings
from app.db import queries
from app.services.handlers.base import IntentHandler

FAQ_INTENTS = {
    "CONSULTAR_FAQ",
    "CONSULTAR_REGLAMENTO",
    "CONSULTAR_ASIGNATURA",
    "HORARIO_TUTORIAS",
}


class FAQHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        return (intent in FAQ_INTENTS
                and confidence >= settings.CONFIDENCE_THRESHOLD
                and intent != "SIN_INTENCION")

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        intencion_row = queries.get_intencion_by_nombre(conn, intent)
        if not intencion_row:
            return None

        respuesta = queries.get_respuesta_by_intencion(conn, intencion_row[0])
        if not respuesta:
            return None

        queries.increment_veces_usada(conn, respuesta[0])
        return {
            "respuesta": respuesta[1],
            "tipo_resolucion": "estatica",
        }

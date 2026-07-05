from app.services.handlers.base import IntentHandler
from app.services.search_service import hybrid_search
from app.utils.logger import logger


class HybridHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float) -> bool:
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        response_text = hybrid_search(conn, mensaje)
        if not response_text:
            return None

        logger.info(f"Hybrid search respondió para intent={intent}, confianza={confidence:.4f}")
        return {
            "respuesta": response_text,
            "tipo_resolucion": "hibrida",
        }

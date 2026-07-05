from app.services.handlers.base import IntentHandler
from app.services.rag_service import respond_with_documents
from app.utils.logger import logger


class RAGHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float) -> bool:
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        context = respond_with_documents(conn, mensaje)
        if not context:
            return None

        logger.info(f"RAG respondió para intent={intent}, confianza={confidence:.4f}")
        return {
            "respuesta": context,
            "tipo_resolucion": "dinamica",
        }

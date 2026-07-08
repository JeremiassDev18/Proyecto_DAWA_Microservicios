from app.core.config import settings
from app.services.handlers.base import IntentHandler
from app.services.handlers.profile_handler import PROFILE_INTENTS
from app.services.handlers.tutorias_handler import TUTORIA_INTENTS
from app.services.handlers.docente_handler import DOCENTE_INTENTS
from app.services.handlers.faq_handler import FAQ_INTENTS
from app.services.rag_service import search_documents, build_context
from app.utils.logger import logger

NON_DOCUMENT_INTENTS = PROFILE_INTENTS | TUTORIA_INTENTS | DOCENTE_INTENTS | FAQ_INTENTS | {"SALUDO", "SIN_INTENCION"}


class RAGFirstHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        if intent in NON_DOCUMENT_INTENTS:
            return False
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        docs = search_documents(conn, mensaje, limit=1)
        if not docs:
            return None

        similarity = float(docs[0][5])
        if similarity < settings.RAG_HIGH_CONFIDENCE:
            return None

        context = build_context(docs)
        logger.info(f"RAGFirst respondió directamente (sim={similarity:.3f})")
        return {
            "respuesta": context,
            "tipo_resolucion": "dinamica",
        }

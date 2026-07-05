from app.services.handlers.rag_first_handler import RAGFirstHandler
from app.services.handlers.external_handler import ExternalHandler
from app.services.handlers.faq_handler import FAQHandler
from app.services.handlers.hybrid_handler import HybridHandler
from app.services.handlers.rag_handler import RAGHandler
from app.services.handlers.fallback_handler import FallbackHandler

HANDLER_CHAIN = [
    ExternalHandler(),
    FAQHandler(),
    HybridHandler(),
    RAGHandler(),
    FallbackHandler(),
]

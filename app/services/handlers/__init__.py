from app.services.handlers.greeting_handler import GreetingHandler
from app.services.handlers.institutional_handler import InstitutionalHandler
from app.services.handlers.profile_handler import ProfileHandler
from app.services.handlers.tutorias_handler import TutoriasHandler
from app.services.handlers.docente_handler import DocenteHandler
from app.services.handlers.faq_handler import FAQHandler
from app.services.handlers.hybrid_handler import HybridHandler
from app.services.handlers.rag_handler import RAGHandler
from app.services.handlers.rag_first_handler import RAGFirstHandler
from app.services.handlers.fallback_handler import FallbackHandler

HANDLER_CHAIN = [
    GreetingHandler(),
    InstitutionalHandler(),
    ProfileHandler(),
    TutoriasHandler(),
    DocenteHandler(),
    FAQHandler(),
    HybridHandler(),
    RAGHandler(),
    RAGFirstHandler(),
    FallbackHandler(),
]

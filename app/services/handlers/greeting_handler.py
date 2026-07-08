import re

from app.db import queries

from app.ml.vectorizer import generate_embedding
from app.services.handlers.base import IntentHandler
from app.utils.logger import logger

GREETING_REGEX = re.compile(
    r'^(hola+|buen[oa]s+\b|buen[oa]s+\s+(d[ií]as|tardes|noches)|'
    r'saludos|qu[eé]\s*tal|hey|hello|hi'
    r')[\s!?.]*$',
    re.IGNORECASE
)

PHRASE_GREETINGS = [
    "buenos dias", "buen dia", "buenas tardes", "buenas noches",
    "buenas", "bueno", "hola", "saludos", "que tal", "hello", "hi", "hey",
]


def _es_saludo_puro(mensaje: str) -> bool:
    texto = mensaje.strip().lower()
    if GREETING_REGEX.match(texto):
        return True
    for phrase in PHRASE_GREETINGS:
        if texto == phrase:
            return True
    return False


class GreetingHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        if not _es_saludo_puro(mensaje):
            return None

        id_intencion = queries.get_or_create_intencion(conn, "SALUDO",
                                                        "Saludos y presentaciones")

        try:
            embedding = generate_embedding(mensaje)
            ds_id = queries.insert_dataset(conn, mensaje, id_intencion,
                                            embedding, origen="auto")
            queries.validate_dataset(conn, ds_id)
        except Exception as e:
            logger.warning(f"GreetingHandler: no se pudo guardar dataset: {e}")

        response_text = (
            "Hola! Soy el asistente virtual de tutorias. "
            "Puedo ayudarte a:\n"
            "* Solicitar una tutoria\n"
            "* Consultar tus tutorias\n"
            "* Buscar informacion sobre docentes\n\n"
            "En que puedo ayudarte?"
        )
        logger.info("GreetingHandler respondio con saludo")
        return {
            "respuesta": response_text,
            "tipo_resolucion": "saludo",
        }

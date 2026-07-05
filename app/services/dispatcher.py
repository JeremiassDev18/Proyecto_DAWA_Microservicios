from app.services.handlers import HANDLER_CHAIN
from app.utils.logger import logger


def dispatch(conn, usuario_id: int, mensaje: str,
             intent: str, confidence: float) -> dict:
    for handler in HANDLER_CHAIN:
        if not handler.can_handle(intent, confidence):
            logger.info(f"Dispatcher: {handler.__class__.__name__} "
                        f"-> skip (can_handle=False para {intent})")
            continue

        result = handler.handle(conn, usuario_id, mensaje, intent, confidence)
        if result is not None:
            logger.info(f"Dispatcher: handler={handler.__class__.__name__} "
                        f"-> responde (intent={intent}, "
                        f"confidence={confidence:.4f}, "
                        f"tipo={result.get('tipo_resolucion')})")
            return result
        logger.info(f"Dispatcher: {handler.__class__.__name__} "
                    f"-> pasó (no produjo respuesta para {intent})")

    logger.warning(f"Dispatcher: ningún handler respondió para intent={intent}")
    return {
        "respuesta": ("Lo siento, no pude resolver tu consulta. "
                      "Un administrador revisará tu pregunta."),
        "tipo_resolucion": "sin_respuesta",
    }

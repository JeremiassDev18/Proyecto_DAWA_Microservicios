from app.core.config import settings
from app.services.handlers.base import IntentHandler
from app.services.microservice_client import INTENT_SERVICE_MAP


EXTERNAL_INTENTS_STATIC = {
    "CANCELAR_SOLICITUD", "CAMBIAR_HORARIO",
    "ESCALAR_DOCENTE", "RESUMEN_SOLICITUD",
}

EXTERNAL_INTENTS_DYNAMIC = {
    "CREAR_SOLICITUD", "SOLICITAR_TUTORIA",
    "BUSCAR_DOCENTE", "CONSULTAR_MIS_TUTORIAS",
    "CONTACTAR_DOCENTE", "DISPONIBILIDAD_DOCENTE",
}

ALL_EXTERNAL = EXTERNAL_INTENTS_STATIC | EXTERNAL_INTENTS_DYNAMIC


class ExternalHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float) -> bool:
        if intent in EXTERNAL_INTENTS_STATIC:
            return True
        if intent in EXTERNAL_INTENTS_DYNAMIC:
            return confidence >= settings.CONFIDENCE_THRESHOLD
        return False

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        tipo_resolucion = "logica"

        if intent == "CANCELAR_SOLICITUD":
            return {
                "respuesta": "Tu solicitud ha sido cancelada.",
                "tipo_resolucion": tipo_resolucion,
            }
        if intent == "CAMBIAR_HORARIO":
            return {
                "respuesta": "El horario de tu solicitud ha sido actualizado.",
                "tipo_resolucion": tipo_resolucion,
            }
        if intent == "ESCALAR_DOCENTE":
            return {
                "respuesta": "Tu solicitud ha sido escalada a un docente superior.",
                "tipo_resolucion": tipo_resolucion,
            }
        if intent == "RESUMEN_SOLICITUD":
            return {
                "respuesta": "Aquí tienes el resumen de tus tutorías...",
                "tipo_resolucion": tipo_resolucion,
            }

        handler = INTENT_SERVICE_MAP.get(intent)
        if not handler:
            return None

        if intent in ("CREAR_SOLICITUD", "SOLICITAR_TUTORIA"):
            result = handler(usuario_id, mensaje)
            return {
                "respuesta": (f"Tu solicitud de tutoría ha sido registrada con código "
                              f"{result['codigo']}. Un docente te contactará pronto."),
                "tipo_resolucion": tipo_resolucion,
            }

        if intent == "CONSULTAR_MIS_TUTORIAS":
            result = handler(usuario_id, mensaje)
            if not result:
                return {
                    "respuesta": "No tienes tutorías registradas.",
                    "tipo_resolucion": tipo_resolucion,
                }
            lines = [f"Tienes {len(result)} tutoría(s) registrada(s):"]
            for s in result:
                lines.append(f"  - Código: {s['codigo']} | Estado: {s['estado']}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo_resolucion,
            }

        if intent in ("BUSCAR_DOCENTE", "CONTACTAR_DOCENTE", "DISPONIBILIDAD_DOCENTE"):
            result = handler(usuario_id, mensaje)
            if not result:
                return {
                    "respuesta": "No encontré docentes con ese criterio.",
                    "tipo_resolucion": tipo_resolucion,
                }
            lines = [f"Docentes encontrados ({len(result)}):"]
            for d in result:
                disp = "Disponible" if d["disponible"] else "No disponible"
                lines.append(f"  - {d['nombre']} ({d['asignatura']}) - {disp}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo_resolucion,
            }

        return None

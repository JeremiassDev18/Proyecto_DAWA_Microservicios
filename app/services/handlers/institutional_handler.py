import re
from app.services.handlers.base import IntentHandler
from app.services.microservice_client import get_admin_client

_INSTITUCIONAL_QUERY = re.compile(
    r'\b(?:carreras|facultades|lista\s+de\s+(?:carreras|facultades)|'
    r'qu[eé]\s+(?:carreras|facultades)\s+(?:existen|hay|tiene|ofrece)|'
    r'cu[aá]les\s+son\s+las\s+(?:carreras|facultades)|'
    r'cu[aá]ntas\s+(?:carreras|facultades)\s+(?:hay|existen)|'
    r'(?:carreras|facultades)\s+(?:disponibles|que\s+ofrece|de\s+la\s+universidad)|'
    r'd[ií]me\s+las\s+(?:carreras|facultades)|'
    r'(?:mu[eé]strame|ense[nñ]ame)\s+las\s+(?:carreras|facultades)|'
    r'qu[eé]\s+(?:carreras|facultades)\s+(?:puedo\s+estudiar|hay\s+disponibles))\b',
    re.I,
)

_POSESIVO_INST = re.compile(
    r'\b(?:mi(?:\s|$)|mis(?:\s|$)|mí(?:\s|$)|pertenezco|estudio(?:\s|$)|cursando|'
    r'tengo(?:\s|$)|perfil)\b',
    re.I,
)


class InstitutionalHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        return True

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        msg_lower = mensaje.lower()

        if not _INSTITUCIONAL_QUERY.search(msg_lower):
            return None
        if _POSESIVO_INST.search(msg_lower):
            return None

        admin = get_admin_client()

        if "carreras" in msg_lower or "carrera" in msg_lower:
            carreras = admin.get_carreras()
            if carreras:
                lines = [f"Carreras disponibles ({len(carreras)}):"]
                for c in carreras:
                    parts = [c["nombre"]]
                    if c.get("modalidad"):
                        parts.append(c["modalidad"])
                    lines.append(f"  - {', '.join(parts)}")
                return {"respuesta": "\n".join(lines), "tipo_resolucion": "logica"}

        if "facultades" in msg_lower or "facultad" in msg_lower:
            facultades = admin.get_facultades()
            if facultades:
                lines = [f"Facultades ({len(facultades)}):"]
                for f in facultades:
                    lines.append(f"  - {f['nombre']}")
                return {"respuesta": "\n".join(lines), "tipo_resolucion": "logica"}

        return None

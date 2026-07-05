import re
from typing import Optional

SENSITIVE_PATTERNS = [
    r"\b\d{8,}\b",                        # números >= 8 dígitos (DNI, teléfono)
    r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b",     # emails
    r"\b(?:contraseña|password|clave)\s*\S+",  # credenciales
]

SCOPE_KEYWORDS = [
    "tutoría", "tutoria", "tutorias", "tutorías",
    "asignatura", "horario", "docente", "profesor",
    "matrícula", "matricula", "examen", "nota",
    "reglamento", "cancelación", "cancelacion",
    "solicitud", "faq", "reglamento",
]


def validar_respuesta(texto: str, mensaje_usuario: str) -> tuple[bool, Optional[str]]:
    if not texto:
        return True, None

    for pattern in SENSITIVE_PATTERNS:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return False, f"La respuesta contiene información sensible: '{match.group()[:30]}'"

    usuario_has_scope = any(kw in mensaje_usuario.lower() for kw in SCOPE_KEYWORDS)
    respuesta_has_scope = any(kw in texto.lower() for kw in SCOPE_KEYWORDS)

    if not usuario_has_scope and not respuesta_has_scope:
        return False, "La respuesta no está relacionada con el alcance institucional"

    return True, None

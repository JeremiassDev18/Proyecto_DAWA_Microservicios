import re
from app.core.config import settings
from app.core.context import get_estudiante_id
from app.services.handlers.base import IntentHandler
from app.services.microservice_client import get_admin_client

_PROFILE_KEYWORDS = re.compile(
    r'\b(?:'
    r'mi\s+(?:perfil|cuenta|informaci[oó]n|carrera|facultad'
    r'|docente|profesor|tutor|maestro'
    r'|materia|asignatura|paralelo)'
    r'|mis\s+(?:docentes|profesores|tutores|maestros|materias|asignaturas|paralelos)'
    r'|m[íi]os|m[ií]as|perfil|pertenezco'
    r'|qu[eé]\s+(?:materias|asignaturas)\s+(?:tengo|veo|estudio|estoy cursando|estoy viendo)'
    r'|cu[aá]les\s+son\s+mis\s+(?:docentes|profesores|materias|asignaturas)'
    r'|(?:docentes|profesores|materias|asignaturas)\s+(?:que\s+tengo|actuales|asignad[oa]s)'
    r'|a\s+qui[ée]n\s+(?:tengo|le\s+tengo)\s+(?:como|de)\s+(?:docente|profesor|tutor)'
    r'|qu[eé]n\s+(?:me\s+)?(?:dicta|da|imparte|enseña)'
    r'|quiero\s+(?:ver|conocer|saber)\s+(?:mis|a\s+mis)\s+(?:docentes|profesores|materias|asignaturas)'
    r'|mu[eé]strame\s+(?:mis|los|las)\s+(?:docentes|profesores|materias|asignaturas)'
    r'|d[ií]me\s+(?:mis|los|las)\s+(?:docentes|profesores|materias|asignaturas)'
    r'|tengo\s+(?:docentes?|profesores?|materias|asignaturas)'
    r'|ense[nñ]ame\s+(?:mis|los)\s+(?:docentes|profesores|materias|asignaturas)'
    r'|dame\s+(?:la\s+)?lista\s+de\s+(?:mis|los)\s+(?:docentes|profesores|materias)'
    r'|puedes\s+(?:decirme|mostrarme|enseñarme)\s+(?:mis|los)\s+(?:docentes|profesores|materias|asignaturas)'
    r'|necesito\s+(?:saber|ver|conocer)\s+(?:mis|los)\s+(?:docentes|profesores|materias|asignaturas)'
    r')\b',
    re.I,
)

PROFILE_INTENTS = {"CONSULTAR_PERFIL"}


class ProfileHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        if mensaje and _PROFILE_KEYWORDS.search(mensaje):
            return True
        return (intent in PROFILE_INTENTS
                and confidence >= settings.CONFIDENCE_THRESHOLD)

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        tipo = "logica"
        estudiante_id = get_estudiante_id() or usuario_id
        admin = get_admin_client()

        estudiante = admin.get_estudiante(estudiante_id)
        if not estudiante:
            return {
                "respuesta": "No encontré información de tu perfil de estudiante.",
                "tipo_resolucion": tipo,
            }

        nombres = estudiante.get("nombres", "")
        apellidos = estudiante.get("apellidos", "")
        correo = estudiante.get("correo", "")
        matricula = estudiante.get("matricula", "")
        carrera_id = estudiante.get("carrera_id")
        estado_ac = estudiante.get("estado_academico", "")

        carrera_nombre = ""
        if carrera_id:
            carrera = admin.get_carrera(carrera_id)
            if carrera:
                carrera_nombre = carrera.get("nombre", "")

        parts = [f"**{nombres} {apellidos}**"]
        if matricula:
            parts.append(f"  - Matrícula: {matricula}")
        if correo:
            parts.append(f"  - Correo: {correo}")
        if carrera_nombre:
            parts.append(f"  - Carrera: {carrera_nombre}")
        if estado_ac:
            parts.append(f"  - Estado académico: {estado_ac}")

        mis_docentes = admin.get_estudiante_docentes(estudiante_id)
        if mis_docentes:
            parts.append("")
            parts.append("**Tus docentes actuales:**")
            for d in mis_docentes:
                full_name = f"{d['nombres']} {d['apellidos']}".strip()
                asigs = ", ".join(a["nombre"] for a in d.get("asignaturas", []))
                parts.append(f"  - {full_name} ({asigs})")

        mis_materias = admin.get_materias_estudiante(estudiante_id)
        if mis_materias:
            parts.append("")
            parts.append("**Tus materias inscritas:**")
            for m in mis_materias:
                parts.append(f"  - {m['nombre']} ({m.get('nivel', '')}, {m['creditos']} créd.)")

        return {
            "respuesta": "\n".join(parts) if parts else "No hay datos de perfil.",
            "tipo_resolucion": tipo,
        }

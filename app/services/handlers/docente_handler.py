import re
from app.core.config import settings
from app.core.context import get_estudiante_id
from app.services.handlers.base import IntentHandler
from app.services.microservice_client import get_admin_client

_DOCENTE_KEYWORDS = re.compile(
    r'\b(?:'
    r'docentes?|profesores?|profes?|maestros?|tutores?|'
    r'qu[ié]n\s+(?:dicta|da|imparte|enseña)|'
    r'qui[ée]n\s+(?:es|ser[aá])\s+(?:el|la|mi)\s+(?:docente|profesor|tutor|maestro)|'
    r'buscar\s+(?:docente|profesor|tutor|maestro)|'
    r'b[uú]scame\s+(?:un\s+)?(?:docente|profesor|tutor|maestro)|'
    r'contactar\s+(?:docente|profesor|tutor|maestro)|'
    r'disponibilidad\s+(?:docente|profesor|tutor|maestro)|'
    r'horario\s+(?:docente|profesor|tutor|maestro)'
    r')\b',
    re.I,
)

_POSESIVO = re.compile(
    r'\b(mis|míos|mías|mis\s*(docentes|profesores|profes|maestros|maestras|tutores|materias|asignaturas)'
    r'|qué\s*(docentes|profesores|profes).*tengo'
    r'|qui[ée]n\s*(me\s*(da|imparte|enseña|dicta)|imparte)'
    r'|materias.*tengo'
    r'|mu[eé]strame\s+(los|las|mis)\s*(docentes|profesores|materias|asignaturas)'
    r'|d[ií]me\s+(los|las|mis)\s*(docentes|profesores|materias|asignaturas)'
    r'|qu[eé]\s*(materias|asignaturas)\s*(tengo|veo|estudio|estoy cursando|estoy viendo)'
    r'|cu[aá]les\s+son\s+mis\s*(docentes|profesores|materias|asignaturas)'
    r'|(docentes|profesores|materias|asignaturas)\s+(que\s+tengo|actuales|asignad[oa]s)'
    r'|los\s*(docentes|profesores|tutores)\s*(que\s*(tengo|me\s*(dan|dictan|imparten)))'
    r'|ense[nñ]ame\s+(mis|los)\s*(docentes|profesores|materias|asignaturas)'
    r'|quiero\s+(ver|conocer|saber)\s+(mis|a\s+mis)\s*(docentes|profesores|maestros|tutores|materias|asignaturas)'
    r'|dame\s+(la\s+)?lista\s+de\s+(mis|los)\s*(docentes|profesores|materias)'
    r'|puedes\s+(decirme|mostrarme|enseñarme)\s+(mis|los)\s*(docentes|profesores|materias|asignaturas)'
    r'|necesito\s+(saber|ver|conocer)\s+(mis|los)\s*(docentes|profesores|materias|asignaturas)'
    r'|qu[eé]\s*(docentes|profesores)\s*(tengo|me\s+corresponden|me\s+asignaron)'
    r'|a\s+qui[ée]n\s+(tengo|le\s+tengo)\s*(como|de)\s+(docente|profesor|tutor)'
    r')\b',
    re.I,
)

DOCENTE_INTENTS = {"BUSCAR_DOCENTE", "CONTACTAR_DOCENTE", "DISPONIBILIDAD_DOCENTE"}


_SEARCH_PATTERNS = [
    re.compile(r'\A(?:buscar|b[uú]scame|encuentra|localiza|ubica|necesito|h[aá]blame|quiero\s+(?:saber|ver|conocer|localizar|contactar|encontrar|hablar\s+con))\s+(?:al?\s+|a\s+)?(?:docente|profesor[a]?|maestro[a]?|tutor[a]?)?\s+(?:de\s+|del\s+)?', re.I),
    re.compile(r'\A(?:d[ií]me|mu[eé]strame|ense[nñ]ame|puedes\s+(?:decirme|mostrarme|enseñarme|darme))\s+(?:me|le|los|las|lo|la|le)?\s*(?:el\s+|la\s+|los\s+|las\s+|al?\s+|del\s+|de\s+)?(?:docente|profesor[a]?|maestro[a]?|tutor[a]?|coordinador[a]?|director[a]?|informaci[oó]n|datos|correo|tel[eé]fono|n[uú]mero|contacto|oficina)?\s+(?:de\s+|del\s+|que\s+)?', re.I),
    re.compile(r'\A(?:qu[eé]\s+(?:docente|profesor[a]?|maestro[a]?|tutor[a]?)\s+(?:da|dicta|imparte|enseña)\s+)', re.I),
    re.compile(r'\A(?:qu[ieé]n\s+(?:es\s+)?(?:el\s+|la\s+)?(?:docente|profesor[a]?|tutor[a]?|maestro[a]?|coordinador[a]?|director[a]?)?\s*(?:que\s+)?(?:da|dicta|imparte|enseña)\s+)', re.I),
    re.compile(r'\A(?:qu[ieé]n\s+(?:me\s+)?(?:dicta|da|imparte|enseña)\s+)', re.I),
    re.compile(r'\A(?:el\s+|la\s+|los\s+|las\s+)?(?:docente|profesor[a]?|tutor[a]?|maestro[a]?)\s+(?:de\s+|del\s+)?', re.I),
]


def _extraer_nombre_busqueda(mensaje: str) -> str:
    q = mensaje.strip()
    for pattern in _SEARCH_PATTERNS:
        m = pattern.match(q)
        if m:
            q = q[m.end():].strip()
            break
    q = q.strip('?.!,;:\'"¿¡ ')
    return q if q and len(q) >= 2 else mensaje


class DocenteHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        if mensaje and _DOCENTE_KEYWORDS.search(mensaje):
            msg_lower = mensaje.lower()
            if not _POSESIVO.search(msg_lower):
                return True
        return (intent in DOCENTE_INTENTS
                and confidence >= settings.CONFIDENCE_THRESHOLD)

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        tipo = "logica"
        estudiante_id = get_estudiante_id() or usuario_id
        admin = get_admin_client()

        mis_docentes = admin.get_estudiante_docentes(estudiante_id)
        if mis_docentes:
            lines = [f"Tus docentes ({len(mis_docentes)}):"]
            for d in mis_docentes:
                full_name = f"{d['nombres']} {d['apellidos']}".strip()
                esp = f" ({d['especialidad']})" if d.get("especialidad") else ""
                asigs = ", ".join(a["nombre"] for a in d.get("asignaturas", []))
                line = f"  - {full_name}{esp}"
                if asigs:
                    line += f"\n    Materias: {asigs}"
                horarios = d.get("horarios", [])
                if horarios:
                    disp = "; ".join(
                        f"{h['dia']} {h['hora_inicio']}-{h['hora_fin']}"
                        for h in horarios[:3]
                    )
                    line += f"\n    Horario: {disp}"
                lines.append(line)
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo,
            }

        search_term = _extraer_nombre_busqueda(mensaje)
        global_result = admin.buscar_docentes(search_term)

        if not global_result:
            todas_asignaturas = admin.get_asignaturas()
            materia_coincidente = next(
                (a for a in todas_asignaturas
                 if search_term.lower() in a["nombre"].lower()),
                None
            )
            if materia_coincidente:
                por_materia = admin.buscar_docentes_por_materia(materia_coincidente["nombre"])
                if por_materia:
                    lines = [f"Docentes que dictan **{materia_coincidente['nombre']}** ({len(por_materia)}):"]
                    for d in por_materia:
                        full = f"{d['nombres']} {d['apellidos']}".strip()
                        esp = f" ({d['especialidad']})" if d.get("especialidad") else ""
                        lines.append(f"  - {full}{esp}")
                    return {"respuesta": "\n".join(lines), "tipo_resolucion": tipo}
            return {
                "respuesta": "No encontré docentes con ese criterio.",
                "tipo_resolucion": tipo,
            }

        ids_mis_docentes: set[int] = set()
        try:
            for d in mis_docentes or []:
                ids_mis_docentes.add(d["id"])
        except Exception:
            pass

        lines = [f"Docentes encontrados ({len(global_result)}):"]
        for d in global_result:
            docente_id = d.get("id")
            full_name = f"{d.get('nombres','')} {d.get('apellidos','')}".strip()
            esp = d.get("especialidad", "")
            line = f"  - {full_name}"
            if esp:
                line += f" ({esp})"

            if docente_id in ids_mis_docentes:
                line += " — ✅ Es uno de tus docentes actuales"
            elif ids_mis_docentes:
                line += " — ℹ️ No imparte clases en tus paralelos"

            disp_info = admin.disponibilidad_docente(docente_id) if docente_id else None
            if disp_info and isinstance(disp_info, dict):
                horarios = disp_info.get("horarios_disponibles") or disp_info.get("horarios") or disp_info.get("disponibilidad", [])
                if horarios:
                    disp_str = "; ".join(
                        f"{h.get('dia','')} {h.get('hora_inicio','')}-{h.get('hora_fin','')}"
                        for h in horarios[:3]
                    )
                    line += f"\n    Disponible: {disp_str}"
            lines.append(line)

        return {
            "respuesta": "\n".join(lines),
            "tipo_resolucion": tipo,
        }

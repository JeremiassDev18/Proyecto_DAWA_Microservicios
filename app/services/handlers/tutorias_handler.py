import re
from app.core.config import settings
from app.core.context import get_estudiante_id
from app.services.handlers.base import IntentHandler
from app.services.microservice_client import get_admin_client, get_tutorias_client, get_tutorias_rest_client

_SOLICITUD_KEYWORDS = re.compile(
    r'\b(solicitar|solicita|registrar|registra|agendar|inscribirme|pedir|apartar|reservar|'
    r'tomar\s+tutor[ií]as?|'
    r'necesito\s+(?:una?\s+)?tutor[ií]a|'
    r'quiero\s+(?:una?\s+)?tutor[ií]a|'
    r'crear\s+(?:mi\s+)?solicitud|'
    r'inscribirme\s+en\s+tutor[ií]as|'
    r'apartar\s+(?:una\s+)?tutor[ií]a)\b',
    re.I,
)

_TUTORIA_KEYWORDS = re.compile(
    r'\b(tutor[ií]a|tutor[ií]as|solicitud|solicitudes|'
    r'cancelar|cancelaci[oó]n|pendientes|'
    r'resumen|bit[aá]cora|historial|'
    r'confirmar|agendar|reprogramar|'
    r'reporte|reportes)\b',
    re.I,
)

_MATERIA_EXTRACT = re.compile(
    r'(?:tutor[ií]a\s+(?:de|en|para)\s+|'
    r'ayuda\s+(?:con|en|de|para)\s+|'
    r'necesito\s+(?:un\s+)?(?:tutor|profesor|docente|apoyo|refuerzo|clases)\s+(?:de|en|para)\s+|'
    r'quiero\s+(?:un\s+)?(?:tutor|profesor|docente)\s+(?:de|en|para)\s+|'
    r'reforzar\s+|repasar\s+|nivelarme\s+(?:en|de|con)\s+|'
    r'materia\s+(?:de|en)\s+|asignatura\s+(?:de|en)\s+)'
    r'([a-záéíóúñA-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,40}?)(?:\s+por\s+|\s+para\s+|$|\.)',
    re.I,
)

_TRANSLIT = str.maketrans('áéíóúñÁÉÍÓÚÑ', 'aeiounAEIOUN')

TUTORIA_INTENTS = {
    "CREAR_SOLICITUD", "SOLICITAR_TUTORIA",
    "CONSULTAR_MIS_TUTORIAS", "CANCELAR_SOLICITUD",
    "CAMBIAR_HORARIO", "ESCALAR_DOCENTE", "RESUMEN_SOLICITUD",
    "REPORTE_DOCENTE", "REPORTE_ESTUDIANTES", "REPORTE_TEMAS",
}


def _extraer_materia(mensaje: str) -> str | None:
    m = _MATERIA_EXTRACT.search(mensaje)
    if m:
        materia = m.group(1).strip().rstrip('.,;:!?¿¡ ')
        if materia and len(materia) >= 3:
            return materia
    return None


def _materia_coincide(busqueda: str, materias: list[dict]) -> dict | None:
    b = busqueda.lower().translate(_TRANSLIT).strip()
    # coincidencia exacta o subcadena
    for m in materias:
        n = m.get("nombre", "").lower().translate(_TRANSLIT)
        if b in n or n in b:
            return m
    # coincidencia por palabras significativas
    palabras_busqueda = [p for p in b.split() if len(p) >= 4]
    for m in materias:
        n = m.get("nombre", "").lower().translate(_TRANSLIT)
        if any(p in n for p in palabras_busqueda):
            return m
    return None


def _extraer_id(mensaje: str) -> int | None:
    match = re.search(r'\b(\d+)\b', mensaje)
    if match:
        return int(match.group(1))
    return None


class TutoriasHandler(IntentHandler):
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        # Intenciones directas de tutoría siempre van aquí
        if intent in ("CREAR_SOLICITUD", "SOLICITAR_TUTORIA"):
            return True
        if mensaje:
            if _TUTORIA_KEYWORDS.search(mensaje):
                return True
            if _SOLICITUD_KEYWORDS.search(mensaje):
                return True
        return (intent in TUTORIA_INTENTS
                and confidence >= settings.CONFIDENCE_THRESHOLD)

    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        tipo = "logica"
        estudiante_id = get_estudiante_id() or usuario_id
        tutorias = get_tutorias_client()
        admin = get_admin_client()
        materia = _extraer_materia(mensaje)
        es_solicitud = (
            intent in ("CREAR_SOLICITUD", "SOLICITAR_TUTORIA")
            or (_SOLICITUD_KEYWORDS.search(mensaje) is not None and materia is not None)
        )

        if intent == "CANCELAR_SOLICITUD":
            tutoria_id = _extraer_id(mensaje)
            if tutoria_id:
                tutorias.cancelar_tutoria(tutoria_id, "Cancelado por el usuario")
            return {
                "respuesta": "Tu solicitud ha sido cancelada.",
                "tipo_resolucion": tipo,
            }

        if intent == "CAMBIAR_HORARIO":
            return {
                "respuesta": "El horario de tu solicitud ha sido actualizado.",
                "tipo_resolucion": tipo,
            }

        if intent == "ESCALAR_DOCENTE":
            tutoria_id = _extraer_id(mensaje)
            if tutoria_id:
                tutorias.gestionar_estado(tutoria_id, "escalada")
            return {
                "respuesta": "Tu solicitud ha sido escalada a un docente superior.",
                "tipo_resolucion": tipo,
            }

        if intent == "RESUMEN_SOLICITUD":
            msg_lower = mensaje.lower()
            if "bitácora" in msg_lower or "bitacora" in msg_lower:
                rest = get_tutorias_rest_client()
                bitacoras = rest.consultar_mis_bitacoras(estudiante_id)
                if not bitacoras:
                    return {
                        "respuesta": "No tienes bitácoras registradas.",
                        "tipo_resolucion": tipo,
                    }
                lines = [f"Bitácoras de tus tutorías ({len(bitacoras)}):"]
                for b in bitacoras:
                    lines.append(f"  - {b['codigo']} | {b['tema']}")
                    obs = b.get("observaciones", "")
                    if obs:
                        lines.append(f"    {obs}")
                    lines.append(f"    {'✅ Asistió' if b.get('asistio') else '❌ No asistió'}")
                    temas = b.get("temas_detectados", "")
                    if temas:
                        lines.append(f"    Temas: {temas}")
                return {
                    "respuesta": "\n".join(lines),
                    "tipo_resolucion": tipo,
                }

            result = tutorias.consultar_mis_tutorias(estudiante_id)
            if not result:
                return {
                    "respuesta": "No tienes tutorías registradas.",
                    "tipo_resolucion": tipo,
                }
            lines = [f"Resumen de tus tutorías ({len(result)}):"]
            for s in result:
                cod = s.get("codigo", s.get("id", "N/A"))
                est = s.get("estado", "desconocido")
                fecha = s.get("fecha_solicitud", s.get("fecha", ""))
                if fecha:
                    lines.append(f"  - Código: {cod} | Estado: {est} | Fecha: {fecha}")
                else:
                    lines.append(f"  - Código: {cod} | Estado: {est}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo,
            }

        if es_solicitud:
            materias_user = admin.get_materias_estudiante(estudiante_id)

            if materia and materias_user:
                coincide = _materia_coincide(materia, materias_user)
                if not coincide:
                    lines = [
                        f"La materia **{materia.title()}** no está disponible para tutorías "
                        f"porque no la estás cursando actualmente."
                    ]
                    lines.append("")
                    lines.append("**Tus materias inscritas:**")
                    for m in materias_user:
                        lines.append(f"  - {m['nombre']}")
                    return {
                        "respuesta": "\n".join(lines),
                        "tipo_resolucion": tipo,
                    }

                # Materia encontrada: crear solicitud vinculada a la asignatura
                result = tutorias.registrar_solicitud(
                    estudiante_id=estudiante_id,
                    tema=mensaje,
                    asignatura_id=coincide.get("id"),
                    periodo_id=coincide.get("periodo_id"),
                )
                codigo = result.get("codigo", "N/A") if result else "N/A"
                return {
                    "respuesta": (f"Tu solicitud de tutoría para **{coincide['nombre']}** "
                                  f"ha sido registrada con código {codigo}. "
                                  f"Un docente te contactará pronto."),
                    "tipo_resolucion": tipo,
                }

            # Sin materia específica: solicitud general
            result = tutorias.registrar_solicitud(
                estudiante_id=estudiante_id,
                tema=mensaje,
            )
            codigo = result.get("codigo", "N/A") if result else "N/A"
            return {
                "respuesta": (f"Tu solicitud de tutoría ha sido registrada con código "
                              f"{codigo}. Un docente te contactará pronto."),
                "tipo_resolucion": tipo,
            }

        if intent == "CONSULTAR_MIS_TUTORIAS":
            result = tutorias.consultar_mis_tutorias(estudiante_id)
            if not result:
                return {
                    "respuesta": "No tienes tutorías registradas.",
                    "tipo_resolucion": tipo,
                }
            lines = [f"Tienes {len(result)} tutoría(s) registrada(s):"]
            for s in result:
                cod = s.get("codigo", s.get("id", "N/A"))
                est = s.get("estado", "desconocido")
                lines.append(f"  - Código: {cod} | Estado: {est}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo,
            }

        if intent == "REPORTE_DOCENTE":
            result = tutorias.reporte_docente(estudiante_id)
            if not result:
                return {
                    "respuesta": "No se pudo generar el reporte del docente.",
                    "tipo_resolucion": tipo,
                }
            lines = ["Reporte del docente:"]
            for k, v in (result.items() if isinstance(result, dict) else []):
                lines.append(f"  - {k}: {v}")
            return {
                "respuesta": "\n".join(lines) if len(lines) > 1 else "No hay datos de reporte.",
                "tipo_resolucion": tipo,
            }

        if intent == "REPORTE_ESTUDIANTES":
            result = tutorias.reporte_estudiantes()
            if not result:
                return {
                    "respuesta": "No se pudo generar el reporte de estudiantes.",
                    "tipo_resolucion": tipo,
                }
            lines = ["Reporte de estudiantes:"]
            if isinstance(result, list):
                for item in result[:10]:
                    nombre = item.get("nombre", item.get("estudiante", "N/A"))
                    lines.append(f"  - {nombre}")
            elif isinstance(result, dict):
                for k, v in result.items():
                    lines.append(f"  - {k}: {v}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo,
            }

        if intent == "REPORTE_TEMAS":
            result = tutorias.reporte_temas()
            if not result:
                return {
                    "respuesta": "No se pudo generar el reporte de temas.",
                    "tipo_resolucion": tipo,
                }
            lines = ["Reporte de temas:"]
            if isinstance(result, list):
                for item in result[:10]:
                    tema = item.get("tema", item.get("nombre", "N/A"))
                    lines.append(f"  - {tema}")
            elif isinstance(result, dict):
                for k, v in result.items():
                    lines.append(f"  - {k}: {v}")
            return {
                "respuesta": "\n".join(lines),
                "tipo_resolucion": tipo,
            }

        return None

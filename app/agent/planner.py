"""
Planificador/orquestador del agente.

Responsabilidades:
1. Decidir si la respuesta del LLM es una respuesta directa o una llamada a tool.
2. Ejecutar la herramienta correspondiente a través del adapter.
3. Permitir múltiples iteraciones de tool calling (hasta un límite seguro).
4. Mantener el estado de conversación actualizado por los adapters.
5. Entregar la respuesta final redactada por el LLM.
"""

import re
from typing import Any

from app.core.config import settings
from app.utils.logger import logger

from .adapters.admin import AdminAdapter
from .adapters.rag import RAGAdapter
from .adapters.security import SecurityAdapter
from .adapters.tutorias import TutoriasAdapter
from .memory import ConversationMemory
from .ollama_client import OllamaClient
from .prompt import build_system_prompt
from .schemas import AgentResponse, ToolCall, ToolDefinition, ToolResult
from .tool_validator import ToolValidationError, ToolValidator
from .tools import get_available_tools


# Patrones para detectar preguntas sobre docentes/materias y forzar tool call.
_DOCEMTE_PATTERNS = [
    re.compile(r"qui[eé]n\s+(ense[nñ]a|imparte|da|dicta|imparte\s+clase|es\s+el\s+profesor|es\s+el\s+docente)\s+(.+)", re.IGNORECASE),
    re.compile(r"(profesor|docente)\s+(de|del|para)\s+(.+)", re.IGNORECASE),
    re.compile(r"(materias?|asignaturas?)\s+(del?\s+)?(profesor|docente)\s+(.+)", re.IGNORECASE),
    re.compile(r"qui[eé]n\s+me\s+(ense[nñ]a|imparte)", re.IGNORECASE),
    re.compile(r"(qué|que)\s+(profesor|docente)\s+(tiene|dicta|imparte|ense[nñ]a)\s+(.+)", re.IGNORECASE),
]
_MIS_PROFESORES_RE = re.compile(r"mis\s+(profesores?|docentes?|profes?)", re.IGNORECASE)


# ─── Admin pre-routing patterns ──────────────────────────────────────────────
_ADMIN_STATS_RE = re.compile(
    r"(cu[aá]nto?s?|cu[aá]nta?s?|total|cu[aá]l|n[uú]mero\s+de)\s+(docentes?|estudiantes?|tutor[ií]as?|carreras?|facultades?)",
    re.IGNORECASE,
)
_ADMIN_LIST_DOCENTES_RE = re.compile(
    r"(listar?|mostrar?|ver|enseñar|dar)\s+(los?\s+)?(docentes?|profesores?|profes?)",
    re.IGNORECASE,
)
_ADMIN_LIST_ESTUDIANTES_RE = re.compile(
    r"(listar?|mostrar?|ver|enseñar|dar)\s+(los?\s+)?estudiantes?",
    re.IGNORECASE,
)
_ADMIN_LIST_TUTORIAS_RE = re.compile(
    r"(listar?|mostrar?|ver|enseñar|dar)\s+(las?\s+)?tutor[ií]as?",
    re.IGNORECASE,
)


# ─── Student pre-routing patterns ────────────────────────────────────────────
_STUDENT_MATERIAS_RE = re.compile(
    r"(mis\s+materias|mis\s+asignaturas|qu[eé]\s+materias|qu[eé]\s+asignaturas"
    r"|materias\s+que\s+tengo|asignaturas\s+que\s+tengo"
    r"|cu[aá]les?\s+son\s+mis\s+materias|cu[aá]les?\s+son\s+mis\s+asignaturas"
    r"|ver\s+mis\s+materias|ver\s+mis\s+asignaturas"
    r"|en\s+qu[eé]\s+materias\s+estoy|en\s+qu[eé]\s+asignaturas\s+estoy"
    r"|qu[eé]\s+estoy\s+cursando|que\s+estoy\tomando)",
    re.IGNORECASE,
)
_STUDENT_BITACORAS_RE = re.compile(
    r"(mis\s+bit[aá]coras|bit[aá]coras|historial\s+de\s+tutor[ií]as"
    r"|qu[eé]\s+bit[aá]coras|ver\s+bit[aá]coras"
    r"|mis\s+sesiones|sesiones\s+atendidas"
    r"|qu[eé]\s+sesiones\s+he\s+tenido|qu[eé]\s+tutor[ií]as\s+he\s+tenido)",
    re.IGNORECASE,
)
_STUDENT_TUTORIAS_RE = re.compile(
    r"(mis\s+tutor[ií]as|ver\s+mis\s+tutor[ií]as|tutor[ií]as\s+pendientes"
    r"|tutor[ií]as\s+solicitadas|tutor[ií]as\s+activas"
    r"|cu[aá]ntas?\s+tutor[ií]as|cu[aá]les?\s+son\s+mis\s+tutor[ií]as"
    r"|qu[eé]\s+tutor[ií]as\s+tengo|mis\s+sesiones\s+de\s+tutor[ií]a)",
    re.IGNORECASE,
)
_STUDENT_PERFIL_RE = re.compile(
    r"(mi\s+perfil|dime\s+mi\s+perfil|quién\s+soy|como\s+estoy\s+registrado"
    r"|mis\s+datos|cu[aá]les?\s+son\s+mis\s+datos"
    r"|informaci[oó]n\s+de\s+mi\s+perfil|ver\s+mi\s+perfil)",
    re.IGNORECASE,
)

# ─── Docente pre-routing patterns (su propia info) ────────────────────────────
_DOCENTE_MIS_MATERIAS_RE = re.compile(
    r"(mis\s+asignaturas|mis\s+materias|qu[eé]\s+asignaturas\s+(doy|dicto|tengo|imparto)"
    r"|qu[eé]\s+materias\s+(doy|dicto|tengo|imparto)"
    r"|en\s+qu[eé]\s+materias\s+(doy|dicto|imparto)"
    r"|cu[aá]les?\s+son\s+mis\s+asignaturas|cu[aá]les?\s+son\s+mis\s+materias"
    r"|ver\s+mis\s+asignaturas|ver\s+mis\s+materias)",
    re.IGNORECASE,
)
_DOCENTE_MIS_ESTUDIANTES_RE = re.compile(
    r"(mis\s+estudiantes|qu[eé]\s+estudiantes\s+(tengo|tienen)"
    r"|estudiantes\s+de\s+mis\s+materias|estudiantes\s+de\s+mis\s+asignaturas"
    r"|cu[aá]ntos?\s+estudiantes?\s+tengo"
    r"|quién\s+(est[aá]\s+en|tiene)\s+(mis\s+materias|mis\s+asignaturas)"
    r"|ver\s+mis\s+estudiantes)",
    re.IGNORECASE,
)

# ─── Session pre-routing patterns ────────────────────────────────────────────
_SESIONES_ABIERTAS_RE = re.compile(
    r"(sesiones?\s+abiertas?|sesiones?\s+disponibles?|qu[eé]\s+sesiones?\s+(hay|existen|est[aá]n)"
    r"|ver\s+sesiones|unirme\s+a\s+sesi[oó]n|inscribirme\s+en\s+sesi[oó]n"
    r"|cu[aá]les?\s+son\s+las?\s+sesiones)",
    re.IGNORECASE,
)
_DOCENTE_MIS_SESIONES_RE = re.compile(
    r"(mis\s+sesiones|ver\s+mis\s+sesiones|sesiones\s+que\s+(tengo|imparto|doy))",
    re.IGNORECASE,
)
_DOCENTE_SOLICITUDES_PENDIENTES_RE = re.compile(
    r"(solicitudes?\s+pendientes|ver\s+solicitudes|solicitudes?\s+de\s+tutor[ií]a"
    r"|cu[aá]ntas?\s+solicitudes|qu[eé]\s+solicitudes\s+(tengo|hay))",
    re.IGNORECASE,
)
_DOCENTE_ACEPTAR_RE = re.compile(
    r"(aceptar\s+(la\s+)?solicitud|aceptar\s+tutor[ií]a|dar\s+ok\s+a\s+solicitud"
    r"|confirmar\s+solicitud|aceptar\s+solicitud\s+#?(\d+))",
    re.IGNORECASE,
)
_DOCENTE_RECHAZAR_RE = re.compile(
    r"(rechazar\s+(la\s+)?solicitud|rechazar\s+tutor[ií]a|rechazar\s+solicitud\s+#?(\d+))",
    re.IGNORECASE,
)
_DOCENTE_INICIAR_SESION_RE = re.compile(
    r"(iniciar\s+sesi[oó]n|empezar\s+sesi[oó]n|comenzar\s+sesi[oó]n"
    r"|iniciar\s+sesi[oó]n\s+#?(\d+))",
    re.IGNORECASE,
)
_DOCENTE_FINALIZAR_SESION_RE = re.compile(
    r"(finalizar\s+sesi[oó]n|terminar\s+sesi[oó]n|cerrar\s+sesi[oó]n"
    r"|finalizar\s+sesi[oó]n\s+#?(\d+))",
    re.IGNORECASE,
)


def _detect_student_query(mensaje: str) -> dict | None:
    """Detecta preguntas del estudiante (materias, bitácoras, tutorías, perfil)."""
    msg = mensaje.strip()

    if _STUDENT_MATERIAS_RE.search(msg):
        return {"tool": "consultar_materias"}
    if _STUDENT_BITACORAS_RE.search(msg):
        return {"tool": "consultar_bitacoras"}
    if _STUDENT_TUTORIAS_RE.search(msg):
        return {"tool": "consultar_tutorias"}
    if _STUDENT_PERFIL_RE.search(msg):
        return {"tool": "consultar_perfil_completo"}

    return None


def _detect_session_query(mensaje: str) -> dict | None:
    """Detecta preguntas sobre sesiones (abiertas, inscripción, etc.)."""
    msg = mensaje.strip()

    if _SESIONES_ABIERTAS_RE.search(msg):
        # Extraer materia si se menciona
        m = re.search(r"(?:de|para|en)\s+(.+?)(?:\?|$)", msg, re.IGNORECASE)
        materia = m.group(1).strip().rstrip("?").strip() if m else None
        return {"tool": "buscar_sesiones_abiertas", "materia_nombre": materia}

    return None


def _detect_docente_session_query(mensaje: str) -> dict | None:
    """Detecta acciones del docente sobre sesiones y solicitudes."""
    msg = mensaje.strip()

    if _DOCENTE_ACEPTAR_RE.search(msg):
        m = _DOCENTE_ACEPTAR_RE.search(msg)
        groups = m.groups() if m else []
        solicitud_id = None
        for g in groups:
            if g and g.isdigit():
                solicitud_id = int(g)
                break
        return {"tool": "aceptar_solicitud_tutoria", "solicitud_id": solicitud_id}

    if _DOCENTE_RECHAZAR_RE.search(msg):
        m = _DOCENTE_RECHAZAR_RE.search(msg)
        groups = m.groups() if m else []
        solicitud_id = None
        motivo = ""
        for g in groups:
            if g and g.isdigit():
                solicitud_id = int(g)
                break
        # Extraer motivo después de "por"
        motivo_match = re.search(r"por\s+(.+)", msg, re.IGNORECASE)
        if motivo_match:
            motivo = motivo_match.group(1).strip().rstrip("?").strip()
        return {"tool": "rechazar_solicitud_tutoria", "solicitud_id": solicitud_id, "motivo": motivo}

    if _DOCENTE_INICIAR_SESION_RE.search(msg):
        m = _DOCENTE_INICIAR_SESION_RE.search(msg)
        groups = m.groups() if m else []
        sesion_id = None
        for g in groups:
            if g and g.isdigit():
                sesion_id = int(g)
                break
        return {"tool": "iniciar_sesion_tutoria", "sesion_id": sesion_id}

    if _DOCENTE_FINALIZAR_SESION_RE.search(msg):
        m = _DOCENTE_FINALIZAR_SESION_RE.search(msg)
        groups = m.groups() if m else []
        sesion_id = None
        for g in groups:
            if g and g.isdigit():
                sesion_id = int(g)
                break
        return {"tool": "finalizar_sesion_tutoria", "sesion_id": sesion_id}

    if _DOCENTE_MIS_SESIONES_RE.search(msg):
        return {"tool": "listar_sesiones_docente"}

    if _DOCENTE_SOLICITUDES_PENDIENTES_RE.search(msg):
        return {"tool": "listar_solicitudes_pendientes"}

    return None


def _detect_docente_self_query(mensaje: str) -> dict | None:
    """Detecta preguntas del docente sobre sus propias asignaturas/estudiantes."""
    msg = mensaje.strip()

    if _DOCENTE_MIS_MATERIAS_RE.search(msg):
        return {"tool": "docente_mis_asignaturas"}
    if _DOCENTE_MIS_ESTUDIANTES_RE.search(msg):
        return {"tool": "docente_mis_estudiantes"}

    return None


def _detect_admin_query(mensaje: str) -> dict | None:
    """Detecta preguntas admin (estadísticas, listar) y retorna tool a ejecutar."""
    msg = mensaje.strip()

    m = _ADMIN_STATS_RE.search(msg)
    if m:
        entity = m.group(2).lower().rstrip("s")
        if "docente" in entity or "profesor" in entity:
            return {"tool": "listar_docentes", "params": {}}
        if "estudiante" in entity:
            return {"tool": "listar_estudiantes", "params": {}}
        if "tutori" in entity:
            return {"tool": "listar_tutorias", "params": {}}
        return {"tool": "estadisticas_sistema", "params": {}}

    if _ADMIN_LIST_DOCENTES_RE.search(msg):
        return {"tool": "listar_docentes", "params": {}}
    if _ADMIN_LIST_ESTUDIANTES_RE.search(msg):
        return {"tool": "listar_estudiantes", "params": {}}
    if _ADMIN_LIST_TUTORIAS_RE.search(msg):
        return {"tool": "listar_tutorias", "params": {}}

    return None


def _detect_docente_query(mensaje: str) -> dict | None:
    """Detecta preguntas sobre docentes/materias y extrae parámetros.
    Retorna {'materia': '...' } o {'posesivo': 'mios' } o None."""
    msg = mensaje.strip()

    # "mis profesores/docentes"
    if _MIS_PROFESORES_RE.search(msg):
        return {"posesivo": "mios", "materia": None}

    for pat in _DOCEMTE_PATTERNS:
        m = pat.search(msg)
        if m:
            groups = m.groups()
            # El último grupo siempre es la materia (si existe)
            materia = groups[-1].strip().rstrip("?").strip()
            # Limpiar artículos sueltos al inicio
            materia = re.sub(r"^(el|la|los|las|un|una|del|de\s+la|al)\s+", "", materia, flags=re.IGNORECASE).strip()
            if materia:
                return {"materia": materia, "posesivo": None}

    return None


# Palabras clave para detectar contenido sensible que requiera escalamiento.
_SENSITIVE_KEYWORDS = (
    "suicidio", "suicida", "matarme", "morirme", "muerte", "asesinato",
    "amenaza", "amenazado", "violencia", "abuso", "discriminación", "acosado",
    "acosada", "agredido", "agredida", "despido", "despedido", "demanda",
    "denuncia", "policía", "emergencia", "urgente medico", "hospital",
    "depresión severa", "no puedo más", "hablar con una persona",
    "hablar con alguien", "coordinador", "administrador", "ayuda profesional",
)

_SENSITIVE_RE = re.compile(
    "|".join(re.escape(kw) for kw in _SENSITIVE_KEYWORDS),
    re.IGNORECASE,
)


def _contains_sensitive_content(text: str) -> bool:
    return bool(_SENSITIVE_RE.search(text))


class AgentPlanner:
    """Orquesta el ciclo LLM → tool → LLM."""

    def __init__(
        self,
        estudiante_id: int | None = None,
        usuario_id: int | None = None,
        carrera_id: int | None = None,
        periodo_id: int | None = None,
        rol: str = "estudiante",
        memory: ConversationMemory | None = None,
    ):
        self.estudiante_id = estudiante_id
        self.usuario_id = usuario_id
        self.carrera_id = carrera_id
        self.periodo_id = periodo_id
        self.rol = rol

        self.tools = get_available_tools()
        self.validator = ToolValidator(self.tools)
        self.ollama = OllamaClient()
        self.memory = memory or ConversationMemory(max_messages=2)

        # Adaptadores disponibles.
        self._security = SecurityAdapter()
        self._admin = AdminAdapter()
        self._tutorias = TutoriasAdapter()
        self._rag = RAGAdapter()

        # Inicializar system prompt (se reconstruye cada vez para incluir estado actual).
        self._refresh_system_prompt()

    def run(self, mensaje: str, db_conn=None) -> AgentResponse:
        """Procesa un mensaje de usuario y devuelve la respuesta final."""
        self.memory.add("user", mensaje)

        # Escalamiento automático por contenido sensible (Gap 6).
        if _contains_sensitive_content(mensaje):
            logger.warning("[AgentPlanner] contenido sensible detectado; escalando conversación")
            result = self._escalar_conversacion(
                motivo="Contenido sensible detectado automáticamente en el mensaje del usuario.",
                usuario_id=self.usuario_id,
                db_conn=db_conn,
            )
            return AgentResponse(
                mensaje=result[0],
                intencion_detectada="escalar_conversacion",
                herramientas_usadas=["escalar_conversacion"],
            )

        # Pre-routing admin: estadísticas y listados del sistema.
        admin_match = _detect_admin_query(mensaje)
        if admin_match and self.rol in ("admin", "docente", "manager"):
            tool_name = admin_match["tool"]
            tool_params = admin_match["params"]
            logger.info(f"[AgentPlanner] pre-routing admin: tool={tool_name}")
            if tool_name == "estadisticas_sistema":
                result = self._admin.estadisticas_sistema()
            elif tool_name == "listar_docentes":
                result = self._admin.listar_docentes_admin(consulta=tool_params.get("consulta", ""))
            elif tool_name == "listar_estudiantes":
                result = self._admin.listar_estudiantes_admin(consulta=tool_params.get("consulta", ""))
            elif tool_name == "listar_tutorias":
                result = self._admin.listar_tutorias_admin(consulta=tool_params.get("consulta", ""))
            else:
                result = self._admin.estadisticas_sistema()
            herramientas_usadas = [tool_name]
            self.memory.update_state(result[1])
            self.memory.add("tool", result[0], name=tool_name)
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else result[0]
            # Si el LLM devuelve basura (función o muy corto), usar resultado raw.
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = result[0]
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada=tool_name,
                herramientas_usadas=herramientas_usadas,
            )

        # Pre-routing: forzar buscar_docentes cuando el modelo no lo hace.
        docente_match = _detect_docente_query(mensaje)
        if docente_match:
            materia = docente_match.get("materia")
            posesivo = docente_match.get("posesivo") or "todos"
            consulta = materia or ""
            logger.info(f"[AgentPlanner] pre-routing docente: materia={materia} posesivo={posesivo}")
            result = self._admin.buscar_docentes(
                consulta=consulta,
                estudiante_id=self.estudiante_id,
                posesivo=posesivo,
                materia=materia,
            )
            herramientas_usadas = ["buscar_docentes"]
            self.memory.update_state(result[1])
            self.memory.add("tool", result[0], name="buscar_docentes")
            # Pedir al LLM que formatee la respuesta.
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else result[0]
            # Si el LLM devuelve basura, usar resultado raw.
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = result[0]
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada="buscar_docentes",
                herramientas_usadas=herramientas_usadas,
            )

        # Pre-routing estudiante: forzar tool call cuando el modelo no lo hace.
        student_match = _detect_student_query(mensaje)
        if student_match and self.rol in ("estudiante", "admin", "docente", "manager"):
            tool_name = student_match["tool"]
            logger.info(f"[AgentPlanner] pre-routing estudiante: tool={tool_name}")
            eid = self.estudiante_id
            try:
                if tool_name == "consultar_materias":
                    content, state = self._admin.consultar_materias(estudiante_id=eid)
                elif tool_name == "consultar_bitacoras":
                    content, state = self._tutorias.consultar_bitacoras_resumidas(estudiante_id=eid, rol=self.rol)
                elif tool_name == "consultar_tutorias":
                    content, state = self._tutorias.consultar_mis_tutorias(estudiante_id=eid)
                elif tool_name == "consultar_perfil_completo":
                    content, state = self._security.consultar_perfil_completo(estudiante_id=eid)
                else:
                    content, state = "No se pudo procesar la solicitud.", {}
            except Exception as e:
                logger.error(f"[AgentPlanner] pre-routing estudiante error: {e}")
                content, state = f"Error al consultar {tool_name}: {e}", {}

            herramientas_usadas = [tool_name]
            self.memory.update_state(state)
            self.memory.add("tool", content, name=tool_name)
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else content
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = content
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada=tool_name,
                herramientas_usadas=herramientas_usadas,
            )

        # Pre-routing docente: sus propias asignaturas y estudiantes.
        docente_self_match = _detect_docente_self_query(mensaje)
        if docente_self_match and self.rol in ("docente", "admin", "manager"):
            tool_name = docente_self_match["tool"]
            logger.info(f"[AgentPlanner] pre-routing docente-self: tool={tool_name}")
            eid = self.estudiante_id
            try:
                if tool_name == "docente_mis_asignaturas":
                    content, state = self._admin.listar_docentes_admin(
                        consulta="", usuario_id=self.usuario_id,
                    )
                elif tool_name == "docente_mis_estudiantes":
                    content, state = self._admin.listar_estudiantes_por_docente(
                        usuario_id=self.usuario_id,
                    )
                else:
                    content, state = "No se pudo procesar la solicitud.", {}
            except Exception as e:
                logger.error(f"[AgentPlanner] pre-routing docente-self error: {e}")
                content, state = f"Error al consultar {tool_name}: {e}", {}

            herramientas_usadas = [tool_name]
            self.memory.update_state(state)
            self.memory.add("tool", content, name=tool_name)
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else content
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = content
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada=tool_name,
                herramientas_usadas=herramientas_usadas,
            )

        # Pre-routing sesiones: buscar sesiones abiertas (estudiantes).
        session_match = _detect_session_query(mensaje)
        if session_match and self.rol in ("estudiante", "admin", "docente", "manager"):
            tool_name = session_match["tool"]
            materia_nombre = session_match.get("materia_nombre")
            logger.info(f"[AgentPlanner] pre-routing sesiones: tool={tool_name} materia={materia_nombre}")
            content, state = self._tutorias.buscar_sesiones_abiertas(materia_nombre=materia_nombre)
            herramientas_usadas = [tool_name]
            self.memory.update_state(state)
            self.memory.add("tool", content, name=tool_name)
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else content
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = content
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada=tool_name,
                herramientas_usadas=herramientas_usadas,
            )

        # Pre-routing docente: acciones sobre sesiones y solicitudes.
        docente_session_match = _detect_docente_session_query(mensaje)
        if docente_session_match and self.rol in ("docente", "admin", "manager"):
            tool_name = docente_session_match["tool"]
            logger.info(f"[AgentPlanner] pre-routing docente-session: tool={tool_name}")
            try:
                if tool_name == "aceptar_solicitud_tutoria":
                    content, state = self._tutorias.aceptar_solicitud(
                        solicitud_id=docente_session_match["solicitud_id"] or 0,
                        usuario_id=self.usuario_id,
                    )
                elif tool_name == "rechazar_solicitud_tutoria":
                    content, state = self._tutorias.rechazar_solicitud(
                        solicitud_id=docente_session_match["solicitud_id"] or 0,
                        motivo=docente_session_match.get("motivo", ""),
                        usuario_id=self.usuario_id,
                    )
                elif tool_name == "iniciar_sesion_tutoria":
                    content, state = self._tutorias.iniciar_sesion(
                        sesion_id=docente_session_match["sesion_id"] or 0,
                    )
                elif tool_name == "finalizar_sesion_tutoria":
                    content, state = self._tutorias.finalizar_sesion(
                        sesion_id=docente_session_match["sesion_id"] or 0,
                    )
                elif tool_name == "listar_sesiones_docente":
                    content, state = self._tutorias.listar_sesiones_docente()
                elif tool_name == "listar_solicitudes_pendientes":
                    content, state = self._tutorias.listar_solicitudes_pendientes()
                else:
                    content, state = "Acción no reconocida.", {}
            except Exception as e:
                logger.error(f"[AgentPlanner] pre-routing docente-session error: {e}")
                content, state = f"Error: {e}", {}

            herramientas_usadas = [tool_name]
            self.memory.update_state(state)
            self.memory.add("tool", content, name=tool_name)
            self._refresh_system_prompt()
            raw_final = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            final_content = raw_final.content if raw_final else content
            if (not final_content
                    or final_content.strip().endswith("()")
                    or len(final_content.strip()) < 10):
                final_content = content
            self.memory.add("assistant", final_content)
            self._maybe_summarize()
            return AgentResponse(
                mensaje=final_content,
                intencion_detectada=tool_name,
                herramientas_usadas=herramientas_usadas,
            )

        max_iterations = settings.OLLAMA_MAX_TOOL_ITERATIONS
        herramientas_usadas: list[str] = []

        for iteration in range(max_iterations):
            self._refresh_system_prompt()
            raw = self.ollama.chat(
                self.memory.get_messages(),
                options={"num_ctx": 2048, "temperature": 0.3},
            )
            content = raw.content if raw else ""

            # 1. ¿El modelo pidió una herramienta?
            tool_call = self.validator.parse(content)
            if tool_call is None:
                # Respuesta directa.
                self.memory.add("assistant", content)
                self._maybe_summarize()
                return AgentResponse(
                    mensaje=content,
                    intencion_detectada="respuesta_directa",
                    herramientas_usadas=herramientas_usadas,
                )

            # 2. Validar y ejecutar herramienta.
            try:
                tool_call = self.validator.validate(tool_call)
            except ToolValidationError as e:
                logger.warning(f"[AgentPlanner] tool validation error: {e}")
                self.memory.add("tool", f"Error de validación: {e}", name="validator")
                continue

            herramientas_usadas.append(tool_call.tool)
            result = self._execute_tool(tool_call, db_conn=db_conn)
            self.memory.update_state(result.state_updates)
            self.memory.add("tool", result.content, name=tool_call.tool)

            # Si la ejecución falló y es la última iteración, responder con el error.
            if not result.success and iteration == max_iterations - 1:
                self.memory.add("assistant", result.content)
                return AgentResponse(
                    mensaje=result.content,
                    intencion_detectada=tool_call.tool,
                    herramientas_usadas=herramientas_usadas,
                )

        # 3. Última llamada al LLM para redactar respuesta final con los resultados.
        self._refresh_system_prompt()
        raw_final = self.ollama.chat(
            self.memory.get_messages(),
            options={"num_ctx": 2048, "temperature": 0.3},
        )
        final_content = raw_final.content if raw_final else (
            "Procesé tu solicitud, pero no pudo generar una respuesta final."
        )
        self.memory.add("assistant", final_content)
        self._maybe_summarize()

        return AgentResponse(
            mensaje=final_content,
            intencion_detectada=herramientas_usadas[-1] if herramientas_usadas else "respuesta_directa",
            herramientas_usadas=herramientas_usadas,
        )

    def _refresh_system_prompt(self) -> None:
        """Reconstruye el system prompt incluyendo el estado actual."""
        state_text = self.memory.render_state_for_prompt()
        system = build_system_prompt(
            estudiante_id=self.estudiante_id,
            usuario_id=self.usuario_id,
            carrera_id=self.carrera_id,
            periodo_id=self.periodo_id,
            rol=self.rol,
            tools=self.tools,
            state_text=state_text,
        )
        self.memory.set_system(system)

    def _execute_tool(self, call: ToolCall, db_conn=None) -> ToolResult:
        """Despacha la ejecución al adapter correspondiente.
        
        NOTA: estudiante_id se fuerza desde el JWT (self.estudiante_id)
        sin importar lo que haya alucinado el modelo. Esto es Categoría A:
        no puede depender del cumplimiento del modelo.
        """
        logger.info(f"[AgentPlanner] ejecutando tool={call.tool} params={call.parameters}")

        # estudiante_id forzado desde JWT — el modelo no decide qué ID usar.
        eid = self.estudiante_id

        try:
            if call.tool == "consultar_perfil":
                content, state = self._security.consultar_perfil(
                    estudiante_id=eid,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "consultar_perfil_completo":
                content, state = self._security.consultar_perfil_completo(
                    estudiante_id=eid,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "consultar_materias":
                content, state = self._admin.consultar_materias(
                    estudiante_id=eid,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "consultar_tutorias":
                content, state = self._tutorias.consultar_mis_tutorias(
                    estudiante_id=eid,
                    periodo_id=self._param_optional_int(call.parameters, "periodo_id"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "crear_tutoria":
                content, state = self._tutorias.crear_tutoria(
                    estudiante_id=eid,
                    asignatura_id=self._param_int(call.parameters, "asignatura_id"),
                    tema=self._param_str(call.parameters, "tema"),
                    periodo_id=self._param_optional_int(call.parameters, "periodo_id"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "cancelar_tutoria":
                content, state = self._tutorias.cancelar_tutoria(
                    tutoria_id=self._param_int(call.parameters, "tutoria_id"),
                    motivo=self._param_str(call.parameters, "motivo"),
                    usuario_id=self._param_int(call.parameters, "usuario_id"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "buscar_docentes":
                content, state = self._admin.buscar_docentes(
                    consulta=self._param_str(call.parameters, "consulta"),
                    estudiante_id=eid,
                    posesivo=call.parameters.get("posesivo") or "todos",
                    materia=call.parameters.get("materia"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "sugerir_docente":
                content, state = self._admin.sugerir_docente(
                    estudiante_id=eid,
                    asignatura_id=self._param_int(call.parameters, "asignatura_id"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "consultar_bitacoras":
                content, state = self._tutorias.consultar_bitacoras_resumidas(
                    estudiante_id=eid,
                    rol=self.rol,
                    periodo_id=self._param_optional_int(call.parameters, "periodo_id"),
                    solicitud_id=self._param_optional_int(call.parameters, "solicitud_id"),
                    busqueda=self._param_str(call.parameters, "busqueda") if call.parameters.get("busqueda") else None,
                    db_conn=db_conn,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "buscar_conocimiento":
                if db_conn is None:
                    return ToolResult(
                        tool=call.tool,
                        parameters=call.parameters,
                        success=False,
                        content="No se pudo acceder a la base de conocimiento en este momento.",
                    )
                documentos = self._rag.buscar_conocimiento(
                    conn=db_conn,
                    consulta=self._param_str(call.parameters, "consulta"),
                )
                content = self._rag.format_context(documentos)
                state = {
                    "ultima_busqueda": self._param_str(call.parameters, "consulta"),
                    "documentos_encontrados": len(documentos),
                }
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "escalar_conversacion":
                content, state = self._escalar_conversacion(
                    motivo=self._param_str(call.parameters, "motivo"),
                    usuario_id=self._param_optional_int(call.parameters, "usuario_id"),
                    db_conn=db_conn,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_docentes":
                content, state = self._admin.listar_docentes_admin(
                    consulta=call.parameters.get("consulta") or "",
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_estudiantes":
                content, state = self._admin.listar_estudiantes_admin(
                    consulta=call.parameters.get("consulta") or "",
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_tutorias":
                content, state = self._admin.listar_tutorias_admin(
                    consulta=call.parameters.get("consulta") or "",
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "estadisticas_sistema":
                content, state = self._admin.estadisticas_sistema()
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_estudiantes_por_docente":
                content, state = self._admin.listar_estudiantes_por_docente(
                    usuario_id=self.usuario_id,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "buscar_sesiones_abiertas":
                content, state = self._tutorias.buscar_sesiones_abiertas(
                    materia_nombre=call.parameters.get("materia_nombre"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "inscribirse_sesion":
                content, state = self._tutorias.inscribirse_sesion(
                    sesion_id=self._param_int(call.parameters, "sesion_id"),
                    estudiante_id=eid,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "aceptar_solicitud_tutoria":
                content, state = self._tutorias.aceptar_solicitud(
                    solicitud_id=self._param_int(call.parameters, "solicitud_id"),
                    usuario_id=self.usuario_id,
                    capacidad_maxima=self._param_optional_int(call.parameters, "capacidad_maxima") or 20,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "rechazar_solicitud_tutoria":
                content, state = self._tutorias.rechazar_solicitud(
                    solicitud_id=self._param_int(call.parameters, "solicitud_id"),
                    motivo=self._param_str(call.parameters, "motivo"),
                    usuario_id=self.usuario_id,
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_sesiones_docente":
                content, state = self._tutorias.listar_sesiones_docente()
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "listar_solicitudes_pendientes":
                content, state = self._tutorias.listar_solicitudes_pendientes()
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "iniciar_sesion_tutoria":
                content, state = self._tutorias.iniciar_sesion(
                    sesion_id=self._param_int(call.parameters, "sesion_id"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            if call.tool == "finalizar_sesion_tutoria":
                content, state = self._tutorias.finalizar_sesion(
                    sesion_id=self._param_int(call.parameters, "sesion_id"),
                    detalle=call.parameters.get("detalle"),
                )
                return ToolResult(tool=call.tool, parameters=call.parameters, success=True, content=content, state_updates=state)

            return ToolResult(
                tool=call.tool,
                parameters=call.parameters,
                success=False,
                content=f"Herramienta '{call.tool}' aún no implementada.",
            )
        except Exception as e:
            logger.error(f"[AgentPlanner] error ejecutando {call.tool}: {e}")
            return ToolResult(
                tool=call.tool,
                parameters=call.parameters,
                success=False,
                content=f"Error al ejecutar '{call.tool}': {e}",
            )

    def _maybe_summarize(self) -> None:
        """Si la memoria es muy larga, genera un resumen y la comprime."""
        if not self.memory.should_summarize(threshold=15):
            return
        logger.info("[AgentPlanner] generando resumen de conversación")
        self.memory.add("user", self.memory.get_summary_prompt())
        raw = self.ollama.chat(
            self.memory.get_messages(),
            options={"num_ctx": 2048, "temperature": 0.3},
        )
        self.memory.apply_summary(raw.content if raw else "Resumen no disponible.")

    def _escalar_conversacion(
        self,
        motivo: str,
        usuario_id: int | None = None,
        db_conn=None,
    ) -> tuple[str, dict]:
        """Registra un pendiente/administrativo y devuelve mensaje de escalamiento."""
        try:
            if db_conn is not None:
                from app.db import queries
                queries.insert_pendiente(
                    db_conn,
                    f"Escalamiento automático (usuario {usuario_id or 'N/A'}): {motivo}",
                )
        except Exception as e:
            logger.warning(f"[AgentPlanner] no se pudo guardar pendiente de escalamiento: {e}")

        mensaje = (
            "He registrado tu caso para que un coordinador se comunique contigo "
            "lo antes posible. Si es una emergencia, por favor contacta directamente "
            "a las líneas de atención de la universidad o a los servicios de emergencia."
        )
        return mensaje, {"escalado": True, "motivo": motivo}

    @staticmethod
    def _param_int(params: dict[str, Any], name: str) -> int:
        value = params.get(name)
        if value is None:
            raise ValueError(f"Parámetro requerido faltante: {name}")
        return int(value)

    @staticmethod
    def _param_optional_int(params: dict[str, Any], name: str) -> int | None:
        value = params.get(name)
        if value is None or value == "":
            return None
        return int(value)

    @staticmethod
    def _param_str(params: dict[str, Any], name: str) -> str:
        value = params.get(name)
        if value is None:
            raise ValueError(f"Parámetro requerido faltante: {name}")
        return str(value)

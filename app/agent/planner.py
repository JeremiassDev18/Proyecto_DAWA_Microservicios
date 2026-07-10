"""
Planificador/orquestador del agente.

Responsabilidades:
1. Decidir si la respuesta del LLM es una respuesta directa o una llamada a tool.
2. Ejecutar la herramienta correspondiente a través del adapter.
3. Permitir múltiples iteraciones de tool calling (hasta un límite seguro).
4. Mantener el estado de conversación actualizado por los adapters.
5. Entregar la respuesta final redactada por el LLM.
"""

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


# Palabras clave para detectar contenido sensible que requiera escalamiento.
_SENSITIVE_KEYWORDS = (
    "suicidio", "suicida", "matarme", "morirme", "muerte", "asesinato",
    "amenaza", "amenazado", "violencia", "abuso", "discriminación", "acosado",
    "acosada", "agredido", "agredida", "despido", "despedido", "demanda",
    "denuncia", "policía", "emergencia", "urgente medico", "hospital",
    "depresión severa", "no puedo más", "hablar con una persona",
    "hablar con alguien", "coordinador", "administrador", "ayuda profesional",
)


def _contains_sensitive_content(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in _SENSITIVE_KEYWORDS)


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

"""
Prompts y plantillas del sistema para el agente LLM.

Optimizado para Qwen 2.5 3B: prompt compacto (<1200 chars) para num_ctx=2048.
"""

from .schemas import ToolDefinition


SYSTEM_PROMPT_TEMPLATE = """Asistente académico universitario. Español, breve, sin credenciales. Usa herramientas; bitácoras=tutorías=académico. Emergencia→escalar. No-académico (famosos, deportes, clima)→responde: "Solo temas académicos." NO escalar esto.

Usuario: id={estudiante_id}, rol={rol}
{state}
Herramientas: {tools}

Formato: <tool_call>{{"name":"herramienta","arguments":{{"param":"valor"}}}}</tool_call>
{examples}Responde directo si no necesitas herramienta. Nunca pidas nombre/ID al usuario — ya lo tienes en el contexto. Usa consultar_perfil."""


def build_system_prompt(
    estudiante_id: int | None,
    usuario_id: int | None,
    carrera_id: int | None,
    periodo_id: int | None,
    tools: list[ToolDefinition],
    state_text: str = "",
    rol: str = "estudiante",
) -> str:
    es_estudiante = rol == "estudiante"

    tools_text = _render_tools(tools)

    if es_estudiante:
        examples = (
            "Ej: \"mis materias\"→<tool_call>"
            '{"name":"consultar_materias","arguments":{"estudiante_id":1}}'
            "</tool_call>  "
            '"bitácoras"→<tool_call>'
            '{"name":"consultar_bitacoras","arguments":{"estudiante_id":1}}'
            "</tool_call>  "
            '"quién enseña álgebra"→<tool_call>'
            '{"name":"buscar_docentes","arguments":{"consulta":"álgebra","materia":"álgebra"}}'
            "</tool_call>  "
            '"mis profesores"→<tool_call>'
            '{"name":"buscar_docentes","arguments":{"consulta":"","posesivo":"mios","estudiante_id":1}}'
            "</tool_call>  "
            '"profesor de Programación"→<tool_call>'
            '{"name":"buscar_docentes","arguments":{"consulta":"Programación","materia":"Programación"}}'
            "</tool_call>\n"
        )
    else:
        examples = (
            "Ej: \"cuántos docentes\"→<tool_call>"
            '{"name":"estadisticas_sistema","arguments":{}}'
            "</tool_call>  "
            '"listar docentes"→<tool_call>'
            '{"name":"listar_docentes","arguments":{}}'
            "</tool_call>  "
            '"listar estudiantes"→<tool_call>'
            '{"name":"listar_estudiantes","arguments":{}}'
            "</tool_call>  "
            '"tutorías del sistema"→<tool_call>'
            '{"name":"listar_tutorias","arguments":{}}'
            "</tool_call>  "
            '"profesor de Programación"→<tool_call>'
            '{"name":"buscar_docentes","arguments":{"consulta":"Programación","materia":"Programación"}}'
            "</tool_call>\n"
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        estudiante_id=estudiante_id or "desconocido",
        usuario_id=usuario_id or "desconocido",
        carrera_id=carrera_id or "desconocido",
        periodo_id=periodo_id or "desconocido",
        rol=rol or "desconocido",
        state=state_text,
        tools=tools_text,
        examples=examples,
    )


def _render_tools(tools: list[ToolDefinition]) -> str:
    """Formato compacto: una línea por herramienta."""
    lines = []
    for tool in tools:
        req = [p.name for p in tool.parameters if p.required]
        opt = [p.name for p in tool.parameters if not p.required]
        sig = ", ".join(req)
        if opt:
            sig += " [" + ", ".join(opt) + "]"
        lines.append(f"  {tool.name}({sig}): {tool.description}")
    return "\n".join(lines)


def build_tool_result_prompt(tool_name: str, result_text: str) -> str:
    return (
        f"Resultado de {tool_name}:\n\n{result_text}\n\n"
        "Redacta respuesta clara y natural."
    )

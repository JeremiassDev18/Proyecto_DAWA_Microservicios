"""
Tests unitarios para el módulo Agente LLM.

No requieren Ollama ni servicios externos. Verifican:
- Importación de componentes.
- Definición de herramientas.
- Validación de llamadas a herramientas.
- Memoria de conversación.
"""

import pytest

from app.agent.memory import ConversationMemory
from app.agent.schemas import ToolDefinition, ToolParameter
from app.agent.tool_validator import ToolValidationError, ToolValidator
from app.agent.tools import get_available_tools


class TestToolDefinitions:
    def test_tools_exist(self):
        tools = get_available_tools()
        names = {t.name for t in tools}
        expected = {
            "consultar_perfil", "consultar_perfil_completo", "consultar_materias",
            "crear_tutoria", "cancelar_tutoria", "buscar_docentes",
            "sugerir_docente", "consultar_bitacoras", "buscar_conocimiento",
            "escalar_conversacion",
        }
        assert expected.issubset(names), f"Faltan herramientas: {expected - names}"

    def test_required_parameters(self):
        tools = get_available_tools()
        by_name = {t.name: t for t in tools}

        perfil = by_name["consultar_perfil"]
        assert any(p.name == "estudiante_id" and p.required for p in perfil.parameters)

        perfil_completo = by_name["consultar_perfil_completo"]
        assert any(p.name == "estudiante_id" and p.required for p in perfil_completo.parameters)

        materias = by_name["consultar_materias"]
        assert any(p.name == "estudiante_id" and p.required for p in materias.parameters)

        crear = by_name["crear_tutoria"]
        required_crear = {p.name for p in crear.parameters if p.required}
        assert {"estudiante_id", "asignatura_id", "tema"}.issubset(required_crear)

    def test_escalar_requires_motivo(self):
        tools = get_available_tools()
        by_name = {t.name: t for t in tools}
        escalar = by_name["escalar_conversacion"]
        assert any(p.name == "motivo" and p.required for p in escalar.parameters)


class TestToolValidator:
    @pytest.fixture
    def validator(self):
        return ToolValidator(get_available_tools())

    def test_parse_direct_response_returns_none(self, validator):
        assert validator.parse("Hola, ¿en qué puedo ayudarte?") is None

    def test_parse_valid_json_tool(self, validator):
        raw = '{"tool": "consultar_perfil", "parameters": {"estudiante_id": 1}}'
        call = validator.parse(raw)
        assert call is not None
        assert call.tool == "consultar_perfil"
        assert call.parameters["estudiante_id"] == 1

    def test_parse_markdown_json_block(self, validator):
        raw = '```json\n{"tool": "consultar_materias", "parameters": {"estudiante_id": 2}}\n```'
        call = validator.parse(raw)
        assert call is not None
        assert call.tool == "consultar_materias"

    def test_parse_qwen_tool_call_format(self, validator):
        raw = '<tool_call>\n{"name": "consultar_perfil", "arguments": {"estudiante_id": 1}}\n</tool_call>'
        call = validator.parse(raw)
        assert call is not None
        assert call.tool == "consultar_perfil"
        assert call.parameters["estudiante_id"] == 1

    def test_validate_missing_parameter_raises(self, validator):
        call = validator.parse('{"tool": "crear_tutoria", "parameters": {"estudiante_id": 1}}')
        assert call is not None
        with pytest.raises(ToolValidationError):
            validator.validate(call)

    def test_validate_unknown_tool_raises(self, validator):
        call = validator.parse('{"tool": "herramienta_falsa", "parameters": {}}')
        assert call is not None
        with pytest.raises(ToolValidationError):
            validator.validate(call)

    def test_parse_buscar_docentes(self, validator):
        raw = '{"tool": "buscar_docentes", "parameters": {"consulta": "López", "posesivo": "todos"}}'
        call = validator.parse(raw)
        assert call is not None
        assert call.tool == "buscar_docentes"
        assert call.parameters["posesivo"] == "todos"

    def test_parse_escalar_conversacion(self, validator):
        raw = '{"tool": "escalar_conversacion", "parameters": {"motivo": "situación sensible"}}'
        call = validator.parse(raw)
        assert call is not None
        assert call.tool == "escalar_conversacion"


class TestConversationMemory:
    def test_window_limit(self):
        memory = ConversationMemory(max_messages=4)
        memory.set_system("Eres un asistente.")
        for i in range(10):
            memory.add("user", f"mensaje {i}")
            memory.add("assistant", f"respuesta {i}")

        messages = memory.get_messages(include_system=False)
        assert len(messages) == 4
        assert messages[-1]["content"] == "respuesta 9"

    def test_system_preserved(self):
        memory = ConversationMemory(max_messages=2)
        memory.set_system("Prompt de sistema")
        memory.add("user", "hola")
        memory.add("assistant", "hola!")
        memory.add("user", "adios")
        memory.add("assistant", "adios!")

        messages = memory.get_messages(include_system=True)
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Prompt de sistema"

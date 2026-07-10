"""
Tests de integración del planificador (planner) con el ciclo completo:

  LLM → tool → adapter → resultado formateado → respuesta final

Mockea el LLM y los adapters para verificar que:
1. El tool calling se parsea correctamente (incluyendo formato {{ ... }} legacy)
2. El adapter devuelve datos formateados como texto natural
3. La respuesta final NO contiene JSON crudo ni <tool_call>
"""

from unittest.mock import MagicMock

import pytest

from app.agent.memory import ConversationMemory
from app.agent.planner import AgentPlanner
from app.agent.schemas import LLMRawResponse


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_ollama_mock(*responses):
    """
    Crea un mock de OllamaClient.chat que devuelve respuestas secuenciales
    según la lista `responses`. Cada elemento puede ser un string (se envuelve
    en LLMRawResponse) o un LLMRawResponse directamente.
    """
    mock = MagicMock()
    chat_results = []
    for r in responses:
        if isinstance(r, str):
            chat_results.append(LLMRawResponse(content=r, finish_reason="stop"))
        else:
            chat_results.append(r)
    mock.chat.side_effect = chat_results
    return mock


def _make_adapter_mock(method_name, return_value):
    """Crea un mock de adapter con un método específico."""
    mock = MagicMock()
    getattr(mock, method_name).return_value = return_value
    return mock


# ── Tests ────────────────────────────────────────────────────────────────────

class TestPlannerToolFlow:
    """Verifica el ciclo planner→tool→adapter→respuesta para cada herramienta."""

    @pytest.fixture
    def planner(self):
        p = AgentPlanner(
            estudiante_id=1,
            usuario_id=1,
            carrera_id=1,
            periodo_id=1,
            rol="estudiante",
            memory=ConversationMemory(max_messages=10),
        )
        return p

    def test_consultar_materias(self, planner):
        # Mock: LLM devuelve tool call, luego respuesta final.
        planner.ollama = _make_ollama_mock(
            # Iteración 1: el LLM pide la herramienta
            '<tool_call>\n{"name": "consultar_materias", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            # Iteración 2: el LLM redacta la respuesta final
            "Estas son tus materias del período actual.",
        )

        # Mock: adapter devuelve datos formateados
        planner._admin = _make_adapter_mock(
            "consultar_materias",
            (
                "Tus materias son:\n"
                "- INTRO1 (Introducción a la Programación)\n"
                "- MD1 (Matemáticas Discretas)\n"
                "- FC1 (Fundamentos de Computación)",
                {"ultima_accion": "consultar_materias"},
            ),
        )

        result = planner.run("Qué materias tengo?")

        assert result is not None
        assert result.mensaje is not None
        # La respuesta debe ser texto natural, NO JSON ni tool_call
        assert "<tool_call>" not in result.mensaje, f"Respuesta contiene <tool_call>: {result.mensaje}"
        assert "{" not in result.mensaje or "herramienta" not in result.mensaje, (
            f"Respuesta parece JSON: {result.mensaje}"
        )
        assert "consultar_materias" in result.herramientas_usadas

    def test_consultar_materias_con_formato_legacy(self, planner):
        """
        Qwen a veces regurgita {{ en vez de { en el JSON.
        Verificar que el validador normaliza este formato.
        """
        planner.ollama = _make_ollama_mock(
            # Formato legacy con {{ }}
            '<tool_call>\n{{"name": "consultar_materias", "arguments": {{"estudiante_id": 1}}}}\n</tool_call>',
            "Listo, aquí tienes tus materias.",
        )
        planner._admin = _make_adapter_mock(
            "consultar_materias",
            ("- INTRO1\n- MD1\n- FC1", {"ultima_accion": "consultar_materias"}),
        )

        result = planner.run("Dame mis materias")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_materias" in result.herramientas_usadas

    def test_consultar_materias_sin_herramienta(self, planner):
        """El LLM responde directamente sin llamar herramienta."""
        planner.ollama = _make_ollama_mock(
            "No tengo acceso a tus materias en este momento.",
        )

        result = planner.run("Qué materias tengo?")

        assert result is not None
        assert result.mensaje is not None
        assert result.herramientas_usadas == []
        assert result.intencion_detectada == "respuesta_directa"

    def test_consultar_tutorias(self, planner):
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_tutorias", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            "Claro, aquí están tus tutorías.",
        )
        planner._tutorias = _make_adapter_mock(
            "consultar_mis_tutorias",
            (
                "Tus tutorías:\n"
                "1. Tutoría #4 - Programación orientada a objetos - Estado: atendida\n"
                "2. Tutoría #15 - Consulta sobre álgebra - Estado: confirmada",
                {"ultima_accion": "consultar_tutorias", "ultima_tutoria": 15},
            ),
        )

        result = planner.run("Y mis tutorías?")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_tutorias" in result.herramientas_usadas

    def test_consultar_bitacoras(self, planner):
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_bitacoras", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            "Estas son tus bitácoras.",
        )
        planner._tutorias = _make_adapter_mock(
            "consultar_bitacoras_resumidas",
            (
                "Bitácoras de tutorías:\n"
                "1. Tutoría #10 - Álgebra (Estado: atendida, Fecha: 2025-06-01). "
                "Resumen: Se explicaron matrices.",
                {"ultima_accion": "consultar_bitacoras"},
            ),
        )

        result = planner.run("Dime las bitácoras")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_bitacoras" in result.herramientas_usadas

    def test_consultar_bitacoras_por_solicitud(self, planner):
        """El LLM pasa solicitud_id para filtrar una tutoría específica."""
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_bitacoras", "arguments": {"estudiante_id": 1, "solicitud_id": 4}}\n</tool_call>',
            "Aquí tienes la bitácora de esa tutoría.",
        )
        planner._tutorias = _make_adapter_mock(
            "consultar_bitacoras_resumidas",
            (
                "Bitácora de la tutoría #4:\n"
                "Observaciones: Se resolvieron dudas de POO. | Temas: Polimorfismo, Herencia",
                {"ultima_accion": "consultar_bitacoras", "ultima_tutoria": 4},
            ),
        )

        result = planner.run("La bitácora de la tutoría 4")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_bitacoras" in result.herramientas_usadas

    def test_consultar_perfil(self, planner):
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_perfil", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            "Aquí tienes tu perfil académico.",
        )
        planner._security = _make_adapter_mock(
            "consultar_perfil",
            (
                "Nombre: Juan Pérez\n"
                "Carrera: Ingeniería en Sistemas\n"
                "Facultad: Ingeniería\n"
                "Email: juan@email.com",
                {"ultima_accion": "consultar_perfil"},
            ),
        )

        result = planner.run("Quiero mi perfil")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_perfil" in result.herramientas_usadas

    def test_consultar_bitacoras_con_busqueda(self, planner):
        """LLM pasa busqueda para filtrar bitácoras por materia."""
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_bitacoras", "arguments": {"estudiante_id": 1, "busqueda": "álgebra"}}\n</tool_call>',
            "Aquí están las bitácoras de Álgebra.",
        )
        planner._tutorias = _make_adapter_mock(
            "consultar_bitacoras_resumidas",
            (
                "Bitácoras de tutorías:\n1. Tutoría #1 - Álgebra - Resumen: Matrices.",
                {"ultima_accion": "consultar_bitacoras", "total_bitacoras": 1},
            ),
        )

        result = planner.run("Las bitácoras de álgebra")

        assert result is not None
        assert "<tool_call>" not in result.mensaje
        assert "consultar_bitacoras" in result.herramientas_usadas

    def test_cambio_de_tema_ejecuta_nueva_herramienta(self, planner):
        """
        Cuando el usuario cambia de tema (ej: materias → bitácoras),
        el LLM debe llamar la nueva herramienta en vez de seguir con el tema anterior.
        """
        planner.ollama = _make_ollama_mock(
            # Primera iteración: consultar_materias
            '<tool_call>\n{"name": "consultar_materias", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            # Segunda iteración: resultado de materias, LLM redacta respuesta
            "Tus materias son INTRO1, MD1 y FC1.",
        )
        planner._admin = _make_adapter_mock(
            "consultar_materias",
            ("INTRO1, MD1, FC1", {"ultimas_materias": "INTRO1, MD1, FC1"}),
        )

        # Primer mensaje: materias
        result1 = planner.run("Qué materias tengo?")
        assert "INTRO1" in result1.mensaje or "consultar_materias" in result1.herramientas_usadas

        # Segundo mensaje: cambio de tema a bitácoras
        planner.ollama = _make_ollama_mock(
            '<tool_call>\n{"name": "consultar_bitacoras", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            "Aquí tienes tus bitácoras.",
        )
        planner._tutorias = _make_adapter_mock(
            "consultar_bitacoras_resumidas",
            ("Bitácora #1: Álgebra", {"ultima_accion": "consultar_bitacoras", "total_bitacoras": 1}),
        )

        result2 = planner.run("Ahora habla de mis bitácoras")

        assert result2 is not None
        assert "<tool_call>" not in result2.mensaje
        assert "consultar_bitacoras" in result2.herramientas_usadas

    def test_escalar_conversacion(self, planner):
        """Contenido sensible debe escalar sin pasar por el LLM."""
        planner.ollama = _make_ollama_mock(
            "ignorado — no debe llegar aquí",
        )

        result = planner.run("Necesito ayuda, tengo pensamientos suicidas")

        assert result is not None
        assert "coordinador" in result.mensaje.lower()
        assert "escalar_conversacion" in result.herramientas_usadas

    def test_multiples_iteraciones(self, planner):
        """
        El planner debe soportar múltiples iteraciones de tool calling.
        En este test, la primera tool falla y la segunda tool es exitosa.
        """
        planner.ollama = _make_ollama_mock(
            # 1er tool call: consultar_materias (falla → reintenta)
            '<tool_call>\n{"name": "consultar_materias", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            # 2o tool call: consultar_tutorias (éxito)
            '<tool_call>\n{"name": "consultar_tutorias", "arguments": {"estudiante_id": 1}}\n</tool_call>',
            # Respuesta final
            "Listo, revisé tus tutorías.",
        )

        def failing_admin(*args, **kwargs):
            raise RuntimeError("Servicio no disponible")

        planner._admin = MagicMock()
        planner._admin.consultar_materias.side_effect = failing_admin

        planner._tutorias = _make_adapter_mock(
            "consultar_mis_tutorias",
            (
                "Tus tutorías:\n1. Tutoría #4 - POO - Estado: atendida",
                {"ultima_accion": "consultar_tutorias", "ultima_tutoria": 4},
            ),
        )

        result = planner.run("Quiero mis datos")

        # Debe haber usado ambas herramientas aunque la primera haya fallado.
        assert result is not None
        assert "consultar_materias" in result.herramientas_usadas
        assert "consultar_tutorias" in result.herramientas_usadas

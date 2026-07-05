from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.fallback_handler import FallbackHandler


@pytest.fixture
def handler():
    return FallbackHandler()


class TestFallbackHandler:
    def test_can_handle_always(self, handler):
        assert handler.can_handle("CUALQUIER_COSA", 0.0) is True
        assert handler.can_handle("SIN_INTENCION", 0.0) is True

    def test_handle_low_confidence(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.fallback_handler.ESCALATION_ENABLED", True):
            with patch("app.services.handlers.fallback_handler.CONFIDENCE_THRESHOLD", 0.6):
                result = handler.handle(conn, 1, "mensaje", "SIN_INTENCION", 0.15)
                assert result is not None
                assert "Confianza baja" in result["respuesta"]
                assert result["tipo_resolucion"] == "sin_respuesta"
                assert result["escalation_reason"] is not None
                assert "0.15" in result["escalation_reason"]

    def test_handle_normal_fallback(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.fallback_handler.ESCALATION_ENABLED", True):
            with patch("app.services.handlers.fallback_handler.CONFIDENCE_THRESHOLD", 0.6):
                result = handler.handle(conn, 1, "mensaje", "CONSULTAR_FAQ", 0.75)
                assert result is not None
                assert "Sin coincidencia" in result["respuesta"]
                assert result["tipo_resolucion"] == "sin_respuesta"
                assert "Sin coincidencia" in result["escalation_reason"]

    def test_handle_escalation_disabled(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.fallback_handler.ESCALATION_ENABLED", False):
            with patch("app.services.handlers.fallback_handler.CONFIDENCE_THRESHOLD", 0.6):
                result = handler.handle(conn, 1, "mensaje", "SIN_INTENCION", 0.15)
                assert result is not None
                assert "Sin coincidencia" in result["respuesta"]

    def test_inserts_pendiente(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "mensaje", "SIN_INTENCION", 0.15)
        assert result is not None
        conn.cursor.return_value.__enter__.return_value.execute.assert_any_call(
            "INSERT INTO chatbot_pregunta_pendiente (contenido) VALUES (%s) RETURNING id",
            ("mensaje",),
        )

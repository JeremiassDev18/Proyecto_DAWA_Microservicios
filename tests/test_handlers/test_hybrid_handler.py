from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.hybrid_handler import HybridHandler


@pytest.fixture
def handler():
    return HybridHandler()


class TestHybridHandler:
    def test_can_handle_always(self, handler):
        assert handler.can_handle("CUALQUIER_COSA", 0.0) is True
        assert handler.can_handle("SIN_INTENCION", 0.0) is True

    def test_handle_returns_response(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.hybrid_handler.hybrid_search",
                   return_value="Respuesta híbrida"):
            result = handler.handle(conn, 1, "test query", "CONSULTAR_FAQ", 0.4)
            assert result is not None
            assert result["respuesta"] == "Respuesta híbrida"
            assert result["tipo_resolucion"] == "hibrida"

    def test_handle_returns_none_on_empty(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.hybrid_handler.hybrid_search",
                   return_value=None):
            result = handler.handle(conn, 1, "test query", "CONSULTAR_FAQ", 0.4)
            assert result is None

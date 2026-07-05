from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.rag_handler import RAGHandler


@pytest.fixture
def handler():
    return RAGHandler()


class TestRAGHandler:
    def test_can_handle_always(self, handler):
        assert handler.can_handle("CUALQUIER_COSA", 0.0) is True
        assert handler.can_handle("SIN_INTENCION", 0.0) is True

    def test_handle_returns_context(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.rag_handler.respond_with_documents",
                   return_value="Documento de prueba:\nContenido importante"):
            result = handler.handle(conn, 1, "test query", "CONSULTAR_REGLAMENTO", 0.4)
            assert result is not None
            assert "Documento de prueba" in result["respuesta"]
            assert result["tipo_resolucion"] == "dinamica"

    def test_handle_returns_none_on_empty(self, handler):
        conn = MagicMock()
        with patch("app.services.rag_service.respond_with_documents",
                   return_value=None):
            result = handler.handle(conn, 1, "test query", "CONSULTAR_REGLAMENTO", 0.4)
            assert result is None

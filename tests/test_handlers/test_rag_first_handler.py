from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.rag_first_handler import RAGFirstHandler


@pytest.fixture
def handler():
    return RAGFirstHandler()


class TestRAGFirstHandler:
    def test_can_handle_always(self, handler):
        assert handler.can_handle("", 0.0) is True
        assert handler.can_handle("CUALQUIER_COSA", 100.0) is True

    def test_handle_returns_context_on_high_similarity(self, handler):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            (1, "Reglamento", "Texto del reglamento", "normativa", "",
             0.45, None),
        ]
        cursor.fetchone.return_value = None

        with patch("app.services.handlers.rag_first_handler.settings.RAG_HIGH_CONFIDENCE",
                   0.35):
            result = handler.handle(conn, 1, "consulta", "", 0.0)
            assert result is not None
            assert "Reglamento" in result["respuesta"]
            assert result["tipo_resolucion"] == "dinamica"

    def test_handle_returns_none_on_low_similarity(self, handler):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            (1, "Reglamento", "Texto", "normativa", "",
             0.20, None),
        ]

        with patch("app.services.handlers.rag_first_handler.settings.RAG_HIGH_CONFIDENCE",
                   0.35):
            result = handler.handle(conn, 1, "consulta", "", 0.0)
            assert result is None

    def test_handle_returns_none_on_no_docs(self, handler):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []

        result = handler.handle(conn, 1, "consulta", "", 0.0)
        assert result is None

from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.faq_handler import FAQHandler


@pytest.fixture
def handler():
    return FAQHandler()


class TestFAQHandlerCanHandle:
    def test_high_confidence_known_intent(self, handler):
        assert handler.can_handle("CONSULTAR_FAQ", 0.75) is True

    def test_low_confidence_rejected(self, handler):
        assert handler.can_handle("CONSULTAR_FAQ", 0.3) is False

    def test_sin_intencion_rejected(self, handler):
        assert handler.can_handle("SIN_INTENCION", 0.9) is False


class TestFAQHandlerHandle:
    def test_found_response(self, handler):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            (1, "CONSULTAR_FAQ", None, True, None),  # get_intencion_by_nombre
            (1, "Respuesta FAQ", "texto", 1, 0),       # get_respuesta_by_intencion
        ]
        result = handler.handle(conn, 1, "consulta", "CONSULTAR_FAQ", 0.9)
        assert result is not None
        assert result["respuesta"] == "Respuesta FAQ"
        assert result["tipo_resolucion"] == "estatica"

    def test_no_intencion_in_db(self, handler):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        result = handler.handle(conn, 1, "test", "UNKNOWN_INTENT", 0.9)
        assert result is None

    def test_no_response_in_db(self, handler):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            (1, "CONSULTAR_FAQ", None, True, None),  # get_intencion_by_nombre exists
            None,                                       # get_respuesta_by_intencion None
        ]
        result = handler.handle(conn, 1, "test", "CONSULTAR_FAQ", 0.9)
        assert result is None

    def test_increments_veces_usada(self, handler):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            (1, "CONSULTAR_FAQ", None, True, None),
            (42, "Respuesta FAQ", "texto", 1, 5),
        ]
        result = handler.handle(conn, 1, "test", "CONSULTAR_FAQ", 0.9)
        assert result is not None
        cursor.execute.assert_any_call(
            "UPDATE chatbot_respuesta SET veces_usada = veces_usada + 1 WHERE id = %s",
            (42,),
        )

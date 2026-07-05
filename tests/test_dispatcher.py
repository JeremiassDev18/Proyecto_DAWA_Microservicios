from unittest.mock import MagicMock, patch

import pytest

from app.services.dispatcher import dispatch
from app.services.handlers.base import IntentHandler


class PassthroughHandler(IntentHandler):
    def __init__(self, can_handle=True, result=None):
        self._can_handle = can_handle
        self._result = result

    def can_handle(self, intent, confidence):
        return self._can_handle

    def handle(self, conn, usuario_id, mensaje, intent, confidence):
        return self._result


class TestDispatcher:
    def test_first_handler_wins(self):
        handler_a = PassthroughHandler(
            can_handle=True,
            result={"respuesta": "A", "tipo_resolucion": "test"},
        )
        handler_b = PassthroughHandler(
            can_handle=True,
            result={"respuesta": "B", "tipo_resolucion": "test"},
        )

        with patch("app.services.dispatcher.HANDLER_CHAIN", [handler_a, handler_b]):
            result = dispatch(MagicMock(), 1, "test", "INTENT", 0.9)
            assert result["respuesta"] == "A"

    def test_skips_handlers_that_cannot_handle(self):
        handler_a = PassthroughHandler(can_handle=False)
        handler_b = PassthroughHandler(
            can_handle=True,
            result={"respuesta": "B", "tipo_resolucion": "test"},
        )

        with patch("app.services.dispatcher.HANDLER_CHAIN", [handler_a, handler_b]):
            result = dispatch(MagicMock(), 1, "test", "INTENT", 0.9)
            assert result["respuesta"] == "B"

    def test_skips_handlers_that_return_none(self):
        handler_a = PassthroughHandler(
            can_handle=True,
            result=None,
        )
        handler_b = PassthroughHandler(
            can_handle=True,
            result={"respuesta": "B", "tipo_resolucion": "test"},
        )

        with patch("app.services.dispatcher.HANDLER_CHAIN", [handler_a, handler_b]):
            result = dispatch(MagicMock(), 1, "test", "INTENT", 0.9)
            assert result["respuesta"] == "B"

    def test_all_handlers_fail_returns_fallback(self):
        handler_a = PassthroughHandler(can_handle=True, result=None)
        handler_b = PassthroughHandler(can_handle=True, result=None)

        with patch("app.services.dispatcher.HANDLER_CHAIN", [handler_a, handler_b]):
            result = dispatch(MagicMock(), 1, "test", "INTENT", 0.9)
            assert "Lo siento" in result["respuesta"]
            assert result["tipo_resolucion"] == "sin_respuesta"

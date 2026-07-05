from unittest.mock import MagicMock, patch

import pytest

from app.services.handlers.external_handler import ExternalHandler


@pytest.fixture
def handler():
    return ExternalHandler()


class TestExternalHandlerCanHandle:
    def test_accepts_static_intents_any_confidence(self, handler):
        assert handler.can_handle("CANCELAR_SOLICITUD", 0.0) is True
        assert handler.can_handle("CAMBIAR_HORARIO", 0.1) is True
        assert handler.can_handle("ESCALAR_DOCENTE", 0.0) is True
        assert handler.can_handle("RESUMEN_SOLICITUD", 0.0) is True

    def test_accepts_dynamic_intents_with_high_confidence(self, handler):
        for intent in ["CREAR_SOLICITUD", "BUSCAR_DOCENTE", "CONTACTAR_DOCENTE"]:
            assert handler.can_handle(intent, 0.9) is True

    def test_rejects_dynamic_intents_with_low_confidence(self, handler):
        for intent in ["CREAR_SOLICITUD", "BUSCAR_DOCENTE", "CONTACTAR_DOCENTE"]:
            assert handler.can_handle(intent, 0.3) is False

    def test_rejects_non_external_intents(self, handler):
        assert handler.can_handle("CONSULTAR_FAQ", 0.9) is False
        assert handler.can_handle("SIN_INTENCION", 0.0) is False
        assert handler.can_handle("HORARIO_TUTORIAS", 0.9) is False


class TestExternalHandlerHandle:
    def test_crear_solicitud(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "Quiero una tutoría", "CREAR_SOLICITUD", 0.95)
        assert result is not None
        assert "registrada" in result["respuesta"]
        assert result["tipo_resolucion"] == "logica"

    def test_solicitar_tutoria(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "Necesito tutoría", "SOLICITAR_TUTORIA", 0.95)
        assert result is not None
        assert "registrada" in result["respuesta"]
        assert result["tipo_resolucion"] == "logica"

    def test_consultar_mis_tutorias_empty(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 99, "Mis tutorías", "CONSULTAR_MIS_TUTORIAS", 0.9)
        assert result is not None
        assert "No tienes tutorías registradas" in result["respuesta"]

    def test_consultar_mis_tutorias_with_data(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.external_handler.INTENT_SERVICE_MAP",
                   {"CONSULTAR_MIS_TUTORIAS": lambda uid, msg: [
                       {"codigo": "TUT-001", "estado": "pendiente"},
                       {"codigo": "TUT-002", "estado": "completada"},
                   ]}):
            result = handler.handle(conn, 1, "", "CONSULTAR_MIS_TUTORIAS", 0.9)
            assert result is not None
            assert "2 tutoría(s)" in result["respuesta"]
            assert "TUT-001" in result["respuesta"]

    def test_buscar_docente_no_results(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.external_handler.INTENT_SERVICE_MAP",
                   {"BUSCAR_DOCENTE": lambda uid, msg: []}):
            result = handler.handle(conn, 1, "", "BUSCAR_DOCENTE", 0.9)
            assert result is not None
            assert "No encontré docentes" in result["respuesta"]

    def test_buscar_docente_with_results(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.external_handler.INTENT_SERVICE_MAP",
                   {"BUSCAR_DOCENTE": lambda uid, msg: [
                       {"nombre": "Dr. Ruiz", "asignatura": "Matemáticas", "disponible": True},
                   ]}):
            result = handler.handle(conn, 1, "", "BUSCAR_DOCENTE", 0.9)
            assert result is not None
            assert "Dr. Ruiz" in result["respuesta"]
            assert "Disponible" in result["respuesta"]

    def test_cancelar_solicitud(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "", "CANCELAR_SOLICITUD", 0.9)
        assert result is not None
        assert "cancelada" in result["respuesta"]

    def test_cambiar_horario(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "", "CAMBIAR_HORARIO", 0.9)
        assert result is not None
        assert "actualizado" in result["respuesta"]

    def test_escalar_docente(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "", "ESCALAR_DOCENTE", 0.9)
        assert result is not None
        assert "escalada" in result["respuesta"]

    def test_resumen_solicitud(self, handler):
        conn = MagicMock()
        result = handler.handle(conn, 1, "", "RESUMEN_SOLICITUD", 0.9)
        assert result is not None
        assert "resumen" in result["respuesta"]

    def test_unknown_intent_returns_none(self, handler):
        conn = MagicMock()
        with patch("app.services.handlers.external_handler.INTENT_SERVICE_MAP", {}):
            result = handler.handle(conn, 1, "", "CREAR_SOLICITUD", 0.9)
            assert result is None

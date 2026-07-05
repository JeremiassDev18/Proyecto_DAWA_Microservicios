from unittest.mock import MagicMock, patch

import pytest

from app.db import queries
from app.services.chat_orchestrator import process_message
from app.services.handlers.rag_first_handler import RAGFirstHandler


class TestProcessMessage:
    @pytest.fixture
    def mock_conn(self):
        conn = MagicMock()

        def create_conversacion_side(conn, id_usuario):
            return 1

        with patch.object(queries, 'create_conversacion',
                          side_effect=create_conversacion_side):
            with patch.object(queries, 'get_conversaciones_by_usuario',
                              return_value=[]):
                with patch.object(queries, 'insert_mensaje', return_value=1):
                    with patch.object(queries, 'insert_prediccion'):
                        with patch.object(queries, 'get_intencion_by_nombre',
                                          return_value=None):
                            yield conn

    def test_full_flow_returns_expected_keys(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle', return_value=None):
            with patch("app.services.chat_orchestrator.predict_with_confidence",
                       return_value=("CONSULTAR_FAQ", 0.85)):
                with patch("app.services.chat_orchestrator.dispatch",
                           return_value={
                               "respuesta": "Respuesta de prueba",
                               "tipo_resolucion": "estatica",
                           }):
                    with patch("app.services.chat_orchestrator.validar_respuesta",
                               return_value=(True, None)):
                        result = process_message(mock_conn, 1, "Hola")

        assert "respuesta" in result
        assert "intencion" in result
        assert "confianza" in result
        assert "tipo_resolucion" in result
        assert "id_conversacion" in result
        assert "id_mensaje" in result
        assert result["respuesta"] == "Respuesta de prueba"
        assert result["intencion"] == "CONSULTAR_FAQ"
        assert result["confianza"] == 0.85

    def test_validation_failure_triggers_pendiente(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle', return_value=None):
            with patch("app.services.chat_orchestrator.predict_with_confidence",
                       return_value=("CONSULTAR_FAQ", 0.85)):
                with patch("app.services.chat_orchestrator.dispatch",
                           return_value={
                               "respuesta": "correo: test@test.com",
                               "tipo_resolucion": "estatica",
                           }):
                    with patch("app.services.chat_orchestrator.validar_respuesta",
                               return_value=(False, "Contiene email")):
                        with patch.object(queries, 'insert_pendiente',
                                          return_value=1):
                            result = process_message(mock_conn, 1, "Hola")

        assert "administrador revisará" in result["respuesta"]
        assert result["tipo_resolucion"] == "sin_respuesta"

    def test_prediction_error_uses_sin_intencion(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle', return_value=None):
            with patch("app.services.chat_orchestrator.predict_with_confidence",
                       side_effect=Exception("Modelo roto")):
                with patch("app.services.chat_orchestrator.dispatch",
                           return_value={
                               "respuesta": "Fallback response",
                               "tipo_resolucion": "sin_respuesta",
                           }):
                    with patch("app.services.chat_orchestrator.validar_respuesta",
                               return_value=(True, None)):
                        result = process_message(mock_conn, 1, "Hola")

        assert result["intencion"] == "SIN_INTENCION"
        assert result["confianza"] == 0.0

    def test_model_not_found_uses_sin_intencion(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle', return_value=None):
            with patch("app.services.chat_orchestrator.predict_with_confidence",
                       side_effect=FileNotFoundError("No existe modelo")):
                with patch("app.services.chat_orchestrator.dispatch",
                           return_value={
                               "respuesta": "Sin modelo response",
                               "tipo_resolucion": "sin_respuesta",
                           }):
                    with patch("app.services.chat_orchestrator.validar_respuesta",
                               return_value=(True, None)):
                        result = process_message(mock_conn, 1, "Hola")

        assert result["intencion"] == "SIN_INTENCION"
        assert result["confianza"] == 0.0

    def test_creates_new_conversation_when_none_provided(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle', return_value=None):
            with patch("app.services.chat_orchestrator.predict_with_confidence",
                       return_value=("SIN_INTENCION", 0.0)):
                with patch("app.services.chat_orchestrator.dispatch",
                           return_value={
                               "respuesta": "Respuesta",
                               "tipo_resolucion": "sin_respuesta",
                           }):
                    with patch("app.services.chat_orchestrator.validar_respuesta",
                               return_value=(True, None)):
                        result = process_message(mock_conn, 1, "Hola")

        assert result["id_conversacion"] == 1

    def test_rag_first_responds_before_ml(self, mock_conn):
        with patch.object(RAGFirstHandler, 'handle',
                          return_value={
                              "respuesta": "Respuesta del documento",
                              "tipo_resolucion": "dinamica",
                          }):
            with patch("app.services.chat_orchestrator.validar_respuesta",
                       return_value=(True, None)):
                result = process_message(mock_conn, 1, "consulta documental")

        assert result["respuesta"] == "Respuesta del documento"
        assert result["intencion"] == "CONSULTA_DOCUMENTAL"
        assert result["confianza"] == 1.0
        assert result["tipo_resolucion"] == "dinamica"

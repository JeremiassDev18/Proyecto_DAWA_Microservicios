"""
Integration tests for microservice clients.

Requires all Docker services running:
  docker compose up -d

Run with: pytest -v tests/test_integration_microservices.py
"""

import httpx
import pytest

from app.services.microservice_client import (
    AdminClient,
    SecurityClient,
    TutoriasClient,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def admin_token() -> str:
    resp = httpx.post(
        "http://localhost:5001/login",
        json={"email": "admin@chatbot.com", "password": "admin123"},
        timeout=10,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return data["access_token"]


class TestSecurityClientIntegration:
    def setup_method(self):
        self.client = SecurityClient()

    def test_validar_token_valido(self, admin_token):
        result = self.client.validar_token(admin_token)
        assert result is not None
        assert result["valido"] is True
        assert result["usuario_id"] == 1
        assert result["tipo"] == "admin"

    def test_validar_token_invalido(self):
        result = self.client.validar_token("token-falso-invalido")
        assert result is None

    def test_get_usuario_admin(self, admin_token):
        result = self.client.get_usuario(1)
        assert result is not None
        assert isinstance(result, dict)

    def test_get_usuario_inexistente(self):
        result = self.client.get_usuario(99999)
        assert result is None


class TestAdminClientIntegration:
    def setup_method(self):
        self.client = AdminClient()

    def test_listar_docentes(self):
        result = self.client.buscar_docentes()
        assert isinstance(result, list)

    def test_get_asignaturas(self):
        result = self.client.get_asignaturas()
        assert isinstance(result, list)

    def test_get_carreras(self):
        result = self.client.get_carreras()
        assert isinstance(result, list)


class TestTutoriasClientIntegration:
    def setup_method(self):
        self.client = TutoriasClient()

    def test_registrar_solicitud(self):
        result = self.client.registrar_solicitud(
            estudiante_id=1,
            tema="Consulta sobre álgebra",
            asignatura_id=1,
            periodo_id=1,
        )
        assert result is not None, (
            "No se recibió respuesta de tutorias-service. "
            "Verifica que RabbitMQ y tutorias-service estén corriendo."
        )

    def test_consultar_mis_tutorias(self):
        result = self.client.consultar_mis_tutorias(1)
        assert isinstance(result, list)

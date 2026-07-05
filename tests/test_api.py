from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_db_and_ml():
    mock_conn = MagicMock()
    patchers = [
        patch("app.db.postgres_client.init_pool"),
        patch("app.db.postgres_client.close_pool"),
        patch("app.db.postgres_client.get_connection", return_value=mock_conn),
        patch("app.db.postgres_client.release_connection"),
        patch("app.core.dependencies.get_connection", return_value=mock_conn),
        patch("app.core.dependencies.release_connection"),
        patch("app.api.router_chat.process_message",
              return_value={
                  "respuesta": "Respuesta mock",
                  "intencion": "SIN_INTENCION",
                  "confianza": 0.0,
                  "tipo_resolucion": "pendiente",
                  "id_conversacion": 1,
                  "id_mensaje": 1,
              }),
        patch("app.api.router_chat.db_queries.insert_feedback",
              return_value=1),
        patch("app.api.router_admin.db_queries.get_pendientes",
              return_value=[]),
        patch("app.api.router_admin.db_queries.get_predicciones",
              return_value=[]),
        patch("app.api.router_admin.db_queries.get_modelo_activo",
              return_value=None),
    ]
    for p in patchers:
        p.start()
    yield
    for p in patchers:
        p.stop()


@pytest.fixture
def client():
    with patch("app.db.postgres_client.init_pool"):
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_sin_modelo(client):
    resp = client.post("/api/v1/chat", json={
        "usuario_id": 1,
        "mensaje": "Hola",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["respuesta"] == "Respuesta mock"
    assert data["intencion"] == "SIN_INTENCION"


def test_chat_mensaje_vacio(client):
    resp = client.post("/api/v1/chat", json={
        "usuario_id": 1,
        "mensaje": "",
    })
    assert resp.status_code == 422


def test_feedback(client):
    resp = client.post("/api/v1/chat/feedback", json={
        "id_mensaje": 1,
        "util": True,
    })
    assert resp.status_code == 200
    assert resp.json()["mensaje"] == "Feedback registrado"


def test_pending(client):
    resp = client.get("/api/v1/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert "pendientes" in data
    assert "total" in data
    assert data["pendientes"] == []


def test_metrics_model(client):
    resp = client.get("/api/v1/metrics/model")
    assert resp.status_code == 200
    assert resp.json() is None


def test_metrics_predictions(client):
    resp = client.get("/api/v1/metrics/predictions")
    assert resp.status_code == 200
    assert resp.json() == []

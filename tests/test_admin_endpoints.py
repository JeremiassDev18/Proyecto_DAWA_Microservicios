from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_db():
    mock_conn = MagicMock()
    patchers = [
        patch("app.db.postgres_client.init_pool"),
        patch("app.db.postgres_client.close_pool"),
        patch("app.db.postgres_client.get_connection", return_value=mock_conn),
        patch("app.db.postgres_client.release_connection"),
        patch("app.core.dependencies.get_connection", return_value=mock_conn),
        patch("app.core.dependencies.release_connection"),
        patch(
            "app.controllers.dataset_controller.generate_embedding",
            return_value=[0.1] * 384,
        ),
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


_NOW = datetime.now()

_PENDING_ROW = (1, "Necesito ayuda", False, _NOW)


class TestConvertPending:
    def test_convert_ok(self, client):
        dataset_row = {
            "id": 10, "texto": "Necesito ayuda", "id_intencion": 1,
            "intencion": "SOLICITAR_TUTORIA", "validado": False,
            "origen": "manual", "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        validated_row = {**dataset_row, "validado": True}

        with (
            patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                  return_value=_PENDING_ROW),
            patch("app.api.router_admin.create_dataset",
                  return_value={**dataset_row, "id": 10, "validado": False}),
            patch("app.controllers.dataset_controller.validate_dataset",
                  return_value=validated_row),
            patch("app.api.router_admin.db_queries.marcar_pendiente_resuelta"),
        ):
            resp = client.post("/api/v1/pending/1/convert", json={
                "id_intencion": 1,
                "validar": True,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["id_pendiente"] == 1
        assert data["id_dataset"] == 10
        assert data["dataset"]["validado"] is True

    def test_convert_sin_validar(self, client):
        dataset_row = {
            "id": 10, "texto": "Necesito ayuda", "id_intencion": 1,
            "intencion": "SOLICITAR_TUTORIA", "validado": False,
            "origen": "manual", "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }

        with (
            patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                  return_value=_PENDING_ROW),
            patch("app.api.router_admin.create_dataset",
                  return_value=dataset_row),
            patch("app.api.router_admin.db_queries.marcar_pendiente_resuelta"),
        ):
            resp = client.post("/api/v1/pending/1/convert", json={
                "id_intencion": 1,
                "validar": False,
            })
        assert resp.status_code == 200
        assert resp.json()["dataset"]["validado"] is False

    def test_convert_not_found(self, client):
        with patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                    return_value=None):
            resp = client.post("/api/v1/pending/999/convert", json={
                "id_intencion": 1,
            })
        assert resp.status_code == 404

    def test_convert_already_resolved(self, client):
        resolved = (1, "Necesito ayuda", True, _NOW)
        with patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                    return_value=resolved):
            resp = client.post("/api/v1/pending/1/convert", json={
                "id_intencion": 1,
            })
        assert resp.status_code == 400


class TestResolvePending:
    def test_resolve_ok(self, client):
        with (
            patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                  return_value=_PENDING_ROW),
            patch("app.api.router_admin.db_queries.resolver_pendiente"),
        ):
            resp = client.patch("/api/v1/pending/1/resolver")
        assert resp.status_code == 200
        assert resp.json()["mensaje"] == "Pendiente resuelto"

    def test_resolve_not_found(self, client):
        with patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                    return_value=None):
            resp = client.patch("/api/v1/pending/999/resolver")
        assert resp.status_code == 404

    def test_resolve_already_resolved(self, client):
        resolved = (1, "Necesito ayuda", True, _NOW)
        with patch("app.api.router_admin.db_queries.get_pendiente_by_id",
                    return_value=resolved):
            resp = client.patch("/api/v1/pending/1/resolver")
        assert resp.status_code == 400

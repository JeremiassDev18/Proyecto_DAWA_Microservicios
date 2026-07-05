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


def _fake_row(id=1, texto="Hola", id_intencion=1, intencion="SALUDO",
              validado=True, origen="manual", activo=True):
    return (id, texto, id_intencion, intencion, validado,
            origen, activo, _NOW, _NOW)


class TestListDataset:
    def test_list_empty(self, client):
        with patch("app.api.router_dataset.ctrl.list_dataset", return_value=[]):
            resp = client.get("/api/v1/dataset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_with_items(self, client):
        row = _fake_row()
        items = [{
            "id": row[0], "texto": row[1], "id_intencion": row[2],
            "intencion": row[3], "validado": row[4], "origen": row[5],
            "activo": row[6], "creado_en": row[7].isoformat(),
            "actualizado_en": row[8].isoformat(),
        }]
        with patch("app.api.router_dataset.ctrl.list_dataset", return_value=items):
            resp = client.get("/api/v1/dataset")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["texto"] == "Hola"
        assert data["items"][0]["intencion"] == "SALUDO"

    def test_list_with_query(self, client):
        with patch("app.api.router_dataset.ctrl.list_dataset", return_value=[]):
            resp = client.get("/api/v1/dataset?query=tutor")
        assert resp.status_code == 200

    def test_list_with_intencion_filter(self, client):
        with patch("app.api.router_dataset.ctrl.list_dataset", return_value=[]):
            resp = client.get("/api/v1/dataset?intencion=SALUDO")
        assert resp.status_code == 200


class TestCreateDataset:
    def test_create_ok(self, client):
        row = _fake_row(id=99, texto="Nuevo ejemplo", id_intencion=2, intencion="CONSULTAR")
        expected = {
            "id": 99, "texto": "Nuevo ejemplo", "id_intencion": 2,
            "intencion": "CONSULTAR", "validado": False, "origen": "manual",
            "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        with patch("app.api.router_dataset.ctrl.create_dataset", return_value=expected):
            resp = client.post("/api/v1/dataset", json={
                "texto": "Nuevo ejemplo",
                "id_intencion": 2,
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 99
        assert data["texto"] == "Nuevo ejemplo"

    def test_create_empty_texto(self, client):
        resp = client.post("/api/v1/dataset", json={
            "texto": "",
            "id_intencion": 1,
        })
        assert resp.status_code == 422


class TestUpdateDataset:
    def test_update_ok(self, client):
        row = _fake_row(id=1, texto="Editado", id_intencion=2, intencion="CONSULTAR")
        expected = {
            "id": 1, "texto": "Editado", "id_intencion": 2,
            "intencion": "CONSULTAR", "validado": True, "origen": "manual",
            "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        with patch("app.api.router_dataset.ctrl.update_dataset", return_value=expected):
            resp = client.put("/api/v1/dataset/1", json={
                "texto": "Editado",
                "id_intencion": 2,
            })
        assert resp.status_code == 200
        assert resp.json()["texto"] == "Editado"

    def test_update_not_found(self, client):
        with patch("app.api.router_dataset.ctrl.update_dataset", return_value=None):
            resp = client.put("/api/v1/dataset/999", json={"texto": "Nope"})
        assert resp.status_code == 404


class TestDeleteDataset:
    def test_delete_ok(self, client):
        with patch("app.api.router_dataset.ctrl.delete_dataset", return_value=True):
            resp = client.delete("/api/v1/dataset/1")
        assert resp.status_code == 200
        assert resp.json()["mensaje"] == "Dataset desactivado"

    def test_delete_not_found(self, client):
        with patch("app.api.router_dataset.ctrl.delete_dataset", return_value=False):
            resp = client.delete("/api/v1/dataset/999")
        assert resp.status_code == 404


class TestValidateDataset:
    def test_validate_ok(self, client):
        row = _fake_row(id=1, texto="Validado", validado=True)
        expected = {
            "id": 1, "texto": "Validado", "id_intencion": 1,
            "intencion": "SALUDO", "validado": True, "origen": "manual",
            "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        with patch("app.api.router_dataset.ctrl.validate_dataset", return_value=expected):
            resp = client.patch("/api/v1/dataset/1/validar")
        assert resp.status_code == 200
        assert resp.json()["validado"] is True

    def test_validate_not_found(self, client):
        with patch("app.api.router_dataset.ctrl.validate_dataset", return_value=None):
            resp = client.patch("/api/v1/dataset/999/validar")
        assert resp.status_code == 404

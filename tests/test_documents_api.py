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
            "app.controllers.document_controller.generate_embedding",
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


_AUTH_HEADER = {"Authorization": "Bearer internal_secret_token_xyz"}
_NOW = datetime.now()


def _fake_doc_row(id=1, titulo="Reglamento", contenido="Texto",
                   categoria="reglamento", fuente="test.pdf",
                   archivo_pdf="", activo=True):
    return (id, titulo, contenido, categoria, fuente, archivo_pdf,
            activo, _NOW, _NOW)


class TestListDocuments:
    def test_list_empty(self, client):
        with patch("app.api.router_documents.ctrl.list_documents", return_value=[]):
            resp = client.get("/api/v1/documents", headers=_AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_with_items(self, client):
        row = _fake_doc_row()
        items = [{
            "id": row[0], "titulo": row[1], "contenido": row[2],
            "categoria": row[3], "fuente": row[4], "archivo_pdf": row[5],
            "activo": row[6],
            "creado_en": row[7].isoformat(),
            "actualizado_en": row[8].isoformat(),
        }]
        with patch("app.api.router_documents.ctrl.list_documents", return_value=items):
            resp = client.get("/api/v1/documents", headers=_AUTH_HEADER)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1
        assert resp.json()["items"][0]["titulo"] == "Reglamento"


class TestCreateDocument:
    def test_create_ok(self, client):
        row = _fake_doc_row(id=99, titulo="Nuevo documento")
        expected = {
            "id": 99, "titulo": "Nuevo documento", "contenido": "Texto",
            "categoria": "reglamento", "fuente": "test.pdf",
            "archivo_pdf": "",
            "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        with patch("app.api.router_documents.ctrl.create_document", return_value=expected):
            resp = client.post("/api/v1/documents", json={
                "titulo": "Nuevo documento",
                "contenido": "Texto del documento",
            }, headers=_AUTH_HEADER)
        assert resp.status_code == 201
        assert resp.json()["id"] == 99
        assert resp.json()["titulo"] == "Nuevo documento"

    def test_create_unauthorized(self, client):
        resp = client.post("/api/v1/documents", json={
            "titulo": "Test",
            "contenido": "Contenido",
        })
        assert resp.status_code == 401


class TestUpdateDocument:
    def test_update_ok(self, client):
        expected = {
            "id": 1, "titulo": "Editado", "contenido": "Nuevo texto",
            "categoria": "faq", "fuente": "", "archivo_pdf": "",
            "activo": True,
            "creado_en": _NOW.isoformat(),
            "actualizado_en": _NOW.isoformat(),
        }
        with patch("app.api.router_documents.ctrl.update_document", return_value=expected):
            resp = client.put("/api/v1/documents/1", json={
                "titulo": "Editado",
                "contenido": "Nuevo texto",
            }, headers=_AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Editado"

    def test_update_not_found(self, client):
        with patch("app.api.router_documents.ctrl.update_document", return_value=None):
            resp = client.put("/api/v1/documents/999", json={
                "titulo": "Nope",
            }, headers=_AUTH_HEADER)
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_delete_ok(self, client):
        with patch("app.api.router_documents.ctrl.delete_document", return_value=True):
            resp = client.delete("/api/v1/documents/1", headers=_AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["mensaje"] == "Documento desactivado"

    def test_delete_not_found(self, client):
        with patch("app.api.router_documents.ctrl.delete_document", return_value=False):
            resp = client.delete("/api/v1/documents/999", headers=_AUTH_HEADER)
        assert resp.status_code == 404

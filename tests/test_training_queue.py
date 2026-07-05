from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.training_queue import enqueue_training, get_task_status


class TestTrainingQueue:
    def test_enqueue_and_status(self):
        task_id = enqueue_training(["hola"], ["SALUDO"])
        assert task_id > 0
        status = get_task_status(task_id)
        assert status is not None
        assert status["status"] == "pending"

    def test_status_inexistente(self):
        assert get_task_status(9999) is None


class TestTrainingEndpoint:
    @pytest.fixture(autouse=True)
    def _mock_db(self):
        mock_conn = MagicMock()
        patchers = [
            patch("app.db.postgres_client.init_pool"),
            patch("app.db.postgres_client.close_pool"),
            patch("app.db.postgres_client.get_connection", return_value=mock_conn),
            patch("app.db.postgres_client.release_connection"),
            patch("app.core.dependencies.get_connection", return_value=mock_conn),
            patch("app.core.dependencies.release_connection"),
        ]
        for p in patchers:
            p.start()
        yield
        for p in patchers:
            p.stop()

    @pytest.fixture
    def client(self):
        with patch("app.db.postgres_client.init_pool"):
            from app.main import app
            with TestClient(app) as c:
                yield c

    def test_train_no_data(self, client):
        with patch("app.api.router_admin.get_training_data",
                   return_value=([], [])):
            resp = client.post("/api/v1/train")
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "no_data"

    def test_train_enqueued(self, client):
        with (
            patch("app.api.router_admin.get_training_data",
                  return_value=(["hola"], ["SALUDO"])),
            patch("app.api.router_admin.enqueue_training",
                  return_value=42),
        ):
            resp = client.post("/api/v1/train")
        assert resp.status_code == 202
        data = resp.json()
        assert data["task_id"] == 42
        assert data["status"] == "pending"

    def test_training_status_ok(self, client):
        from app.services.training_queue import _tasks, _lock
        with _lock:
            _tasks[1] = {
                "status": "completed",
                "modelo_version": "setfit-v3",
                "metricas": {"accuracy": 0.95},
                "completed_at": None,
                "error": None,
            }
        resp = client.get("/api/v1/train/status/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == 1
        assert data["status"] == "completed"
        assert data["modelo_version"] == "setfit-v3"

    def test_training_status_not_found(self, client):
        resp = client.get("/api/v1/train/status/9999")
        assert resp.status_code == 404

# AGENTS.md — chatbot-service

## Project

FastAPI chatbot microservice (port 5004) with ML intent classification (SetFit),
hybrid semantic+trigram search (pgvector + pg_trgm), and RAG document retrieval.

Entrypoint: `app/main.py` — registers 4 routers under `/api/v1`.

## Architecture

```
POST /api/v1/chat            → router_chat.py → chat_orchestrator.py
POST /api/v1/train           → router_admin.py → training_queue.py (background thread)
CRUD /api/v1/dataset         → router_dataset.py → dataset_controller.py
CRUD /api/v1/documents       → router_documents.py → document_controller.py
GET  /api/v1/metrics/usage   → router_admin.py → aggregated metrics (AIA-R12)
GET  /api/v1/summary/...     → router_admin.py → conversation summaries (AIA-R04/R05)
```

- All routers declare `conn=Depends(get_db)` which yields a psycopg2 connection from `ThreadedConnectionPool`.
- Training runs in a daemon thread via `training_queue.py` — in-memory `_tasks` dict (lost on restart).
- ML: `setfit_trainer.py` trains/caches model in `data/setfit_model/`; `vectorizer.py` generates 384‑dim embeddings via `all-MiniLM-L6-v2` (lazy‑loaded singleton).
- Microservice clients (`microservice_client.py`) are mocks but support HTTP mode via `MICROSOFT_HTTP_ENABLED=1`.
- Auth: `app/core/auth.py` — token‑based (Bearer header). `requerir_admin` dependency guards admin endpoints.
- Response validation: `app/services/response_validator.py` filters sensitive data (emails, DNI) and checks institutional scope (AIA-R11).
- Escalation: orchestrator uses `CONFIDENCE_THRESHOLD` (default 0.75) from config; low‑confidence messages are escalated with reason (AIA-R07).

## DB

PostgreSQL 16 with `pgvector` + `pg_trgm` extensions.
- Port: **5435** (not 5432)
- Schema in `init.sql` — also seeds intents, dataset examples, responses, and documents.
- Connection pool: `psycopg2.pool.ThreadedConnectionPool`, min=2, max=10.

## Commands

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5004 --reload
docker compose up --build
```

## Tests

```bash
pytest -v
```

All tests heavily mock DB (`init_pool`, `get_connection`, `release_connection`) and ML.
No real PostgreSQL or ML model needed. Admin endpoints need `Authorization: Bearer internal_secret_token_xyz`.

Standard test fixture pattern:
```python
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
    ]
    ...
```

See `tests/test_api.py`, `test_admin_endpoints.py`, `test_dataset_api.py`, `test_ml.py`,
`test_documents_api.py`, `test_auth.py`, `test_response_validator.py`.

## Scripts

```bash
python scripts/train_setfit.py       # standalone training from DB
python scripts/generate_embeddings.py
python scripts/admin_task.py
```

Scripts use `sys.path` manipulation to resolve `app` imports.

## Config

`app/core/config.py` — `pydantic-settings` reads from `.env` (which is empty; all defaults apply).
Key variables: `DB_HOST`, `DB_PORT=5435`, `MODEL_NAME=all-MiniLM-L6-v2`,
`SIMILARITY_THRESHOLD=0.25`, `VECTOR_WEIGHT=0.70`, `TRGM_WEIGHT=0.30`,
`AUTO_TRAIN=True`, `AUTO_TRAIN_THRESHOLD=100`, `CONFIDENCE_THRESHOLD=0.75`,
`ESCALATION_ENABLED=True`.

## Notable

- `setfit_manager.py` is **empty** — ignore it.
- `embedding_generator.py` is a thin re-export of `vectorizer.py`.
- Vector dimension: 384.
- Model artifacts stored at `data/setfit_model/` and `data/*.pkl`.
- No Alembic or migrations — schema is `init.sql` applied at DB container start.

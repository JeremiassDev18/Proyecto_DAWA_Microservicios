# Chatbot Service - Documentación de Arquitectura

## Visión general

Este proyecto es un microservicio de chatbot basado en FastAPI que combina:
- clasificación de intenciones con SetFit
- búsqueda híbrida semántica + trigramas en PostgreSQL
- recuperación de documentos (RAG) para respuestas basadas en contenido
- administración de datos de entrenamiento y feedback

El servicio expone endpoints REST en `/api/v1` y usa PostgreSQL con extensiones `pg_trgm` y `vector`.

## Estructura de carpetas

- `app/`
  - `main.py`: entrypoint de FastAPI, registra routers y gestiona lifecycle de la base de datos.
  - `api/`: define rutas HTTP y esquemas de respuesta.
    - `router_chat.py`: chat, feedback.
    - `router_admin.py`: entrenamiento, métricas, pendientes.
    - `router_dataset.py`: CRUD de dataset.
  - `core/`: configuración y dependencias.
    - `config.py`: carga settings desde `.env` y define `DATABASE_URL`.
    - `dependencies.py`: dependencia para obtener conexión DB.
  - `db/`: acceso a datos.
    - `postgres_client.py`: pool de conexiones `psycopg2` y registro de vectores.
    - `queries.py`: SQL crudo para todas las entidades.
    - `dataset_repository.py`: capa de persistencia de datasets.
    - `training_repository.py`: lógica de entrenamiento/cola de reentrenamiento.
  - `ml/`: componentes de ML.
    - `vectorizer.py`: generación de embeddings con `sentence-transformers`.
    - `setfit_trainer.py`: entrenamiento y carga del modelo SetFit.
    - `predictor.py`: inferencia de intención y confianza.
  - `services/`: orquestación de respuesta.
    - `chat_orchestrator.py`: flujo principal de procesamiento de mensajes.
    - `microservice_client.py`: emulación/resolución de intenciones externas.
    - `rag_service.py`: búsqueda de documentos y creación de contexto.
  - `schemas/`: modelos Pydantic para request/response.
  - `utils/`: utilidades generales.
    - `logger.py`: logger simple.

- `data/`
  - `setfit_model/`: carpeta de modelo SetFit generado en tiempo de entrenamiento.

- `scripts/`
  - Secuencias para tareas externas (entrenamiento, generación de embeddings, etc.).

- `tests/`
  - Pruebas unitarias y de integración.

- `init.sql`
  - Esquema DB y datos iniciales.

- `docker-compose.yml`
  - Orquesta `chatbot-db` y `chatbot-service`.

- `Dockerfile`
  - Construye la imagen del microservicio.

## Flujo de petición HTTP (Chat request)

1. El cliente envía `POST /api/v1/chat` con JSON `{ usuario_id, mensaje, nombre, id_conversacion? }`.
2. `app/main.py` carga los routers y `app/core/dependencies.py` obtiene una conexión DB.
3. `router_chat.py` recibe la petición y llama a `process_message` en `app/services/chat_orchestrator.py`.
4. `chat_orchestrator.py`:
   - asegura una conversación activa (`chatbot_conversacion`).
   - guarda el mensaje del usuario en `chatbot_mensaje`.
   - predice intención usando `app/ml/predictor.py`.
   - guarda la predicción en `chatbot_prediccion`.
   - determina tipo de resolución:
     - intentos de flujo externo (`EXTERNAL_INTENTS`) con `microservice_client.py`
     - respuesta directa por intención con `chatbot_respuesta`
     - búsqueda híbrida semántica + trigramas en `queries.search_hybrid`
     - fallback RAG en `rag_service.respond_with_documents`
     - si nada resuelve, registra `chatbot_pregunta_pendiente`.
   - guarda la respuesta del bot en `chatbot_mensaje`.
5. La respuesta retorna al cliente con `ChatResponse`.

## Conexión DB → Backend

- `app/db/postgres_client.py` crea un pool `ThreadedConnectionPool` usando `settings.DATABASE_URL`.
- `app/core/config.py` lee variables de entorno y construye la URL de PostgreSQL.
- `app/core/dependencies.py` expone `get_db()` para inyectar la conexión en routers.
- Los repositorios y servicios usan `queries.py` para ejecutar SQL dentro de `with conn.cursor():`.
- El backend gestiona transacciones explícitas con `conn.commit()` tras operaciones de escritura.

## Conexión Backend → ML

- `app/ml/vectorizer.py` usa `SentenceTransformer(settings.MODEL_NAME)` y `clean_text` para generar embeddings.
- `app/ml/setfit_trainer.py` usa SetFit para:
  - `train_model(texts, labels)` entrenar un modelo con dataset validado.
  - `load_model()` cargar el modelo almacenado en `data/setfit_model`.
  - `evaluate_model()` recalcula métricas.
- `app/ml/predictor.py` abstrae inferencia:
  - `predict_intent(text)` devuelve la intención.
  - `predict_with_confidence(text)` devuelve la intención y score de probabilidad.
- `chat_orchestrator.py` llama a `predict_with_confidence()` en cada mensaje para obtener la intención de SetFit.

## Lógica de búsqueda híbrida y RAG

- `queries.search_hybrid()` combina:
  - similitud de embedding vectorial `1 - (embedding <=> query)`.
  - similitud de texto trigram `similarity(cd.texto, query)`.
- Se aplican pesos `VECTOR_WEIGHT` y `TRGM_WEIGHT` desde configuración.
- Si la confianza de SetFit es baja, el servicio intenta primero la búsqueda híbrida.
- Si aún no hay respuesta, `rag_service.py` busca documentos en `documento_base` con embeddings.
- RAG devuelve contexto textual si la similitud del top-k supera `RAG_SIMILARITY_THRESHOLD`.

## Base de datos y tablas clave

Principales tablas utilizadas por el backend:

- `chatbot_intencion`: intenciones ML.
- `chatbot_dataset`: ejemplos de entrenamiento con embeddings.
- `chatbot_respuesta`: respuestas asociadas a intenciones.
- `chatbot_conversacion`: conversaciones de usuario.
- `chatbot_mensaje`: mensajes tanto usuario como bot.
- `chatbot_prediccion`: historial de predicciones ML.
- `chatbot_pregunta_pendiente`: preguntas que no pudieron resolverse.
- `entrenamiento_pendiente`: cola para reentrenar modelo.
- `modelo_ml` y `chatbot_training`: versiones y métricas de modelo.
- `documento_base`: corpus de documentos para RAG.

## Entrenamiento y reentrenamiento

- `router_admin.py` ofrece `POST /api/v1/train`.
- Cuando se ejecuta, `get_training_data()` carga ejemplos validados desde `chatbot_dataset`.
- `train_model()` entrena SetFit y guarda el modelo en `data/setfit_model`.
- `training_repository.py` registra versión y métricas en DB.
- La lógica de `auto_train_if_needed()` puede dispararse cuando se validan nuevos datos.

## Dockerización y despliegue

- `Dockerfile` construye la app con Python 3.11 y expone el puerto `5004`.
- `docker-compose.yml` define:
  - `chatbot-db`: PostgreSQL 16 en `5435:5432`.
  - `chatbot-service`: servicio Python que depende de la DB.
- Variables de entorno para la app se configuran en `docker-compose.yml`.

### Nota importante

El `docker-compose.yml` actual monta `./database/init.sql`, pero en el repositorio el script de inicialización está en `./init.sql`.
Si usas Docker Compose, actualiza la ruta a `./init.sql:/docker-entrypoint-initdb.d/init.sql:ro` o mueve el archivo a `database/init.sql`.

## ¿Usa SetFit?

Sí. El proyecto usa SetFit en `app/ml/setfit_trainer.py` y `app/ml/predictor.py` para clasificación de intenciones.
El servicio no usa un modelo de lenguaje grande para clasificación; usa SetFit sobre embeddings y texto.

## Flujo de datos completo

1. Petición HTTP llega a FastAPI (`app/main.py`).
2. El router específico maneja la ruta y obtiene conexión DB.
3. Si es una petición de chat:
   - se guarda el mensaje del usuario
   - se predice intención con SetFit
   - se intenta resolver con respuestas estáticas, búsqueda híbrida, RAG o intentos externos
   - se guarda la respuesta del bot y se devuelve JSON.
4. Si es una petición de dataset o administración:
   - se realizan operaciones CRUD o entrenamiento usando repositorios y queries.
5. Los embeddings se generan con `sentence-transformers` y se almacenan en PostgreSQL usando `vector`.

## Cambios mínimos para migrar a otra librería de ML

Si quieres cambiar la librería SetFit, ajusta principalmente:
- `app/ml/setfit_trainer.py`: reemplaza entrenamiento/carga por la nueva API.
- `app/ml/predictor.py`: reemplaza `model([text])` y `predict_proba` por la nueva inferencia.
- `requirements.txt`: quita `setfit_trainer` y añade la nueva dependencia.
- `app/services/chat_orchestrator.py`: si cambia la forma de obtener `confidence`, adapta el control de umbrales.

## Resumen rápido

- Backend: `FastAPI` + `psycopg2` + `SQL`.
- ML: `SetFit` para clasificación de intención + `sentence-transformers` para embeddings.
- DB: PostgreSQL con `pgvector`, `pg_trgm`.
- Search: combinación de vectorial y trigram para respuestas similares.
- RAG: búsqueda de documentos cuando la clasificación y la búsqueda híbrida fallan.

---

Documentación generada para facilitar la comprensión de la arquitectura y las conexiones entre el backend, la base de datos y el ML.
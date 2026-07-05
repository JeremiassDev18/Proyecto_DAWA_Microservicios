# Contexto completo del proyecto - Chatbot Service

## 1. Resumen ejecutivo

Este repositorio contiene un microservicio FastAPI para un agente de inteligencia artificial orientado a tutorías académicas. El servicio permite:

- atender consultas frecuentes de estudiantes,
- clasificar intenciones con ML,
- buscar respuestas mediante una mezcla de coincidencias semánticas y textuales,
- recuperar documentos institucionales con RAG,
- administrar datasets, documentos y métricas,
- registrar conversaciones, predicciones y feedback.

El objetivo principal no es reemplazar al docente, sino actuar como apoyo inicial, orientación automatizada y canal de escalamiento controlado.

---

## 2. Propósito de negocio

El sistema está pensado para ser el primer punto de contacto entre un estudiante y el proceso de tutorías. Su rol es:

- responder preguntas frecuentes sobre procesos, horarios, requisitos y asuntos académicos básicos,
- clasificar solicitudes según tema, asignatura o urgencia,
- sugerir docentes o acciones de apoyo cuando la intención es clara,
- escalar casos que no puedan resolverse con seguridad a personal humano,
- mantener trazabilidad de interacciones por auditoría y mejora continua.

Las respuestas deben basarse únicamente en información institucional validada y no deben exponer datos sensibles ni salirse del alcance del sistema.

---

## 3. Stack tecnológico

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- psycopg2-binary
- Pydantic y pydantic-settings
- python-multipart

### Base de datos
- PostgreSQL 16
- Extensiones: pg_trgm y vector (pgvector)

### ML
- SetFit
- sentence-transformers
- transformers
- torch
- scikit-learn
- datasets

### Pruebas
- pytest
- pytest-asyncio
- httpx

---

## 4. Estructura del proyecto

### Raíz del proyecto
- [AGENTS.md](AGENTS.md): guía operativa y contexto para el desarrollo del proyecto.
- [Alcance.md](Alcance.md): requisitos funcionales y alcance del microservicio.
- [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md): documentación técnica general.
- [init.sql](init.sql): esquema SQL inicial y datos base.
- [docker-compose.yml](docker-compose.yml): orquestación de la base de datos y del servicio.
- [Dockerfile](Dockerfile): imagen de la app.
- [requirements.txt](requirements.txt): dependencias del proyecto.

### Aplicación principal
- [app/main.py](app/main.py): punto de entrada de FastAPI, registra routers y gestiona inicio/cierre.

### Routers
- [app/api/router_chat.py](app/api/router_chat.py): chat principal, feedback y manejo de mensajes.
- [app/api/router_admin.py](app/api/router_admin.py): entrenamiento, métricas, pendientes y resúmenes.
- [app/api/router_dataset.py](app/api/router_dataset.py): CRUD del dataset.
- [app/api/router_documents.py](app/api/router_documents.py): CRUD de documentos de conocimiento.

### Core y dependencias
- [app/core/config.py](app/core/config.py): configuración con variables de entorno y construcción de DATABASE_URL.
- [app/core/dependencies.py](app/core/dependencies.py): inyección de conexión a la base de datos.
- [app/core/auth.py](app/core/auth.py): autenticación y autorización para endpoints administrativos.

### Base de datos y repositorios
- [app/db/postgres_client.py](app/db/postgres_client.py): pool de conexiones PostgreSQL.
- [app/db/queries.py](app/db/queries.py): consultas SQL del negocio.
- [app/db/dataset_repository.py](app/db/dataset_repository.py): lógica de persistencia del dataset.
- [app/db/training_repository.py](app/db/training_repository.py): registro de modelos y métricas.

### Machine Learning
- [app/ml/vectorizer.py](app/ml/vectorizer.py): generación de embeddings.
- [app/ml/setfit_trainer.py](app/ml/setfit_trainer.py): entrenamiento y carga del modelo SetFit.
- [app/ml/predictor.py](app/ml/predictor.py): inferencia de intención y confianza.
- [app/ml/text_cleaner.py](app/ml/text_cleaner.py): limpieza de texto para procesamiento.

### Servicios de negocio
- [app/services/chat_orchestrator.py](app/services/chat_orchestrator.py): orquestación completa del flujo de respuesta.
- [app/services/rag_service.py](app/services/rag_service.py): recuperación de documentos para RAG.
- [app/services/microservice_client.py](app/services/microservice_client.py): integración mock/HTTP con servicios externos.
- [app/services/response_validator.py](app/services/response_validator.py): validación de seguridad y alcance institucional.
- [app/services/training_queue.py](app/services/training_queue.py): cola de entrenamiento en segundo plano.

### Schemas y utilidades
- [app/schemas/requests.py](app/schemas/requests.py): modelos de entrada.
- [app/schemas/responses.py](app/schemas/responses.py): modelos de salida.
- [app/utils/logger.py](app/utils/logger.py): logger reutilizable.
- [app/utils/codigo_generator.py](app/utils/codigo_generator.py): generación de códigos para solicitudes.

### Datos y scripts auxiliares
- [data](data): artefactos del modelo y datos persistidos.
- [scripts](scripts): tareas de entrenamiento y generación de embeddings.
- [tests](tests): suite de pruebas del sistema.

---

## 5. Cómo funciona el sistema

### 5.1 Flujo principal de una petición de chat

1. El cliente envía una petición a [app/api/router_chat.py](app/api/router_chat.py).
2. El router obtiene una conexión DB mediante [app/core/dependencies.py](app/core/dependencies.py).
3. Se invoca [app/services/chat_orchestrator.py](app/services/chat_orchestrator.py).
4. El orquestador:
   - crea o recupera la conversación,
   - guarda el mensaje del usuario,
   - predice la intención con ML,
   - intenta responder con lógica directa, búsqueda híbrida o RAG,
   - valida la respuesta y la guarda en la base de datos.
5. Se devuelve una respuesta JSON con la intención, confianza y tipo de resolución.

### 5.2 Decisiones internas del orquestador

El flujo prioriza en este orden:

1. Intenciones de tipo externo (por ejemplo creación de solicitud, búsqueda de docente, etc.).
2. Respuestas directas asociadas a intenciones registradas.
3. Búsqueda híbrida semántica + trigramas.
4. Búsqueda RAG sobre documentos institucionales.
5. Escalamiento a pendiente si no se encuentra una respuesta segura.

---

## 6. Endpoints principales

### Salud
- GET /health
  - Retorna estado del servicio.

### Chat
- POST /api/v1/chat
  - Envía un mensaje del usuario y obtiene una respuesta del bot.
- POST /api/v1/chat/feedback
  - Registra si la respuesta fue útil.

### Entrenamiento y administración
- POST /api/v1/train
  - Encola un entrenamiento del modelo.
- GET /api/v1/train/status/{task_id}
  - Consulta el estado del entrenamiento.
- GET /api/v1/pending
  - Lista preguntas pendientes.
- POST /api/v1/pending/{id}/convert
  - Convierte un pendiente en dataset.
- PATCH /api/v1/pending/{id}/resolver
  - Marca un pendiente como resuelto.
- GET /api/v1/metrics/usage
  - Devuelve métricas de uso.
- GET /api/v1/summary/conversations
  - Genera resúmenes de conversaciones.

### Dataset
- GET /api/v1/dataset
- POST /api/v1/dataset
- PUT /api/v1/dataset/{id}
- DELETE /api/v1/dataset/{id}
- PATCH /api/v1/dataset/{id}/validar

### Documentos base
- GET /api/v1/documents
- GET /api/v1/documents/{id}
- POST /api/v1/documents
- PUT /api/v1/documents/{id}
- DELETE /api/v1/documents/{id}

---

## 7. Base de datos y esquema

El sistema usa PostgreSQL con las extensiones pg_trgm y vector.

### Tablas clave
- chatbot_intencion: categorías o intenciones de clasificación.
- chatbot_dataset: ejemplos usados para entrenar el modelo.
- chatbot_respuesta: respuestas predefinidas asociadas a intenciones.
- chatbot_conversacion: conversaciones de usuario.
- chatbot_mensaje: mensajes de usuario y bot.
- chatbot_prediccion: historial de predicciones del modelo.
- chatbot_pregunta_pendiente: preguntas que requieren revisión humana.
- documento_base: documentos institucionales para RAG.
- chatbot_feedback: valoración de utilidad de las respuestas.
- modelo_ml y chatbot_training: control de versiones y métricas de modelos.
- entrenamiento_pendiente: cola de reentrenamiento.

### Datos iniciales
El archivo [init.sql](init.sql) crea el esquema y carga instrucciones, intenciones, ejemplos de entrenamiento y documentos base.

---

## 8. Manejo de ML y búsquedas

### 8.1 Clasificación de intenciones
- Se usa SetFit para clasificar mensajes.
- El modelo se entrena con ejemplos del dataset validado.
- El predictor devuelve intención y confianza.

### 8.2 Embeddings
- Se usan embeddings generados con sentence-transformers.
- El modelo base por defecto es all-MiniLM-L6-v2.
- La dimensión esperada es 384.

### 8.3 Búsqueda híbrida
- La búsqueda combina:
  - similitud vectorial (embedding),
  - similitud textual con trigramas.
- Se aplican pesos configurables: VECTOR_WEIGHT y TRGM_WEIGHT.

### 8.4 RAG
- Si la predicción o la búsqueda híbrida no son suficientes, el sistema busca documentos en la base de conocimiento.
- Se usa [app/services/rag_service.py](app/services/rag_service.py) para recuperar contexto relevante.

---

## 9. Seguridad, validación y alcance

### Autenticación
- Se usa autenticación por token Bearer.
- El token interno por defecto es internal_secret_token_xyz.
- Los endpoints administrativos requieren permisos de administrador.

### Validación de respuestas
- [app/services/response_validator.py](app/services/response_validator.py) bloquea respuestas que:
  - contienen datos sensibles como emails, números largos o credenciales,
  - salen del alcance institucional.

### Reglas de negocio
- El sistema debe responder solo con información institucionalmente validada.
- Las respuestas se presentan como orientación, no como decisiones académicas definitivas.
- Cuando la confianza es baja o el tema está fuera de alcance, se escala a personal humano.

---

## 10. Entrenamiento y reentrenamiento

El entrenamiento se activa por el endpoint /api/v1/train.

### Proceso
1. Se obtienen ejemplos validados desde el dataset.
2. Se encola una tarea de entrenamiento en [app/services/training_queue.py](app/services/training_queue.py).
3. El entrenamiento se ejecuta en un hilo en segundo plano.
4. Se registran métricas y versión del modelo en la base de datos.

### Nota importante
- La cola de entrenamiento se mantiene en memoria, por lo que no sobrevive a reinicios del proceso.

---

## 11. Configuración

La configuración central se encuentra en [app/core/config.py](app/core/config.py).

### Variables principales
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- SECURITY_SERVICE_URL, ADMIN_SERVICE_URL, RESERVATION_SERVICE_URL
- INTERNAL_TOKEN
- SIMILARITY_THRESHOLD
- VECTOR_WEIGHT, TRGM_WEIGHT
- CONFIDENCE_THRESHOLD
- ESCALATION_ENABLED
- AUTO_TRAIN, AUTO_TRAIN_THRESHOLD
- RAG_TOP_K, RAG_SIMILARITY_THRESHOLD

El archivo .env se usa si existe; si no, se aplican los valores por defecto.

---

## 12. Cómo correr el proyecto

### Opción local
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5004 --reload
```

### Opción con Docker
```bash
docker compose up --build
```

### Pruebas
```bash
pytest -v
```

---

## 13. Comportamiento esperado de las pruebas

Las pruebas están diseñadas para mockear la base de datos y el modelo ML. No requieren una instancia real de PostgreSQL ni un modelo entrenado para ejecutarse.

Los tests cubren:
- API general,
- endpoints administrativos,
- CRUD de dataset y documentos,
- autenticación,
- validación de respuestas,
- microservicios mock,
- ML y cola de entrenamiento.

---

## 14. Notas técnicas importantes

- El puerto de la base de datos es 5435, no 5432.
- El servicio expone el backend en el puerto 5004.
- No hay migraciones Alembic; el esquema se crea desde [init.sql](init.sql).
- El archivo [app/ml/setfit_manager.py](app/ml/setfit_manager.py) está vacío y no se usa actualmente.
- [app/ml/embedding_generator.py](app/ml/embedding_generator.py) es un re-export de la lógica de vectorización.
- El modelo y artefactos se almacenan en la carpeta [data](data).

---

## 15. Recomendaciones para trabajar en este proyecto

Si vas a modificar el comportamiento del microservicio, empieza por:

1. [app/services/chat_orchestrator.py](app/services/chat_orchestrator.py): cambia el flujo principal de respuesta.
2. [app/ml/predictor.py](app/ml/predictor.py) y [app/ml/setfit_trainer.py](app/ml/setfit_trainer.py): ajusta clasificación y entrenamiento.
3. [app/db/queries.py](app/db/queries.py): adapta la lógica de acceso a datos.
4. [app/services/response_validator.py](app/services/response_validator.py): modifica validaciones si cambian las reglas de seguridad.
5. [init.sql](init.sql): actualiza esquema si cambian tablas o campos.

---

## 16. Resumen corto para nuevos desarrolladores

- Backend: FastAPI + PostgreSQL + SQL.
- ML: SetFit para clasificación y embeddings para búsqueda semántica.
- Búsqueda: combinación de vectorial y trigramas.
- RAG: recuperación de documentos institucionales para responder con contexto.
- Seguridad: validación de contenido, alcance institucional y control de acceso para administradores.
- Operación: el sistema soporta chat, entrenamiento, métricas, dataset, documentos y escalamiento.

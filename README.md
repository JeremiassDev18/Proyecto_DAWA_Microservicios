# TutorBot AI — Sistema de Gestión de Tutorías Académicas

Sistema multi-servicio para la gestión de tutorías académicas con agente conversacional
inteligente basado en LLM local (Qwen 2.5 3B vía Ollama).

---

## Arquitectura General

```
┌───────────────┐     ┌───────────────────────────────────────────────────────────────┐
│   Frontend    │     │                    API Gateway (nginx :8080)                   │
│  (Next.js)    │────▶│  /security/* → security-service:5001                          │
│  :3008        │     │  /administracion/* → administration-service:5002              │
│               │     │  /tutorias/* → tutorias-service:5003                          │
│               │     │  /chatbot/* → chatbot-service:5004                            │
└───────────────┘     └───────────────────────────────────────────────────────────────┘
                              │           │           │           │
                    ┌─────────┘           │           │           └──────────┐
                    ▼                     ▼           ▼                      ▼
         ┌──────────────────┐  ┌──────────────┐  ┌──────────┐    ┌───────────────────┐
         │ Security Service │  │ Admin Service│  │Tutorías  │    │  Chatbot Service  │
         │ (FastAPI :5001)  │  │(Flask :5002) │  │(Flask    │    │ (FastAPI :5004)   │
         │ JWT + SMTP       │  │Fac./Carreras │  │ :5003)   │    │ Qwen + RAG        │
         │                  │  │Docentes/Est. │  │RabbitMQ  │    │ Ollama + MiniLM   │
         └──────────────────┘  └──────────────┘  └──────────┘    └───────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │   Worker     │
                                              │(Resúmenes de │
                                              │ bitácoras)   │
                                              └──────────────┘
```

### Servicios

| Servicio | Puerto | Tecnología | Base de Datos |
|---|---|---|---|
| **API Gateway** | 8080 | nginx | — |
| **Security** | 5001 | FastAPI | PostgreSQL 16 (:5432) |
| **Administration** | 5002 | Flask | PostgreSQL 16 (:5433) |
| **Tutorías** | 5003 | Flask + RabbitMQ | PostgreSQL 16 (:5434) |
| **Chatbot** | 5004 | FastAPI | pgvector/pg16 (:5435) |
| **Chatbot Worker** | — | Python | — |
| **Ollama** | 11434 | Ollama (Qwen 2.5 3B) | — |
| **Frontend** | 3008 | Next.js | — |
| **RabbitMQ** | 5672 / 15672 | RabbitMQ 3.12 | — |

---

## Chatbot Service — Agente Conversacional

### Arquitectura del Agente

```
Mensaje usuario
      │
      ▼
┌─────────────────────┐
│  /api/v1/chat       │
│  router_chat.py     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ agent_orchestrator  │  ← Carga/crea conversación + memoria
│ services/           │
└─────────┬───────────┘
          │
          ▼
┌───────────────────────────────────────────────────────┐
│                  Agent (agent.py)                     │
│                                                       │
│  1. planner.py: ciclo LLM → tool → LLM               │
│     a. Envía historial + herramientas disponibles     │
│     b. LLM responde (texto) o pide tool call          │
│     c. Si tool call → ejecuta adapter → continúa      │
│     d. Máximo OLLAMA_MAX_TOOL_ITERATIONS iteraciones  │
│                                                       │
│  2. Pre-routing (antes del LLM):                      │
│     - Patrones regex para facultades, carreras,       │
│       tutorías, saludos → respuesta inmediata         │
│     - Evita llamada LLM innecesaria                   │
│                                                       │
│  3. Tool calling (el LLM decide):                     │
│     - consultar_perfil                                │
│     - consultar_materias                              │
│     - consultar_tutorias / crear_tutoria              │
│     - cancelar_tutoria                                │
│     - buscar_conocimiento (RAG)                       │
│     - listar_facultades / listar_carreras             │
│     - listar_tutorias_admin                           │
│     - estadisticas_sistema                            │
└─────────┬─────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────┐
│  Adapters (app/agent/adapters/)                       │
│                                                       │
│  AdminAdapter    → administration-service (HTTP)      │
│  TutoriasAdapter → tutorias-service (HTTP + RabbitMQ) │
│  SecurityAdapter → security-service (HTTP)            │
│  RAGAdapter      → centro_conocimiento (local DB)     │
└─────────┬─────────────────────────────────────────────┘
          │
          ▼
    Respuesta al usuario + persistencia (mensaje + memoria)
```

### Pre-routing (respuestas sin LLM)

El `planner.py` detecta patrones con regex y responde directamente:

| Patrón | Respuesta |
|---|---|
| `facultades` / `facultades disponibles` | `listar_facultades()` → lista de facultades |
| `carreras` / `qué carreras` / `carreras disponibles` | `listar_carreras()` → lista de carreras |
| `lista todas las tutorias` / `todas las tutorias` | `listar_tutorias_admin()` → lista todas |
| `hola` / `buenos días` / `qué tal` | Saludo genérico hardcoded |

Si no hay match de pre-routing, se delega al LLM con las herramientas disponibles.

---

## RAG — Retrieval-Augmented Generation

### Pipeline completo

```
Documento (texto)
      │
      ▼
┌─────────────────────┐
│ Centro de            │
│ Conocimiento         │
│ (tabla PostgreSQL)   │
│                      │
│ titulo               │
│ contenido            │
│ embedding (VECTOR)   │
│ tags (TEXT[])        │
└─────────┬────────────┘
          │
          ▼
┌─────────────────────┐
│ MiniLM L6 v2        │  ← sentence-transformers
│ (384-dim embedding) │  ← generado automáticamente
└─────────────────────┘  ← al crear/actualizar entrada
          │
          ▼
┌──────────────────────────────────────────────────────┐
│               Búsqueda Híbrida                       │
│  PostgreSQL function: buscar_conocimiento_hibrido()  │
│                                                      │
│  score = (1 - coseno_dist(vector_consulta, vector))  │
│          × peso_vector (0.80)                        │
│        + similarity(texto_consulta, contenido)       │
│          × peso_trgm (0.20)                          │
│                                                      │
│  WHERE activo = TRUE AND embedding IS NOT NULL       │
│  ORDER BY score DESC                                 │
│  LIMIT candidatos (20) → top_k (5)                   │
└──────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐
│ RAGAdapter          │
│ format_context()    │  ← arma bloque de contexto
│ responder_con_      │  ← prompt + docs → LLM
│ contexto()          │
└─────────┬───────────┘
          │
          ▼
    LLM genera respuesta basada en contexto
```

### Componentes RAG

| Archivo | Rol |
|---|---|
| `app/ml/vectorizer.py` | MiniLM embedding model (cacheado en RAM) |
| `app/agent/adapters/rag.py` | Consulta híbrida + formateo + respuesta con contexto |
| `app/db/queries.py` (buscar_conocimiento) | Ejecuta `SELECT buscar_conocimiento_hibrido(...)` |
| `init.sql` | Define la función `buscar_conocimiento_hibrido()` + `centro_conocimiento` |

### Configuración (variables de entorno)

| Variable | Default | Descripción |
|---|---|---|
| `RAG_TOP_K` | 5 | Documentos finales entregados al LLM |
| `RAG_CANDIDATES` | 20 | Candidatos antes del filtro por score |
| `RAG_MIN_SCORE` | 0.35 | Score mínimo para incluir un documento |
| `RAG_VECTOR_WEIGHT` | 0.80 | Peso de similitud semántica (vector) |
| `RAG_TEXT_WEIGHT` | 0.20 | Peso de similitud textual (trigramas) |
| `MODEL_NAME` | all-MiniLM-L6-v2 | Modelo de embeddings |

---

## Estructura del Proyecto

```
chatbot-service/
│
├── app/                          # Chatbot (FastAPI)
│   ├── agent/
│   │   ├── adapters/
│   │   │   ├── admin.py          # AdminAdapter (facultades, carreras, docentes, etc.)
│   │   │   ├── tutorias.py       # TutoriasAdapter (solicitudes, bitácoras)
│   │   │   ├── security.py       # SecurityAdapter (perfil, login)
│   │   │   └── rag.py            # RAGAdapter (búsqueda en centro_conocimiento)
│   │   ├── agent.py              # Fachada del agente
│   │   ├── planner.py            # Ciclo LLM + pre-routing
│   │   ├── memory.py             # Memoria por conversación
│   │   ├── ollama_client.py      # Cliente HTTP para Ollama
│   │   ├── prompt.py             # System prompt
│   │   ├── tools.py              # Definición de herramientas (function calling)
│   │   └── tool_validator.py     # Parseo de tool calls
│   ├── api/
│   │   ├── router_chat.py        # POST /chat, POST /feedback
│   │   └── router_knowledge.py   # CRUD centro_conocimiento
│   ├── controllers/
│   │   └── knowledge_controller.py
│   ├── core/
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── dependencies.py       # Inyección de dependencias
│   │   ├── exceptions.py
│   │   └── microservice_client.py# Cliente HTTP para servicios externos
│   ├── db/
│   │   ├── connection.py         # Pool de conexiones PostgreSQL
│   │   └── queries.py            # Queries SQL
│   ├── ml/
│   │   └── vectorizer.py         # MiniLM embeddings
│   ├── schemas/
│   │   ├── requests.py
│   │   └── responses.py
│   ├── services/
│   │   └── agent_orchestrator.py # Orquestador del agente
│   ├── utils/
│   │   └── helpers.py
│   ├── worker/
│   │   └── summary_worker.py     # RabbitMQ consumer (resúmenes)
│   └── main.py                   # FastAPI entrypoint
│
├── backend/
│   ├── security-service/         # FastAPI :5001
│   ├── administracion/           # Flask :5002
│   └── tutorias_service/         # Flask :5003
│       ├── service.py            # Lógica principal de tutorías
│       ├── api.py                # Endpoints REST
│       ├── worker.py             # RabbitMQ worker
│       └── ...
│
├── frontend/                     # Next.js :3008
├── database/
│   └── init_tutorias.sql         # Schema BD tutorías
├── gateway/
│   └── nginx.conf                # Proxy + CORS
├── docker/
│   └── ollama-entrypoint.sh      # Script de inicio de Ollama
├── tests/                        # Pytest (27+ tests)
├── docker-compose.yml            # Stack completo
├── Dockerfile                    # chatbot-service + worker
├── Dockerfile.tutorias           # tutorias-service
├── init.sql                      # Schema BD chatbot
└── requirements.txt
```

---

## API — Chatbot Service

### Chat

```
POST /api/v1/chat
Authorization: Bearer <token>

{
  "conversacion_id": 1,        // opcional, null = nueva
  "mensaje": "¿Qué carreras hay?",
  "usuario": {
    "id": 123,
    "nombre": "Juan Pérez",
    "rol": "estudiante"
  }
}
```

Respuesta:
```json
{
  "conversacion_id": 1,
  "respuesta": "Las carreras disponibles son: Ing. Sistemas, Ing. Civil, Medicina, Derecho...",
  "tipo_resolucion": "logica"
}
```

### Feedback

```
POST /api/v1/chat/feedback
{
  "mensaje_id": 42,
  "fue_util": true,
  "comentario": "opcional"
}
```

### Centro de Conocimiento (CRUD)

```
GET    /api/v1/knowledge             # Listar (paginado)
GET    /api/v1/knowledge/{id}        # Obtener uno
POST   /api/v1/knowledge             # Crear (genera embedding)
PUT    /api/v1/knowledge/{id}        # Actualizar (regenera embedding)
DELETE /api/v1/knowledge/{id}        # Eliminar
POST   /api/v1/knowledge/test        # Probar búsqueda RAG
```

### Admin / Debug

```
GET    /api/v1/health                # Health check
GET    /api/v1/agent/health          # Estado del agente + Ollama
POST   /api/v1/agent/llm-test        # Prueba directa del LLM
GET    /api/v1/admin/pending         # Preguntas pendientes
GET    /api/v1/admin/metrics/usage   # Métricas de uso
GET    /api/v1/admin/summary/conversations  # Resumen de conversaciones
```

---

## API Gateway (nginx :8080)

### CORS

El gateway maneja CORS centralizadamente con:

```
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, PATCH, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, Origin, X-Requested-With" always;
```

Los servicios NO tienen CORS configurado (sin `CORS(app)` ni `CORSMiddleware`).

### Endpoints externos

| Ruta | Proxy a |
|---|---|
| `GET /security/*` | `http://security-service:5001` |
| `POST /security/*` | `http://security-service:5001` |
| `GET /administracion/*` | `http://administration-service:5002/api/administracion/` |
| `GET /tutorias/*` | `http://tutorias-service:5003/api/tutorias/` |
| `GET /chatbot/health` | `http://chatbot-service:5004/health` |
| `POST /chatbot/*` | `http://chatbot-service:5004/api/v1/` |
| `GET /chatbot/*` | `http://chatbot-service:5004/api/v1/` |

---

## Flujo del Chat (detallado)

### 1. Recepción
`POST /api/v1/chat` → `router_chat.py` → `agent_orchestrator.py`

### 2. Memoria
Se carga/crea `agente_memoria` (JSONB con contexto), se obtienen últimos N mensajes.

### 3. Pre-routing (planner.py)
Se evalúan patrones regex antes de invocar el LLM. Si hay match, respuesta directa.

### 4. Ciclo LLM (planner.py)
- Se envía system prompt + historial + tools disponibles a Ollama (Qwen 2.5 3B)
- El LLM responde: texto directo o tool call
- Si tool call: se ejecuta el adapter correspondiente, se agrega resultado al historial
- Se repite hasta: respuesta textual o máximo de iteraciones

### 5. Adapters
- **AdminAdapter** → HTTP a administration-service (facultades, carreras, docentes, estudiantes)
- **TutoriasAdapter** → HTTP a tutorias-service (solicitudes, bitácoras, sesiones)
- **SecurityAdapter** → HTTP a security-service (perfil del usuario)
- **RAGAdapter** → Consulta local a `centro_conocimiento` + formatea contexto

### 6. Persistencia
Se guarda mensaje en `chatbot_mensaje` + se actualiza `agente_memoria`.

### 7. Respuesta
Se retorna `{ conversacion_id, respuesta, tipo_resolucion }`.

---

## Integración con Tutorías

### Eventos RabbitMQ

| Cola | Publicador | Consumidor | Propósito |
|---|---|---|---|
| `tutorias.solicitudes` | chatbot-service | tutorias-service | Creación de solicitudes |
| `tutorias.eventos` | tutorias-service | chatbot-worker | Notificaciones para resúmenes |

### Chatbot Worker

El `summary_worker.py` consume eventos de tutorías (`tutorias.eventos`) y genera
resúmenes automáticos de bitácoras usando Ollama, almacenándolos en
`bitacora_resumen`.

### Notificaciones en el servicio de tutorías

- `finalizar_sesion` → envía notificación al estudiante y a todos los inscritos en `InscripcionSesion`
- `registrar_bitacora_sesion` → envía notificación al estudiante y a todos los inscritos
- `consultar_mis_bitacoras` → incluye bitácoras de sesiones grupales vía `InscripcionSesion`

---

## Levantar el proyecto

### Requisitos

- Docker + Docker Compose
- WSL2 con al menos 6 GB de RAM (Windows)

### Pasos

```bash
# 1. Clonar
git clone <repo>
cd chatbot-service

# 2. Crear .env (opcional, valores default funcionales)
# Ver sección de variables de entorno

# 3. Construir y levantar
docker compose up --build

# 4. Verificar health
curl http://localhost:5004/health

# 5. Swagger UI
# http://localhost:5004/docs
```

### Pull del modelo LLM (primera vez)

```bash
docker exec -it ollama ollama pull qwen2.5:3b
```

### Ejecutar tests

```bash
# Unitarios del chatbot
docker compose exec chatbot-service pytest

# O localmente (con Python)
pytest
```

---

## Variables de entorno principales

### Chatbot Service

| Variable | Default | Descripción |
|---|---|---|
| `AI_ENGINE` | `qwen` | Motor LLM (`qwen` u `ollama`) |
| `OLLAMA_HOST` | `http://ollama:11434` | URL de Ollama |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Modelo Ollama |
| `OLLAMA_TIMEOUT` | `60` | Timeout de llamada al LLM (seg) |
| `OLLAMA_MAX_TOOL_ITERATIONS` | `3` | Máx. tool calls por mensaje |
| `RAG_TOP_K` | `5` | Documentos para contexto |
| `RAG_CANDIDATES` | `20` | Candidatos de búsqueda |
| `RAG_MIN_SCORE` | `0.35` | Score mínimo |
| `RAG_VECTOR_WEIGHT` | `0.80` | Peso vector |
| `RAG_TEXT_WEIGHT` | `0.20` | Peso trigramas |
| `INTERNAL_TOKEN` | `change_me_in_production` | Token interno entre servicios |
| `SECURITY_SERVICE_URL` | `http://security-service:5001` | URL security |
| `ADMIN_SERVICE_URL` | `http://administration-service:5002` | URL admin |
| `TUTORIAS_SERVICE_URL` | `http://tutorias-service:5003` | URL tutorías |

### JWT (compartido entre servicios)

| Variable | Default |
|---|---|
| `JWT_SECRET_KEY` | `1a6790ea7aee933b903e74fcaa2804dfbf61387d6c4d7cb61206fd32b211958b` |
| `JWT_ALGORITHM` | `HS256` |

---

## Base de Datos — Chatbot (pgvector/pg16 :5435)

### Tablas principales

| Tabla | Propósito |
|---|---|
| `chatbot_conversacion` | Conversaciones activas/finalizadas |
| `chatbot_mensaje` | Mensajes con rol, tipo_resolución, score |
| `chatbot_feedback` | Feedback del usuario (fue_util, comentario) |
| `chatbot_pregunta_pendiente` | Preguntas no respondidas, con embedding |
| `centro_conocimiento` | Documentos para RAG (con embedding VECTOR(384)) |
| `agente_memoria` | Contexto persistente del agente (JSONB) |
| `bitacora_resumen` | Resúmenes generados por worker |
| `worker_evento_procesado` | Deduplicación de eventos RabbitMQ |

### Búsqueda Híbrida (PostgreSQL function)

```sql
buscar_conocimiento_hibrido(
  p_texto TEXT,                    -- Consulta en lenguaje natural
  p_vector VECTOR(384),           -- Embedding de la consulta
  p_candidatos INT DEFAULT 20,    -- Candidatos a recuperar
  p_w_vector FLOAT DEFAULT 0.80,  -- Peso semántico
  p_w_trgm FLOAT DEFAULT 0.20    -- Peso textual
)
RETURNS TABLE (id INT, titulo TEXT, contenido TEXT, score FLOAT)
```

---

## Troubleshooting

### Error: modelo no encontrado en Ollama
```bash
docker exec -it ollama ollama pull qwen2.5:3b
```

### Error de memoria en Ollama (WSL2)
Asignar al menos 6 GB de RAM en `.wslconfig`:
```ini
[wsl2]
memory=6GB
```

### CORS: errores en frontend
Verificar que NGINX tiene los headers CORS y que ningún servicio tiene `CORS(app)` o `CORSMiddleware`.

### Error de conexión entre servicios
Verificar que están en la misma red de Docker:
```bash
docker network ls
docker network inspect chatbot-service_default
```

### Reconstruir un servicio específico
```bash
docker compose up -d --build chatbot-service
```

---

## Notas técnicas

- SetFit fue eliminado del proyecto. No se usa clasificación ML; toda la lógica de
  decisión es vía pre-routing regex + LLM con tool calling.
- Los embeddings se generan automáticamente al insertar/actualizar en
  `centro_conocimiento` vía el hook en `knowledge_controller.py`.
- El modelo MiniLM se carga una sola vez y se cachea en el vectorizer.
- No hay certificados SSL en desarrollo; todas las conexiones son HTTP.
- En producción, cambiar `JWT_SECRET_KEY` e `INTERNAL_TOKEN`.

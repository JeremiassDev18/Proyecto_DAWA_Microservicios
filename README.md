# 🤖 Chatbot Service - Microservicio de Inteligencia Artificial

Microservicio encargado de proporcionar un agente conversacional inteligente para el Sistema de Gestión de Tutorías Académicas.

El servicio permite responder preguntas frecuentes, realizar búsquedas documentales mediante RAG (Retrieval-Augmented Generation), clasificar consultas mediante Machine Learning y comunicarse con otros microservicios del sistema.

---

# Características

- Agente conversacional con LLM local (Qwen 2.5 3B vía Ollama).
- Tool calling: el LLM decide cuándo consultar perfil, materias, tutorías o conocimiento institucional.
- Memoria por conversación en RAM + persistencia en PostgreSQL.
- RAG agentic sobre el Centro de Conocimiento (búsqueda híbrida pgvector + pg_trgm).
- Centro de Conocimiento administrable para normas, reglamentos, FAQs y procedimientos.
- Registro completo de conversaciones.
- Feedback del usuario.
- Integración con microservicios de Administración, Tutorías y Seguridad.

---

# Tecnologías

- Python 3.11
- FastAPI
- PostgreSQL 16 + pgvector + pg_trgm
- Docker / Docker Compose
- Ollama (motor LLM)
- Qwen 2.5 3B
- Sentence Transformers (MiniLM para embeddings)
- PyTorch

---

# Estructura del proyecto

```
app/
│
├── agent/              # Agente LLM, planner, memoria, tools y adapters
│   ├── adapters/
│   ├── agent.py
│   ├── planner.py
│   ├── memory.py
│   ├── ollama_client.py
│   ├── prompt.py
│   ├── tools.py
│   └── tool_validator.py
├── api/
├── controllers/
├── core/
├── db/
├── ml/                 # Embeddings (MiniLM / sentence-transformers)
├── schemas/
├── services/
│   └── agent_orchestrator.py
├── utils/
└── main.py

tests/
docker-compose.yml
requirements.txt
init.sql
```

---

# Requisitos

- Docker
- Docker Compose

o bien

- Python 3.11
- PostgreSQL 16+
- pgvector

---

# Instalación

Clonar el proyecto

```bash
git clone <repositorio>

cd chatbot-service
```

---

## Variables de entorno

Crear el archivo

```
.env
```

Ejemplo

```env
DB_HOST=chatbot-db
DB_PORT=5432
DB_NAME=chatbot
DB_USER=postgres
DB_PASSWORD=postgres

INTERNAL_TOKEN=change_me_in_production

# Motor LLM
AI_ENGINE=qwen
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=30
OLLAMA_MAX_TOOL_ITERATIONS=3

# RAG
RAG_TOP_K=5
RAG_CANDIDATES=20
RAG_MIN_SCORE=0.35
RAG_VECTOR_WEIGHT=0.80
RAG_TEXT_WEIGHT=0.20

# Microservicios
ADMIN_SERVICE_URL=http://administracion:5001
TUTORIAS_SERVICE_URL=http://tutorias:5003
SECURITY_SERVICE_URL=http://security:5000
RABBITMQ_HOST=rabbitmq
RABBITMQ_QUEUE_SOLICITUDES=tutorias.solicitudes
RABBITMQ_QUEUE_EVENTOS=tutorias.eventos
```

---

# Levantar con Docker

```bash
docker compose up --build
```

La API estará disponible en

```
http://localhost:5004
```

Swagger

```
http://localhost:5004/docs
```

---

# Inicializar la Base de Datos

El proyecto ejecuta automáticamente el script

```
init.sql
```

durante la creación del contenedor de PostgreSQL.

Este script crea:

- tablas de conversaciones, mensajes, feedback y preguntas pendientes
- tabla `centro_conocimiento` para el RAG
- tabla `agente_memoria` para persistir el contexto del agente LLM
- función `buscar_conocimiento_hibrido` (pgvector + pg_trgm)
- datos iniciales de ejemplo en el centro de conocimiento

---

# Configurar Ollama

El contenedor `ollama` se levanta automáticamente con `docker compose up`.
La primera vez debes descargar el modelo:

```bash
docker exec -it ollama ollama pull qwen2.5:3b
```

En Windows con Docker Desktop asegúrate de asignar al menos **6 GB de RAM** a WSL2 para evitar errores de memoria al cargar el modelo.

---

# Centro de Conocimiento (RAG)

Los administradores pueden gestionar fragmentos de conocimiento en:

```
/api/v1/knowledge
```

Cada entrada genera automáticamente un embedding con MiniLM.
Para probar qué recupera el RAG y qué respondería el agente:

```
POST /api/v1/knowledge/test
{
  "consulta": "¿Cómo cancelo una tutoría?",
  "top_k": 5
}
```

---

# Endpoints principales

## Chat

```
POST /api/v1/chat
```

Procesa el mensaje a través del agente LLM.

## Feedback

```
POST /api/v1/chat/feedback
```

## Agente (debug)

```
GET  /api/v1/agent/health
POST /api/v1/agent/llm-test
```

## Centro de Conocimiento

```
GET    /api/v1/knowledge
GET    /api/v1/knowledge/{id}
POST   /api/v1/knowledge
PUT    /api/v1/knowledge/{id}
DELETE /api/v1/knowledge/{id}
POST   /api/v1/knowledge/test
```

## Admin

```
GET /api/v1/pending
GET /api/v1/metrics/usage
GET /api/v1/summary/conversations
```

---

# Flujo del Chat

```
Usuario
      │
      ▼
/api/v1/chat
      │
      ▼
Agent Orchestrator
      │
      ├── Carga/crea conversación y memoria
      │
      ▼
Agent LLM (Qwen vía Ollama)
      │
      ├── Tool calling: consultar_perfil, consultar_materias,
      │   consultar_tutorias, crear_tutoria, cancelar_tutoria,
      │   buscar_conocimiento
      │
      ▼
Adapters → microservicios / centro_conocimiento
      │
      ▼
Respuesta natural redactada por el LLM
      │
      ▼
Persistencia en chatbot_mensaje + agente_memoria
      │
      ▼
Usuario
```

---

# Arquitectura

El proyecto está dividido en los siguientes módulos.

## API

Expone todos los endpoints REST.

## Agente (`app/agent/`)

- `agent.py`: fachada principal.
- `planner.py`: ciclo LLM → tool → LLM.
- `memory.py`: historial de mensajes y estado de conversación.
- `ollama_client.py`: cliente del motor LLM.
- `tools.py`: definición de herramientas disponibles.
- `tool_validator.py`: parseo y validación de llamadas a tool.
- `adapters/`: ejecutan herramientas reutilizando microservice_client.

## ML

Generación de embeddings con MiniLM (`sentence-transformers`) para el RAG.

## Services

`agent_orchestrator.py` orquesta el procesamiento de mensajes, la persistencia de memoria y el registro de mensajes.

## Database

Acceso a PostgreSQL, pgvector y consultas SQL.

## Controllers

`knowledge_controller.py` gestiona el Centro de Conocimiento.

---

# Integración con otros microservicios

Este microservicio está preparado para consumir información proveniente de:

- Administración Académica
- Tutorías
- Usuarios

Actualmente estas integraciones utilizan mocks mediante:

```
microservice_client.py
```

Posteriormente podrán reemplazarse por llamadas REST sin modificar la lógica principal del chatbot.

---

# Ejecutar pruebas

```bash
pytest
```

Actualmente el proyecto cuenta con más de 100 pruebas automatizadas.

---

# Notas

El modelo LLM (Qwen) se ejecuta dentro del contenedor de Ollama y no se almacena en Git. Los embeddings se generan automáticamente al crear o actualizar entradas del Centro de Conocimiento.

---

# Git Ignore

El proyecto ignora automáticamente:

- entornos virtuales
- modelos entrenados
- caché
- archivos temporales
- logs
- configuraciones locales

---

# Estado del proyecto

Características implementadas:

- Agente conversacional con LLM local (Qwen 2.5 3B)
- Tool calling con validación y reintentos
- Memoria persistente por conversación
- RAG agentic sobre Centro de Conocimiento
- Centro de Conocimiento administrable
- Feedback de usuarios
- Registro histórico de conversaciones
- Métricas de uso por tipo de resolución
- Integración con microservicios de Administración, Tutorías y Seguridad

Pendiente de integración:

- API Gateway
- Autenticación unificada entre microservicios

---

## Estado actual del microservicio de Tutorías (rama Reservas)

### Cumplimiento funcional
- El microservicio implementa los requisitos TUT-R01 a TUT-R12 en una versión funcional base.
- Se ejecuta dockerizado junto a RabbitMQ y consume/publica eventos.
- Las pruebas unitarias del servicio pasan correctamente.

### Integración con otros microservicios del repositorio
- Actualmente no existe integración directa con todos los microservicios del repositorio.
- En esta rama, la integración implementada es por mensajería con RabbitMQ (colas `tutorias.solicitudes` y `tutorias.eventos`).
- No hay llamadas HTTP activas desde Tutorías hacia Security, Administración o Chatbot en el código actual de la rama Reservas.

### Qué fue adicional (mejora de calidad)
- Se añadió `.gitignore` y se excluyeron artefactos compilados de Python (`__pycache__`, `*.pyc`).
- Esta mejora no cambia la lógica de negocio; solo mejora orden y mantenibilidad del repositorio.

### Si se requiere interacción completa entre microservicios
- Definir contratos (endpoints o eventos) entre Tutorías, Security, Administración y Chatbot.
- Unificar red de Docker Compose o usar un compose raíz para todos los servicios.
- Configurar variables de entorno con URLs/colas de cada servicio y agregar pruebas de integración.


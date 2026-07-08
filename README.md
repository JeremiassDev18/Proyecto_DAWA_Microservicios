# 🤖 Chatbot Service - Microservicio de Inteligencia Artificial

Microservicio encargado de proporcionar un agente conversacional inteligente para el Sistema de Gestión de Tutorías Académicas.

El servicio permite responder preguntas frecuentes, realizar búsquedas documentales mediante RAG (Retrieval-Augmented Generation), clasificar consultas mediante Machine Learning y comunicarse con otros microservicios del sistema.

---

# Características

- Clasificación de intenciones mediante SetFit.
- Búsqueda híbrida (texto + embeddings).
- Motor RAG sobre documentos institucionales.
- Gestión de FAQs.
- Registro completo de conversaciones.
- Feedback del usuario.
- Escalamiento automático cuando la IA no posee suficiente confianza.
- Entrenamiento del modelo desde API.
- Arquitectura basada en servicios y handlers.
- Integración preparada para microservicios externos.

---

# Tecnologías

- Python 3.11
- FastAPI
- PostgreSQL
- pgvector
- Docker
- Docker Compose
- Sentence Transformers
- SetFit
- PyTorch

---

# Estructura del proyecto

```
app/
│
├── api/
├── controllers/
├── core/
├── db/
├── ml/
├── schemas/
├── services/
│   ├── handlers/
│   ├── dispatcher.py
│   ├── rag_service.py
│   ├── search_service.py
│   └── chat_orchestrator.py
│
├── utils/
└── main.py

scripts/
tests/
data/
docker-compose.yml
requirements.txt
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
DB_HOST=postgres
DB_PORT=5432
DB_NAME=chatbot
DB_USER=postgres
DB_PASSWORD=postgres

CONFIDENCE_THRESHOLD=0.6
RAG_SIMILARITY_THRESHOLD=0.20
ESCALATION_ENABLED=true
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

- tablas
- intenciones
- respuestas
- documentos base
- dataset inicial

---

# Entrenar el modelo

La primera vez es necesario entrenar el modelo.

```
POST

/api/v1/train
```

o mediante Swagger.

Una vez entrenado, el modelo queda almacenado en

```
data/setfit_model/
```

y permanece disponible gracias al volumen de Docker.

No es necesario volver a entrenar después de reiniciar los contenedores.

Únicamente deberá reentrenarse cuando:

- se agreguen nuevas intenciones
- se modifique el dataset
- se validen nuevas preguntas

---

# Generar embeddings

Si se agregan documentos nuevos se recomienda regenerar embeddings.

```bash
python scripts/generate_embeddings.py
```

---

# Endpoints principales

## Chat

```
POST /api/v1/chat
```

---

## Feedback

```
POST /api/v1/chat/feedback
```

---

## Entrenamiento

```
POST /api/v1/train
```

---

## Dataset

```
GET    /api/v1/dataset
POST   /api/v1/dataset
PUT    /api/v1/dataset
DELETE /api/v1/dataset
```

---

## Documentos

```
GET
POST
PUT
DELETE
```

sobre

```
/api/v1/documents
```

---

# Flujo del Chat

```
Usuario
      │
      ▼
Router
      │
      ▼
Chat Orchestrator
      │
      ▼
Clasificador SetFit
      │
      ▼
Dispatcher
      │
      ├── External Handler
      │
      ├── FAQ Handler
      │
      ├── Hybrid Handler
      │
      ├── RAG Handler
      │
      └── Fallback Handler
      │
      ▼
Validador
      │
      ▼
Respuesta al usuario
```

---

# Arquitectura

El proyecto está dividido en cinco módulos principales.

## API

Expone todos los endpoints REST.

## ML

Contiene:

- entrenamiento
- predicción
- embeddings
- vectorización

## Services

Implementa toda la lógica del chatbot mediante handlers especializados.

## Database

Acceso a PostgreSQL y consultas SQL.

## Controllers

Orquesta la administración del dataset y documentos.

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

El modelo entrenado y los artefactos generados no se almacenan en Git.

Se regeneran mediante:

```
POST /api/v1/train
```

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

- Clasificación de intenciones
- FAQ
- RAG
- Búsqueda híbrida
- Feedback
- Gestión documental
- Entrenamiento desde API
- Dispatcher basado en handlers
- Registro histórico de conversaciones
- Escalamiento automático
- Dashboard preparado para métricas

Pendiente de integración:

- Microservicio de Tutorías
- Microservicio Académico
- Microservicio de Usuarios
- API Gateway

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


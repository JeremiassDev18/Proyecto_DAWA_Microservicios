"""
Router del Agente Inteligente Académico.

Endpoints de prueba y salud para la FASE 2 de integración con Ollama.
El nombre final de las rutas lo definirás tú al cerrar la migración;
por ahora usan prefijos claros de *agent* para no colisionar con /chat.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.ollama_client import OllamaClient
from app.core.config import settings
from app.core.dependencies import get_db
from app.services.agent_orchestrator import process_message_agent
from app.utils.logger import logger

router = APIRouter(prefix="/agent", tags=["Agente LLM"])


class LLMTestRequest(BaseModel):
    mensaje: str = "Hola"


class LLMTestResponse(BaseModel):
    respuesta: str
    modelo: str
    engine_configurado: str


class AgentChatRequest(BaseModel):
    usuario_id: int
    mensaje: str
    id_conversacion: int | None = None
    nombre: str = ""
    estudiante_id: int | None = None
    carrera_id: int | None = None
    periodo_id: int | None = None
    rol: str = "estudiante"
    email: str = ""


class AgentChatResponse(BaseModel):
    respuesta: str
    intencion: str
    confianza: float
    tipo_resolucion: str
    id_conversacion: int
    id_mensaje: int


class HealthResponse(BaseModel):
    ollama_available: bool
    model: str
    host: str


@router.get("/health", response_model=HealthResponse)
def agent_health():
    """Verifica que Ollama esté accesible desde el chatbot-service."""
    client = OllamaClient()
    return HealthResponse(
        ollama_available=client.is_available(),
        model=settings.OLLAMA_MODEL,
        host=settings.OLLAMA_HOST,
    )


@router.post("/llm-test", response_model=LLMTestResponse)
def llm_test(payload: LLMTestRequest):
    """
    Endpoint de prueba para la FASE 2.

    Envía un mensaje simple a Qwen y devuelve la respuesta cruda.
    No usa herramientas ni memoria. Útil para validar conectividad.
    """
    client = OllamaClient()
    raw = client.chat(
        messages=[
            {"role": "system", "content": "Eres un asistente universitario útil y breve."},
            {"role": "user", "content": payload.mensaje},
        ]
    )

    if raw.finish_reason in ("timeout", "connection_error", "error"):
        logger.error(f"[llm-test] fallo de Ollama: {raw.finish_reason}")
        raise HTTPException(status_code=503, detail=raw.content)

    return LLMTestResponse(
        respuesta=raw.content,
        modelo=settings.OLLAMA_MODEL,
        engine_configurado=settings.AI_ENGINE,
    )


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest, conn=Depends(get_db)):
    """
    Endpoint de prueba para la FASE 3.

    Usa el agente LLM con herramientas reales. Permite probar tool calling
    sin afectar el endpoint público /api/v1/chat.
    """
    result = process_message_agent(
        conn,
        usuario_id=payload.usuario_id,
        mensaje=payload.mensaje,
        id_conversacion=payload.id_conversacion,
        nombre_cliente=payload.nombre,
        estudiante_id=payload.estudiante_id,
        carrera_id=payload.carrera_id,
        periodo_id=payload.periodo_id,
        rol=payload.rol,
        email=payload.email,
    )
    return AgentChatResponse(**result)

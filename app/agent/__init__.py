"""
Módulo Agente Inteligente Académico.

Este paquete contiene la implementación del agente basado en LLM (Qwen 2.5 3B)
que orquesta herramientas para atender consultas de estudiantes.

El resto del sistema (handlers, microservicios, RabbitMQ, RAG) sigue intacto;
el agente simplemente los consume a través de los adaptadores.
"""

from .agent import Agent
from .memory import ConversationMemory
from .ollama_client import OllamaClient
from .schemas import ToolCall, ToolResult, AgentResponse

__all__ = [
    "Agent",
    "ConversationMemory",
    "OllamaClient",
    "ToolCall",
    "ToolResult",
    "AgentResponse",
]

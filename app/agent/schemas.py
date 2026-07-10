"""
Esquemas Pydantic usados por el agente LLM.

Los modelos definen la interfaz de contrato entre:
- El LLM (que emite llamadas a herramientas en JSON).
- El validador (que corrige/parsea esas llamadas).
- Los adaptadores (que ejecutan la lógica de negocio real).
"""

from typing import Any
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Descriptor de un parámetro de herramienta."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True


class ToolDefinition(BaseModel):
    """Definición expuesta al LLM para que decida qué herramienta usar."""
    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)


class ToolCall(BaseModel):
    """Llamada a herramienta parseada desde la respuesta del LLM."""
    tool: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Resultado de ejecutar una herramienta."""
    tool: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    success: bool
    content: str
    state_updates: dict[str, Any] = Field(default_factory=dict)
    """Campos de estado de conversación que deben actualizarse tras ejecutar la tool."""


class AgentResponse(BaseModel):
    """Respuesta final del agente hacia el usuario/chat."""
    mensaje: str
    intencion_detectada: str | None = None
    herramientas_usadas: list[str] = Field(default_factory=list)
    id_conversacion: int | None = None


class LLMRawResponse(BaseModel):
    """Respuesta cruda del modelo antes de ser interpretada."""
    content: str
    finish_reason: str | None = None

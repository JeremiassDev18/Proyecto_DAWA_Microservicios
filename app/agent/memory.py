"""
Gestión de contexto/memoria de conversación para el agente.

Diseño:
- Nivel 1: RAM (ConversationMemory en el planner).
- Nivel 2: PostgreSQL (tabla agente_memoria) para persistencia.

Además de mensajes, guarda un "estado de conversación" compacto:
usuario, materia_actual, ultima_tutoria, ultima_accion, esperando_confirmacion, etc.
Esto permite referencias como "la primera", "cancélala", "sí" sin reenviar todo
el historial al LLM.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None  # nombre de la herramienta cuando role == "tool"


class ConversationMemory:
    """
    Memoria de conversación con ventana fija y estado interno.

    Args:
        max_messages: número máximo de mensajes de usuario/asistente/tool a conservar.
        state: diccionario de estado de conversación (actualizado por adapters).
    """

    def __init__(self, max_messages: int = 3, state: dict[str, Any] | None = None):
        self.max_messages = max_messages
        self._messages: list[Message] = []
        self.state: dict[str, Any] = state or {}

    def add(self, role: Literal["user", "assistant", "tool"], content: str, name: str | None = None) -> None:
        """Agrega un mensaje y recorta la ventana si es necesario."""
        self._messages.append(Message(role=role, content=content, name=name))
        self._trim()

    def update_state(self, updates: dict[str, Any]) -> None:
        """Actualiza el estado compacto de la conversación."""
        self.state.update(updates)

    def set_system(self, content: str) -> None:
        """Reemplaza o establece el mensaje de sistema."""
        self._messages = [m for m in self._messages if m.role != "system"]
        self._messages.insert(0, Message(role="system", content=content))

    def get_messages(self, include_system: bool = True) -> list[dict]:
        """Devuelve la memoria lista para enviar a Ollama/OpenAI-style chat."""
        messages = self._messages if include_system else [m for m in self._messages if m.role != "system"]
        result = []
        for m in messages:
            msg: dict = {"role": m.role, "content": m.content}
            if m.name:
                msg["name"] = m.name
            result.append(msg)
        return result

    def last_user_message(self) -> str | None:
        """Último mensaje del usuario; útil para logs o resúmenes."""
        for m in reversed(self._messages):
            if m.role == "user":
                return m.content
        return None

    def clear(self) -> None:
        """Limpia toda la memoria excepto el system prompt y el estado."""
        system = [m for m in self._messages if m.role == "system"]
        self._messages = system

    def should_summarize(self, threshold: int = 15) -> bool:
        """True si hay más de `threshold` mensajes de chat (sin contar system)."""
        chat = [m for m in self._messages if m.role != "system"]
        return len(chat) > threshold

    def get_summary_prompt(self) -> str:
        """Prompt para que el LLM genere un resumen de la conversación."""
        return (
            "Resume la conversación anterior en 2-3 oraciones. "
            "Conserva: nombre del estudiante, materia consultada, "
            "ID de tutorías creadas/canceladas, y cualquier preferencia explícita. "
            "El resumen servirá como contexto para continuar la conversación."
        )

    def apply_summary(self, summary: str) -> None:
        """Reemplaza los mensajes antiguos por un resumen."""
        system = [m for m in self._messages if m.role == "system"]
        self._messages = system
        self.add("assistant", f"[Resumen de la conversación anterior]: {summary}")

    def to_dict(self) -> dict[str, Any]:
        """Serializa memoria y estado para guardar en PostgreSQL."""
        return {
            "messages": [
                {"role": m.role, "content": m.content, "name": m.name}
                for m in self._messages
            ],
            "state": self.state,
            "total_messages": len(self._messages),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], max_messages: int = 3) -> "ConversationMemory":
        """Reconstruye la memoria desde PostgreSQL."""
        memory = cls(max_messages=max_messages, state=data.get("state", {}))
        for m in data.get("messages", []):
            memory._messages.append(
                Message(role=m["role"], content=m["content"], name=m.get("name"))
            )
        memory._trim()
        return memory

    def render_state_for_prompt(self) -> str:
        """Renderiza el estado como texto para incluir en el system prompt.
        Limitado a 300 caracteres para no inflar el prompt.
        """
        if not self.state:
            return ""
        lines = ["\nESTADO DE LA CONVERSACIÓN:"]
        for key, value in self.state.items():
            val_str = str(value)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            lines.append(f"- {key}: {val_str}")
        result = "\n".join(lines)
        if len(result) > 300:
            result = result[:297] + "..."
        return result

    def _trim(self) -> None:
        """Conserva solo los últimos `max_messages` intercambios."""
        system = [m for m in self._messages if m.role == "system"]
        chat = [m for m in self._messages if m.role != "system"]

        if len(chat) > self.max_messages:
            chat = chat[-self.max_messages:]

        self._messages = system + chat

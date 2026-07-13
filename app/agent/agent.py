"""
Agente Inteligente Académico — punto de entrada principal.

Esta clase es una fachada ligera sobre AgentPlanner. Permite:
- Procesar mensajes de usuario.
- Gestionar la memoria por conversación (RAM + persistencia).
- Alternar entre motores (SetFit / Qwen) sin cambiar el consumidor.
"""

from app.core.config import settings
from app.utils.logger import logger

from .memory import ConversationMemory
from .planner import AgentPlanner
from .schemas import AgentResponse


class Agent:
    """Agente conversacional para consultas académicas."""

    def __init__(
        self,
        estudiante_id: int | None = None,
        usuario_id: int | None = None,
        carrera_id: int | None = None,
        periodo_id: int | None = None,
        rol: str = "estudiante",
        email: str = "",
        memory: ConversationMemory | None = None,
    ):
        self.estudiante_id = estudiante_id
        self.usuario_id = usuario_id
        self.carrera_id = carrera_id
        self.periodo_id = periodo_id
        self.rol = rol
        self.email = email
        self._memory = memory
        self._planner: AgentPlanner | None = None

    def process(self, mensaje: str, db_conn=None) -> AgentResponse:
        """Procesa un mensaje y devuelve la respuesta del agente."""
        logger.info(
            f"[Agent] procesando mensaje para estudiante_id={self.estudiante_id} "
            f"usuario_id={self.usuario_id}"
        )

        if self._planner is None:
            self._planner = AgentPlanner(
                estudiante_id=self.estudiante_id,
                usuario_id=self.usuario_id,
                carrera_id=self.carrera_id,
                periodo_id=self.periodo_id,
                rol=self.rol,
                email=self.email,
                memory=self._memory,
            )
        else:
            # Propagar cambios de contexto (pueden llegar en peticiones posteriores).
            self._planner.estudiante_id = self.estudiante_id
            self._planner.usuario_id = self.usuario_id
            self._planner.carrera_id = self.carrera_id
            self._planner.periodo_id = self.periodo_id
            self._planner.rol = self.rol
            self._planner.email = self.email

        return self._planner.run(mensaje, db_conn=db_conn)

    def get_memory(self) -> ConversationMemory:
        """Devuelve la memoria actual del agente (para persistir)."""
        if self._planner is not None:
            return self._planner.memory
        if self._memory is None:
            self._memory = ConversationMemory(max_messages=3)
        return self._memory

    @staticmethod
    def is_enabled() -> bool:
        """Indica si el motor de agente LLM está activo por configuración."""
        return settings.AI_ENGINE.lower() == "qwen"

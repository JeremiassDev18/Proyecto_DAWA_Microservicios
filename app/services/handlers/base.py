from abc import ABC, abstractmethod


class IntentHandler(ABC):
    @abstractmethod
    def can_handle(self, intent: str, confidence: float, mensaje: str = "") -> bool:
        ...

    @abstractmethod
    def handle(self, conn, usuario_id: int, mensaje: str,
               intent: str, confidence: float) -> dict | None:
        ...

"""
Cliente HTTP para Ollama/Qwen 2.5 3B.

Responsabilidades:
- Enviar mensajes al endpoint /api/chat de Ollama.
- Manejar timeouts y errores de conexión con mensajes claros.
- Soportar modo streaming para el futuro.
"""

import json
from typing import Any, Iterator

import httpx

from app.core.config import settings
from app.utils.logger import logger
from .schemas import LLMRawResponse


class OllamaClient:
    """Cliente síncrono para interactuar con Ollama."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        self.host = (host or settings.OLLAMA_HOST).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self._chat_url = f"{self.host}/api/chat"

    def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> LLMRawResponse | Iterator[str]:
        """
        Envía mensajes a Ollama y devuelve la respuesta completa.

        Args:
            messages: lista de mensajes en formato OpenAI-style.
            stream: si es True, devuelve un iterador de chunks (no implementado aún).
            options: opciones adicionales de Ollama (temperature, num_ctx, etc.).
        """
        if stream:
            return self._stream_chat(messages, options)

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options or {},
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._chat_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                message = data.get("message", {})
                return LLMRawResponse(
                    content=message.get("content", "").strip(),
                    finish_reason="stop" if data.get("done") else None,
                )
        except httpx.TimeoutException:
            logger.error(f"Ollama timeout después de {self.timeout}s")
            return LLMRawResponse(
                content="El servicio de IA está tardando demasiado. Intenta de nuevo en unos segundos.",
                finish_reason="timeout",
            )
        except httpx.ConnectError as e:
            logger.error(f"No se pudo conectar con Ollama en {self.host}: {e}")
            return LLMRawResponse(
                content="No pude contactar al modelo de lenguaje. Verifica que Ollama esté corriendo.",
                finish_reason="connection_error",
            )
        except Exception as e:
            logger.error(f"Error inesperado en OllamaClient.chat: {e}")
            return LLMRawResponse(
                content="Ocurrió un error al procesar tu mensaje. Por favor intenta de nuevo.",
                finish_reason="error",
            )

    def _stream_chat(
        self,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
    ) -> Iterator[str]:
        """Streaming básico para futuras mejoras del frontend."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": options or {},
        }
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", self._chat_url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        continue

    def is_available(self) -> bool:
        """Verifica rápidamente si Ollama responde."""
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

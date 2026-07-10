"""
Validador y corrector de llamadas a herramientas emitidas por el LLM.

Qwen 2.5 3B puede devolver JSON malformado, Markdown envolvente,
o parámetros con tipos incorrectos. Este módulo normaliza esos casos
y, si es posible, intenta una segunda vez pidiendo al modelo que corrija.
"""

import json
import re
from typing import Any

from app.utils.logger import logger
from .schemas import ToolCall, ToolDefinition


class ToolValidationError(Exception):
    """La llamada a herramienta no pudo ser validada."""
    pass


class ToolValidator:
    """Parsea y valida JSON de tool calling contra definiciones conocidas."""

    def __init__(self, tools: list[ToolDefinition]):
        self.tools = {t.name: t for t in tools}

    def parse(self, raw: str) -> ToolCall | None:
        """
        Extrae un ToolCall de la respuesta cruda del modelo.

        Returns:
            ToolCall si se detectó una llamada válida.
            None si la respuesta parece una respuesta directa (sin herramienta).
        """
        raw = raw.strip()
        if not raw:
            return None

        # 0. Normalizar {{ → { a nivel global ({{ nunca es válido en JSON).
        raw = raw.replace("{{", "{")

        # 1. Formato Qwen: <tool_call>{...}</tool_call> (o {{ ... }} legacy)
        qwen_block = self._extract_qwen_tool_call(raw)
        if qwen_block:
            try:
                data = json.loads(qwen_block)
                call = self._to_tool_call(data)
                if call:
                    return call
            except json.JSONDecodeError:
                pass

        # 2. Intenta parsear directamente.
        try:
            data = json.loads(raw)
            return self._to_tool_call(data)
        except json.JSONDecodeError:
            pass

        # 3. Busca bloque JSON Markdown.
        block = self._extract_json_block(raw)
        if block:
            try:
                data = json.loads(block)
                call = self._to_tool_call(data)
                if call:
                    return call
            except json.JSONDecodeError:
                pass

        # 4. Busca la primera estructura JSON-like con llaves.
        fallback = self._extract_first_json_object(raw)
        if fallback:
            try:
                data = json.loads(fallback)
                call = self._to_tool_call(data)
                if call:
                    return call
            except json.JSONDecodeError:
                pass

        # 5. Formato markdown link: [text](toolname{...}) o [text](toolname)
        md_link = self._extract_markdown_tool_call(raw)
        if md_link:
            return md_link

        return None

    def validate(self, call: ToolCall) -> ToolCall:
        """Verifica que la herramienta exista y tenga los parámetros requeridos."""
        definition = self.tools.get(call.tool)
        if not definition:
            raise ToolValidationError(f"Herramienta desconocida: {call.tool}")

        provided = set(call.parameters.keys())
        required = {p.name for p in definition.parameters if p.required}
        missing = required - provided
        if missing:
            raise ToolValidationError(
                f"Faltan parámetros obligatorios para '{call.tool}': {missing}"
            )

        return call

    def build_retry_prompt(self, original: str, error: str) -> str:
        """Genera un prompt para pedir al LLM que corrija el JSON."""
        return (
            "Tu respuesta anterior no pudo ser procesada. "
            "Devuelve ÚNICAMENTE un objeto JSON válido con la forma:\n"
            '{"tool": "nombre_herramienta", "parameters": { ... }}\n'
            f"Error detectado: {error}\n"
            f"Respuesta original: {original}\n"
            "JSON corregido:"
        )

    def _to_tool_call(self, data: Any) -> ToolCall | None:
        if not isinstance(data, dict):
            return None

        # Soporta múltiples formas de tool calling.
        tool_name = (
            data.get("tool")
            or data.get("name")
            or data.get("function", {}).get("name")
        )
        if not tool_name:
            return None

        parameters = (
            data.get("parameters")
            or data.get("arguments")
            or data.get("function", {}).get("arguments", {})
        )
        if not isinstance(parameters, dict):
            parameters = {}

        return ToolCall(tool=tool_name, parameters=parameters)

    def _extract_qwen_tool_call(self, text: str) -> str | None:
        """Extrae el contenido de un bloque <tool_call>...</tool_call>."""
        match = re.search(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
        if match:
            block = match.group(1).strip()
            # Normalizar {{ → { que el LLM puede regurgitar del prompt.
            block = block.replace("{{", "{")
            block = block.replace("}}", "}")
            return block
        return None

    def _extract_json_block(self, text: str) -> str | None:
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_first_json_object(self, text: str) -> str | None:
        # Encuentra el primer par de llaves balanceado.
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    def _extract_markdown_tool_call(self, text: str) -> ToolCall | None:
        """Detecta [texto](nombre_herramienta{...}) y lo convierte en ToolCall."""
        md_pattern = re.search(r'\[.*?\]\((\w+)\s*(\{.*?\})\)', text, re.DOTALL)
        if not md_pattern:
            return None
        tool_name = md_pattern.group(1)
        args_text = md_pattern.group(2)
        try:
            args = json.loads(args_text)
        except json.JSONDecodeError:
            return None
        if not isinstance(args, dict):
            return None
        return ToolCall(tool=tool_name, parameters=args)

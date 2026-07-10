"""
Adaptadores de herramientas del agente.

Cada adapter traduce entre:
- Parámetros planos que entiende el LLM.
- Llamadas a los microservice_client existentes (Security, Admin, Tutorias).
- Resultados técnicos en texto natural para el LLM.
"""

from .admin import AdminAdapter
from .security import SecurityAdapter
from .tutorias import TutoriasAdapter

__all__ = ["AdminAdapter", "SecurityAdapter", "TutoriasAdapter"]

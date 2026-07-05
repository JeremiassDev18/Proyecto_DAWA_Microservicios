from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Docente:
    id: str
    nombre: str
    disponibilidades: List[str] = field(default_factory=list)


@dataclass
class Tutoria:
    id: str
    estudiante_id: str
    carrera: str
    tema: str
    fecha_solicitud: str
    hora_solicitud: str
    estado: str = "solicitada"
    docente_id: Optional[str] = None
    asistencia: Optional[bool] = None
    bitacora: List[str] = field(default_factory=list)
    observaciones: List[str] = field(default_factory=list)
    creado_en: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CasoAcademico:
    id: str
    estudiante_id: str
    descripcion: str
    severidad: str
    estado: str = "abierto"
    creado_en: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Notificacion:
    id: str
    tutoria_id: str
    mensaje: str
    creado_en: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

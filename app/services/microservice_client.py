import os
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.utils.codigo_generator import generar_codigo_tutoria
from app.utils.logger import logger

_HTTP_ENABLED = os.getenv("MICROSOFT_HTTP_ENABLED", "").lower() in ("1", "true", "yes")

_SECURITY_BASE = settings.SECURITY_SERVICE_URL
_ADMIN_BASE = settings.ADMIN_SERVICE_URL
_TUTORIAS_BASE = settings.RESERVATION_SERVICE_URL
_INTERNAL_TOKEN = settings.INTERNAL_TOKEN


def _headers() -> dict:
    return {"Authorization": f"Bearer {_INTERNAL_TOKEN}", "Content-Type": "application/json"}


async def _http_get(url: str) -> Optional[dict | list]:
    if not _HTTP_ENABLED:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=_headers())
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"HTTP GET {url} falló: {e}")
    return None


async def _http_post(url: str, json_data: dict) -> Optional[dict]:
    if not _HTTP_ENABLED:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=json_data, headers=_headers())
            if resp.status_code in (200, 201):
                return resp.json()
    except Exception as e:
        logger.warning(f"HTTP POST {url} falló: {e}")
    return None


# ── security-service ───────────────────────────────────────────────────

USUARIOS_MOCK = {
    1: {"id": 1, "nombre": "Juan Pérez", "email": "jperez@unal.edu.pe", "tipo": "estudiante"},
    2: {"id": 2, "nombre": "María López", "email": "mlopez@unal.edu.pe", "tipo": "estudiante"},
    3: {"id": 3, "nombre": "Dr. Carlos Ruiz", "email": "cruiz@unal.edu.pe", "tipo": "docente"},
}


def get_usuario(usuario_id: int) -> dict | None:
    return USUARIOS_MOCK.get(usuario_id)


def validar_token(token: str) -> dict | None:
    if token == "mock-token-estudiante":
        return {"valido": True, "usuario_id": 1, "tipo": "estudiante"}
    if token == "mock-token-admin":
        return {"valido": True, "usuario_id": 3, "tipo": "admin"}
    if token == settings.INTERNAL_TOKEN:
        return {"valido": True, "usuario_id": 0, "tipo": "admin"}
    return None


# ── administration-service (asignaturas, docentes) ─────────────────────

DOCENTES_MOCK = [
    {"id": 1, "nombre": "Dr. Carlos Ruiz", "asignatura": "Matemáticas", "disponible": True},
    {"id": 2, "nombre": "Mg. Ana Torres", "asignatura": "Física", "disponible": True},
    {"id": 3, "nombre": "Dr. Luis Mendoza", "asignatura": "Química", "disponible": False},
    {"id": 4, "nombre": "Mg. Sofía García", "asignatura": "Literatura", "disponible": True},
]

ASIGNATURAS_MOCK = [
    {"id": 1, "nombre": "Matemáticas Básicas", "codigo": "MAT101", "docente": "Dr. Carlos Ruiz"},
    {"id": 2, "nombre": "Física General", "codigo": "FIS101", "docente": "Mg. Ana Torres"},
    {"id": 3, "nombre": "Química Orgánica", "codigo": "QUI101", "docente": "Dr. Luis Mendoza"},
    {"id": 4, "nombre": "Literatura Peruana", "codigo": "LIT101", "docente": "Mg. Sofía García"},
]


def buscar_docente(query: str) -> list[dict]:
    q = query.lower()
    return [
        d for d in DOCENTES_MOCK
        if q in d["nombre"].lower() or q in d["asignatura"].lower()
    ]


# ── tutorias-service ────────────────────────────────────────────────────

SOLICITUDES_MOCK = {}
contador_solicitudes = [0]


def crear_solicitud(usuario_id: int, asignatura: str, mensaje: str) -> dict:
    contador_solicitudes[0] += 1
    codigo = generar_codigo_tutoria()
    solicitud = {
        "id": contador_solicitudes[0],
        "codigo": codigo,
        "usuario_id": usuario_id,
        "asignatura": asignatura,
        "mensaje": mensaje,
        "estado": "pendiente",
        "creado_en": datetime.now().isoformat(),
    }
    SOLICITUDES_MOCK[solicitud["id"]] = solicitud
    return solicitud


def consultar_tutoria(usuario_id: int) -> list[dict]:
    return [
        s for s in SOLICITUDES_MOCK.values()
        if s["usuario_id"] == usuario_id
    ]


def cancelar_solicitud(id_solicitud: int) -> bool:
    if id_solicitud in SOLICITUDES_MOCK:
        SOLICITUDES_MOCK[id_solicitud]["estado"] = "cancelada"
        return True
    return False


def cambiar_horario(id_solicitud: int, nuevo_horario: str) -> dict | None:
    if id_solicitud in SOLICITUDES_MOCK:
        SOLICITUDES_MOCK[id_solicitud]["horario"] = nuevo_horario
        SOLICITUDES_MOCK[id_solicitud]["estado"] = "reprogramada"
        return SOLICITUDES_MOCK[id_solicitud]
    return None


def escalar_docente(id_solicitud: int) -> dict | None:
    if id_solicitud in SOLICITUDES_MOCK:
        SOLICITUDES_MOCK[id_solicitud]["estado"] = "escalada"
        return SOLICITUDES_MOCK[id_solicitud]
    return None


# ── dispatcher ─────────────────────────────────────────────────────────

INTENT_SERVICE_MAP = {
    "CREAR_SOLICITUD": lambda uid, msg: crear_solicitud(uid, "general", msg),
    "SOLICITAR_TUTORIA": lambda uid, msg: crear_solicitud(uid, "general", msg),
    "BUSCAR_DOCENTE": lambda uid, msg: buscar_docente(msg),
    "CANCELAR_SOLICITUD": lambda uid, msg: cancelar_solicitud(uid),
    "CAMBIAR_HORARIO": lambda uid, msg: cambiar_horario(uid, msg),
    "ESCALAR_DOCENTE": lambda uid, msg: escalar_docente(uid),
    "CONSULTAR_MIS_TUTORIAS": lambda uid, msg: consultar_tutoria(uid),
}

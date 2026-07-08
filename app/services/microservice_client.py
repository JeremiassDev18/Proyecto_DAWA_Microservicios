import json
import uuid
from typing import Any, Optional

import httpx
import pika

from app.core.config import settings
from app.utils.logger import logger


# ─── Security Client ───────────────────────────────────────────────────────────

class SecurityClient:
    def __init__(self):
        self._base = settings.SECURITY_SERVICE_URL
        self._internal_token = settings.INTERNAL_TOKEN

    def validar_token(self, token: str) -> Optional[dict]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self._base}/usuarios/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "valido": True,
                        "usuario_id": data.get("id"),
                        "tipo": "admin" if self._es_admin(data) else "estudiante",
                        "nombre": data.get("nombre", ""),
                        "email": data.get("email", ""),
                    }
        except httpx.RequestError as e:
            logger.warning(f"SecurityClient.validar_token falló: {e}")
        return None

    def get_usuario(self, usuario_id: int) -> Optional[dict]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self._base}/usuarios/{usuario_id}",
                    headers={"Authorization": f"Bearer {self._internal_token}"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except httpx.RequestError as e:
            logger.warning(f"SecurityClient.get_usuario({usuario_id}) falló: {e}")
        return None

    def _es_admin(self, user_data: dict) -> bool:
        roles = user_data.get("roles", []) or []
        return any(
            (r.get("nombre") or r.get("rol") or "").lower() == "admin"
            for r in roles
        )


# ─── Admin Client ──────────────────────────────────────────────────────────────

_API = "/api/administracion"

class AdminClient:
    def __init__(self):
        self._base = settings.ADMIN_SERVICE_URL
        self._internal_token = settings.INTERNAL_TOKEN

    def _get(self, path: str, params: dict | None = None) -> Optional[Any]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self._base}{path}",
                    params=params,
                    headers={"Authorization": f"Bearer {self._internal_token}"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except httpx.RequestError as e:
            logger.warning(f"AdminClient GET {path} falló: {e}")
        return None

    def buscar_docentes(self, query: str = "") -> list[dict]:
        data = self._get(f"{_API}/docentes/", params={"search": query} if query else None)
        return data if isinstance(data, list) else []

    def get_docente(self, docente_id: int) -> Optional[dict]:
        return self._get(f"{_API}/docentes/{docente_id}")

    def get_asignaturas(self) -> list[dict]:
        data = self._get(f"{_API}/asignaturas/")
        return data if isinstance(data, list) else []

    def get_asignatura(self, asignatura_id: int) -> Optional[dict]:
        return self._get(f"{_API}/asignaturas/{asignatura_id}")

    def get_horarios_docente(self, docente_id: int) -> list[dict]:
        data = self._get(f"{_API}/horarios/docente/{docente_id}")
        return data if isinstance(data, list) else []

    def get_carreras(self) -> list[dict]:
        data = self._get(f"{_API}/carreras/")
        return data if isinstance(data, list) else []

    def get_carrera(self, carrera_id: int) -> Optional[dict]:
        return self._get(f"{_API}/carreras/{carrera_id}")

    def get_estudiante(self, estudiante_id: int) -> Optional[dict]:
        return self._get(f"{_API}/estudiantes/{estudiante_id}")

    def validar_estudiante(self, estudiante_id: int) -> Optional[dict]:
        return self._get(f"{_API}/internos/validar-estudiante/{estudiante_id}")

    def disponibilidad_docente(self, docente_id: int) -> Optional[dict]:
        return self._get(f"{_API}/internos/disponibilidad-docente/{docente_id}")

    def get_facultades(self) -> list[dict]:
        data = self._get(f"{_API}/facultades/")
        return data if isinstance(data, list) else []

    def get_estudiante_docentes(self, estudiante_id: int) -> list[dict]:
        data = self._get(f"{_API}/internos/estudiantes/{estudiante_id}/docentes")
        return data if isinstance(data, list) else []

    def buscar_docentes_por_materia(self, materia: str) -> list[dict]:
        data = self._get(f"{_API}/docentes/", params={"materia": materia})
        return data if isinstance(data, list) else []

    def get_materias_estudiante(self, estudiante_id: int) -> list[dict]:
        data = self._get(f"{_API}/internos/estudiantes/{estudiante_id}/materias")
        return data if isinstance(data, list) else []


# ─── Tutorias REST Client (solo consultas) ─────────────────────────────────────

class TutoriasRestClient:
    def __init__(self):
        self._base = settings.TUTORIAS_SERVICE_URL
        self._headers = {
            "Authorization": f"Bearer {settings.INTERNAL_TOKEN}",
            "Content-Type": "application/json",
        }

    def consultar_mis_bitacoras(self, estudiante_id: int) -> list[dict]:
        try:
            resp = httpx.get(
                f"{self._base}/api/tutorias/estudiantes/{estudiante_id}/bitacoras",
                headers=self._headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("bitacoras", [])
        except Exception as e:
            logger.warning(f"TutoriasRestClient.consultar_mis_bitacoras({estudiante_id}) falló: {e}")
        return []


# ─── RabbitMQ Client ───────────────────────────────────────────────────────────

class RabbitMQClient:
    def __init__(self):
        self._host = settings.RABBITMQ_HOST
        self._port = settings.RABBITMQ_PORT
        self._user = settings.RABBITMQ_USER
        self._pass = settings.RABBITMQ_PASS
        self._solicitudes_queue = settings.RABBITMQ_QUEUE_SOLICITUDES
        self._eventos_queue = settings.RABBITMQ_QUEUE_EVENTOS
        self._timeout = settings.RABBITMQ_RESPONSE_TIMEOUT
        self._connection = None
        self._channel = None

    def _connect(self):
        if self._connection is None or self._connection.is_closed:
            credentials = pika.PlainCredentials(self._user, self._pass)
            params = pika.ConnectionParameters(
                host=self._host, port=self._port, credentials=credentials,
                heartbeat=600, blocked_connection_timeout=300,
            )
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self._solicitudes_queue, durable=True)
            self._channel.queue_declare(queue=self._eventos_queue, durable=True)

    def _ensure_connection(func):
        def wrapper(self, *args, **kwargs):
            self._connect()
            try:
                return func(self, *args, **kwargs)
            except (pika.exceptions.ConnectionClosed,
                    pika.exceptions.ChannelClosed) as e:
                logger.warning(f"RabbitMQ reconectando: {e}")
                self._connection = None
                self._connect()
                return func(self, *args, **kwargs)
        return wrapper

    @_ensure_connection
    def publish_and_wait(self, payload: dict) -> dict | None:
        correlation_id = str(uuid.uuid4())
        result_queue = self._channel.queue_declare(queue='', exclusive=True)
        callback_queue = result_queue.method.queue

        self._response = None

        def on_response(ch, method, properties, body):
            if properties.correlation_id == correlation_id:
                self._response = json.loads(body)

        self._channel.basic_consume(
            queue=callback_queue, on_message_callback=on_response, auto_ack=True,
        )

        self._channel.basic_publish(
            exchange='',
            routing_key=self._solicitudes_queue,
            properties=pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=correlation_id,
                delivery_mode=2,
            ),
            body=json.dumps(payload, ensure_ascii=False).encode(),
        )
        logger.info(f"RMQ publish: tipo={payload.get('tipo')} correlation={correlation_id}")

        self._connection.process_data_events(time_limit=self._timeout)
        return self._response

    def publish(self, payload: dict):
        self._connect()
        try:
            self._channel.basic_publish(
                exchange='',
                routing_key=self._solicitudes_queue,
                properties=pika.BasicProperties(delivery_mode=2),
                body=json.dumps(payload, ensure_ascii=False).encode(),
            )
            logger.info(f"RMQ publish (fire&forget): tipo={payload.get('tipo')}")
        except Exception as e:
            logger.warning(f"RMQ publish falló: {e}")
            self._connection = None

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()


# ─── Tutorias Client ───────────────────────────────────────────────────────────

class TutoriasClient:
    def _call(self, tipo: str, datos: dict) -> Optional[Any]:
        payload = {"tipo": tipo, "datos": datos}
        client = get_rabbitmq_client()
        try:
            resp = client.publish_and_wait(payload)
            if resp is not None:
                return resp.get("datos") or resp
        except Exception as e:
            logger.warning(f"TutoriasClient.{tipo} falló: {e}")
        return None

    def registrar_docente(self, id: int, nombre: str, disponibilidades: list) -> Optional[dict]:
        return self._call("registrar_docente", {
            "id": id, "nombre": nombre, "disponibilidades": disponibilidades,
        })

    def registrar_solicitud(self, estudiante_id: int, tema: str,
                            asignatura_id: int | None = None,
                            periodo_id: int | None = None,
                            fecha_solicitud: str | None = None,
                            fecha_agendada: str | None = None) -> Optional[dict]:
        return self._call("registrar_solicitud", {
            "estudiante_id": estudiante_id,
            "asignatura_id": asignatura_id,
            "periodo_id": periodo_id,
            "tema": tema,
            "fecha_solicitud": fecha_solicitud,
            "fecha_agendada": fecha_agendada,
        })

    def validar_disponibilidad(self, docente_id: int, fecha: str) -> Optional[dict]:
        return self._call("validar_disponibilidad", {
            "docente_id": docente_id, "fecha": fecha,
        })

    def asignar_tutoria(self, tutoria_id: int, docente_id: int,
                        usuario_id: int | None = None) -> Optional[dict]:
        return self._call("asignar_tutoria", {
            "tutoria_id": tutoria_id, "docente_id": docente_id,
            "usuario_id": usuario_id,
        })

    def confirmar_tutoria(self, tutoria_id: int, motivo: str = "",
                          usuario_id: int | None = None,
                          rol_usuario: str | None = None) -> Optional[dict]:
        return self._call("confirmar_tutoria", {
            "tutoria_id": tutoria_id, "motivo": motivo,
            "usuario_id": usuario_id, "rol_usuario": rol_usuario,
        })

    def cancelar_tutoria(self, tutoria_id: int, motivo: str = "",
                         usuario_id: int | None = None,
                         rol_usuario: str | None = None) -> Optional[dict]:
        return self._call("cancelar_tutoria", {
            "tutoria_id": tutoria_id, "motivo": motivo,
            "usuario_id": usuario_id, "rol_usuario": rol_usuario,
        })

    def registrar_asistencia(self, tutoria_id: int, asistio: bool,
                             usuario_id: int | None = None) -> Optional[dict]:
        return self._call("registrar_asistencia", {
            "tutoria_id": tutoria_id, "asistio": asistio,
            "usuario_id": usuario_id,
        })

    def registrar_bitacora(self, tutoria_id: int, detalle: str,
                           temas_detectados: str | None = None,
                           usuario_id: int | None = None) -> Optional[dict]:
        return self._call("registrar_bitacora", {
            "tutoria_id": tutoria_id, "detalle": detalle,
            "temas_detectados": temas_detectados,
            "usuario_id": usuario_id,
        })

    def gestionar_estado(self, tutoria_id: int, estado: str,
                         usuario_id: int | None = None,
                         rol_usuario: str | None = None,
                         comentario: str | None = None) -> Optional[dict]:
        return self._call("gestionar_estado", {
            "tutoria_id": tutoria_id, "estado": estado,
            "usuario_id": usuario_id, "rol_usuario": rol_usuario,
            "comentario": comentario,
        })

    def registrar_caso_academico(self, estudiante_id: int, descripcion: str,
                                 severidad: str) -> Optional[dict]:
        return self._call("registrar_caso_academico", {
            "estudiante_id": estudiante_id, "descripcion": descripcion,
            "severidad": severidad,
        })

    def reporte_docente(self, docente_id: int,
                        periodo_id: int | None = None) -> Optional[dict]:
        data: dict[str, Any] = {"docente_id": docente_id}
        if periodo_id:
            data["periodo_id"] = periodo_id
        return self._call("reporte_docente", data)

    def reporte_estudiantes(self, periodo_id: int | None = None) -> Optional[dict]:
        data: dict[str, Any] = {}
        if periodo_id:
            data["periodo_id"] = periodo_id
        return self._call("reporte_estudiantes", data)

    def reporte_temas(self, periodo_id: int | None = None) -> Optional[dict]:
        data: dict[str, Any] = {}
        if periodo_id:
            data["periodo_id"] = periodo_id
        return self._call("reporte_temas", data)

    def consultar_mis_tutorias(self, estudiante_id: int,
                               periodo_id: int | None = None) -> list[dict]:
        data: dict[str, Any] = {"estudiante_id": estudiante_id}
        if periodo_id:
            data["periodo_id"] = periodo_id
        result = self._call("consultar_mis_tutorias", data)
        return result if isinstance(result, list) else []


# ─── Factory functions ─────────────────────────────────────────────────────────

_security_client: SecurityClient | None = None
_admin_client: AdminClient | None = None
_rabbitmq_client: RabbitMQClient | None = None
_tutorias_client: TutoriasClient | None = None
_tutorias_rest_client: TutoriasRestClient | None = None


def get_security_client() -> SecurityClient:
    global _security_client
    if _security_client is None:
        _security_client = SecurityClient()
    return _security_client


def get_admin_client() -> AdminClient:
    global _admin_client
    if _admin_client is None:
        _admin_client = AdminClient()
    return _admin_client


def get_rabbitmq_client() -> RabbitMQClient:
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient()
    return _rabbitmq_client


def get_tutorias_client() -> TutoriasClient:
    global _tutorias_client
    if _tutorias_client is None:
        _tutorias_client = TutoriasClient()
    return _tutorias_client


def get_tutorias_rest_client() -> TutoriasRestClient:
    global _tutorias_rest_client
    if _tutorias_rest_client is None:
        _tutorias_rest_client = TutoriasRestClient()
    return _tutorias_rest_client

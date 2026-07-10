"""
Worker RabbitMQ para precalcular resúmenes de bitácoras de tutorías.

Escucha la cola `tutorias.eventos` y, cuando llega un evento del tipo
`bitacora_registrada`, genera un resumen amigable para estudiantes y lo
persiste en la tabla `bitacora_resumen` del chatbot-service.

Ejecución:
    python -m app.worker.summary_worker

Variables de entorno (toman defaults de app.core.config):
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS,
    RABBITMQ_QUEUE_EVENTOS, DB_* (para chatbotdb),
    OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT
"""

import json
import logging
import os
import sys
import uuid
from typing import Any

import pika

# Permite importar app.* cuando se ejecuta desde la raíz del proyecto
# o como módulo (python -m app.worker.summary_worker).
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.core.config import settings
from app.db import postgres_client
from app.db import queries
from app.agent.ollama_client import OllamaClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BitacoraSummaryWorker:
    """Worker que resumen bitácoras de tutorías a medida que se registran."""

    def __init__(self):
        self.ollama = OllamaClient()
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.channel.Channel | None = None

    def _connect(self) -> None:
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASS
        )
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(
            queue=settings.RABBITMQ_QUEUE_EVENTOS, durable=True
        )
        logger.info(
            f"Conectado a RabbitMQ en {settings.RABBITMQ_HOST}:"
            f"{settings.RABBITMQ_PORT}, cola {settings.RABBITMQ_QUEUE_EVENTOS}"
        )

    def _ensure_connection(self) -> None:
        if self._connection is None or self._connection.is_closed:
            self._connect()

    def _generar_resumen(self, observaciones: str, temas: str | None) -> str:
        """Genera un resumen amigable; usa LLM si está disponible o un fallback simple."""
        texto = observaciones or ""
        if temas:
            texto += f". Temas detectados: {temas}"

        if not texto.strip():
            return "Sesión registrada sin observaciones detalladas."

        try:
            prompt = (
                "Resume en una oración corta y amigable para un estudiante "
                "qué se trató en su sesión de tutoría. No uses lenguaje técnico "
                "ni nombres de docentes. Texto:\n"
                f"{texto}\n\nResumen:"
            )
            resp = self.ollama.chat(
                messages=[
                    {"role": "system", "content": "Eres un asistente académico breve."},
                    {"role": "user", "content": prompt},
                ]
            )
            if resp and resp.finish_reason == "stop" and resp.content:
                return resp.content.strip()
        except Exception as e:
            logger.warning(f"[SummaryWorker] LLM no disponible, usando fallback: {e}")

        # Fallback: primera oración.
        return texto.split(".")[0].strip() + "."

    def _procesar_bitacora_registrada(self, datos: dict[str, Any]) -> None:
        """Genera y guarda el resumen de una bitácora recién registrada."""
        solicitud_id = datos.get("solicitud_id") or datos.get("tutoria_id")
        observaciones = datos.get("detalle") or datos.get("observaciones", "")
        temas_detectados = datos.get("temas_detectados")

        if not solicitud_id:
            logger.warning("[SummaryWorker] evento bitacora_registrada sin solicitud_id")
            return

        conn = None
        try:
            conn = postgres_client.get_connection()

            # Evitar reprocesamiento del mismo evento por correlation_id si viene.
            # El idempotencia por solicitud_id es suficiente para este caso.
            resumen_existente = queries.get_bitacora_resumen_by_solicitud(conn, int(solicitud_id))
            if resumen_existente:
                logger.info(f"[SummaryWorker] resumen ya existe para solicitud {solicitud_id}")
                return

            # Resolver estudiante_id si no viene en el evento.
            estudiante_id = datos.get("estudiante_id")
            if estudiante_id is None:
                # Consultar el servicio de tutorías vía HTTP interno.
                estudiante_id = self._resolver_estudiante_por_solicitud(int(solicitud_id))

            if estudiante_id is None:
                logger.warning(f"[SummaryWorker] no se pudo resolver estudiante para solicitud {solicitud_id}")
                return

            resumen = self._generar_resumen(str(observaciones), temas_detectados)

            queries.insert_bitacora_resumen(
                conn,
                solicitud_id=int(solicitud_id),
                estudiante_id=int(estudiante_id),
                observaciones=str(observaciones),
                resumen=resumen,
                temas_detectados=temas_detectados,
            )
            logger.info(f"[SummaryWorker] resumen guardado solicitud={solicitud_id}")
        except Exception as e:
            logger.error(f"[SummaryWorker] error procesando bitácora {solicitud_id}: {e}")
        finally:
            if conn:
                postgres_client.release_connection(conn)

    def _resolver_estudiante_por_solicitud(self, solicitud_id: int) -> int | None:
        """Consulta al tutorias-service REST para obtener el estudiante_id."""
        import httpx
        try:
            url = f"{settings.TUTORIAS_SERVICE_URL}/api/tutorias/solicitudes/{solicitud_id}"
            headers = {"Authorization": f"Bearer {settings.INTERNAL_TOKEN}"}
            resp = httpx.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("estudiante_id")
        except Exception as e:
            logger.warning(f"[SummaryWorker] error consultando solicitud {solicitud_id}: {e}")
        return None

    def _callback(
        self,
        ch: pika.channel.Channel,
        method: pika.frame.Method,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        try:
            mensaje = json.loads(body)
            tipo = mensaje.get("tipo")
            datos = mensaje.get("datos", {})
            evento_id = str(properties.correlation_id or uuid.uuid4())

            logger.info(f"[SummaryWorker] evento recibido tipo={tipo}")

            if tipo == "bitacora_registrada":
                self._procesar_bitacora_registrada(datos)
            else:
                logger.debug(f"[SummaryWorker] evento ignorado: {tipo}")

            # Registrar evento procesado (idempotencia).
            try:
                conn = postgres_client.get_connection()
                if not queries.existe_evento_procesado(conn, evento_id):
                    queries.insert_evento_procesado(conn, evento_id, tipo, datos)
            except Exception as e:
                logger.warning(f"[SummaryWorker] no se pudo guardar evento procesado: {e}")
            finally:
                if conn:
                    postgres_client.release_connection(conn)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"[SummaryWorker] error en callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self) -> None:
        """Inicia el consumo de eventos."""
        self._ensure_connection()
        if self._channel is None:
            raise RuntimeError("No se pudo obtener canal de RabbitMQ")

        self._channel.basic_qos(prefetch_count=1)
        self._channel.basic_consume(
            queue=settings.RABBITMQ_QUEUE_EVENTOS,
            on_message_callback=self._callback,
        )
        logger.info("[SummaryWorker] esperando eventos...")
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("[SummaryWorker] deteniendo...")
            self.stop()

    def stop(self) -> None:
        if self._channel and not self._channel.is_closed:
            self._channel.stop_consuming()
        if self._connection and not self._connection.is_closed:
            self._connection.close()


def main() -> None:
    postgres_client.init_pool(minconn=1, maxconn=3)
    worker = BitacoraSummaryWorker()
    worker.start()


if __name__ == "__main__":
    main()

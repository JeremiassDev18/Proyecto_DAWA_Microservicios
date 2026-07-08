import json
import logging
import pika
import sys
import os
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.tutorias_service.service import TutoriasService
    from backend.tutorias_service.database import Base, engine, SessionLocal
    from backend.administracion_client import AdministracionClient
    from backend.api import start_api_thread
except ImportError:
    from tutorias_service.service import TutoriasService
    from tutorias_service.database import Base, engine, SessionLocal
    from administracion_client import AdministracionClient
    from api import start_api_thread

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TutoriasWorker:
    def __init__(self, rabbitmq_host=None, administracion_url=None):
        if rabbitmq_host is None:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        if administracion_url is None:
            administracion_url = os.getenv('ADMINISTRACION_URL')

        Base.metadata.create_all(bind=engine)

        admin_client = AdministracionClient(base_url=administracion_url) if administracion_url else None
        self.service = TutoriasService(
            db_session_factory=SessionLocal,
            admin_client=admin_client,
        )
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.setup_connection()

    def setup_connection(self):
        """Conectar a RabbitMQ"""
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Intentando conectar a RabbitMQ en {self.rabbitmq_host}...")
                credentials = pika.PlainCredentials('guest', 'guest')
                parameters = pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    credentials=credentials,
                    connection_attempts=5,
                    retry_delay=2
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declarar colas
                self.channel.queue_declare(queue='tutorias.solicitudes', durable=True)
                self.channel.queue_declare(queue='tutorias.eventos', durable=True)
                
                logger.info("✅ Conectado a RabbitMQ correctamente")
                return
            except Exception as e:
                retry_count += 1
                logger.warning(f"Intento {retry_count}/{max_retries} fallido: {e}")
                if retry_count < max_retries:
                    import time
                    time.sleep(3)
                else:
                    logger.error(f"Error crítico conectando a RabbitMQ después de {max_retries} intentos: {e}")
                    raise

    def publish_event(self, event_type, data):
        """Publicar evento en la cola de eventos"""
        event = {
            'tipo': event_type,
            'datos': data
        }
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key='tutorias.eventos',
                body=json.dumps(event),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"Evento publicado: {event_type}")
        except Exception as e:
            logger.error(f"Error publicando evento: {e}")

    def handle_registrar_solicitud(self, message):
        """TUT-R01: Registro de solicitudes de tutoría"""
        try:
            data = message['datos']
            resultado = self.service.registrar_solicitud_tutoria(
                estudiante_id=data['estudiante_id'],
                asignatura_id=data.get('asignatura_id'),
                periodo_id=data.get('periodo_id'),
                tema=data['tema'],
                fecha_solicitud=data.get('fecha_solicitud'),
                fecha_agendada=data.get('fecha_agendada'),
            )
            self.publish_event('tutoria_solicitada', resultado)
            logger.info(f"Solicitud registrada: {resultado['id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error registrando solicitud: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_validar_disponibilidad(self, message):
        """TUT-R02: Validación de disponibilidad docente"""
        try:
            data = message['datos']
            disponible = self.service.validar_disponibilidad_docente(
                docente_id=data['docente_id'],
                fecha=data['fecha']
            )
            resultado = {
                'docente_id': data['docente_id'],
                'fecha': data['fecha'],
                'disponible': disponible
            }
            self.publish_event('disponibilidad_validada', resultado)
            logger.info(f"Disponibilidad validada: {resultado}")
            return resultado
        except Exception as e:
            logger.error(f"Error validando disponibilidad: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_registrar_docente(self, message):
        """Registrar docente"""
        try:
            data = message['datos']
            resultado = self.service.registrar_docente(
                docente_id=data['id'],
                nombre=data['nombre'],
                disponibilidades=data.get('disponibilidades', [])
            )
            self.publish_event('docente_registrado', resultado)
            logger.info(f"Docente registrado: {resultado['id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error registrando docente: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_asignar_tutoria(self, message):
        """TUT-R03: Asignación de tutorías a docentes"""
        try:
            data = message['datos']
            resultado = self.service.asignar_tutoria(
                tutoria_id=data['tutoria_id'],
                docente_id=data['docente_id'],
                usuario_id=data.get('usuario_id'),
            )
            if resultado['asignada']:
                self.publish_event('tutoria_asignada', resultado)
                logger.info(f"Tutoría asignada: {data['tutoria_id']}")
                return resultado
            else:
                self.publish_event('asignacion_rechazada', resultado)
                logger.warning(f"Asignación rechazada: {resultado['motivo']}")
                return resultado
        except Exception as e:
            logger.error(f"Error asignando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_confirmar_tutoria(self, message):
        """TUT-R04: Confirmación de tutorías"""
        try:
            data = message['datos']
            resultado = self.service.confirmar_o_cancelar_tutoria(
                tutoria_id=data['tutoria_id'],
                accion='confirmar',
                motivo=data.get('motivo'),
                usuario_id=data.get('usuario_id'),
                rol_usuario=data.get('rol_usuario'),
            )
            self.publish_event('tutoria_confirmada', resultado)
            logger.info(f"Tutoría confirmada: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error confirmando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_cancelar_tutoria(self, message):
        """TUT-R04: Cancelación de tutorías"""
        try:
            data = message['datos']
            resultado = self.service.confirmar_o_cancelar_tutoria(
                tutoria_id=data['tutoria_id'],
                accion='cancelar',
                motivo=data.get('motivo'),
                usuario_id=data.get('usuario_id'),
                rol_usuario=data.get('rol_usuario'),
            )
            self.publish_event('tutoria_cancelada', resultado)
            logger.info(f"Tutoría cancelada: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error cancelando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_registrar_asistencia(self, message):
        """TUT-R05: Registro de asistencia del estudiante"""
        try:
            data = message['datos']
            resultado = self.service.registrar_asistencia_estudiante(
                tutoria_id=data['tutoria_id'],
                asistio=data['asistio'],
                usuario_id=data.get('usuario_id'),
            )
            self.publish_event('asistencia_registrada', resultado)
            logger.info(f"Asistencia registrada: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error registrando asistencia: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_registrar_bitacora(self, message):
        """TUT-R06: Registro de bitácora de atención"""
        try:
            data = message['datos']
            resultado = self.service.registrar_bitacora_atencion(
                tutoria_id=data['tutoria_id'],
                detalle=data['detalle'],
                temas_detectados=data.get('temas_detectados'),
                usuario_id=data.get('usuario_id'),
            )
            self.publish_event('bitacora_registrada', resultado)
            logger.info(f"Bitácora registrada: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error registrando bitácora: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_gestionar_estado(self, message):
        """TUT-R07: Gestión de estados de la tutoría"""
        try:
            data = message['datos']
            resultado = self.service.gestionar_estado_tutoria(
                tutoria_id=data['tutoria_id'],
                estado=data['estado'],
                usuario_id=data.get('usuario_id'),
                rol_usuario=data.get('rol_usuario'),
                comentario=data.get('comentario'),
            )
            self.publish_event('estado_gestionado', resultado)
            logger.info(f"Estado gestionado: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error gestionando estado: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_registrar_caso_academico(self, message):
        """TUT-R08: Seguimiento de casos académicos"""
        try:
            data = message['datos']
            resultado = self.service.registrar_seguimiento_caso_academico(
                estudiante_id=data['estudiante_id'],
                descripcion=data['descripcion'],
                severidad=data['severidad']
            )
            self.publish_event('caso_academico_registrado', resultado)
            logger.info(f"Caso académico registrado: {resultado['id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error registrando caso académico: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_reporte_docente(self, message):
        """TUT-R09: Reporte de tutorías por docente"""
        try:
            data = message['datos']
            resultado = self.service.generar_reporte_tutorias_por_docente(
                docente_id=data['docente_id'],
                periodo_id=data.get('periodo_id'),
            )
            self.publish_event('reporte_docente_generado', resultado)
            logger.info(f"Reporte de docente generado: {data['docente_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error generando reporte de docente: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_reporte_estudiantes(self, message):
        """TUT-R10: Reporte de estudiantes atendidos"""
        try:
            data = message.get('datos', {})
            resultado = self.service.generar_reporte_estudiantes_atendidos(
                periodo_id=data.get('periodo_id'),
            )
            self.publish_event('reporte_estudiantes_generado', resultado)
            logger.info("Reporte de estudiantes generado")
            return resultado
        except Exception as e:
            logger.error(f"Error generando reporte de estudiantes: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_reporte_temas(self, message):
        """TUT-R11: Reporte de temas académicos recurrentes"""
        try:
            data = message.get('datos', {})
            resultado = self.service.generar_reporte_temas_recurrentes(
                periodo_id=data.get('periodo_id'),
            )
            self.publish_event('reporte_temas_generado', resultado)
            logger.info("Reporte de temas generado")
            return resultado
        except Exception as e:
            logger.error(f"Error generando reporte de temas: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_consultar_mis_tutorias(self, message):
        """Consultar tutorías de un estudiante"""
        try:
            data = message['datos']
            resultado = self.service.consultar_tutorias_por_estudiante(
                estudiante_id=data['estudiante_id'],
                periodo_id=data.get('periodo_id'),
            )
            logger.info(f"Tutorías consultadas para estudiante {data['estudiante_id']}: {len(resultado)} encontradas")
            return resultado
        except Exception as e:
            logger.error(f"Error consultando tutorías: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def handle_notificar_cambio(self, message):
        """TUT-R12: Notificaciones internas sobre cambios de estado"""
        try:
            data = message['datos']
            resultado = self.service.notificar_cambio_estado(
                tutoria_id=data['tutoria_id'],
                estado=data['estado'],
                destinatario_id=data.get('destinatario_id'),
                destinatario_rol=data.get('destinatario_rol', 'estudiante'),
            )
            self.publish_event('cambio_notificado', resultado)
            logger.info(f"Notificación enviada: {data['tutoria_id']}")
            return resultado
        except Exception as e:
            logger.error(f"Error notificando cambio: {e}")
            self.publish_event('error', {'mensaje': str(e)})
            raise

    def process_message(self, ch, method, properties, body):
        """Procesar mensaje recibido"""
        try:
            message = json.loads(body)
            event_type = message.get('tipo')
            
            logger.info(f"Evento recibido: {event_type}")
            
            # Router de eventos
            handlers = {
                'registrar_solicitud': self.handle_registrar_solicitud,
                'validar_disponibilidad': self.handle_validar_disponibilidad,
                'registrar_docente': self.handle_registrar_docente,
                'asignar_tutoria': self.handle_asignar_tutoria,
                'confirmar_tutoria': self.handle_confirmar_tutoria,
                'cancelar_tutoria': self.handle_cancelar_tutoria,
                'registrar_asistencia': self.handle_registrar_asistencia,
                'registrar_bitacora': self.handle_registrar_bitacora,
                'gestionar_estado': self.handle_gestionar_estado,
                'registrar_caso_academico': self.handle_registrar_caso_academico,
                'reporte_docente': self.handle_reporte_docente,
                'reporte_estudiantes': self.handle_reporte_estudiantes,
                'reporte_temas': self.handle_reporte_temas,
                'consultar_mis_tutorias': self.handle_consultar_mis_tutorias,
                'notificar_cambio': self.handle_notificar_cambio,
            }
            
            handler = handlers.get(event_type)
            resultado = None
            if handler:
                resultado = handler(message)
            else:
                logger.warning(f"Evento desconocido: {event_type}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # Responder al RPC si el mensaje trae reply_to
            if properties.reply_to:
                response = json.dumps({
                    "estado": "ok",
                    "datos": resultado
                }).encode()
                ch.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    ),
                    body=response
                )
                logger.info(f"Respuesta RPC enviada a {properties.reply_to}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if properties and properties.reply_to:
                ch.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    ),
                    body=json.dumps({"estado": "error", "mensaje": str(e)}).encode()
                )

    def start(self):
        """Iniciar el worker y la API REST"""
        try:
            logger.info("Iniciando worker de tutorias...")
            start_api_thread(self.service)
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='tutorias.solicitudes',
                on_message_callback=self.process_message
            )
            logger.info("Esperando eventos en tutorias.solicitudes...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Cerrando worker...")
            self.channel.stop_consuming()
            self.connection.close()
        except Exception as e:
            logger.error(f"Error en el worker: {e}")
            if self.connection:
                self.connection.close()


if __name__ == '__main__':
    worker = TutoriasWorker()
    worker.start()

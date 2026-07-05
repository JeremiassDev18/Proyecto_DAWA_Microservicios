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
except ImportError:
    # Intenta importar directamente si no funciona el anterior
    from tutorias_service.service import TutoriasService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TutoriasWorker:
    def __init__(self, rabbitmq_host=None):
        if rabbitmq_host is None:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.service = TutoriasService()
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
                carrera=data['carrera'],
                tema=data['tema'],
                fecha_solicitud=data['fecha_solicitud'],
                hora_solicitud=data['hora_solicitud']
            )
            self.publish_event('tutoria_solicitada', resultado)
            logger.info(f"Solicitud registrada: {resultado['id']}")
        except Exception as e:
            logger.error(f"Error registrando solicitud: {e}")
            self.publish_event('error', {'mensaje': str(e)})

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
        except Exception as e:
            logger.error(f"Error validando disponibilidad: {e}")
            self.publish_event('error', {'mensaje': str(e)})

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
        except Exception as e:
            logger.error(f"Error registrando docente: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_asignar_tutoria(self, message):
        """TUT-R03: Asignación de tutorías a docentes"""
        try:
            data = message['datos']
            resultado = self.service.asignar_tutoria(
                tutoria_id=data['tutoria_id'],
                docente_id=data['docente_id']
            )
            if resultado['asignada']:
                self.publish_event('tutoria_asignada', resultado)
                logger.info(f"Tutoría asignada: {data['tutoria_id']}")
            else:
                self.publish_event('asignacion_rechazada', resultado)
                logger.warning(f"Asignación rechazada: {resultado['motivo']}")
        except Exception as e:
            logger.error(f"Error asignando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_confirmar_tutoria(self, message):
        """TUT-R04: Confirmación de tutorías"""
        try:
            data = message['datos']
            resultado = self.service.confirmar_o_cancelar_tutoria(
                tutoria_id=data['tutoria_id'],
                accion='confirmar',
                motivo=data.get('motivo')
            )
            self.publish_event('tutoria_confirmada', resultado)
            logger.info(f"Tutoría confirmada: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error confirmando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_cancelar_tutoria(self, message):
        """TUT-R04: Cancelación de tutorías"""
        try:
            data = message['datos']
            resultado = self.service.confirmar_o_cancelar_tutoria(
                tutoria_id=data['tutoria_id'],
                accion='cancelar',
                motivo=data.get('motivo')
            )
            self.publish_event('tutoria_cancelada', resultado)
            logger.info(f"Tutoría cancelada: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error cancelando tutoría: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_registrar_asistencia(self, message):
        """TUT-R05: Registro de asistencia del estudiante"""
        try:
            data = message['datos']
            resultado = self.service.registrar_asistencia_estudiante(
                tutoria_id=data['tutoria_id'],
                asistio=data['asistio']
            )
            self.publish_event('asistencia_registrada', resultado)
            logger.info(f"Asistencia registrada: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error registrando asistencia: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_registrar_bitacora(self, message):
        """TUT-R06: Registro de bitácora de atención"""
        try:
            data = message['datos']
            resultado = self.service.registrar_bitacora_atencion(
                tutoria_id=data['tutoria_id'],
                detalle=data['detalle']
            )
            self.publish_event('bitacora_registrada', resultado)
            logger.info(f"Bitácora registrada: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error registrando bitácora: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_gestionar_estado(self, message):
        """TUT-R07: Gestión de estados de la tutoría"""
        try:
            data = message['datos']
            resultado = self.service.gestionar_estado_tutoria(
                tutoria_id=data['tutoria_id'],
                estado=data['estado']
            )
            self.publish_event('estado_gestionado', resultado)
            logger.info(f"Estado gestionado: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error gestionando estado: {e}")
            self.publish_event('error', {'mensaje': str(e)})

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
        except Exception as e:
            logger.error(f"Error registrando caso académico: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_reporte_docente(self, message):
        """TUT-R09: Reporte de tutorías por docente"""
        try:
            data = message['datos']
            resultado = self.service.generar_reporte_tutorias_por_docente(
                docente_id=data['docente_id']
            )
            self.publish_event('reporte_docente_generado', resultado)
            logger.info(f"Reporte de docente generado: {data['docente_id']}")
        except Exception as e:
            logger.error(f"Error generando reporte de docente: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_reporte_estudiantes(self, message):
        """TUT-R10: Reporte de estudiantes atendidos"""
        try:
            resultado = self.service.generar_reporte_estudiantes_atendidos()
            self.publish_event('reporte_estudiantes_generado', resultado)
            logger.info("Reporte de estudiantes generado")
        except Exception as e:
            logger.error(f"Error generando reporte de estudiantes: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_reporte_temas(self, message):
        """TUT-R11: Reporte de temas académicos recurrentes"""
        try:
            resultado = self.service.generar_reporte_temas_recurrentes()
            self.publish_event('reporte_temas_generado', resultado)
            logger.info("Reporte de temas generado")
        except Exception as e:
            logger.error(f"Error generando reporte de temas: {e}")
            self.publish_event('error', {'mensaje': str(e)})

    def handle_notificar_cambio(self, message):
        """TUT-R12: Notificaciones internas sobre cambios de estado"""
        try:
            data = message['datos']
            resultado = self.service.notificar_cambio_estado(
                tutoria_id=data['tutoria_id'],
                estado=data['estado']
            )
            self.publish_event('cambio_notificado', resultado)
            logger.info(f"Notificación enviada: {data['tutoria_id']}")
        except Exception as e:
            logger.error(f"Error notificando cambio: {e}")
            self.publish_event('error', {'mensaje': str(e)})

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
                'notificar_cambio': self.handle_notificar_cambio,
            }
            
            handler = handlers.get(event_type)
            if handler:
                handler(message)
            else:
                logger.warning(f"Evento desconocido: {event_type}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self):
        """Iniciar el worker"""
        try:
            logger.info("Iniciando worker de tutorias...")
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

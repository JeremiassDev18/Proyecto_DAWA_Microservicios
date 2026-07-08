import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_client import init_pool, get_connection, release_connection
from app.db import queries


INTENT_EXAMPLES = {
    "SOLICITAR_TUTORIA": [
        "Necesito un tutor de Matemáticas",
        "Quiero apoyo académico en Física",
        "¿Pueden asignarme un tutor?",
        "Busco ayuda para mi curso de Programación",
        "Estoy atrasado en Cálculo, necesito un tutor",
        "Necesito reforzar Química",
        "Tengo dudas de Álgebra, necesito un tutor",
        "¿Cómo consigo un tutor para Redes?",
        "Necesito ayuda urgente con mi tesis",
        "Quiero que me ayuden con Estadística",
    ],
    "CONSULTAR_MIS_TUTORIAS": [
        "¿Cuántas tutorías tengo?",
        "Revisa mis tutorías activas",
        "¿En qué tutorías estoy inscrito?",
        "Muéstrame mis sesiones",
        "Lista de tutorías que he solicitado",
        "¿Tengo tutorías pendientes?",
        "Estado de mis tutorías",
        "¿Cuáles son mis tutorías registradas?",
        "Ver historial de tutorías",
        "¿Qué tutorías tengo programadas?",
    ],
    "CREAR_SOLICITUD": [
        "Quiero inscribirme en una tutoría",
        "Necesito agendar una tutoría",
        "Solicita una tutoría para mí",
        "Registra una tutoría de Cálculo",
        "Agenda una sesión de tutoría",
        "Aparta un espacio con un tutor",
        "Quiero pedir una tutoría de Base de Datos",
        "Crea una solicitud para tutoría grupal",
        "Registra mi interés en tutoría de Inglés",
        "Agéndame una tutoría con el profe de Física",
    ],
    "CANCELAR_SOLICITUD": [
        "Quiero cancelar mi tutoría",
        "Anula mi solicitud de tutoría",
        "Ya no necesito la tutoría programada",
        "Cancelar la tutoría de mañana",
        "Elimina la tutoría que pedí ayer",
        "No podré asistir, cancela la sesión",
        "Deja sin efecto mi solicitud",
        "Cancelar la cita con el tutor",
        "Quiero anular la reserva",
        "Ya resolví mis dudas, cancela la tutoría",
    ],
    "CAMBIAR_HORARIO": [
        "Quiero reprogramar mi tutoría",
        "Cambiar la hora de la tutoría",
        "¿Puedo mover la tutoría a otro día?",
        "Necesito cambiar el horario",
        "Adelantar la tutoría a las 2",
        "Recorre la tutoría media hora más tarde",
        "Atrasa la tutoría 1 hora por favor",
        "Cambiar la fecha de la tutoría",
        "Necesito reagendar urgente",
        "Pasar la tutoría al viernes",
    ],
    "BUSCAR_DOCENTE": [
        "Busca un profesor de Matemáticas",
        "¿Qué docentes hay disponibles?",
        "Necesito un profesor de Programación",
        "¿Quién enseña Física?",
        "Buscar docente de Química",
        "¿Hay profesor de Inglés?",
        "Docentes de la facultad",
        "¿Qué tutores están disponibles?",
        "Muéstrame los docentes",
        "Quiero saber qué profesores hay",
    ],
    "CONSULTAR_ASIGNATURA": [
        "¿Qué asignaturas tienen tutoría?",
        "¿Dan tutoría de Cálculo?",
        "¿Hay apoyo para Estadística?",
        "¿En qué materias hay tutorías?",
        "Lista de asignaturas con tutoría",
        "¿Tienen tutoría de Programación?",
        "¿Puedo recibir ayuda en Física?",
        "¿Qué cursos tienen tutor?",
        "Asignaturas disponibles para tutoría",
        "¿Hay tutorías de todas las materias?",
    ],
    "CONSULTAR_REGLAMENTO": [
        "¿Cuáles son las reglas de las tutorías?",
        "¿Hay límite de tutorías por ciclo?",
        "Normas de las tutorías",
        "¿Cuántas tutorías puedo tomar?",
        "Reglamento del programa de tutorías",
        "¿Las tutorías son gratuitas?",
        "Políticas del servicio de tutoría",
        "¿Cómo funciona el sistema de tutorías?",
        "Requisitos para solicitar tutoría",
        "¿Hay sanciones por inasistencia?",
    ],
    "CONSULTAR_FAQ": [
        "Preguntas frecuentes sobre tutorías",
        "¿Cómo funciona el chat de tutoría?",
        "¿Puedo cambiar de tutor?",
        "¿Cuánto duran las tutorías?",
        "FAQ del servicio de tutoría",
        "¿Las tutorías son individuales o grupales?",
        "¿Cómo sé si mi tutoría fue aceptada?",
        "¿Puedo tener tutoría virtual?",
        "¿Hay certificado por las tutorías?",
        "¿Cuándo empiezan las tutorías?",
    ],
    "HORARIO_TUTORIAS": [
        "¿En qué horarios hay tutorías?",
        "¿Las tutorías son presenciales?",
        "¿Hay tutorías virtuales?",
        "Horario de tutorías disponibles",
        "¿A qué hora son las tutorías?",
        "¿Hay tutorías los fines de semana?",
        "¿Dan tutoría en la noche?",
        "¿Cuándo puedo ir a tutoría?",
        "Horarios disponibles para tutoría",
        "¿Hay tutorías en la mañana?",
    ],
    "CONTACTAR_DOCENTE": [
        "¿Cómo contacto a mi tutor?",
        "Correo del profesor de Física",
        "Quiero el email del docente García",
        "Número de contacto del tutor",
        "¿Cómo escribo al coordinador?",
        "Dirección del profesor",
        "Muéstrame el correo del rector",
        "Teléfono del tutor",
        "¿Dónde encuentro al profesor?",
        "Oficina del docente de Matemáticas",
    ],
    "DISPONIBILIDAD_DOCENTE": [
        "¿Hay tutor disponible para Álgebra?",
        "¿Puedo conseguir tutoría de Física?",
        "¿Hay tutorías de Base de Datos?",
        "¿Qué profesor está disponible?",
        "¿Hay tutores disponibles esta semana?",
        "¿Quién puede ayudarme con Cálculo?",
        "Disponibilidad de tutores",
        "¿Hay un tutor libre ahora?",
        "¿Qué tutores tienen cupo?",
        "¿Puedo agendar con el profesor Ruiz?",
    ],
    "ESCALAR_DOCENTE": [
        "Necesito hablar con un supervisor",
        "Quiero escalar mi caso",
        "Quejarme sobre un tutor",
        "Necesito un docente de mayor rango",
        "Escalar mi solicitud de tutoría",
        "Quiero reportar un problema",
        "Necesito ayuda que mi tutor no resolvió",
        "Derivar mi caso a coordinación",
        "Quiero hablar con el coordinador",
        "Mi tutor no pudo ayudarme",
    ],
    "RESUMEN_SOLICITUD": [
        "Resumen de mis tutorías",
        "¿Puedes darme un resumen?",
        "Reporte de mis tutorías",
        "Necesito un resumen de mis sesiones",
        "¿Cuántas tutorías he tomado?",
        "Historial completo de tutorías",
        "Resumen de solicitudes",
        "Dame un reporte de mis avances",
        "¿Cómo voy en mis tutorías?",
        "Balance de mis tutorías",
    ],
    "SIN_INTENCION": [
        "Hola",
        "Buenos días",
        "Gracias",
        "Adiós",
        "Qué tal",
        "OK",
        "Entendido",
        "Claro",
        "Perfecto",
        "Hasta luego",
    ],
}


def main():
    init_pool()
    conn = get_connection()
    try:
        intenciones = {row[1]: row[0] for row in queries.get_all_intenciones(conn)}

        total = 0
        for nombre, ejemplos in INTENT_EXAMPLES.items():
            id_intencion = intenciones.get(nombre)
            if id_intencion is None:
                print(f"Intención '{nombre}' no encontrada en BD, se omite.")
                continue

            for texto in ejemplos:
                existing = queries.query_dataset(conn, texto_query=texto,
                                                  intencion=nombre)
                if existing:
                    print(f"  Ya existe: '{texto}' → {nombre}")
                    continue

                queries.insert_dataset(conn, texto, id_intencion, origen="manual")
                print(f"  Insertado: '{texto}' → {nombre}")
                total += 1

        print(f"\n✅ Seed completado: {total} ejemplos nuevos insertados.")
    finally:
        release_connection(conn)


if __name__ == "__main__":
    main()

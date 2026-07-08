import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.predictor import predict_with_confidence
from app.ml.setfit_trainer import models_exist

TEST_SET = [
    ("Quiero una tutoría", "SOLICITAR_TUTORIA"),
    ("Necesito un tutor", "SOLICITAR_TUTORIA"),
    ("Necesito apoyo académico", "SOLICITAR_TUTORIA"),
    ("Busco un tutor particular", "SOLICITAR_TUTORIA"),
    ("Requiero asesoría académica", "SOLICITAR_TUTORIA"),
    ("Ayúdame a entender el tema", "SOLICITAR_TUTORIA"),
    ("No entiendo Cálculo, necesito ayuda", "SOLICITAR_TUTORIA"),
    ("Quiero una tutoría de Programación", "SOLICITAR_TUTORIA"),
    ("Estoy atrasado en Redes, necesito un tutor", "SOLICITAR_TUTORIA"),
    ("Necesito un tutor de Matemáticas", "SOLICITAR_TUTORIA"),
    ("Necesito ayuda con mi tesis", "SOLICITAR_TUTORIA"),
    ("Quiero reforzar Matemáticas", "SOLICITAR_TUTORIA"),
    ("Necesito prepararme para el examen", "SOLICITAR_TUTORIA"),
    ("Muéstrame mis tutorías", "CONSULTAR_MIS_TUTORIAS"),
    ("¿Cuántas tutorías tengo?", "CONSULTAR_MIS_TUTORIAS"),
    ("Ver mis tutorías", "CONSULTAR_MIS_TUTORIAS"),
    ("Estado de mis tutorías", "CONSULTAR_MIS_TUTORIAS"),
    ("En qué tutorías estoy", "CONSULTAR_MIS_TUTORIAS"),
    ("Mis tutorías programadas", "CONSULTAR_MIS_TUTORIAS"),
    ("Revisar mis tutorías activas", "CONSULTAR_MIS_TUTORIAS"),
    ("¿Hay tutorías los lunes?", "HORARIO_TUTORIAS"),
    ("Cuál es el horario de tutorías", "HORARIO_TUTORIAS"),
    ("¿Las tutorías son presenciales o virtuales?", "HORARIO_TUTORIAS"),
    ("¿En qué horarios hay tutorías?", "HORARIO_TUTORIAS"),
    ("Hay tutorías los fines de semana", "HORARIO_TUTORIAS"),
    ("Cuánto dura cada tutoría", "HORARIO_TUTORIAS"),
    ("A qué hora empiezan las tutorías", "HORARIO_TUTORIAS"),
    ("¿Dan tutorías de Estadística?", "HORARIO_TUTORIAS"),
    ("Muéstrame el correo del rector", "CONTACTAR_DOCENTE"),
    ("¿Cómo contacto a mi tutor?", "CONTACTAR_DOCENTE"),
    ("Correo del profesor de Física", "CONTACTAR_DOCENTE"),
    ("Cómo contacto al profesor", "CONTACTAR_DOCENTE"),
    ("Datos de contacto del docente", "CONTACTAR_DOCENTE"),
    ("Quiero hablar con el coordinador", "CONTACTAR_DOCENTE"),
    ("¿Quién da Álgebra?", "CONTACTAR_DOCENTE"),
    ("Hay tutor disponibles para Sistemas Operativos", "DISPONIBILIDAD_DOCENTE"),
    ("¿Hay tutorías de Base de Datos?", "DISPONIBILIDAD_DOCENTE"),
    ("Hay tutores disponibles ahora", "DISPONIBILIDAD_DOCENTE"),
    ("Qué tutores están disponibles", "DISPONIBILIDAD_DOCENTE"),
    ("Hay profesor de Física disponible", "DISPONIBILIDAD_DOCENTE"),
    ("¿Hay tutores disponibles esta semana?", "DISPONIBILIDAD_DOCENTE"),
    ("Hay disponibilidad con el tutor de Cálculo", "DISPONIBILIDAD_DOCENTE"),
    ("¿Quién ganó el Mundial?", "SIN_INTENCION"),
    ("¿Cómo está el clima?", "SIN_INTENCION"),
    ("Cuál es la capital de Perú", "SIN_INTENCION"),
    ("Hola", "SIN_INTENCION"),
    ("Gracias", "SIN_INTENCION"),
    ("Buenos días", "SIN_INTENCION"),
    ("¿Cuánto es 2 más 2?", "SIN_INTENCION"),
    ("Qué día es hoy", "SIN_INTENCION"),
    ("Quién descubrió América", "SIN_INTENCION"),
    ("¿Cuántas tutorías puedo solicitar?", "CONSULTAR_FAQ"),
    ("¿Las tutorías tienen costo?", "CONSULTAR_FAQ"),
    ("¿Cómo funciona el sistema?", "CONSULTAR_FAQ"),
    ("Quiero crear una solicitud de tutoría", "CREAR_SOLICITUD"),
    ("Necesito agendar una tutoría", "CREAR_SOLICITUD"),
    ("Quiero cancelar mi tutoría", "CANCELAR_SOLICITUD"),
    ("Cancela la tutoría de mañana", "CANCELAR_SOLICITUD"),
    ("Quiero reprogramar mi tutoría", "CAMBIAR_HORARIO"),
    ("¿Puedo mover la tutoría a otro día?", "CAMBIAR_HORARIO"),
    ("¿Quién dicta Programación?", "BUSCAR_DOCENTE"),
    ("¿Qué profesor está disponible?", "BUSCAR_DOCENTE"),
    ("¿Cuándo es el examen de Cálculo?", "CONSULTAR_ASIGNATURA"),
    ("Prerrequisitos para cursar Base de Datos II", "CONSULTAR_ASIGNATURA"),
    ("Explícame el reglamento de tutorías", "CONSULTAR_REGLAMENTO"),
    ("¿Cuántas faltas están permitidas?", "CONSULTAR_REGLAMENTO"),
    ("Necesito hablar con el profesor", "ESCALAR_DOCENTE"),
    ("Quiero presentar una queja sobre mi tutor", "ESCALAR_DOCENTE"),
    ("Resumen de mis tutorías", "RESUMEN_SOLICITUD"),
    ("¿Cuántas tutorías he tenido?", "RESUMEN_SOLICITUD"),
    ("Necesito un tutor de Programación", "SOLICITAR_TUTORIA"),
    ("Quiero un docente", "SOLICITAR_TUTORIA"),
    ("Necesito ayuda urgente con mi tesis", "SOLICITAR_TUTORIA"),
    ("Lista de mis tutorías", "CONSULTAR_MIS_TUTORIAS"),
    ("¿Tengo tutorías pendientes?", "CONSULTAR_MIS_TUTORIAS"),
    ("¿Hay tutorías en la noche?", "HORARIO_TUTORIAS"),
    ("Modalidad de las tutorías", "HORARIO_TUTORIAS"),
    ("¿Cómo envío un mensaje al tutor?", "CONTACTAR_DOCENTE"),
    ("Email del tutor asignado", "CONTACTAR_DOCENTE"),
    ("¿Quién puede ayudarme con Álgebra Lineal?", "DISPONIBILIDAD_DOCENTE"),
    ("Hay tutor de Matemáticas disponible", "DISPONIBILIDAD_DOCENTE"),
    ("Cuál es el sílabo de Análisis Numérico", "CONSULTAR_ASIGNATURA"),
    ("¿La asignatura de Inglés es obligatoria?", "CONSULTAR_ASIGNATURA"),
    ("Normas para tutorías virtuales", "CONSULTAR_REGLAMENTO"),
    ("Política de cancelación", "CONSULTAR_REGLAMENTO"),
    ("¿Cuánto dura una tutoría?", "CONSULTAR_FAQ"),
    ("¿Puedo pedir tutoría de más de una materia?", "CONSULTAR_FAQ"),
    ("Necesito que un docente revise mi caso", "ESCALAR_DOCENTE"),
    ("Comunícame con el coordinador académico", "ESCALAR_DOCENTE"),
    ("Ver bitácora de tutorías", "RESUMEN_SOLICITUD"),
    ("Necesito un reporte de asistencia a tutorías", "RESUMEN_SOLICITUD"),
    ("Hasta luego", "SIN_INTENCION"),
    ("De acuerdo", "SIN_INTENCION"),
]


def evaluate():
    if not models_exist():
        print("ERROR: No hay modelo entrenado. Ejecuta POST /api/v1/train o scripts/train_setfit.py primero.")
        sys.exit(1)

    correctas = 0
    total = len(TEST_SET)
    confianza_acumulada = 0.0
    errores = []

    print(f"{'PREGUNTA':<55} {'ESPERADA':<28} {'PREDICHA':<28} {'CONF':<8} {'?'}")
    print("=" * 130)

    for texto, expected in TEST_SET:
        intent, confidence = predict_with_confidence(texto)
        acierto = intent == expected
        if acierto:
            correctas += 1
        else:
            errores.append((texto, expected, intent, confidence))
        confianza_acumulada += confidence
        marca = "✓" if acierto else "✗"
        print(f"{texto:<55} {expected:<28} {intent:<28} {confidence:<8.4f} {marca}")

    exactitud = correctas / total
    conf_promedio = confianza_acumulada / total

    print()
    print("=" * 130)
    print(f"Total: {total} preguntas")
    print(f"Exactitud: {exactitud:.2%} ({correctas}/{total})")
    print(f"Confianza promedio: {conf_promedio:.4f}")
    print(f"Errores: {len(errores)}")

    if errores:
        print()
        print("--- Errores ---")
        for texto, esperada, predicha, conf in errores:
            print(f"  [{conf:.4f}] '{texto}' → esperada: {esperada}, predicha: {predicha}")

    print()
    if exactitud >= 0.70:
        print("VEREDICTO: Modelo aceptable (≥70%)")
    elif exactitud >= 0.50:
        print("VEREDICTO: Modelo regular (50-70%) — necesita más datos")
    else:
        print("VEREDICTO: Modelo insuficiente (<50%) — requiere más entrenamiento y datos")

    if conf_promedio >= 0.60:
        print(f"Confianza promedio buena (≥{CONFIDENCE_THRESHOLD})")
    else:
        print(f"Confianza promedio baja (<{CONFIDENCE_THRESHOLD}) — considera ajustar umbral")


if __name__ == "__main__":
    from app.core.config import settings
    CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD
    evaluate()

from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Docente, Estudiante, Paralelo, Carrera, Asignatura, HorarioAtencion

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.route("/docentes", methods=["GET"])
def reporte_docentes():
    carrera_id = request.args.get("carrera_id")

    db = SessionLocal()

    try:
        consulta = db.query(Docente).filter(Docente.estado == True)

        docentes = consulta.all()
        resultado = []

        for docente in docentes:
            resultado.append({
                "id": docente.id,
                "nombres": docente.nombres,
                "apellidos": docente.apellidos,
                "correo": docente.correo,
                "telefono": docente.telefono,
                "especialidad": docente.especialidad,
                "facultad_id": docente.facultad_id,
                "carga_horaria_maxima": docente.carga_horaria_maxima
            })

        return jsonify({
            "filtro_carrera_id": carrera_id,
            "formato": "JSON",
            "mensaje": "Reporte de docentes generado correctamente",
            "data": resultado
        }), 200

    finally:
        db.close()


@reportes_bp.route("/estudiantes", methods=["GET"])
def reporte_estudiantes():
    carrera_id = request.args.get("carrera_id")
    periodo_id = request.args.get("periodo_id")

    db = SessionLocal()

    try:
        consulta = db.query(Estudiante).filter(Estudiante.estado == True)

        if carrera_id:
            consulta = consulta.filter(Estudiante.carrera_id == carrera_id)

        if periodo_id:
            consulta = consulta.filter(Estudiante.periodo_id == periodo_id)

        estudiantes = consulta.all()
        resultado = []

        for estudiante in estudiantes:
            resultado.append({
                "id": estudiante.id,
                "nombres": estudiante.nombres,
                "apellidos": estudiante.apellidos,
                "correo": estudiante.correo,
                "matricula": estudiante.matricula,
                "carrera_id": estudiante.carrera_id,
                "periodo_id": estudiante.periodo_id,
                "estado_academico": estudiante.estado_academico
            })

        return jsonify({
            "formato": "JSON",
            "mensaje": "Reporte de estudiantes generado correctamente",
            "data": resultado
        }), 200

    finally:
        db.close()


@reportes_bp.route("/tutorias", methods=["GET"])
def reporte_tutorias():
    carrera_id = request.args.get("carrera_id")
    periodo_id = request.args.get("periodo_id")
    docente_id = request.args.get("docente_id")

    db = SessionLocal()

    try:
        consulta = db.query(Paralelo).filter(Paralelo.estado == True)

        if carrera_id:
            consulta = consulta.filter(Paralelo.carrera_id == carrera_id)

        if periodo_id:
            consulta = consulta.filter(Paralelo.periodo_id == periodo_id)

        if docente_id:
            consulta = consulta.filter(Paralelo.docente_id == docente_id)

        paralelos = consulta.all()
        resultado = []

        for paralelo in paralelos:
            horarios = db.query(HorarioAtencion).filter(
                HorarioAtencion.docente_id == paralelo.docente_id,
                HorarioAtencion.estado == True
            ).all()

            resultado.append({
                "paralelo_id": paralelo.id,
                "paralelo": paralelo.nombre,
                "carrera_id": paralelo.carrera_id,
                "asignatura_id": paralelo.asignatura_id,
                "docente_id": paralelo.docente_id,
                "periodo_id": paralelo.periodo_id,
                "horarios_docente": [
                    {
                        "dia": horario.dia,
                        "hora_inicio": str(horario.hora_inicio),
                        "hora_fin": str(horario.hora_fin)
                    }
                    for horario in horarios
                ]
            })

        return jsonify({
            "formato": "JSON",
            "mensaje": "Reporte de tutorías generado correctamente",
            "nota": "La exportación PDF/Excel queda preparada para una fase posterior",
            "data": resultado
        }), 200

    finally:
        db.close()


@reportes_bp.route("/asignaturas", methods=["GET"])
def reporte_asignaturas():
    carrera_id = request.args.get("carrera_id")
    periodo_id = request.args.get("periodo_id")

    db = SessionLocal()

    try:
        consulta = db.query(Asignatura).filter(Asignatura.estado == True)

        if carrera_id:
            consulta = consulta.filter(Asignatura.carrera_id == carrera_id)

        if periodo_id:
            consulta = consulta.filter(Asignatura.periodo_id == periodo_id)

        asignaturas = consulta.all()
        resultado = []

        for asignatura in asignaturas:
            resultado.append({
                "id": asignatura.id,
                "nombre": asignatura.nombre,
                "codigo": asignatura.codigo,
                "creditos": asignatura.creditos,
                "nivel": asignatura.nivel,
                "carrera_id": asignatura.carrera_id,
                "periodo_id": asignatura.periodo_id
            })

        return jsonify({
            "formato": "JSON",
            "mensaje": "Reporte de asignaturas generado correctamente",
            "data": resultado
        }), 200

    finally:
        db.close()
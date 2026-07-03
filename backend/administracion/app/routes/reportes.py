from flask import Blueprint, jsonify
from app.database import SessionLocal
from app.models import Docente, Estudiante, Paralelo, Carrera, Asignatura, HorarioAtencion

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.route("/docentes", methods=["GET"])
def reporte_docentes():
    db = SessionLocal()
    try:
        docentes = db.query(Docente).filter(Docente.estado == True).all()
        resultado = []

        for docente in docentes:
            resultado.append({
                "id": docente.id,
                "nombres": docente.nombres,
                "apellidos": docente.apellidos,
                "correo": docente.correo,
                "telefono": docente.telefono,
                "especialidad": docente.especialidad
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@reportes_bp.route("/estudiantes", methods=["GET"])
def reporte_estudiantes():
    db = SessionLocal()
    try:
        estudiantes = db.query(Estudiante).filter(Estudiante.estado == True).all()
        resultado = []

        for estudiante in estudiantes:
            resultado.append({
                "id": estudiante.id,
                "nombres": estudiante.nombres,
                "apellidos": estudiante.apellidos,
                "correo": estudiante.correo,
                "matricula": estudiante.matricula,
                "carrera_id": estudiante.carrera_id
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@reportes_bp.route("/tutorias", methods=["GET"])
def reporte_tutorias():
    db = SessionLocal()
    try:
        paralelos = db.query(Paralelo).filter(Paralelo.estado == True).all()
        resultado = []

        for paralelo in paralelos:
            horarios = db.query(HorarioAtencion).filter(
                HorarioAtencion.paralelo_id == paralelo.id,
                HorarioAtencion.estado == True
            ).all()

            resultado.append({
                "paralelo_id": paralelo.id,
                "paralelo": paralelo.nombre,
                "carrera_id": paralelo.carrera_id,
                "asignatura_id": paralelo.asignatura_id,
                "docente_id": paralelo.docente_id,
                "periodo_id": paralelo.periodo_id,
                "horarios": [
                    {
                        "dia": horario.dia,
                        "hora_inicio": str(horario.hora_inicio),
                        "hora_fin": str(horario.hora_fin)
                    }
                    for horario in horarios
                ]
            })

        return jsonify(resultado), 200
    finally:
        db.close()
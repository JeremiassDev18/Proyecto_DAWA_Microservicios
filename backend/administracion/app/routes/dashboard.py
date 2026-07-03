from flask import Blueprint, jsonify
from app.database import SessionLocal
from app.models import Facultad, Carrera, Asignatura, Docente, Estudiante, Paralelo, PeriodoAcademico

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
def obtener_dashboard():
    db = SessionLocal()
    try:
        total_facultades = db.query(Facultad).filter(Facultad.estado == True).count()
        total_carreras = db.query(Carrera).filter(Carrera.estado == True).count()
        total_asignaturas = db.query(Asignatura).filter(Asignatura.estado == True).count()
        total_docentes = db.query(Docente).filter(Docente.estado == True).count()
        total_estudiantes = db.query(Estudiante).filter(Estudiante.estado == True).count()
        total_paralelos = db.query(Paralelo).filter(Paralelo.estado == True).count()
        total_periodos = db.query(PeriodoAcademico).filter(PeriodoAcademico.estado == True).count()

        return jsonify({
            "facultades": total_facultades,
            "carreras": total_carreras,
            "asignaturas": total_asignaturas,
            "docentes": total_docentes,
            "estudiantes": total_estudiantes,
            "paralelos": total_paralelos,
            "periodos_academicos": total_periodos
        }), 200
    finally:
        db.close()
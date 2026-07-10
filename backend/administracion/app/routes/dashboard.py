from flask import Blueprint, jsonify
from app.database import SessionLocal
from app.models import Facultad, Carrera, Asignatura, Docente, Estudiante, Paralelo, PeriodoAcademico

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
def obtener_dashboard():
    db = SessionLocal()

    try:
        facultades = db.query(Facultad).filter(Facultad.estado == True).count()
        carreras = db.query(Carrera).filter(Carrera.estado == True).count()
        asignaturas = db.query(Asignatura).filter(Asignatura.estado == True).count()
        docentes = db.query(Docente).filter(Docente.estado == True).count()
        estudiantes = db.query(Estudiante).filter(
            Estudiante.estado == True,
            Estudiante.estado_academico == "activo"
        ).count()
        periodos = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado == True,
            PeriodoAcademico.estado_periodo == "activo"
        ).count()

        return jsonify({
            "total_facultades": facultades,
            "total_carreras": carreras,
            "total_asignaturas": asignaturas,
            "total_docentes": docentes,
            "total_estudiantes": estudiantes,
            "periodos_activos": periodos,
        }), 200

    finally:
        db.close()
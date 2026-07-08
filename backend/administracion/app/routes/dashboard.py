from flask import Blueprint, jsonify
from app.database import SessionLocal
from app.models import Facultad, Carrera, Asignatura, Docente, Estudiante, Paralelo, PeriodoAcademico

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
def obtener_dashboard():
    db = SessionLocal()

    try:
        return jsonify({
            "facultades_activas": db.query(Facultad).filter(Facultad.estado == True).count(),
            "carreras_activas": db.query(Carrera).filter(Carrera.estado == True).count(),
            "asignaturas_activas": db.query(Asignatura).filter(Asignatura.estado == True).count(),
            "docentes_activos": db.query(Docente).filter(Docente.estado == True).count(),
            "estudiantes_activos": db.query(Estudiante).filter(
                Estudiante.estado == True,
                Estudiante.estado_academico == "activo"
            ).count(),
            "paralelos_activos": db.query(Paralelo).filter(Paralelo.estado == True).count(),
            "periodos_activos": db.query(PeriodoAcademico).filter(
                PeriodoAcademico.estado == True,
                PeriodoAcademico.estado_periodo == "activo"
            ).count()
        }), 200

    finally:
        db.close()
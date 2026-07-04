from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Asignatura, Docente, Estudiante, HorarioAtencion, PeriodoAcademico

internos_bp = Blueprint("internos", __name__)


@internos_bp.route("/validar-asignatura/<int:asignatura_id>", methods=["GET"])
def validar_asignatura(asignatura_id):
    db = SessionLocal()

    try:
        asignatura = db.query(Asignatura).filter(
            Asignatura.id == asignatura_id,
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({
                "valida": False,
                "mensaje": "Asignatura no encontrada o inactiva"
            }), 404

        return jsonify({
            "valida": True,
            "asignatura_id": asignatura.id,
            "nombre": asignatura.nombre,
            "carrera_id": asignatura.carrera_id,
            "periodo_id": asignatura.periodo_id
        }), 200

    finally:
        db.close()


@internos_bp.route("/disponibilidad-docente/<int:docente_id>", methods=["GET"])
def disponibilidad_docente(docente_id):
    db = SessionLocal()

    try:
        docente = db.query(Docente).filter(
            Docente.id == docente_id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({
                "disponible": False,
                "mensaje": "Docente no encontrado o inactivo"
            }), 404

        horarios = db.query(HorarioAtencion).filter(
            HorarioAtencion.docente_id == docente_id,
            HorarioAtencion.estado == True
        ).all()

        return jsonify({
            "docente_id": docente.id,
            "docente": f"{docente.nombres} {docente.apellidos}",
            "horarios_disponibles": [
                {
                    "dia": horario.dia,
                    "hora_inicio": str(horario.hora_inicio),
                    "hora_fin": str(horario.hora_fin)
                }
                for horario in horarios
            ]
        }), 200

    finally:
        db.close()


@internos_bp.route("/validar-estudiante/<int:estudiante_id>", methods=["GET"])
def validar_estudiante(estudiante_id):
    db = SessionLocal()

    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == estudiante_id,
            Estudiante.estado == True,
            Estudiante.estado_academico == "activo"
        ).first()

        if not estudiante:
            return jsonify({
                "valido": False,
                "mensaje": "Estudiante no encontrado, inactivo o no apto para tutorías"
            }), 404

        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == estudiante.periodo_id,
            PeriodoAcademico.estado == True,
            PeriodoAcademico.estado_periodo == "activo"
        ).first()

        if not periodo:
            return jsonify({
                "valido": False,
                "mensaje": "El estudiante no pertenece a un periodo académico activo"
            }), 400

        return jsonify({
            "valido": True,
            "estudiante_id": estudiante.id,
            "nombres": estudiante.nombres,
            "apellidos": estudiante.apellidos,
            "carrera_id": estudiante.carrera_id,
            "periodo_id": estudiante.periodo_id
        }), 200

    finally:
        db.close()
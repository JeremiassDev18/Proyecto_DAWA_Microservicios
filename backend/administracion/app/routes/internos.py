from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Asignatura, Docente, Estudiante, HorarioAtencion, Paralelo, PeriodoAcademico

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


@internos_bp.route("/estudiantes/<int:estudiante_id>/docentes", methods=["GET"])
def docentes_de_estudiante(estudiante_id):
    db = SessionLocal()
    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == estudiante_id,
            Estudiante.estado == True,
            Estudiante.estado_academico == "activo"
        ).first()

        if not estudiante:
            return jsonify({
                "error": "Estudiante no encontrado o inactivo"
            }), 404

        paralelos = db.query(Paralelo).filter(
            Paralelo.carrera_id == estudiante.carrera_id,
            Paralelo.periodo_id == estudiante.periodo_id,
            Paralelo.estado == True
        ).all()

        docentes_dict: dict = {}
        for p in paralelos:
            doc_id = p.docente_id
            if doc_id not in docentes_dict:
                docentes_dict[doc_id] = {
                    "id": p.docente.id,
                    "nombres": p.docente.nombres,
                    "apellidos": p.docente.apellidos,
                    "especialidad": p.docente.especialidad or "",
                    "asignaturas": [],
                    "horarios": [],
                }
            docentes_dict[doc_id]["asignaturas"].append({
                "id": p.asignatura.id,
                "nombre": p.asignatura.nombre,
            })

        for doc_id in docentes_dict:
            horarios = db.query(HorarioAtencion).filter(
                HorarioAtencion.docente_id == doc_id,
                HorarioAtencion.estado == True
            ).all()
            docentes_dict[doc_id]["horarios"] = [
                {
                    "dia": h.dia,
                    "hora_inicio": str(h.hora_inicio),
                    "hora_fin": str(h.hora_fin),
                }
                for h in horarios
            ]

        return jsonify(list(docentes_dict.values())), 200

    finally:
        db.close()


@internos_bp.route("/estudiantes/<int:estudiante_id>/materias", methods=["GET"])
def materias_estudiante(estudiante_id):
    db = SessionLocal()
    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == estudiante_id,
            Estudiante.estado == True
        ).first()

        if not estudiante:
            return jsonify({"error": "Estudiante no encontrado o inactivo"}), 404

        asignaturas = db.query(Asignatura).filter(
            Asignatura.carrera_id == estudiante.carrera_id,
            Asignatura.periodo_id == estudiante.periodo_id,
            Asignatura.estado == True
        ).all()

        return jsonify([
            {
                "id": a.id,
                "nombre": a.nombre,
                "codigo": a.codigo,
                "nivel": a.nivel,
                "creditos": a.creditos,
                "carrera_id": a.carrera_id,
                "periodo_id": a.periodo_id,
            }
            for a in asignaturas
        ]), 200

    finally:
        db.close()
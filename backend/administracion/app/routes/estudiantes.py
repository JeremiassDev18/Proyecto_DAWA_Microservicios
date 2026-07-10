from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Estudiante, Carrera, PeriodoAcademico
from app.auth import requiere_roles
from app.audit import registrar_auditoria

estudiantes_bp = Blueprint("estudiantes", __name__)

ESTADOS_ACADEMICOS = ["activo", "egresado", "retirado"]


@estudiantes_bp.route("/", methods=["GET"])
def listar_estudiantes():
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
                "carrera_id": estudiante.carrera_id,
                "periodo_id": estudiante.periodo_id,
                "estado_academico": estudiante.estado_academico,
                "estado": estudiante.estado,
                "fecha_creacion": str(estudiante.fecha_creacion)
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@estudiantes_bp.route("/<int:id>", methods=["GET"])
def obtener_estudiante(id):
    db = SessionLocal()
    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == id,
            Estudiante.estado == True
        ).first()

        if not estudiante:
            return jsonify({"error": "Estudiante no encontrado"}), 404

        carrera = db.query(Carrera).filter(
            Carrera.id == estudiante.carrera_id
        ).first()
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == estudiante.periodo_id
        ).first()

        return jsonify({
            "id": estudiante.id,
            "nombres": estudiante.nombres,
            "apellidos": estudiante.apellidos,
            "correo": estudiante.correo,
            "matricula": estudiante.matricula,
            "carrera_id": estudiante.carrera_id,
            "carrera_nombre": carrera.nombre if carrera else None,
            "facultad_nombre": carrera.facultad.nombre if carrera and carrera.facultad else None,
            "periodo_id": estudiante.periodo_id,
            "periodo_nombre": periodo.nombre if periodo else None,
            "nivel": estudiante.nivel,
            "estado_academico": estudiante.estado_academico,
            "estado": estudiante.estado,
            "fecha_creacion": str(estudiante.fecha_creacion)
        }), 200
    finally:
        db.close()


@estudiantes_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_estudiante():
    data = request.get_json()

    if not data or not data.get("nombres") or not data.get("apellidos") or not data.get("correo") or not data.get("carrera_id") or not data.get("periodo_id"):
        return jsonify({
            "error": "Nombres, apellidos, correo, carrera_id y periodo_id son obligatorios"
        }), 400

    estado_academico = data.get("estado_academico", "activo").lower()

    if estado_academico not in ESTADOS_ACADEMICOS:
        return jsonify({
            "error": "estado_academico debe ser: activo, egresado o retirado"
        }), 400

    db = SessionLocal()

    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == data.get("carrera_id"),
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == data.get("periodo_id"),
            PeriodoAcademico.estado == True,
            PeriodoAcademico.estado_periodo == "activo"
        ).first()

        if not periodo:
            return jsonify({
                "error": "El estudiante debe estar matriculado en un periodo académico activo"
            }), 400

        nuevo_estudiante = Estudiante(
            nombres=data.get("nombres"),
            apellidos=data.get("apellidos"),
            correo=data.get("correo"),
            matricula=data.get("matricula"),
            carrera_id=data.get("carrera_id"),
            periodo_id=data.get("periodo_id"),
            nivel=data.get("nivel", "Primero"),
            estado_academico=estado_academico,
            estado=True
        )

        db.add(nuevo_estudiante)
        db.commit()
        db.refresh(nuevo_estudiante)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "ESTUDIANTES",
            f"Se creó el estudiante {nuevo_estudiante.nombres} {nuevo_estudiante.apellidos}"
        )

        return jsonify({
            "mensaje": "Estudiante creado correctamente",
            "estudiante": {
                "id": nuevo_estudiante.id,
                "nombres": nuevo_estudiante.nombres,
                "apellidos": nuevo_estudiante.apellidos,
                "correo": nuevo_estudiante.correo,
                "matricula": nuevo_estudiante.matricula,
                "carrera_id": nuevo_estudiante.carrera_id,
                "periodo_id": nuevo_estudiante.periodo_id,
                "nivel": nuevo_estudiante.nivel,
                "estado_academico": nuevo_estudiante.estado_academico,
                "estado": nuevo_estudiante.estado,
                "fecha_creacion": str(nuevo_estudiante.fecha_creacion)
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@estudiantes_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_estudiante(id):
    data = request.get_json()

    db = SessionLocal()

    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == id,
            Estudiante.estado == True
        ).first()

        if not estudiante:
            return jsonify({"error": "Estudiante no encontrado"}), 404

        estudiante.nombres = data.get("nombres", estudiante.nombres)
        estudiante.apellidos = data.get("apellidos", estudiante.apellidos)
        estudiante.correo = data.get("correo", estudiante.correo)
        estudiante.matricula = data.get("matricula", estudiante.matricula)

        if data.get("nivel"):
            estudiante.nivel = data.get("nivel")

        if data.get("estado_academico"):
            estado_academico = data.get("estado_academico").lower()

            if estado_academico not in ESTADOS_ACADEMICOS:
                return jsonify({
                    "error": "estado_academico debe ser: activo, egresado o retirado"
                }), 400

            estudiante.estado_academico = estado_academico

        if data.get("carrera_id"):
            carrera = db.query(Carrera).filter(
                Carrera.id == data.get("carrera_id"),
                Carrera.estado == True
            ).first()

            if not carrera:
                return jsonify({"error": "La carrera indicada no existe"}), 404

            estudiante.carrera_id = data.get("carrera_id")

        if data.get("periodo_id"):
            periodo = db.query(PeriodoAcademico).filter(
                PeriodoAcademico.id == data.get("periodo_id"),
                PeriodoAcademico.estado == True,
                PeriodoAcademico.estado_periodo == "activo"
            ).first()

            if not periodo:
                return jsonify({
                    "error": "El periodo académico indicado no está activo"
                }), 400

            estudiante.periodo_id = data.get("periodo_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "ESTUDIANTES",
            f"Se actualizó el estudiante con ID {id}"
        )

        return jsonify({"mensaje": "Estudiante actualizado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@estudiantes_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_estudiante(id):
    db = SessionLocal()

    try:
        estudiante = db.query(Estudiante).filter(
            Estudiante.id == id,
            Estudiante.estado == True
        ).first()

        if not estudiante:
            return jsonify({"error": "Estudiante no encontrado"}), 404

        estudiante.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "ESTUDIANTES",
            f"Se inactivó el estudiante con ID {id}"
        )

        return jsonify({"mensaje": "Estudiante inactivado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
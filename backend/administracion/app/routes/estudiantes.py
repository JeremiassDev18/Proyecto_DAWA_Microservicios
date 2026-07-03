from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Estudiante, Carrera
from app.auth import requiere_roles
from app.audit import registrar_auditoria

estudiantes_bp = Blueprint("estudiantes", __name__)


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
                "estado": estudiante.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@estudiantes_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_estudiante():
    data = request.get_json()

    if not data or not data.get("nombres") or not data.get("apellidos") or not data.get("correo") or not data.get("carrera_id"):
        return jsonify({"error": "Nombres, apellidos, correo y carrera_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == data.get("carrera_id"),
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        nuevo_estudiante = Estudiante(
            nombres=data.get("nombres"),
            apellidos=data.get("apellidos"),
            correo=data.get("correo"),
            matricula=data.get("matricula"),
            carrera_id=data.get("carrera_id"),
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

        return jsonify({"mensaje": "Estudiante creado correctamente"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
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

        return jsonify({
            "id": estudiante.id,
            "nombres": estudiante.nombres,
            "apellidos": estudiante.apellidos,
            "correo": estudiante.correo,
            "matricula": estudiante.matricula,
            "carrera_id": estudiante.carrera_id,
            "estado": estudiante.estado
        }), 200
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

        if data.get("carrera_id"):
            carrera = db.query(Carrera).filter(
                Carrera.id == data.get("carrera_id"),
                Carrera.estado == True
            ).first()

            if not carrera:
                return jsonify({"error": "La carrera indicada no existe"}), 404

            estudiante.carrera_id = data.get("carrera_id")

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
            f"Se eliminó lógicamente el estudiante con ID {id}"
        )

        return jsonify({"mensaje": "Estudiante eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
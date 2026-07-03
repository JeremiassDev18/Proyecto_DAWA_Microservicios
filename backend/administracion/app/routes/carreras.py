from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Carrera, Facultad
from app.auth import requiere_roles
from app.audit import registrar_auditoria

carreras_bp = Blueprint("carreras", __name__)


@carreras_bp.route("/", methods=["GET"])
def listar_carreras():
    db = SessionLocal()
    try:
        carreras = db.query(Carrera).filter(Carrera.estado == True).all()
        resultado = []

        for carrera in carreras:
            resultado.append({
                "id": carrera.id,
                "nombre": carrera.nombre,
                "codigo": carrera.codigo,
                "facultad_id": carrera.facultad_id,
                "estado": carrera.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@carreras_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_carrera():
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("facultad_id"):
        return jsonify({"error": "Nombre y facultad_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        facultad = db.query(Facultad).filter(
            Facultad.id == data.get("facultad_id"),
            Facultad.estado == True
        ).first()

        if not facultad:
            return jsonify({"error": "La facultad indicada no existe"}), 404

        nueva_carrera = Carrera(
            nombre=data.get("nombre"),
            codigo=data.get("codigo"),
            facultad_id=data.get("facultad_id"),
            estado=True
        )

        db.add(nueva_carrera)
        db.commit()
        db.refresh(nueva_carrera)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "CARRERAS",
            f"Se creó la carrera {nueva_carrera.nombre}"
        )

        return jsonify({"mensaje": "Carrera creada correctamente"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@carreras_bp.route("/<int:id>", methods=["GET"])
def obtener_carrera(id):
    db = SessionLocal()
    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == id,
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "Carrera no encontrada"}), 404

        return jsonify({
            "id": carrera.id,
            "nombre": carrera.nombre,
            "codigo": carrera.codigo,
            "facultad_id": carrera.facultad_id,
            "estado": carrera.estado
        }), 200
    finally:
        db.close()


@carreras_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_carrera(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == id,
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "Carrera no encontrada"}), 404

        carrera.nombre = data.get("nombre", carrera.nombre)
        carrera.codigo = data.get("codigo", carrera.codigo)

        if data.get("facultad_id"):
            facultad = db.query(Facultad).filter(
                Facultad.id == data.get("facultad_id"),
                Facultad.estado == True
            ).first()

            if not facultad:
                return jsonify({"error": "La facultad indicada no existe"}), 404

            carrera.facultad_id = data.get("facultad_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "CARRERAS",
            f"Se actualizó la carrera con ID {id}"
        )

        return jsonify({"mensaje": "Carrera actualizada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@carreras_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_carrera(id):
    db = SessionLocal()
    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == id,
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "Carrera no encontrada"}), 404

        carrera.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "CARRERAS",
            f"Se eliminó lógicamente la carrera con ID {id}"
        )

        return jsonify({"mensaje": "Carrera eliminada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
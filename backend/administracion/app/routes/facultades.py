from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Facultad
from app.auth import requiere_roles
from app.audit import registrar_auditoria

facultades_bp = Blueprint("facultades", __name__)


@facultades_bp.route("/", methods=["GET"])
def listar_facultades():
    db = SessionLocal()
    try:
        facultades = db.query(Facultad).filter(Facultad.estado == True).all()

        resultado = []

        for facultad in facultades:
            resultado.append({
                "id": facultad.id,
                "nombre": facultad.nombre,
                "codigo": facultad.codigo,
                "descripcion": facultad.descripcion,
                "estado": facultad.estado,
                "fecha_creacion": str(facultad.fecha_creacion)
            })

        return jsonify(resultado), 200

    finally:
        db.close()


@facultades_bp.route("/<int:id>", methods=["GET"])
def obtener_facultad(id):
    db = SessionLocal()
    try:
        facultad = db.query(Facultad).filter(
            Facultad.id == id,
            Facultad.estado == True
        ).first()

        if not facultad:
            return jsonify({"error": "Facultad no encontrada"}), 404

        return jsonify({
            "id": facultad.id,
            "nombre": facultad.nombre,
            "codigo": facultad.codigo,
            "descripcion": facultad.descripcion,
            "estado": facultad.estado,
            "fecha_creacion": str(facultad.fecha_creacion)
        }), 200

    finally:
        db.close()


@facultades_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_facultad():
    data = request.get_json()

    if not data or not data.get("nombre"):
        return jsonify({
            "error": "El nombre de la facultad es obligatorio"
        }), 400

    db = SessionLocal()

    try:
        nueva_facultad = Facultad(
            nombre=data.get("nombre"),
            codigo=data.get("codigo"),
            descripcion=data.get("descripcion"),
            estado=True
        )

        db.add(nueva_facultad)
        db.commit()
        db.refresh(nueva_facultad)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "FACULTADES",
            f"Se creó la facultad {nueva_facultad.nombre}"
        )

        return jsonify({
            "mensaje": "Facultad creada correctamente",
            "facultad": {
                "id": nueva_facultad.id,
                "nombre": nueva_facultad.nombre,
                "codigo": nueva_facultad.codigo,
                "descripcion": nueva_facultad.descripcion,
                "estado": nueva_facultad.estado,
                "fecha_creacion": str(nueva_facultad.fecha_creacion)
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@facultades_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_facultad(id):
    data = request.get_json()

    db = SessionLocal()

    try:
        facultad = db.query(Facultad).filter(
            Facultad.id == id,
            Facultad.estado == True
        ).first()

        if not facultad:
            return jsonify({"error": "Facultad no encontrada"}), 404

        facultad.nombre = data.get("nombre", facultad.nombre)
        facultad.codigo = data.get("codigo", facultad.codigo)
        facultad.descripcion = data.get("descripcion", facultad.descripcion)

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "FACULTADES",
            f"Se actualizó la facultad con ID {id}"
        )

        return jsonify({
            "mensaje": "Facultad actualizada correctamente"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@facultades_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_facultad(id):
    db = SessionLocal()

    try:
        facultad = db.query(Facultad).filter(
            Facultad.id == id,
            Facultad.estado == True
        ).first()

        if not facultad:
            return jsonify({"error": "Facultad no encontrada"}), 404

        facultad.estado = False

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "FACULTADES",
            f"Se inactivó la facultad con ID {id}"
        )

        return jsonify({
            "mensaje": "Facultad inactivada correctamente"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
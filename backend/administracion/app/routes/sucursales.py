from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Sucursal, Restaurante
from app.auth import requiere_roles
from app.audit import registrar_auditoria

sucursales_bp = Blueprint("sucursales", __name__)


@sucursales_bp.route("/", methods=["GET"])
def listar_sucursales():
    db = SessionLocal()
    try:
        sucursales = db.query(Sucursal).filter(Sucursal.estado == True).all()

        resultado = []
        for sucursal in sucursales:
            resultado.append({
                "id": sucursal.id,
                "nombre": sucursal.nombre,
                "direccion": sucursal.direccion,
                "telefono": sucursal.telefono,
                "restaurante_id": sucursal.restaurante_id,
                "estado": sucursal.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@sucursales_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_sucursal():
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("direccion") or not data.get("restaurante_id"):
        return jsonify({"error": "Nombre, dirección y restaurante_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        restaurante = db.query(Restaurante).filter(
            Restaurante.id == data.get("restaurante_id"),
            Restaurante.estado == True
        ).first()

        if not restaurante:
            return jsonify({"error": "El restaurante indicado no existe"}), 404

        nueva_sucursal = Sucursal(
            nombre=data.get("nombre"),
            direccion=data.get("direccion"),
            telefono=data.get("telefono"),
            restaurante_id=data.get("restaurante_id"),
            estado=True
        )

        db.add(nueva_sucursal)
        db.commit()
        db.refresh(nueva_sucursal)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "SUCURSALES",
            f"Se creó la sucursal {nueva_sucursal.nombre}"
        )

        return jsonify({
            "mensaje": "Sucursal creada correctamente",
            "sucursal": {
                "id": nueva_sucursal.id,
                "nombre": nueva_sucursal.nombre,
                "direccion": nueva_sucursal.direccion,
                "telefono": nueva_sucursal.telefono,
                "restaurante_id": nueva_sucursal.restaurante_id,
                "estado": nueva_sucursal.estado
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@sucursales_bp.route("/<int:id>", methods=["GET"])
def obtener_sucursal(id):
    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == id,
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "Sucursal no encontrada"}), 404

        return jsonify({
            "id": sucursal.id,
            "nombre": sucursal.nombre,
            "direccion": sucursal.direccion,
            "telefono": sucursal.telefono,
            "restaurante_id": sucursal.restaurante_id,
            "estado": sucursal.estado
        }), 200
    finally:
        db.close()


@sucursales_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_sucursal(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == id,
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "Sucursal no encontrada"}), 404

        sucursal.nombre = data.get("nombre", sucursal.nombre)
        sucursal.direccion = data.get("direccion", sucursal.direccion)
        sucursal.telefono = data.get("telefono", sucursal.telefono)

        if data.get("restaurante_id"):
            restaurante = db.query(Restaurante).filter(
                Restaurante.id == data.get("restaurante_id"),
                Restaurante.estado == True
            ).first()

            if not restaurante:
                return jsonify({"error": "El restaurante indicado no existe"}), 404

            sucursal.restaurante_id = data.get("restaurante_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "SUCURSALES",
            f"Se actualizó la sucursal con ID {id}"
        )

        return jsonify({"mensaje": "Sucursal actualizada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@sucursales_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_sucursal(id):
    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == id,
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "Sucursal no encontrada"}), 404

        sucursal.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "SUCURSALES",
            f"Se eliminó lógicamente la sucursal con ID {id}"
        )

        return jsonify({"mensaje": "Sucursal eliminada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
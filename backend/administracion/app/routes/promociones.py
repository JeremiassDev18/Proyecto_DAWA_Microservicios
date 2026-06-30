from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Promocion, Sucursal

promociones_bp = Blueprint("promociones", __name__)


@promociones_bp.route("/", methods=["GET"])
def listar_promociones():
    db = SessionLocal()
    try:
        promociones = db.query(Promocion).filter(Promocion.estado == True).all()

        resultado = []
        for promocion in promociones:
            resultado.append({
                "id": promocion.id,
                "nombre": promocion.nombre,
                "descripcion": promocion.descripcion,
                "descuento": float(promocion.descuento),
                "sucursal_id": promocion.sucursal_id,
                "estado": promocion.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@promociones_bp.route("/", methods=["POST"])
def crear_promocion():
    data = request.get_json()

    if not data or not data.get("nombre") or data.get("descuento") is None or not data.get("sucursal_id"):
        return jsonify({"error": "Nombre, descuento y sucursal_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == data.get("sucursal_id"),
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "La sucursal indicada no existe"}), 404

        nueva_promocion = Promocion(
            nombre=data.get("nombre"),
            descripcion=data.get("descripcion"),
            descuento=data.get("descuento"),
            sucursal_id=data.get("sucursal_id"),
            estado=True
        )

        db.add(nueva_promocion)
        db.commit()
        db.refresh(nueva_promocion)

        return jsonify({
            "mensaje": "Promoción creada correctamente",
            "promocion": {
                "id": nueva_promocion.id,
                "nombre": nueva_promocion.nombre,
                "descripcion": nueva_promocion.descripcion,
                "descuento": float(nueva_promocion.descuento),
                "sucursal_id": nueva_promocion.sucursal_id,
                "estado": nueva_promocion.estado
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@promociones_bp.route("/<int:id>", methods=["GET"])
def obtener_promocion(id):
    db = SessionLocal()
    try:
        promocion = db.query(Promocion).filter(
            Promocion.id == id,
            Promocion.estado == True
        ).first()

        if not promocion:
            return jsonify({"error": "Promoción no encontrada"}), 404

        return jsonify({
            "id": promocion.id,
            "nombre": promocion.nombre,
            "descripcion": promocion.descripcion,
            "descuento": float(promocion.descuento),
            "sucursal_id": promocion.sucursal_id,
            "estado": promocion.estado
        }), 200
    finally:
        db.close()


@promociones_bp.route("/<int:id>", methods=["PUT"])
def actualizar_promocion(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        promocion = db.query(Promocion).filter(
            Promocion.id == id,
            Promocion.estado == True
        ).first()

        if not promocion:
            return jsonify({"error": "Promoción no encontrada"}), 404

        promocion.nombre = data.get("nombre", promocion.nombre)
        promocion.descripcion = data.get("descripcion", promocion.descripcion)

        if data.get("descuento") is not None:
            promocion.descuento = data.get("descuento")

        if data.get("sucursal_id"):
            sucursal = db.query(Sucursal).filter(
                Sucursal.id == data.get("sucursal_id"),
                Sucursal.estado == True
            ).first()

            if not sucursal:
                return jsonify({"error": "La sucursal indicada no existe"}), 404

            promocion.sucursal_id = data.get("sucursal_id")

        db.commit()

        return jsonify({"mensaje": "Promoción actualizada correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@promociones_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_promocion(id):
    db = SessionLocal()
    try:
        promocion = db.query(Promocion).filter(
            Promocion.id == id,
            Promocion.estado == True
        ).first()

        if not promocion:
            return jsonify({"error": "Promoción no encontrada"}), 404

        promocion.estado = False
        db.commit()

        return jsonify({"mensaje": "Promoción eliminada correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
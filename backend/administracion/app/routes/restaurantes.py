from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Restaurante

restaurantes_bp = Blueprint("restaurantes", __name__)


@restaurantes_bp.route("/", methods=["GET"])
def listar_restaurantes():
    db = SessionLocal()
    try:
        restaurantes = db.query(Restaurante).filter(Restaurante.estado == True).all()

        resultado = []
        for restaurante in restaurantes:
            resultado.append({
                "id": restaurante.id,
                "nombre": restaurante.nombre,
                "descripcion": restaurante.descripcion,
                "estado": restaurante.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@restaurantes_bp.route("/", methods=["POST"])
def crear_restaurante():
    data = request.get_json()

    if not data or not data.get("nombre"):
        return jsonify({"error": "El nombre del restaurante es obligatorio"}), 400

    db = SessionLocal()
    try:
        nuevo_restaurante = Restaurante(
            nombre=data.get("nombre"),
            descripcion=data.get("descripcion"),
            estado=True
        )

        db.add(nuevo_restaurante)
        db.commit()
        db.refresh(nuevo_restaurante)

        return jsonify({
            "mensaje": "Restaurante creado correctamente",
            "restaurante": {
                "id": nuevo_restaurante.id,
                "nombre": nuevo_restaurante.nombre,
                "descripcion": nuevo_restaurante.descripcion,
                "estado": nuevo_restaurante.estado
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@restaurantes_bp.route("/<int:id>", methods=["GET"])
def obtener_restaurante(id):
    db = SessionLocal()
    try:
        restaurante = db.query(Restaurante).filter(
            Restaurante.id == id,
            Restaurante.estado == True
        ).first()

        if not restaurante:
            return jsonify({"error": "Restaurante no encontrado"}), 404

        return jsonify({
            "id": restaurante.id,
            "nombre": restaurante.nombre,
            "descripcion": restaurante.descripcion,
            "estado": restaurante.estado
        }), 200
    finally:
        db.close()


@restaurantes_bp.route("/<int:id>", methods=["PUT"])
def actualizar_restaurante(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        restaurante = db.query(Restaurante).filter(
            Restaurante.id == id,
            Restaurante.estado == True
        ).first()

        if not restaurante:
            return jsonify({"error": "Restaurante no encontrado"}), 404

        restaurante.nombre = data.get("nombre", restaurante.nombre)
        restaurante.descripcion = data.get("descripcion", restaurante.descripcion)

        db.commit()

        return jsonify({"mensaje": "Restaurante actualizado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@restaurantes_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_restaurante(id):
    db = SessionLocal()
    try:
        restaurante = db.query(Restaurante).filter(
            Restaurante.id == id,
            Restaurante.estado == True
        ).first()

        if not restaurante:
            return jsonify({"error": "Restaurante no encontrado"}), 404

        restaurante.estado = False
        db.commit()

        return jsonify({"mensaje": "Restaurante eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
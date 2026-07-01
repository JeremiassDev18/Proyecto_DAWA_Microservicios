from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Mesa, Sucursal
from app.auth import requiere_roles
from app.audit import registrar_auditoria

mesas_bp = Blueprint("mesas", __name__)


@mesas_bp.route("/", methods=["GET"])
def listar_mesas():
    db = SessionLocal()
    try:
        mesas = db.query(Mesa).filter(Mesa.estado == True).all()

        resultado = []
        for mesa in mesas:
            resultado.append({
                "id": mesa.id,
                "numero": mesa.numero,
                "capacidad": mesa.capacidad,
                "ubicacion": mesa.ubicacion,
                "sucursal_id": mesa.sucursal_id,
                "estado": mesa.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@mesas_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_mesa():
    data = request.get_json()

    if not data or not data.get("numero") or not data.get("capacidad") or not data.get("sucursal_id"):
        return jsonify({"error": "Número, capacidad y sucursal_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == data.get("sucursal_id"),
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "La sucursal indicada no existe"}), 404

        nueva_mesa = Mesa(
            numero=data.get("numero"),
            capacidad=data.get("capacidad"),
            ubicacion=data.get("ubicacion"),
            sucursal_id=data.get("sucursal_id"),
            estado=True
        )

        db.add(nueva_mesa)
        db.commit()
        db.refresh(nueva_mesa)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "MESAS",
            f"Se creó la mesa número {nueva_mesa.numero}"
        )

        return jsonify({
            "mensaje": "Mesa creada correctamente",
            "mesa": {
                "id": nueva_mesa.id,
                "numero": nueva_mesa.numero,
                "capacidad": nueva_mesa.capacidad,
                "ubicacion": nueva_mesa.ubicacion,
                "sucursal_id": nueva_mesa.sucursal_id,
                "estado": nueva_mesa.estado
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["GET"])
def obtener_mesa(id):
    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        return jsonify({
            "id": mesa.id,
            "numero": mesa.numero,
            "capacidad": mesa.capacidad,
            "ubicacion": mesa.ubicacion,
            "sucursal_id": mesa.sucursal_id,
            "estado": mesa.estado
        }), 200
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_mesa(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        mesa.numero = data.get("numero", mesa.numero)
        mesa.capacidad = data.get("capacidad", mesa.capacidad)
        mesa.ubicacion = data.get("ubicacion", mesa.ubicacion)

        if data.get("sucursal_id"):
            sucursal = db.query(Sucursal).filter(
                Sucursal.id == data.get("sucursal_id"),
                Sucursal.estado == True
            ).first()

            if not sucursal:
                return jsonify({"error": "La sucursal indicada no existe"}), 404

            mesa.sucursal_id = data.get("sucursal_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "MESAS",
            f"Se actualizó la mesa con ID {id}"
        )

        return jsonify({"mensaje": "Mesa actualizada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_mesa(id):
    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        mesa.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "MESAS",
            f"Se eliminó lógicamente la mesa con ID {id}"
        )

        return jsonify({"mensaje": "Mesa eliminada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Mesa, Sucursal

mesas_bp = Blueprint("mesas", __name__)


@mesas_bp.route("/", methods=["GET"])
def listar_mesas():
    db = SessionLocal()
    try:
        mesas = db.query(Mesa).filter(Mesa.estado == True).all()

        resultado = []
        for mesa in mesas:
            resultado.append({
                "id": mesa.id,
                "numero": mesa.numero,
                "capacidad": mesa.capacidad,
                "ubicacion": mesa.ubicacion,
                "sucursal_id": mesa.sucursal_id,
                "estado": mesa.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@mesas_bp.route("/", methods=["POST"])
def crear_mesa():
    data = request.get_json()

    if not data or not data.get("numero") or not data.get("capacidad") or not data.get("sucursal_id"):
        return jsonify({"error": "Número, capacidad y sucursal_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == data.get("sucursal_id"),
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "La sucursal indicada no existe"}), 404

        nueva_mesa = Mesa(
            numero=data.get("numero"),
            capacidad=data.get("capacidad"),
            ubicacion=data.get("ubicacion"),
            sucursal_id=data.get("sucursal_id"),
            estado=True
        )

        db.add(nueva_mesa)
        db.commit()
        db.refresh(nueva_mesa)

        return jsonify({
            "mensaje": "Mesa creada correctamente",
            "mesa": {
                "id": nueva_mesa.id,
                "numero": nueva_mesa.numero,
                "capacidad": nueva_mesa.capacidad,
                "ubicacion": nueva_mesa.ubicacion,
                "sucursal_id": nueva_mesa.sucursal_id,
                "estado": nueva_mesa.estado
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["GET"])
def obtener_mesa(id):
    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        return jsonify({
            "id": mesa.id,
            "numero": mesa.numero,
            "capacidad": mesa.capacidad,
            "ubicacion": mesa.ubicacion,
            "sucursal_id": mesa.sucursal_id,
            "estado": mesa.estado
        }), 200
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["PUT"])
def actualizar_mesa(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        mesa.numero = data.get("numero", mesa.numero)
        mesa.capacidad = data.get("capacidad", mesa.capacidad)
        mesa.ubicacion = data.get("ubicacion", mesa.ubicacion)

        if data.get("sucursal_id"):
            sucursal = db.query(Sucursal).filter(
                Sucursal.id == data.get("sucursal_id"),
                Sucursal.estado == True
            ).first()

            if not sucursal:
                return jsonify({"error": "La sucursal indicada no existe"}), 404

            mesa.sucursal_id = data.get("sucursal_id")

        db.commit()

        return jsonify({"mensaje": "Mesa actualizada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@mesas_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_mesa(id):
    db = SessionLocal()
    try:
        mesa = db.query(Mesa).filter(
            Mesa.id == id,
            Mesa.estado == True
        ).first()

        if not mesa:
            return jsonify({"error": "Mesa no encontrada"}), 404

        mesa.estado = False
        db.commit()

        return jsonify({"mensaje": "Mesa eliminada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@mesas_bp.route("/disponibles", methods=["GET"])
def mesas_disponibles():
    sucursal_id = request.args.get("sucursal_id")
    personas = request.args.get("personas")

    if not sucursal_id or not personas:
        return jsonify({
            "error": "Los parámetros sucursal_id y personas son obligatorios"
        }), 400

    db = SessionLocal()
    try:
        mesas = db.query(Mesa).filter(
            Mesa.sucursal_id == int(sucursal_id),
            Mesa.capacidad >= int(personas),
            Mesa.estado == True
        ).all()

        resultado = []
        for mesa in mesas:
            resultado.append({
                "id": mesa.id,
                "numero": mesa.numero,
                "capacidad": mesa.capacidad,
                "ubicacion": mesa.ubicacion,
                "sucursal_id": mesa.sucursal_id
            })

        return jsonify({
            "mensaje": "Mesas disponibles obtenidas correctamente",
            "mesas_disponibles": resultado
        }), 200

    except ValueError:
        return jsonify({
            "error": "sucursal_id y personas deben ser números"
        }), 400
    finally:
        db.close()        
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import SessionLocal
from app.models import HorarioAtencion, Sucursal

horarios_bp = Blueprint("horarios", __name__)


@horarios_bp.route("/", methods=["GET"])
def listar_horarios():
    db = SessionLocal()
    try:
        horarios = db.query(HorarioAtencion).filter(HorarioAtencion.estado == True).all()

        resultado = []
        for horario in horarios:
            resultado.append({
                "id": horario.id,
                "dia": horario.dia,
                "hora_apertura": str(horario.hora_apertura),
                "hora_cierre": str(horario.hora_cierre),
                "sucursal_id": horario.sucursal_id,
                "estado": horario.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@horarios_bp.route("/", methods=["POST"])
def crear_horario():
    data = request.get_json()

    if not data or not data.get("dia") or not data.get("hora_apertura") or not data.get("hora_cierre") or not data.get("sucursal_id"):
        return jsonify({"error": "Día, hora_apertura, hora_cierre y sucursal_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).filter(
            Sucursal.id == data.get("sucursal_id"),
            Sucursal.estado == True
        ).first()

        if not sucursal:
            return jsonify({"error": "La sucursal indicada no existe"}), 404

        hora_apertura = datetime.strptime(data.get("hora_apertura"), "%H:%M").time()
        hora_cierre = datetime.strptime(data.get("hora_cierre"), "%H:%M").time()

        if hora_apertura >= hora_cierre:
            return jsonify({"error": "La hora de apertura debe ser menor que la hora de cierre"}), 400

        nuevo_horario = HorarioAtencion(
            dia=data.get("dia"),
            hora_apertura=hora_apertura,
            hora_cierre=hora_cierre,
            sucursal_id=data.get("sucursal_id"),
            estado=True
        )

        db.add(nuevo_horario)
        db.commit()
        db.refresh(nuevo_horario)

        return jsonify({
            "mensaje": "Horario creado correctamente",
            "horario": {
                "id": nuevo_horario.id,
                "dia": nuevo_horario.dia,
                "hora_apertura": str(nuevo_horario.hora_apertura),
                "hora_cierre": str(nuevo_horario.hora_cierre),
                "sucursal_id": nuevo_horario.sucursal_id,
                "estado": nuevo_horario.estado
            }
        }), 201
    except ValueError:
        return jsonify({"error": "Formato de hora inválido. Use HH:MM, ejemplo 08:00"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@horarios_bp.route("/<int:id>", methods=["GET"])
def obtener_horario(id):
    db = SessionLocal()
    try:
        horario = db.query(HorarioAtencion).filter(
            HorarioAtencion.id == id,
            HorarioAtencion.estado == True
        ).first()

        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404

        return jsonify({
            "id": horario.id,
            "dia": horario.dia,
            "hora_apertura": str(horario.hora_apertura),
            "hora_cierre": str(horario.hora_cierre),
            "sucursal_id": horario.sucursal_id,
            "estado": horario.estado
        }), 200
    finally:
        db.close()


@horarios_bp.route("/<int:id>", methods=["PUT"])
def actualizar_horario(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        horario = db.query(HorarioAtencion).filter(
            HorarioAtencion.id == id,
            HorarioAtencion.estado == True
        ).first()

        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404

        if data.get("dia"):
            horario.dia = data.get("dia")

        if data.get("hora_apertura"):
            horario.hora_apertura = datetime.strptime(data.get("hora_apertura"), "%H:%M").time()

        if data.get("hora_cierre"):
            horario.hora_cierre = datetime.strptime(data.get("hora_cierre"), "%H:%M").time()

        if horario.hora_apertura >= horario.hora_cierre:
            return jsonify({"error": "La hora de apertura debe ser menor que la hora de cierre"}), 400

        if data.get("sucursal_id"):
            sucursal = db.query(Sucursal).filter(
                Sucursal.id == data.get("sucursal_id"),
                Sucursal.estado == True
            ).first()

            if not sucursal:
                return jsonify({"error": "La sucursal indicada no existe"}), 404

            horario.sucursal_id = data.get("sucursal_id")

        db.commit()

        return jsonify({"mensaje": "Horario actualizado correctamente"}), 200
    except ValueError:
        return jsonify({"error": "Formato de hora inválido. Use HH:MM, ejemplo 08:00"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@horarios_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_horario(id):
    db = SessionLocal()
    try:
        horario = db.query(HorarioAtencion).filter(
            HorarioAtencion.id == id,
            HorarioAtencion.estado == True
        ).first()

        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404

        horario.estado = False
        db.commit()

        return jsonify({"mensaje": "Horario eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import SessionLocal
from app.models import HorarioAtencion, Paralelo
from app.auth import requiere_roles
from app.audit import registrar_auditoria

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
                "hora_inicio": str(horario.hora_inicio),
                "hora_fin": str(horario.hora_fin),
                "paralelo_id": horario.paralelo_id,
                "estado": horario.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@horarios_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_horario():
    data = request.get_json()

    if not data or not data.get("dia") or not data.get("hora_inicio") or not data.get("hora_fin") or not data.get("paralelo_id"):
        return jsonify({"error": "Día, hora_inicio, hora_fin y paralelo_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        paralelo = db.query(Paralelo).filter(
            Paralelo.id == data.get("paralelo_id"),
            Paralelo.estado == True
        ).first()

        if not paralelo:
            return jsonify({"error": "El paralelo indicado no existe"}), 404

        hora_inicio = datetime.strptime(data.get("hora_inicio"), "%H:%M").time()
        hora_fin = datetime.strptime(data.get("hora_fin"), "%H:%M").time()

        if hora_inicio >= hora_fin:
            return jsonify({"error": "La hora de inicio debe ser menor que la hora de fin"}), 400

        nuevo_horario = HorarioAtencion(
            dia=data.get("dia"),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            paralelo_id=data.get("paralelo_id"),
            estado=True
        )

        db.add(nuevo_horario)
        db.commit()
        db.refresh(nuevo_horario)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "HORARIOS",
            f"Se creó horario para el paralelo ID {nuevo_horario.paralelo_id}"
        )

        return jsonify({"mensaje": "Horario creado correctamente"}), 201

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
            "hora_inicio": str(horario.hora_inicio),
            "hora_fin": str(horario.hora_fin),
            "paralelo_id": horario.paralelo_id,
            "estado": horario.estado
        }), 200
    finally:
        db.close()


@horarios_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
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

        if data.get("hora_inicio"):
            horario.hora_inicio = datetime.strptime(data.get("hora_inicio"), "%H:%M").time()

        if data.get("hora_fin"):
            horario.hora_fin = datetime.strptime(data.get("hora_fin"), "%H:%M").time()

        if horario.hora_inicio >= horario.hora_fin:
            return jsonify({"error": "La hora de inicio debe ser menor que la hora de fin"}), 400

        if data.get("paralelo_id"):
            paralelo = db.query(Paralelo).filter(
                Paralelo.id == data.get("paralelo_id"),
                Paralelo.estado == True
            ).first()

            if not paralelo:
                return jsonify({"error": "El paralelo indicado no existe"}), 404

            horario.paralelo_id = data.get("paralelo_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "HORARIOS",
            f"Se actualizó el horario con ID {id}"
        )

        return jsonify({"mensaje": "Horario actualizado correctamente"}), 200

    except ValueError:
        return jsonify({"error": "Formato de hora inválido. Use HH:MM, ejemplo 08:00"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@horarios_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
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

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "HORARIOS",
            f"Se eliminó lógicamente el horario con ID {id}"
        )

        return jsonify({"mensaje": "Horario eliminado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import SessionLocal
from app.models import HorarioAtencion, Docente
from app.auth import requiere_roles
from app.audit import registrar_auditoria

horarios_bp = Blueprint("horarios", __name__)

HORA_MINIMA = "07:00"
HORA_MAXIMA = "22:00"


def convertir_hora(hora_texto):
    return datetime.strptime(hora_texto, "%H:%M").time()


def existe_solapamiento(db, docente_id, dia, hora_inicio, hora_fin, horario_id=None):
    consulta = db.query(HorarioAtencion).filter(
        HorarioAtencion.docente_id == docente_id,
        HorarioAtencion.dia == dia,
        HorarioAtencion.estado == True,
        HorarioAtencion.hora_inicio < hora_fin,
        HorarioAtencion.hora_fin > hora_inicio
    )

    if horario_id:
        consulta = consulta.filter(HorarioAtencion.id != horario_id)

    return consulta.first() is not None


@horarios_bp.route("/", methods=["GET"])
def listar_horarios():
    db = SessionLocal()
    try:
        horarios = db.query(HorarioAtencion).filter(HorarioAtencion.estado == True).all()
        resultado = []

        for horario in horarios:
            resultado.append({
                "id": horario.id,
                "docente_id": horario.docente_id,
                "dia": horario.dia,
                "hora_inicio": str(horario.hora_inicio),
                "hora_fin": str(horario.hora_fin),
                "estado": horario.estado,
                "fecha_creacion": str(horario.fecha_creacion)
            })

        return jsonify(resultado), 200
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
            "docente_id": horario.docente_id,
            "dia": horario.dia,
            "hora_inicio": str(horario.hora_inicio),
            "hora_fin": str(horario.hora_fin),
            "estado": horario.estado,
            "fecha_creacion": str(horario.fecha_creacion)
        }), 200
    finally:
        db.close()


@horarios_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_horario():
    data = request.get_json()

    if not data or not data.get("docente_id") or not data.get("dia") or not data.get("hora_inicio") or not data.get("hora_fin"):
        return jsonify({
            "error": "docente_id, día, hora_inicio y hora_fin son obligatorios"
        }), 400

    db = SessionLocal()

    try:
        docente = db.query(Docente).filter(
            Docente.id == data.get("docente_id"),
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "El docente indicado no existe"}), 404

        hora_inicio = convertir_hora(data.get("hora_inicio"))
        hora_fin = convertir_hora(data.get("hora_fin"))
        hora_minima = convertir_hora(HORA_MINIMA)
        hora_maxima = convertir_hora(HORA_MAXIMA)

        if hora_inicio >= hora_fin:
            return jsonify({
                "error": "La hora de inicio debe ser menor que la hora de fin"
            }), 400

        if hora_inicio < hora_minima or hora_fin > hora_maxima:
            return jsonify({
                "error": f"El horario debe estar entre {HORA_MINIMA} y {HORA_MAXIMA}"
            }), 400

        if existe_solapamiento(
            db,
            data.get("docente_id"),
            data.get("dia"),
            hora_inicio,
            hora_fin
        ):
            return jsonify({
                "error": "El docente ya tiene un horario de atención que se solapa en ese día y rango de horas"
            }), 400

        nuevo_horario = HorarioAtencion(
            docente_id=data.get("docente_id"),
            dia=data.get("dia"),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado=True
        )

        db.add(nuevo_horario)
        db.commit()
        db.refresh(nuevo_horario)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "HORARIOS",
            f"Se creó horario de atención para docente ID {nuevo_horario.docente_id}"
        )

        return jsonify({
            "mensaje": "Horario de atención creado correctamente",
            "horario": {
                "id": nuevo_horario.id,
                "docente_id": nuevo_horario.docente_id,
                "dia": nuevo_horario.dia,
                "hora_inicio": str(nuevo_horario.hora_inicio),
                "hora_fin": str(nuevo_horario.hora_fin),
                "estado": nuevo_horario.estado,
                "fecha_creacion": str(nuevo_horario.fecha_creacion)
            }
        }), 201

    except ValueError:
        return jsonify({
            "error": "Formato de hora inválido. Use HH:MM, ejemplo 08:00"
        }), 400

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

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

        docente_id = data.get("docente_id", horario.docente_id)
        dia = data.get("dia", horario.dia)
        hora_inicio = horario.hora_inicio
        hora_fin = horario.hora_fin

        if data.get("hora_inicio"):
            hora_inicio = convertir_hora(data.get("hora_inicio"))

        if data.get("hora_fin"):
            hora_fin = convertir_hora(data.get("hora_fin"))

        docente = db.query(Docente).filter(
            Docente.id == docente_id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "El docente indicado no existe"}), 404

        hora_minima = convertir_hora(HORA_MINIMA)
        hora_maxima = convertir_hora(HORA_MAXIMA)

        if hora_inicio >= hora_fin:
            return jsonify({
                "error": "La hora de inicio debe ser menor que la hora de fin"
            }), 400

        if hora_inicio < hora_minima or hora_fin > hora_maxima:
            return jsonify({
                "error": f"El horario debe estar entre {HORA_MINIMA} y {HORA_MAXIMA}"
            }), 400

        if existe_solapamiento(db, docente_id, dia, hora_inicio, hora_fin, id):
            return jsonify({
                "error": "El docente ya tiene un horario de atención que se solapa en ese día y rango de horas"
            }), 400

        horario.docente_id = docente_id
        horario.dia = dia
        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "HORARIOS",
            f"Se actualizó el horario de atención con ID {id}"
        )

        return jsonify({
            "mensaje": "Horario de atención actualizado correctamente"
        }), 200

    except ValueError:
        return jsonify({
            "error": "Formato de hora inválido. Use HH:MM, ejemplo 08:00"
        }), 400

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
            f"Se inactivó el horario de atención con ID {id}"
        )

        return jsonify({
            "mensaje": "Horario de atención inactivado correctamente"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@horarios_bp.route("/docente/<int:docente_id>", methods=["GET"])
def obtener_horarios_por_docente(docente_id):
    db = SessionLocal()

    try:
        horarios = db.query(HorarioAtencion).filter(
            HorarioAtencion.docente_id == docente_id,
            HorarioAtencion.estado == True
        ).all()

        resultado = []

        for horario in horarios:
            resultado.append({
                "id": horario.id,
                "docente_id": horario.docente_id,
                "dia": horario.dia,
                "hora_inicio": str(horario.hora_inicio),
                "hora_fin": str(horario.hora_fin)
            })

        return jsonify(resultado), 200

    finally:
        db.close()
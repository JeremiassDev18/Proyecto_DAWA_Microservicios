from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import PeriodoAcademico
from app.auth import requiere_roles
from app.audit import registrar_auditoria

periodos_bp = Blueprint("periodos", __name__)


@periodos_bp.route("/", methods=["GET"])
def listar_periodos():
    db = SessionLocal()
    try:
        periodos = db.query(PeriodoAcademico).filter(PeriodoAcademico.estado == True).all()
        resultado = []

        for periodo in periodos:
            resultado.append({
                "id": periodo.id,
                "nombre": periodo.nombre,
                "fecha_inicio": periodo.fecha_inicio,
                "fecha_fin": periodo.fecha_fin,
                "estado": periodo.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@periodos_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_periodo():
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("fecha_inicio") or not data.get("fecha_fin"):
        return jsonify({"error": "Nombre, fecha_inicio y fecha_fin son obligatorios"}), 400

    db = SessionLocal()
    try:
        nuevo_periodo = PeriodoAcademico(
            nombre=data.get("nombre"),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            estado=True
        )

        db.add(nuevo_periodo)
        db.commit()
        db.refresh(nuevo_periodo)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "PERIODOS",
            f"Se creó el periodo académico {nuevo_periodo.nombre}"
        )

        return jsonify({"mensaje": "Periodo académico creado correctamente"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@periodos_bp.route("/<int:id>", methods=["GET"])
def obtener_periodo(id):
    db = SessionLocal()
    try:
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == id,
            PeriodoAcademico.estado == True
        ).first()

        if not periodo:
            return jsonify({"error": "Periodo académico no encontrado"}), 404

        return jsonify({
            "id": periodo.id,
            "nombre": periodo.nombre,
            "fecha_inicio": periodo.fecha_inicio,
            "fecha_fin": periodo.fecha_fin,
            "estado": periodo.estado
        }), 200
    finally:
        db.close()


@periodos_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_periodo(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == id,
            PeriodoAcademico.estado == True
        ).first()

        if not periodo:
            return jsonify({"error": "Periodo académico no encontrado"}), 404

        periodo.nombre = data.get("nombre", periodo.nombre)
        periodo.fecha_inicio = data.get("fecha_inicio", periodo.fecha_inicio)
        periodo.fecha_fin = data.get("fecha_fin", periodo.fecha_fin)

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "PERIODOS",
            f"Se actualizó el periodo académico con ID {id}"
        )

        return jsonify({"mensaje": "Periodo académico actualizado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@periodos_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_periodo(id):
    db = SessionLocal()
    try:
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == id,
            PeriodoAcademico.estado == True
        ).first()

        if not periodo:
            return jsonify({"error": "Periodo académico no encontrado"}), 404

        periodo.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "PERIODOS",
            f"Se eliminó lógicamente el periodo académico con ID {id}"
        )

        return jsonify({"mensaje": "Periodo académico eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
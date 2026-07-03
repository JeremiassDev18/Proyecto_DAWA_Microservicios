from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Asignatura, Carrera
from app.auth import requiere_roles
from app.audit import registrar_auditoria

asignaturas_bp = Blueprint("asignaturas", __name__)


@asignaturas_bp.route("/", methods=["GET"])
def listar_asignaturas():
    db = SessionLocal()
    try:
        asignaturas = db.query(Asignatura).filter(Asignatura.estado == True).all()
        resultado = []

        for asignatura in asignaturas:
            resultado.append({
                "id": asignatura.id,
                "nombre": asignatura.nombre,
                "codigo": asignatura.codigo,
                "creditos": asignatura.creditos,
                "carrera_id": asignatura.carrera_id,
                "estado": asignatura.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@asignaturas_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_asignatura():
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("creditos") or not data.get("carrera_id"):
        return jsonify({"error": "Nombre, créditos y carrera_id son obligatorios"}), 400

    db = SessionLocal()
    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == data.get("carrera_id"),
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        nueva_asignatura = Asignatura(
            nombre=data.get("nombre"),
            codigo=data.get("codigo"),
            creditos=data.get("creditos"),
            carrera_id=data.get("carrera_id"),
            estado=True
        )

        db.add(nueva_asignatura)
        db.commit()
        db.refresh(nueva_asignatura)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "ASIGNATURAS",
            f"Se creó la asignatura {nueva_asignatura.nombre}"
        )

        return jsonify({"mensaje": "Asignatura creada correctamente"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@asignaturas_bp.route("/<int:id>", methods=["GET"])
def obtener_asignatura(id):
    db = SessionLocal()
    try:
        asignatura = db.query(Asignatura).filter(
            Asignatura.id == id,
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({"error": "Asignatura no encontrada"}), 404

        return jsonify({
            "id": asignatura.id,
            "nombre": asignatura.nombre,
            "codigo": asignatura.codigo,
            "creditos": asignatura.creditos,
            "carrera_id": asignatura.carrera_id,
            "estado": asignatura.estado
        }), 200
    finally:
        db.close()


@asignaturas_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_asignatura(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        asignatura = db.query(Asignatura).filter(
            Asignatura.id == id,
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({"error": "Asignatura no encontrada"}), 404

        asignatura.nombre = data.get("nombre", asignatura.nombre)
        asignatura.codigo = data.get("codigo", asignatura.codigo)
        asignatura.creditos = data.get("creditos", asignatura.creditos)

        if data.get("carrera_id"):
            carrera = db.query(Carrera).filter(
                Carrera.id == data.get("carrera_id"),
                Carrera.estado == True
            ).first()

            if not carrera:
                return jsonify({"error": "La carrera indicada no existe"}), 404

            asignatura.carrera_id = data.get("carrera_id")

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "ASIGNATURAS",
            f"Se actualizó la asignatura con ID {id}"
        )

        return jsonify({"mensaje": "Asignatura actualizada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@asignaturas_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_asignatura(id):
    db = SessionLocal()
    try:
        asignatura = db.query(Asignatura).filter(
            Asignatura.id == id,
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({"error": "Asignatura no encontrada"}), 404

        asignatura.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "ASIGNATURAS",
            f"Se eliminó lógicamente la asignatura con ID {id}"
        )

        return jsonify({"mensaje": "Asignatura eliminada correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
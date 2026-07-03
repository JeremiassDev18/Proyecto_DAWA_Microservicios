from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Docente
from app.auth import requiere_roles
from app.audit import registrar_auditoria

docentes_bp = Blueprint("docentes", __name__)


@docentes_bp.route("/", methods=["GET"])
def listar_docentes():
    db = SessionLocal()
    try:
        docentes = db.query(Docente).filter(Docente.estado == True).all()
        resultado = []

        for docente in docentes:
            resultado.append({
                "id": docente.id,
                "nombres": docente.nombres,
                "apellidos": docente.apellidos,
                "correo": docente.correo,
                "telefono": docente.telefono,
                "especialidad": docente.especialidad,
                "estado": docente.estado
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@docentes_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_docente():
    data = request.get_json()

    if not data or not data.get("nombres") or not data.get("apellidos") or not data.get("correo"):
        return jsonify({"error": "Nombres, apellidos y correo son obligatorios"}), 400

    db = SessionLocal()
    try:
        nuevo_docente = Docente(
            nombres=data.get("nombres"),
            apellidos=data.get("apellidos"),
            correo=data.get("correo"),
            telefono=data.get("telefono"),
            especialidad=data.get("especialidad"),
            estado=True
        )

        db.add(nuevo_docente)
        db.commit()
        db.refresh(nuevo_docente)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "DOCENTES",
            f"Se creó el docente {nuevo_docente.nombres} {nuevo_docente.apellidos}"
        )

        return jsonify({"mensaje": "Docente creado correctamente"}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@docentes_bp.route("/<int:id>", methods=["GET"])
def obtener_docente(id):
    db = SessionLocal()
    try:
        docente = db.query(Docente).filter(
            Docente.id == id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "Docente no encontrado"}), 404

        return jsonify({
            "id": docente.id,
            "nombres": docente.nombres,
            "apellidos": docente.apellidos,
            "correo": docente.correo,
            "telefono": docente.telefono,
            "especialidad": docente.especialidad,
            "estado": docente.estado
        }), 200
    finally:
        db.close()


@docentes_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_docente(id):
    data = request.get_json()

    db = SessionLocal()
    try:
        docente = db.query(Docente).filter(
            Docente.id == id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "Docente no encontrado"}), 404

        docente.nombres = data.get("nombres", docente.nombres)
        docente.apellidos = data.get("apellidos", docente.apellidos)
        docente.correo = data.get("correo", docente.correo)
        docente.telefono = data.get("telefono", docente.telefono)
        docente.especialidad = data.get("especialidad", docente.especialidad)

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "DOCENTES",
            f"Se actualizó el docente con ID {id}"
        )

        return jsonify({"mensaje": "Docente actualizado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@docentes_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_docente(id):
    db = SessionLocal()
    try:
        docente = db.query(Docente).filter(
            Docente.id == id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "Docente no encontrado"}), 404

        docente.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "DOCENTES",
            f"Se eliminó lógicamente el docente con ID {id}"
        )

        return jsonify({"mensaje": "Docente eliminado correctamente"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
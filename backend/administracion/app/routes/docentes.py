from sqlalchemy import func

from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Asignatura, Docente, Facultad, Paralelo
from app.auth import requiere_roles
from app.audit import registrar_auditoria

docentes_bp = Blueprint("docentes", __name__)


@docentes_bp.route("/", methods=["GET"])
def listar_docentes():
    db = SessionLocal()
    try:
        query = db.query(Docente).filter(Docente.estado == True)

        materia = request.args.get("materia", "").strip()
        if materia:
            try:
                query = query.join(Paralelo, Paralelo.docente_id == Docente.id)\
                             .join(Asignatura, Asignatura.id == Paralelo.asignatura_id)\
                             .filter(func.unaccent(Asignatura.nombre).ilike(func.unaccent(f"%{materia}%")))\
                             .distinct()
            except Exception:
                query = query.join(Paralelo, Paralelo.docente_id == Docente.id)\
                             .join(Asignatura, Asignatura.id == Paralelo.asignatura_id)\
                             .filter(Asignatura.nombre.ilike(f"%{materia}%"))\
                             .distinct()

        search = request.args.get("search", "").strip()
        if search:
            for term in search.split():
                try:
                    query = query.filter(
                        func.unaccent(Docente.nombres).ilike(func.unaccent(f"%{term}%")) |
                        func.unaccent(Docente.apellidos).ilike(func.unaccent(f"%{term}%"))
                    )
                except Exception:
                    query = query.filter(
                        Docente.nombres.ilike(f"%{term}%") |
                        Docente.apellidos.ilike(f"%{term}%")
                    )

        docentes = query.all()
        resultado = []

        for docente in docentes:
            resultado.append({
                "id": docente.id,
                "nombres": docente.nombres,
                "apellidos": docente.apellidos,
                "correo": docente.correo,
                "telefono": docente.telefono,
                "especialidad": docente.especialidad,
                "facultad_id": docente.facultad_id,
                "carga_horaria_maxima": docente.carga_horaria_maxima,
                "estado": docente.estado,
                "fecha_creacion": str(docente.fecha_creacion)
            })

        return jsonify(resultado), 200
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
            "facultad_id": docente.facultad_id,
            "carga_horaria_maxima": docente.carga_horaria_maxima,
            "estado": docente.estado,
            "fecha_creacion": str(docente.fecha_creacion)
        }), 200
    finally:
        db.close()


@docentes_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_docente():
    data = request.get_json()

    if not data or not data.get("nombres") or not data.get("apellidos") or not data.get("correo") or not data.get("facultad_id"):
        return jsonify({
            "error": "Nombres, apellidos, correo y facultad_id son obligatorios"
        }), 400

    db = SessionLocal()

    try:
        facultad = db.query(Facultad).filter(
            Facultad.id == data.get("facultad_id"),
            Facultad.estado == True
        ).first()

        if not facultad:
            return jsonify({"error": "La facultad indicada no existe"}), 404

        nuevo_docente = Docente(
            nombres=data.get("nombres"),
            apellidos=data.get("apellidos"),
            correo=data.get("correo"),
            telefono=data.get("telefono"),
            especialidad=data.get("especialidad"),
            facultad_id=data.get("facultad_id"),
            carga_horaria_maxima=data.get("carga_horaria_maxima", 40),
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

        return jsonify({
            "mensaje": "Docente creado correctamente",
            "docente": {
                "id": nuevo_docente.id,
                "nombres": nuevo_docente.nombres,
                "apellidos": nuevo_docente.apellidos,
                "correo": nuevo_docente.correo,
                "telefono": nuevo_docente.telefono,
                "especialidad": nuevo_docente.especialidad,
                "facultad_id": nuevo_docente.facultad_id,
                "carga_horaria_maxima": nuevo_docente.carga_horaria_maxima,
                "estado": nuevo_docente.estado,
                "fecha_creacion": str(nuevo_docente.fecha_creacion)
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

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
        docente.carga_horaria_maxima = data.get(
            "carga_horaria_maxima",
            docente.carga_horaria_maxima
        )

        if data.get("facultad_id"):
            facultad = db.query(Facultad).filter(
                Facultad.id == data.get("facultad_id"),
                Facultad.estado == True
            ).first()

            if not facultad:
                return jsonify({"error": "La facultad indicada no existe"}), 404

            docente.facultad_id = data.get("facultad_id")

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
            f"Se inactivó el docente con ID {id}"
        )

        return jsonify({"mensaje": "Docente inactivado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Paralelo, Carrera, Asignatura, Docente, PeriodoAcademico
from app.auth import requiere_roles
from app.audit import registrar_auditoria

paralelos_bp = Blueprint("paralelos", __name__)


@paralelos_bp.route("/", methods=["GET"])
def listar_paralelos():
    db = SessionLocal()
    try:
        paralelos = db.query(Paralelo).filter(Paralelo.estado == True).all()
        resultado = []

        for paralelo in paralelos:
            resultado.append({
                "id": paralelo.id,
                "nombre": paralelo.nombre,
                "carrera_id": paralelo.carrera_id,
                "asignatura_id": paralelo.asignatura_id,
                "docente_id": paralelo.docente_id,
                "periodo_id": paralelo.periodo_id,
                "estado": paralelo.estado,
                "fecha_creacion": str(paralelo.fecha_creacion)
            })

        return jsonify(resultado), 200
    finally:
        db.close()


@paralelos_bp.route("/<int:id>", methods=["GET"])
def obtener_paralelo(id):
    db = SessionLocal()
    try:
        paralelo = db.query(Paralelo).filter(
            Paralelo.id == id,
            Paralelo.estado == True
        ).first()

        if not paralelo:
            return jsonify({"error": "Paralelo no encontrado"}), 404

        return jsonify({
            "id": paralelo.id,
            "nombre": paralelo.nombre,
            "carrera_id": paralelo.carrera_id,
            "asignatura_id": paralelo.asignatura_id,
            "docente_id": paralelo.docente_id,
            "periodo_id": paralelo.periodo_id,
            "estado": paralelo.estado,
            "fecha_creacion": str(paralelo.fecha_creacion)
        }), 200
    finally:
        db.close()


@paralelos_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_paralelo():
    data = request.get_json()

    campos = ["nombre", "carrera_id", "asignatura_id", "docente_id", "periodo_id"]

    if not data or any(not data.get(campo) for campo in campos):
        return jsonify({
            "error": "Nombre, carrera_id, asignatura_id, docente_id y periodo_id son obligatorios"
        }), 400

    db = SessionLocal()

    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == data.get("carrera_id"),
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        asignatura = db.query(Asignatura).filter(
            Asignatura.id == data.get("asignatura_id"),
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({"error": "La asignatura indicada no existe"}), 404

        docente = db.query(Docente).filter(
            Docente.id == data.get("docente_id"),
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "El docente indicado no existe"}), 404

        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == data.get("periodo_id"),
            PeriodoAcademico.estado == True,
            PeriodoAcademico.estado_periodo == "activo"
        ).first()

        if not periodo:
            return jsonify({"error": "El periodo académico debe estar activo"}), 400

        if asignatura.carrera_id != int(data.get("carrera_id")):
            return jsonify({
                "error": "La asignatura no pertenece a la carrera indicada"
            }), 400

        if asignatura.periodo_id != int(data.get("periodo_id")):
            return jsonify({
                "error": "La asignatura no pertenece al periodo académico indicado"
            }), 400

        nuevo_paralelo = Paralelo(
            nombre=data.get("nombre"),
            carrera_id=data.get("carrera_id"),
            asignatura_id=data.get("asignatura_id"),
            docente_id=data.get("docente_id"),
            periodo_id=data.get("periodo_id"),
            estado=True
        )

        db.add(nuevo_paralelo)
        db.commit()
        db.refresh(nuevo_paralelo)

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "CREAR",
            "PARALELOS",
            f"Se creó el paralelo {nuevo_paralelo.nombre}"
        )

        return jsonify({
            "mensaje": "Paralelo creado correctamente",
            "paralelo": {
                "id": nuevo_paralelo.id,
                "nombre": nuevo_paralelo.nombre,
                "carrera_id": nuevo_paralelo.carrera_id,
                "asignatura_id": nuevo_paralelo.asignatura_id,
                "docente_id": nuevo_paralelo.docente_id,
                "periodo_id": nuevo_paralelo.periodo_id,
                "estado": nuevo_paralelo.estado,
                "fecha_creacion": str(nuevo_paralelo.fecha_creacion)
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@paralelos_bp.route("/<int:id>", methods=["PUT"])
@requiere_roles(["admin", "administrador"])
def actualizar_paralelo(id):
    data = request.get_json()

    db = SessionLocal()

    try:
        paralelo = db.query(Paralelo).filter(
            Paralelo.id == id,
            Paralelo.estado == True
        ).first()

        if not paralelo:
            return jsonify({"error": "Paralelo no encontrado"}), 404

        paralelo.nombre = data.get("nombre", paralelo.nombre)

        carrera_id = data.get("carrera_id", paralelo.carrera_id)
        asignatura_id = data.get("asignatura_id", paralelo.asignatura_id)
        docente_id = data.get("docente_id", paralelo.docente_id)
        periodo_id = data.get("periodo_id", paralelo.periodo_id)

        carrera = db.query(Carrera).filter(
            Carrera.id == carrera_id,
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        asignatura = db.query(Asignatura).filter(
            Asignatura.id == asignatura_id,
            Asignatura.estado == True
        ).first()

        if not asignatura:
            return jsonify({"error": "La asignatura indicada no existe"}), 404

        docente = db.query(Docente).filter(
            Docente.id == docente_id,
            Docente.estado == True
        ).first()

        if not docente:
            return jsonify({"error": "El docente indicado no existe"}), 404

        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == periodo_id,
            PeriodoAcademico.estado == True,
            PeriodoAcademico.estado_periodo == "activo"
        ).first()

        if not periodo:
            return jsonify({"error": "El periodo académico debe estar activo"}), 400

        if asignatura.carrera_id != int(carrera_id):
            return jsonify({
                "error": "La asignatura no pertenece a la carrera indicada"
            }), 400

        if asignatura.periodo_id != int(periodo_id):
            return jsonify({
                "error": "La asignatura no pertenece al periodo académico indicado"
            }), 400

        paralelo.carrera_id = carrera_id
        paralelo.asignatura_id = asignatura_id
        paralelo.docente_id = docente_id
        paralelo.periodo_id = periodo_id

        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ACTUALIZAR",
            "PARALELOS",
            f"Se actualizó el paralelo con ID {id}"
        )

        return jsonify({"mensaje": "Paralelo actualizado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


@paralelos_bp.route("/<int:id>", methods=["DELETE"])
@requiere_roles(["admin", "administrador"])
def eliminar_paralelo(id):
    db = SessionLocal()

    try:
        paralelo = db.query(Paralelo).filter(
            Paralelo.id == id,
            Paralelo.estado == True
        ).first()

        if not paralelo:
            return jsonify({"error": "Paralelo no encontrado"}), 404

        paralelo.estado = False
        db.commit()

        registrar_auditoria(
            request.headers.get("X-User-Id"),
            "ELIMINAR",
            "PARALELOS",
            f"Se inactivó el paralelo con ID {id}"
        )

        return jsonify({"mensaje": "Paralelo inactivado correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
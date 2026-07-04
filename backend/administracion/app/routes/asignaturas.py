from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Asignatura, Carrera, PeriodoAcademico
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
                "nivel": asignatura.nivel,
                "carrera_id": asignatura.carrera_id,
                "periodo_id": asignatura.periodo_id,
                "estado": asignatura.estado,
                "fecha_creacion": str(asignatura.fecha_creacion)
            })

        return jsonify(resultado), 200
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
            "nivel": asignatura.nivel,
            "carrera_id": asignatura.carrera_id,
            "periodo_id": asignatura.periodo_id,
            "estado": asignatura.estado,
            "fecha_creacion": str(asignatura.fecha_creacion)
        }), 200
    finally:
        db.close()


@asignaturas_bp.route("/", methods=["POST"])
@requiere_roles(["admin", "administrador"])
def crear_asignatura():
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("creditos") or not data.get("carrera_id") or not data.get("periodo_id"):
        return jsonify({
            "error": "Nombre, créditos, carrera_id y periodo_id son obligatorios"
        }), 400

    db = SessionLocal()

    try:
        carrera = db.query(Carrera).filter(
            Carrera.id == data.get("carrera_id"),
            Carrera.estado == True
        ).first()

        if not carrera:
            return jsonify({"error": "La carrera indicada no existe"}), 404

        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == data.get("periodo_id"),
            PeriodoAcademico.estado == True
        ).first()

        if not periodo:
            return jsonify({"error": "El periodo académico indicado no existe"}), 404

        nueva_asignatura = Asignatura(
            nombre=data.get("nombre"),
            codigo=data.get("codigo"),
            creditos=data.get("creditos"),
            nivel=data.get("nivel"),
            carrera_id=data.get("carrera_id"),
            periodo_id=data.get("periodo_id"),
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

        return jsonify({
            "mensaje": "Asignatura creada correctamente",
            "asignatura": {
                "id": nueva_asignatura.id,
                "nombre": nueva_asignatura.nombre,
                "codigo": nueva_asignatura.codigo,
                "creditos": nueva_asignatura.creditos,
                "nivel": nueva_asignatura.nivel,
                "carrera_id": nueva_asignatura.carrera_id,
                "periodo_id": nueva_asignatura.periodo_id,
                "estado": nueva_asignatura.estado,
                "fecha_creacion": str(nueva_asignatura.fecha_creacion)
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

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
        asignatura.nivel = data.get("nivel", asignatura.nivel)

        if data.get("carrera_id"):
            carrera = db.query(Carrera).filter(
                Carrera.id == data.get("carrera_id"),
                Carrera.estado == True
            ).first()

            if not carrera:
                return jsonify({"error": "La carrera indicada no existe"}), 404

            asignatura.carrera_id = data.get("carrera_id")

        if data.get("periodo_id"):
            periodo = db.query(PeriodoAcademico).filter(
                PeriodoAcademico.id == data.get("periodo_id"),
                PeriodoAcademico.estado == True
            ).first()

            if not periodo:
                return jsonify({"error": "El periodo académico indicado no existe"}), 404

            asignatura.periodo_id = data.get("periodo_id")

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
            f"Se inactivó la asignatura con ID {id}"
        )

        return jsonify({"mensaje": "Asignatura inactivada correctamente"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
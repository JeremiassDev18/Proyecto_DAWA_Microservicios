from __future__ import annotations

import logging
import os
from threading import Thread
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

logger = logging.getLogger(__name__)


def create_app(service: Any) -> Flask:
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/detalle", methods=["GET"])
    def detalle_solicitud(solicitud_id: str):
        try:
            tutoria = service.obtener_tutoria(solicitud_id)
            return jsonify(tutoria), 200
        except KeyError:
            return jsonify({"error": "Solicitud no encontrada"}), 404
        except Exception as e:
            logger.error(f"Error obteniendo detalle de solicitud {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/bitacoras/<solicitud_id>", methods=["GET"])
    def bitacoras_solicitud(solicitud_id: str):
        try:
            service.obtener_tutoria(solicitud_id)
        except KeyError:
            return jsonify({"error": "Solicitud no encontrada"}), 404
        try:
            bitacoras = service.obtener_bitacoras(solicitud_id)
            return jsonify({
                "solicitud_id": int(solicitud_id),
                "cantidad": len(bitacoras),
                "bitacoras": bitacoras,
            }), 200
        except Exception as e:
            logger.error(f"Error obteniendo bitácoras de solicitud {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes", methods=["POST"])
    def crear_solicitud():
        data = request.get_json(silent=True) or {}
        try:
            resultado = service.registrar_solicitud_tutoria(
                estudiante_id=data.get("estudiante_id"),
                asignatura_id=data.get("asignatura_id"),
                periodo_id=data.get("periodo_id"),
                tema=data.get("tema", ""),
                fecha_solicitud=data.get("fecha_solicitud"),
                fecha_agendada=data.get("fecha_agendada"),
            )
            return jsonify(resultado), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error creando solicitud: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes/<solicitud_id>", methods=["GET"])
    def obtener_solicitud(solicitud_id: str):
        try:
            tutoria = service.obtener_tutoria(solicitud_id)
            return jsonify(tutoria), 200
        except KeyError:
            return jsonify({"error": "Solicitud no encontrada"}), 404
        except Exception as e:
            logger.error(f"Error obteniendo solicitud {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes", methods=["GET"])
    def listar_solicitudes():
        estudiante_id = request.args.get("estudiante_id")
        if not estudiante_id:
            return jsonify({"error": "Parámetro estudiante_id requerido"}), 400
        try:
            periodo_id = request.args.get("periodo_id")
            resultado = service.consultar_tutorias_por_estudiante(estudiante_id, periodo_id)
            return jsonify({
                "cantidad": len(resultado),
                "solicitudes": resultado,
            }), 200
        except Exception as e:
            logger.error(f"Error listando solicitudes: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/asignar", methods=["PUT"])
    def asignar(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        docente_id = data.get("docente_id")
        if not docente_id:
            return jsonify({"error": "docente_id requerido"}), 400
        try:
            resultado = service.asignar_tutoria(
                tutoria_id=solicitud_id,
                docente_id=docente_id,
                usuario_id=data.get("usuario_id"),
            )
            if not resultado.get("asignada"):
                return jsonify(resultado), 409
            return jsonify(resultado), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error asignando tutoría {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/confirmar", methods=["PUT"])
    def confirmar(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        try:
            resultado = service.confirmar_o_cancelar_tutoria(
                tutoria_id=solicitud_id,
                accion="confirmar",
                usuario_id=data.get("usuario_id"),
                rol_usuario=data.get("rol_usuario"),
            )
            return jsonify(resultado), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error confirmando tutoría {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/cancelar", methods=["PUT"])
    def cancelar(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        try:
            resultado = service.confirmar_o_cancelar_tutoria(
                tutoria_id=solicitud_id,
                accion="cancelar",
                motivo=data.get("motivo"),
                usuario_id=data.get("usuario_id"),
                rol_usuario=data.get("rol_usuario"),
            )
            return jsonify(resultado), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error cancelando tutoría {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/atender", methods=["PUT"])
    def atender(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        asistio = data.get("asistio")
        if asistio is None:
            return jsonify({"error": "asistio requerido (true/false)"}), 400
        try:
            resultado = service.registrar_asistencia_estudiante(
                tutoria_id=solicitud_id,
                asistio=bool(asistio),
                usuario_id=data.get("usuario_id"),
            )
            if data.get("detalle"):
                service.registrar_bitacora_atencion(
                    tutoria_id=solicitud_id,
                    detalle=data["detalle"],
                    temas_detectados=data.get("temas_detectados"),
                    usuario_id=data.get("usuario_id"),
                )
            return jsonify(resultado), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error atendiendo tutoría {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tutorias/reportes/temas-recurrentes", methods=["GET"])
    def reporte_temas_recurrentes():
        periodo_id = request.args.get("periodo_id")
        try:
            resultado = service.generar_reporte_temas_recurrentes(periodo_id)
            return jsonify(resultado), 200
        except Exception as e:
            logger.error(f"Error generando reporte de temas recurrentes: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R02: Disponibilidad docente (conecta con Administración) ──

    @app.route("/api/tutorias/docentes/<docente_id>/disponibilidad", methods=["GET"])
    def disponibilidad_docente(docente_id: str):
        try:
            disponibilidad = service.admin_client.obtener_disponibilidad_docente(docente_id)
            fecha = request.args.get("fecha")
            if fecha:
                disponible = service.validar_disponibilidad_docente(docente_id, fecha)
                disponibilidad["disponible"] = disponible
            return jsonify(disponibilidad), 200
        except Exception as e:
            logger.error(f"Error obteniendo disponibilidad del docente {docente_id}: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R06: Bitácora independiente ──

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/bitacora", methods=["POST"])
    def registrar_bitacora(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        detalle = data.get("detalle")
        if not detalle:
            return jsonify({"error": "detalle requerido"}), 400
        try:
            resultado = service.registrar_bitacora_atencion(
                tutoria_id=solicitud_id,
                detalle=detalle,
                temas_detectados=data.get("temas_detectados"),
                usuario_id=data.get("usuario_id"),
            )
            return jsonify(resultado), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error registrando bitácora: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R07: Gestión manual de estado ──

    @app.route("/api/tutorias/solicitudes/<solicitud_id>/estado", methods=["PUT"])
    def gestionar_estado(solicitud_id: str):
        data = request.get_json(silent=True) or {}
        estado = data.get("estado")
        if not estado:
            return jsonify({"error": "estado requerido"}), 400
        try:
            resultado = service.gestionar_estado_tutoria(
                tutoria_id=solicitud_id,
                estado=estado,
                usuario_id=data.get("usuario_id"),
                rol_usuario=data.get("rol_usuario"),
                comentario=data.get("comentario"),
            )
            return jsonify(resultado), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error gestionando estado de tutoría {solicitud_id}: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R08: Casos académicos ──

    @app.route("/api/tutorias/casos-academicos", methods=["POST"])
    def crear_caso_academico():
        data = request.get_json(silent=True) or {}
        estudiante_id = data.get("estudiante_id")
        descripcion = data.get("descripcion")
        if not estudiante_id or not descripcion:
            return jsonify({"error": "estudiante_id y descripcion requeridos"}), 400
        try:
            resultado = service.registrar_seguimiento_caso_academico(
                estudiante_id=estudiante_id,
                descripcion=descripcion,
                severidad=data.get("severidad", "media"),
            )
            return jsonify(resultado), 201
        except Exception as e:
            logger.error(f"Error creando caso académico: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R09: Reporte por docente ──

    @app.route("/api/tutorias/reportes/por-docente", methods=["GET"])
    def reporte_por_docente():
        docente_id = request.args.get("docente_id")
        if not docente_id:
            return jsonify({"error": "docente_id requerido"}), 400
        try:
            periodo_id = request.args.get("periodo_id")
            resultado = service.generar_reporte_tutorias_por_docente(docente_id, periodo_id)
            return jsonify(resultado), 200
        except Exception as e:
            logger.error(f"Error generando reporte por docente: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R10: Reporte estudiantes atendidos ──

    @app.route("/api/tutorias/reportes/estudiantes-atendidos", methods=["GET"])
    def reporte_estudiantes_atendidos():
        try:
            periodo_id = request.args.get("periodo_id")
            resultado = service.generar_reporte_estudiantes_atendidos(periodo_id)
            return jsonify(resultado), 200
        except Exception as e:
            logger.error(f"Error generando reporte de estudiantes atendidos: {e}")
            return jsonify({"error": str(e)}), 500

    # ── TUT-R12: Consultar notificaciones ──

    @app.route("/api/tutorias/notificaciones", methods=["GET"])
    def listar_notificaciones():
        destinatario_id = request.args.get("destinatario_id")
        if not destinatario_id:
            return jsonify({"error": "destinatario_id requerido"}), 400
        try:
            solo_no_leidas = request.args.get("solo_no_leidas", "false").lower() == "true"
            resultado = service.consultar_notificaciones(destinatario_id, solo_no_leidas)
            return jsonify({
                "cantidad": len(resultado),
                "notificaciones": resultado,
            }), 200
        except Exception as e:
            logger.error(f"Error consultando notificaciones: {e}")
            return jsonify({"error": str(e)}), 500

    return app


def run_api(service: Any, host: str = "0.0.0.0", port: int | None = None) -> None:
    if port is None:
        port = int(os.getenv("API_PORT", "5003"))
    app = create_app(service)
    logger.info(f"Iniciando API REST en {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


def start_api_thread(service: Any) -> Thread:
    port = int(os.getenv("API_PORT", "5003"))
    thread = Thread(target=run_api, args=(service,), kwargs={"port": port}, daemon=True)
    thread.start()
    logger.info(f"API REST iniciada en hilo secundario (puerto {port})")
    return thread

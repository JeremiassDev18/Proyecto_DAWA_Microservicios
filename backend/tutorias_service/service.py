from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from .models_db import (
    BitacoraAtencion,
    CasoAcademicoDB,
    HistorialEstado,
    Notificacion,
    SolicitudTutoria,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TutoriasService:
    def __init__(
        self,
        db_session_factory: Callable[[], Session] | None = None,
        admin_client: Any | None = None,
    ) -> None:
        self.db_session_factory = db_session_factory
        self.admin_client = admin_client

    # ── helpers ─────────────────────────────────────────────────

    def _get_db(self) -> Session:
        if not self.db_session_factory:
            raise RuntimeError("db_session_factory no configurado")
        return self.db_session_factory()

    def _serializar_solicitud(self, s: SolicitudTutoria) -> Dict[str, Any]:
        fs = s.fecha_solicitud
        fa = s.fecha_agendada
        return {
            "id": s.id,
            "codigo": str(s.id),
            "estudiante_id": s.estudiante_id,
            "docente_id": s.docente_id,
            "asignatura_id": s.asignatura_id,
            "periodo_id": s.periodo_id,
            "tema": s.tema,
            "estado": s.estado,
            "fecha_solicitud": fs.isoformat() if fs else None,
            "fecha_agendada": fa.isoformat() if fa else None,
            "fecha_actualizacion": s.fecha_actualizacion.isoformat() if s.fecha_actualizacion else None,
            "motivo_cancelacion": s.motivo_cancelacion,
        }

    def _registrar_auditoria(self, db: Session, usuario_id: str | None, accion: str, descripcion: str) -> None:
        from .models_db import AuditoriaTutoria

        auditoria = AuditoriaTutoria(
            usuario_id=usuario_id,
            accion=accion,
            modulo="TUTORIAS",
            descripcion=descripcion,
            fecha=_now(),
        )
        db.add(auditoria)

    def _crear_historial(
        self,
        db: Session,
        solicitud_id: int,
        estado_anterior: str | None,
        estado_nuevo: str,
        usuario_id: str | None = None,
        rol_usuario: str | None = None,
        comentario: str | None = None,
    ) -> HistorialEstado:
        h = HistorialEstado(
            solicitud_id=solicitud_id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario_id=usuario_id,
            rol_usuario=rol_usuario,
            fecha_cambio=_now(),
            comentario=comentario,
        )
        db.add(h)
        return h

    def _crear_notificacion(
        self,
        db: Session,
        solicitud_id: int,
        destinatario_id: int,
        destinatario_rol: str,
        tipo: str,
        mensaje: str,
    ) -> Notificacion:
        n = Notificacion(
            solicitud_id=solicitud_id,
            destinatario_id=destinatario_id,
            destinatario_rol=destinatario_rol,
            tipo=tipo,
            mensaje=mensaje,
            leida=False,
            fecha_creacion=_now(),
        )
        db.add(n)
        return n

    # ── métodos de negocio ──────────────────────────────────────

    def registrar_docente(self, docente_id: str, nombre: str, disponibilidades: Optional[List[str]] = None) -> Dict[str, object]:
        if self.admin_client:
            resultado = self.admin_client.obtener_docente(docente_id)
            if resultado and "nombres" in resultado:
                nombre = f"{resultado['nombres']} {resultado.get('apellidos', '')}".strip()
            elif not resultado:
                raise ValueError(f"Docente {docente_id} no encontrado en Administracionfix")
        return {"id": docente_id, "nombre": nombre, "disponibilidades": disponibilidades or []}

    def registrar_solicitud_tutoria(
        self,
        estudiante_id: int | str,
        asignatura_id: int | str | None = None,
        periodo_id: int | str | None = None,
        tema: str = "",
        fecha_solicitud: str | None = None,
        fecha_agendada: str | None = None,
    ) -> Dict[str, object]:
        asignatura_periodo_id = None
        if self.admin_client:
            validacion = self.admin_client.validar_estudiante(estudiante_id)
            if not validacion.get("valido"):
                raise ValueError(validacion.get("mensaje", "Estudiante no válido para tutoría"))
            estudiante_carrera_id = validacion.get("carrera_id")
            estudiante_periodo_id = validacion.get("periodo_id")

            if asignatura_id:
                val_asig = self.admin_client.validar_asignatura(asignatura_id)
                if not val_asig.get("valida"):
                    raise ValueError(val_asig.get("mensaje", "Asignatura no válida"))
                if estudiante_carrera_id and val_asig.get("carrera_id") != estudiante_carrera_id:
                    raise ValueError("La materia no pertenece a la carrera del estudiante")
                if estudiante_periodo_id and val_asig.get("periodo_id") != estudiante_periodo_id:
                    raise ValueError("La materia no corresponde al periodo académico del estudiante")
                asignatura_periodo_id = val_asig.get("periodo_id")
            if periodo_id:
                val_per = self.admin_client.validar_periodo_activo(periodo_id)
                if not val_per.get("valido"):
                    raise ValueError(val_per.get("mensaje", "Periodo académico no válido"))

        # Si no se envió periodo_id pero hay asignatura, se hereda el periodo de la asignatura
        if not periodo_id and asignatura_periodo_id:
            periodo_id = asignatura_periodo_id

        db = self._get_db()
        try:
            fs = _now()
            if fecha_solicitud:
                try:
                    fs = datetime.fromisoformat(fecha_solicitud)
                except ValueError:
                    pass

            fa = None
            if fecha_agendada:
                try:
                    fa = datetime.fromisoformat(fecha_agendada)
                except ValueError:
                    pass

            solicitud = SolicitudTutoria(
                estudiante_id=int(estudiante_id),
                docente_id=None,
                asignatura_id=int(asignatura_id) if asignatura_id else None,
                periodo_id=int(periodo_id) if periodo_id else None,
                tema=tema,
                estado="solicitada",
                fecha_solicitud=fs,
                fecha_agendada=fa,
                fecha_actualizacion=_now(),
            )
            db.add(solicitud)
            db.flush()

            self._crear_historial(db, solicitud.id, None, "solicitada",
                                  usuario_id=str(estudiante_id), rol_usuario="estudiante")
            self._registrar_auditoria(db, str(estudiante_id), "CREAR_SOLICITUD",
                                      f"Solicitud de tutoría creada por estudiante {estudiante_id}")

            db.commit()
            db.refresh(solicitud)
            return self._serializar_solicitud(solicitud)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def validar_disponibilidad_docente(self, docente_id: str, fecha: str) -> bool:
        if self.admin_client:
            return self.admin_client.validar_disponibilidad_en_fecha(docente_id, fecha)
        return True

    def asignar_tutoria(
        self,
        tutoria_id: int | str,
        docente_id: int | str,
        usuario_id: str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            if self.admin_client:
                val_doc = self.admin_client.validar_docente_existe(docente_id)
                if not val_doc.get("valido"):
                    raise ValueError(val_doc.get("mensaje", "Docente no encontrado en Administracionfix"))

            if not self.validar_disponibilidad_docente(str(docente_id),
                                                        solicitud.fecha_solicitud.strftime("%Y-%m-%d")):
                return {"asignada": False, "docente_id": int(docente_id), "motivo": "Docente sin disponibilidad"}

            estado_anterior = solicitud.estado
            solicitud.docente_id = int(docente_id)
            solicitud.estado = "asignada"
            solicitud.fecha_actualizacion = _now()

            self._crear_historial(db, solicitud.id, estado_anterior, "asignada",
                                  usuario_id=usuario_id, rol_usuario="coordinador")
            self._registrar_auditoria(db, usuario_id, "ASIGNAR_TUTORIA",
                                      f"Tutoría {tutoria_id} asignada a docente {docente_id}")
            self._crear_notificacion(db, solicitud.id, int(docente_id), "docente",
                                     "asignacion", f"Se te ha asignado la tutoría #{tutoria_id}")

            db.commit()
            return {"asignada": True, "docente_id": int(docente_id), "estado": "asignada"}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def confirmar_o_cancelar_tutoria(
        self,
        tutoria_id: int | str,
        accion: str,
        motivo: str | None = None,
        usuario_id: str | None = None,
        rol_usuario: str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            estado_anterior = solicitud.estado
            if accion == "confirmar":
                solicitud.estado = "confirmada"
            elif accion == "cancelar":
                solicitud.estado = "cancelada"
                solicitud.motivo_cancelacion = motivo
            else:
                raise ValueError("Acción no soportada")

            solicitud.fecha_actualizacion = _now()

            self._crear_historial(db, solicitud.id, estado_anterior, solicitud.estado,
                                  usuario_id=usuario_id, rol_usuario=rol_usuario,
                                  comentario=motivo)
            self._registrar_auditoria(db, usuario_id, f"{accion.upper()}_TUTORIA",
                                      f"Tutoría {tutoria_id} {accion}ada")

            if solicitud.estudiante_id:
                self._crear_notificacion(db, solicitud.id, solicitud.estudiante_id, "estudiante",
                                         "cambio_estado",
                                         f"Tu tutoría #{tutoria_id} ha sido {solicitud.estado}")

            db.commit()
            db.refresh(solicitud)
            return self._serializar_solicitud(solicitud)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def registrar_asistencia_estudiante(
        self,
        tutoria_id: int | str,
        asistio: bool,
        usuario_id: str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            bitacora = BitacoraAtencion(
                solicitud_id=solicitud.id,
                asistio=asistio,
                fecha_registro=_now(),
            )
            db.add(bitacora)
            solicitud.estado = "atendida" if asistio else "no_asistida"
            solicitud.fecha_actualizacion = _now()

            self._crear_historial(db, solicitud.id, None, solicitud.estado,
                                  usuario_id=usuario_id, rol_usuario="docente")
            self._registrar_auditoria(db, usuario_id, "REGISTRAR_ASISTENCIA",
                                      f"Asistencia de tutoría {tutoria_id}: {'asistió' if asistio else 'no asistió'}")

            db.commit()
            return {"tutoria_id": solicitud.id, "asistio": asistio, "estado": solicitud.estado}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def registrar_bitacora_atencion(
        self,
        tutoria_id: int | str,
        detalle: str,
        temas_detectados: str | None = None,
        usuario_id: str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            bitacora = BitacoraAtencion(
                solicitud_id=solicitud.id,
                observaciones=detalle,
                temas_detectados=temas_detectados,
                fecha_registro=_now(),
            )
            db.add(bitacora)
            solicitud.fecha_actualizacion = _now()

            self._registrar_auditoria(db, usuario_id, "REGISTRAR_BITACORA",
                                      f"Bitácora registrada para tutoría {tutoria_id}")

            db.commit()
            return {"tutoria_id": solicitud.id, "bitacora": [detalle]}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def gestionar_estado_tutoria(
        self,
        tutoria_id: int | str,
        estado: str,
        usuario_id: str | None = None,
        rol_usuario: str | None = None,
        comentario: str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            estado_anterior = solicitud.estado
            solicitud.estado = estado
            solicitud.fecha_actualizacion = _now()

            self._crear_historial(db, solicitud.id, estado_anterior, estado,
                                  usuario_id=usuario_id, rol_usuario=rol_usuario, comentario=comentario)
            self._registrar_auditoria(db, usuario_id, "GESTIONAR_ESTADO",
                                      f"Estado de tutoría {tutoria_id} cambiado de {estado_anterior} a {estado}")

            db.commit()
            db.refresh(solicitud)
            return self._serializar_solicitud(solicitud)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def registrar_seguimiento_caso_academico(
        self,
        estudiante_id: str,
        descripcion: str,
        severidad: str = "media",
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            caso = CasoAcademicoDB(
                estudiante_id=int(estudiante_id),
                descripcion=descripcion,
                severidad=severidad,
                estado="abierto",
            )
            db.add(caso)
            db.commit()
            db.refresh(caso)
            return {
                "id": caso.id,
                "estudiante_id": caso.estudiante_id,
                "descripcion": caso.descripcion,
                "severidad": caso.severidad,
                "estado": caso.estado,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def generar_reporte_tutorias_por_docente(
        self,
        docente_id: int | str,
        periodo_id: int | str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            query = db.query(SolicitudTutoria).filter(SolicitudTutoria.docente_id == int(docente_id))
            if periodo_id:
                query = query.filter(SolicitudTutoria.periodo_id == int(periodo_id))
            tutorias = query.all()
            return {
                "docente_id": int(docente_id),
                "periodo_id": int(periodo_id) if periodo_id else None,
                "cantidad": len(tutorias),
                "tutorias": [self._serializar_solicitud(s) for s in tutorias],
            }
        finally:
            db.close()

    def generar_reporte_estudiantes_atendidos(
        self,
        periodo_id: int | str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            query = db.query(SolicitudTutoria).join(
                BitacoraAtencion,
                BitacoraAtencion.solicitud_id == SolicitudTutoria.id,
            ).filter(BitacoraAtencion.asistio == True)
            if periodo_id:
                query = query.filter(SolicitudTutoria.periodo_id == int(periodo_id))
            tutorias = query.all()
            estudiantes = sorted({s.estudiante_id for s in tutorias})
            return {
                "cantidad": len(estudiantes),
                "estudiantes": estudiantes,
                "periodo_id": int(periodo_id) if periodo_id else None,
            }
        finally:
            db.close()

    def generar_reporte_temas_recurrentes(
        self,
        periodo_id: int | str | None = None,
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            query = db.query(SolicitudTutoria)
            if periodo_id:
                query = query.filter(SolicitudTutoria.periodo_id == int(periodo_id))
            tutorias = query.all()

            contador: Dict[str, int] = {}
            for s in tutorias:
                contador[s.tema] = contador.get(s.tema, 0) + 1

            temas = sorted(contador.keys())
            detalle = [{"tema": t, "cantidad": contador[t]} for t in temas]
            return {
                "temas": temas,
                "detalle": detalle,
                "periodo_id": int(periodo_id) if periodo_id else None,
            }
        finally:
            db.close()

    def notificar_cambio_estado(
        self,
        tutoria_id: int | str,
        estado: str,
        destinatario_id: int | None = None,
        destinatario_rol: str = "estudiante",
    ) -> Dict[str, object]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise ValueError("No existe la tutoría")

            n = self._crear_notificacion(
                db,
                solicitud.id,
                destinatario_id or solicitud.estudiante_id,
                destinatario_rol,
                "cambio_estado",
                f"Cambio de estado en tutoría #{tutoria_id}: {estado}",
            )
            db.commit()
            return {
                "id": n.id,
                "tutoria_id": n.solicitud_id,
                "mensaje": n.mensaje,
                "tipo": n.tipo,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def obtener_tutoria(self, tutoria_id: int | str) -> Dict[str, Any]:
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(SolicitudTutoria.id == int(tutoria_id)).first()
            if not solicitud:
                raise KeyError(f"No existe la tutoría {tutoria_id}")
            return self._serializar_solicitud(solicitud)
        finally:
            db.close()

    def obtener_bitacoras(self, solicitud_id: int | str) -> List[Dict[str, Any]]:
        db = self._get_db()
        try:
            registros = db.query(BitacoraAtencion).filter(
                BitacoraAtencion.solicitud_id == int(solicitud_id)
            ).all()
            return [
                {
                    "id": r.id,
                    "observaciones": r.observaciones,
                    "asistio": r.asistio,
                    "temas_detectados": r.temas_detectados,
                    "fecha_registro": r.fecha_registro.isoformat() if r.fecha_registro else None,
                }
                for r in registros
            ]
        finally:
            db.close()

    def consultar_tutorias_por_estudiante(
        self,
        estudiante_id: int | str,
        periodo_id: int | str | None = None,
    ) -> List[Dict[str, object]]:
        db = self._get_db()
        try:
            query = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.estudiante_id == int(estudiante_id)
            )
            if periodo_id:
                query = query.filter(SolicitudTutoria.periodo_id == int(periodo_id))
            return [self._serializar_solicitud(s) for s in query.all()]
        finally:
            db.close()

    def consultar_mis_bitacoras(self, estudiante_id: int | str) -> List[Dict[str, object]]:
        db = self._get_db()
        try:
            resultados = (
                db.query(SolicitudTutoria, BitacoraAtencion)
                .join(BitacoraAtencion, BitacoraAtencion.solicitud_id == SolicitudTutoria.id)
                .filter(SolicitudTutoria.estudiante_id == int(estudiante_id))
                .all()
            )
            return [
                {
                    "solicitud_id": s.id,
                    "codigo": str(s.id),
                    "tema": s.tema,
                    "estado": s.estado,
                    "docente_id": s.docente_id,
                    "asignatura_id": s.asignatura_id,
                    "periodo_id": s.periodo_id,
                    "bitacora_id": b.id,
                    "observaciones": b.observaciones,
                    "asistio": b.asistio,
                    "temas_detectados": b.temas_detectados,
                    "fecha_registro": b.fecha_registro.isoformat() if b.fecha_registro else None,
                    "fecha_solicitud": s.fecha_solicitud.isoformat() if s.fecha_solicitud else None,
                }
                for s, b in resultados
            ]
        finally:
            db.close()

    def consultar_notificaciones(
        self,
        destinatario_id: int | str,
        solo_no_leidas: bool = False,
    ) -> List[Dict[str, object]]:
        db = self._get_db()
        try:
            query = db.query(Notificacion).filter(
                Notificacion.destinatario_id == int(destinatario_id)
            )
            if solo_no_leidas:
                query = query.filter(Notificacion.leida == False)
            registros = query.all()
            return [
                {
                    "id": n.id,
                    "solicitud_id": n.solicitud_id,
                    "destinatario_id": n.destinatario_id,
                    "destinatario_rol": n.destinatario_rol,
                    "tipo": n.tipo,
                    "mensaje": n.mensaje,
                    "leida": n.leida,
                    "fecha_creacion": n.fecha_creacion.isoformat() if n.fecha_creacion else None,
                    "fecha_lectura": n.fecha_lectura.isoformat() if n.fecha_lectura else None,
                }
                for n in registros
            ]
        finally:
            db.close()

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from .models_db import (
    BitacoraAtencion,
    CasoAcademicoDB,
    HistorialEstado,
    InscripcionSesion,
    Notificacion,
    SesionTutoria,
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

    # ── batch cache helpers ─────────────────────────────────────

    def _build_caches(self, solicitudes: list, sesiones: list | None = None) -> Dict[str, Dict]:
        """Fetch docentes, estudiantes, and asignaturas once for all rows."""
        cache: Dict[str, Dict] = {"docentes": {}, "estudiantes": {}, "asignaturas": {}}
        if not self.admin_client:
            return cache

        # Collect unique IDs
        est_ids = set()
        doc_ids = set()
        asig_ids = set()
        for s in solicitudes:
            est_ids.add(s.estudiante_id)
            if s.docente_id:
                doc_ids.add(s.docente_id)
            if s.asignatura_id:
                asig_ids.add(s.asignatura_id)
        if sesiones:
            for s in sesiones:
                if s.docente_id:
                    doc_ids.add(s.docente_id)
                if s.asignatura_id:
                    asig_ids.add(s.asignatura_id)

        # Batch fetch estudiantes
        for eid in est_ids:
            try:
                est = self.admin_client.obtener_estudiante(eid)
                if est:
                    cache["estudiantes"][eid] = f"{est.get('nombres', '')} {est.get('apellidos', '')}".strip()
            except Exception:
                pass

        # Batch fetch docentes
        for did in doc_ids:
            try:
                doc = self.admin_client.obtener_docente(did)
                if doc:
                    cache["docentes"][did] = f"{doc.get('nombres', '')} {doc.get('apellidos', '')}".strip()
            except Exception:
                pass

        # Batch fetch asignaturas (single call)
        if asig_ids:
            try:
                all_asig = self.admin_client.listar_asignaturas()
                for a in all_asig:
                    if a.get("id") in asig_ids:
                        cache["asignaturas"][a["id"]] = a.get("nombre")
            except Exception:
                pass

        return cache

    def _serializar_solicitud(self, s: SolicitudTutoria, cache: Dict[str, Dict] | None = None) -> Dict[str, Any]:
        fs = s.fecha_solicitud
        fa = s.fecha_agendada
        estudiante_nombre = None
        materia_nombre = None
        if cache:
            estudiante_nombre = cache.get("estudiantes", {}).get(s.estudiante_id)
            if s.asignatura_id:
                materia_nombre = cache.get("asignaturas", {}).get(s.asignatura_id)
        elif self.admin_client:
            try:
                estudiante = self.admin_client.obtener_estudiante(s.estudiante_id)
                if estudiante:
                    estudiante_nombre = f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip()
            except Exception:
                pass
            try:
                if s.asignatura_id:
                    asignaturas = self.admin_client._get(f"/asignaturas/")
                    if isinstance(asignaturas, list):
                        for a in asignaturas:
                            if a.get("id") == s.asignatura_id:
                                materia_nombre = a.get("nombre")
                                break
            except Exception:
                pass
        return {
            "id": s.id,
            "codigo": str(s.id),
            "estudiante_id": s.estudiante_id,
            "estudiante_nombre": estudiante_nombre,
            "docente_id": s.docente_id,
            "asignatura_id": s.asignatura_id,
            "materia_nombre": materia_nombre,
            "periodo_id": s.periodo_id,
            "sesion_id": s.sesion_id,
            "tema": s.tema,
            "estado": s.estado,
            "fecha_solicitud": fs.isoformat() if fs else None,
            "fecha_agendada": fa.isoformat() if fa else None,
            "fecha_actualizacion": s.fecha_actualizacion.isoformat() if s.fecha_actualizacion else None,
            "motivo_cancelacion": s.motivo_cancelacion,
            "motivo_rechazo": s.motivo_rechazo,
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

            if solicitud.fecha_agendada and not self.validar_disponibilidad_docente(
                str(docente_id), solicitud.fecha_agendada.strftime("%Y-%m-%d")
            ):
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
            cache = self._build_caches(tutorias)
            return {
                "docente_id": int(docente_id),
                "periodo_id": int(periodo_id) if periodo_id else None,
                "cantidad": len(tutorias),
                "tutorias": [self._serializar_solicitud(s, cache) for s in tutorias],
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
            rows = query.all()
            cache = self._build_caches(rows)
            return [self._serializar_solicitud(s, cache) for s in rows]
        finally:
            db.close()

    def listar_todas_solicitudes(
        self,
        periodo_id: int | str | None = None,
    ) -> List[Dict[str, object]]:
        """Retorna todas las solicitudes de tutoría (sin filtro por estudiante)."""
        db = self._get_db()
        try:
            query = db.query(SolicitudTutoria)
            if periodo_id:
                query = query.filter(SolicitudTutoria.periodo_id == int(periodo_id))
            rows = query.all()
            cache = self._build_caches(rows)
            return [self._serializar_solicitud(s, cache) for s in rows]
        finally:
            db.close()

    def consultar_mis_bitacoras(self, estudiante_id: int | str) -> List[Dict[str, object]]:
        db = self._get_db()
        try:
            eid = int(estudiante_id)
            # Bitácoras de tutorías individuales (directas del estudiante)
            directos = (
                db.query(SolicitudTutoria, BitacoraAtencion)
                .join(BitacoraAtencion, BitacoraAtencion.solicitud_id == SolicitudTutoria.id)
                .filter(SolicitudTutoria.estudiante_id == eid)
                .all()
            )
            # Bitácoras de sesiones grupales donde el estudiante se inscribió
            grupales = (
                db.query(SolicitudTutoria, BitacoraAtencion)
                .join(SesionTutoria, SesionTutoria.solicitud_id == SolicitudTutoria.id)
                .join(InscripcionSesion, InscripcionSesion.sesion_id == SesionTutoria.id)
                .join(BitacoraAtencion, BitacoraAtencion.solicitud_id == SolicitudTutoria.id)
                .filter(InscripcionSesion.estudiante_id == eid)
                .all()
            )
            # Combinar evitando duplicados
            seen = set()
            resultados = []
            for s, b in directos + grupales:
                key = (s.id, b.id)
                if key not in seen:
                    seen.add(key)
                    resultados.append((s, b))
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

    # ── Métodos de sesiones grupales ─────────────────────────────

    def _serializar_sesion(self, s: SesionTutoria, cache: Dict[str, Dict] | None = None) -> Dict[str, Any]:
        fa = s.fecha_agendada
        fi = s.fecha_inicio
        ff = s.fecha_fin
        docente_nombre = None
        materia_nombre = None
        if cache:
            docente_nombre = cache.get("docentes", {}).get(s.docente_id)
            if s.asignatura_id:
                materia_nombre = cache.get("asignaturas", {}).get(s.asignatura_id)
        elif self.admin_client:
            try:
                docente = self.admin_client.obtener_docente(s.docente_id)
                if docente:
                    docente_nombre = f"{docente.get('nombres', '')} {docente.get('apellidos', '')}".strip()
            except Exception:
                pass
            try:
                if s.asignatura_id:
                    asignaturas = self.admin_client._get(f"/asignaturas/")
                    if isinstance(asignaturas, list):
                        for a in asignaturas:
                            if a.get("id") == s.asignatura_id:
                                materia_nombre = a.get("nombre")
                                break
            except Exception:
                pass
        return {
            "id": s.id,
            "solicitud_id": s.solicitud_id,
            "docente_id": s.docente_id,
            "docente_nombre": docente_nombre,
            "asignatura_id": s.asignatura_id,
            "materia_nombre": materia_nombre,
            "tema": s.tema,
            "descripcion": s.descripcion,
            "estado": s.estado,
            "fecha_creacion": s.fecha_creacion.isoformat() if s.fecha_creacion else None,
            "fecha_agendada": fa.isoformat() if fa else None,
            "fecha_inicio": fi.isoformat() if fi else None,
            "fecha_fin": ff.isoformat() if ff else None,
            "capacidad_maxima": s.capacidad_maxima,
            "total_inscritos": s.total_inscritos,
            "inscritos_count": s.total_inscritos,
        }

    def _serializar_inscripcion(self, ins: InscripcionSesion) -> Dict[str, Any]:
        return {
            "id": ins.id,
            "sesion_id": ins.sesion_id,
            "estudiante_id": ins.estudiante_id,
            "fecha_inscripcion": ins.fecha_inscripcion.isoformat() if ins.fecha_inscripcion else None,
            "asistio": ins.asistio,
        }

    def aceptar_solicitud(
        self,
        solicitud_id: int | str,
        docente_id: int | str,
        usuario_id: str | None = None,
        capacidad_maxima: int = 20,
        fecha_agendada: str | None = None,
    ) -> Dict[str, Any]:
        """Docente acepta la solicitud → se crea una sesión grupal abierta."""
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.id == int(solicitud_id)
            ).first()
            if not solicitud:
                raise ValueError("No existe la solicitud")

            if solicitud.estado not in ("solicitada", "asignada", "sin_asignar"):
                raise ValueError(f"No se puede aceptar: estado actual '{solicitud.estado}'")

            fa = None
            if fecha_agendada:
                try:
                    fa = datetime.fromisoformat(fecha_agendada)
                except ValueError:
                    pass

            estado_anterior = solicitud.estado
            solicitud.docente_id = int(docente_id)
            solicitud.estado = "confirmada"
            solicitud.fecha_actualizacion = _now()

            sesion = SesionTutoria(
                solicitud_id=solicitud.id,
                docente_id=int(docente_id),
                asignatura_id=solicitud.asignatura_id,
                tema=solicitud.tema,
                descripcion=f"Sesión de tutoría aceptada por el docente",
                estado="abierta",
                fecha_creacion=_now(),
                fecha_agendada=fa,
                capacidad_maxima=capacidad_maxima,
                total_inscritos=0,
            )
            db.add(sesion)
            db.flush()

            solicitud.sesion_id = sesion.id

            self._crear_historial(db, solicitud.id, estado_anterior, "confirmada",
                                  usuario_id=usuario_id, rol_usuario="docente",
                                  comentario="Solicitud aceptada, sesión grupal creada")
            self._registrar_auditoria(db, usuario_id, "ACEPTAR_SOLICITUD",
                                      f"Solicitud {solicitud_id} aceptada, sesión {sesion.id} creada")
            self._crear_notificacion(db, solicitud.id, solicitud.estudiante_id, "estudiante",
                                     "solicitud_aceptada",
                                     f"Tu solicitud #{solicitud_id} fue aceptada. Sesión #{sesion.id} abierta.")

            db.commit()
            db.refresh(sesion)
            return self._serializar_sesion(sesion)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def rechazar_solicitud(
        self,
        solicitud_id: int | str,
        docente_id: int | str,
        motivo: str = "",
        usuario_id: str | None = None,
    ) -> Dict[str, Any]:
        """Docente rechaza la solicitud → vuelve a 'sin_asignar'."""
        db = self._get_db()
        try:
            solicitud = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.id == int(solicitud_id)
            ).first()
            if not solicitud:
                raise ValueError("No existe la solicitud")

            estado_anterior = solicitud.estado
            solicitud.docente_id = None
            solicitud.estado = "sin_asignar"
            solicitud.motivo_rechazo = motivo
            solicitud.fecha_actualizacion = _now()

            self._crear_historial(db, solicitud.id, estado_anterior, "sin_asignar",
                                  usuario_id=usuario_id, rol_usuario="docente",
                                  comentario=f"Rechazada: {motivo}")
            self._registrar_auditoria(db, usuario_id, "RECHAZAR_SOLICITUD",
                                      f"Solicitud {solicitud_id} rechazada: {motivo}")
            self._crear_notificacion(db, solicitud.id, solicitud.estudiante_id, "estudiante",
                                     "solicitud_rechazada",
                                     f"Tu solicitud #{solicitud_id} fue rechazada. Motivo: {motivo}")

            db.commit()
            db.refresh(solicitud)
            return self._serializar_solicitud(solicitud)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def inscribir_en_sesion(
        self,
        sesion_id: int | str,
        estudiante_id: int | str,
    ) -> Dict[str, Any]:
        """Estudiante se inscribe en una sesión grupal abierta."""
        db = self._get_db()
        try:
            sesion = db.query(SesionTutoria).filter(
                SesionTutoria.id == int(sesion_id)
            ).first()
            if not sesion:
                raise ValueError("No existe la sesión")

            if sesion.estado != "abierta":
                raise ValueError(f"La sesión no está abierta (estado: {sesion.estado})")

            existente = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == int(sesion_id),
                InscripcionSesion.estudiante_id == int(estudiante_id),
            ).first()
            if existente:
                raise ValueError("Ya estás inscrito en esta sesión")

            if sesion.total_inscritos >= sesion.capacidad_maxima:
                raise ValueError("La sesión está llena")

            inscripcion = InscripcionSesion(
                sesion_id=int(sesion_id),
                estudiante_id=int(estudiante_id),
                fecha_inscripcion=_now(),
            )
            db.add(inscripcion)
            sesion.total_inscritos += 1

            self._registrar_auditoria(db, str(estudiante_id), "INSCRIBIR_SESION",
                                      f"Estudiante {estudiante_id} inscrito en sesión {sesion_id}")

            db.commit()
            db.refresh(inscripcion)
            return self._serializar_inscripcion(inscripcion)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def iniciar_sesion(
        self,
        sesion_id: int | str,
        usuario_id: str | None = None,
    ) -> Dict[str, Any]:
        """Docente inicia la sesión grupal."""
        db = self._get_db()
        try:
            sesion = db.query(SesionTutoria).filter(
                SesionTutoria.id == int(sesion_id)
            ).first()
            if not sesion:
                raise ValueError("No existe la sesión")

            if sesion.estado != "abierta":
                raise ValueError(f"No se puede iniciar: estado actual '{sesion.estado}'")

            sesion.estado = "en_curso"
            sesion.fecha_inicio = _now()

            self._registrar_auditoria(db, usuario_id, "INICIAR_SESION",
                                      f"Sesión {sesion_id} iniciada")

            db.commit()
            db.refresh(sesion)
            return self._serializar_sesion(sesion)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def finalizar_sesion(
        self,
        sesion_id: int | str,
        usuario_id: str | None = None,
        detalle: str | None = None,
    ) -> Dict[str, Any]:
        """Docente finaliza la sesión grupal y registra bitácora."""
        db = self._get_db()
        try:
            sesion = db.query(SesionTutoria).filter(
                SesionTutoria.id == int(sesion_id)
            ).first()
            if not sesion:
                raise ValueError("No existe la sesión")

            if sesion.estado != "en_curso":
                raise ValueError(f"No se puede finalizar: estado actual '{sesion.estado}'")

            sesion.estado = "atendida"
            sesion.fecha_fin = _now()

            solicitud = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.id == sesion.solicitud_id
            ).first()
            if solicitud:
                solicitud.estado = "atendida"
                solicitud.fecha_actualizacion = _now()

            if detalle:
                bitacora = BitacoraAtencion(
                    solicitud_id=sesion.solicitud_id,
                    observaciones=detalle,
                    fecha_registro=_now(),
                )
                db.add(bitacora)

            if solicitud and solicitud.estudiante_id:
                self._crear_notificacion(db, sesion.solicitud_id, solicitud.estudiante_id, "estudiante",
                                         "bitacora", f"La sesión de tutoría #{sesion.id} ha finalizado. Revisa la bitácora registrada.")
            inscripciones = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == sesion.id,
                InscripcionSesion.estudiante_id != (solicitud.estudiante_id if solicitud else None),
            ).all()
            for ins in inscripciones:
                self._crear_notificacion(db, sesion.solicitud_id, ins.estudiante_id, "estudiante",
                                         "bitacora", f"La sesión de tutoría grupal #{sesion.id} en la que participaste ha finalizado. Revisa la bitácora.")

            self._registrar_auditoria(db, usuario_id, "FINALIZAR_SESION",
                                      f"Sesión {sesion_id} finalizada")

            db.commit()
            db.refresh(sesion)
            return self._serializar_sesion(sesion)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def listar_sesiones_abiertas(
        self,
        asignatura_id: int | str | None = None,
        materia_nombre: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Lista sesiones abiertas para que estudiantes se inscriban."""
        db = self._get_db()
        try:
            query = db.query(SesionTutoria).filter(SesionTutoria.estado == "abierta")
            if asignatura_id:
                query = query.filter(SesionTutoria.asignatura_id == int(asignatura_id))
            elif materia_nombre and self.admin_client:
                try:
                    all_asig = self.admin_client.listar_asignaturas()
                    if isinstance(all_asig, list):
                        ids = [a.get("id") for a in all_asig if materia_nombre.lower() in (a.get("nombre") or "").lower()]
                        if ids:
                            query = query.filter(SesionTutoria.asignatura_id.in_(ids))
                except Exception:
                    pass
            sesiones = query.all()
            cache = self._build_caches([], sesiones)
            return [self._serializar_sesion(s, cache) for s in sesiones]
        finally:
            db.close()

    def listar_sesiones_docente(
        self,
        docente_id: int | str,
    ) -> List[Dict[str, Any]]:
        """Lista todas las sesiones de un docente."""
        db = self._get_db()
        try:
            sesiones = db.query(SesionTutoria).filter(
                SesionTutoria.docente_id == int(docente_id)
            ).all()
            cache = self._build_caches([], sesiones)
            return [self._serializar_sesion(s, cache) for s in sesiones]
        finally:
            db.close()

    def listar_inscritos_sesion(
        self,
        sesion_id: int | str,
    ) -> List[Dict[str, Any]]:
        """Lista los estudiantes inscritos en una sesión."""
        db = self._get_db()
        try:
            inscripciones = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == int(sesion_id)
            ).all()
            resultado = []
            # Batch fetch student names
            est_names: Dict[int, str] = {}
            if self.admin_client:
                for i in inscripciones:
                    try:
                        est = self.admin_client.obtener_estudiante(i.estudiante_id)
                        if est:
                            est_names[i.estudiante_id] = f"{est.get('nombres', '')} {est.get('apellidos', '')}".strip()
                    except Exception:
                        pass
            for i in inscripciones:
                item = self._serializar_inscripcion(i)
                if i.estudiante_id in est_names:
                    item["estudiante_nombre"] = est_names[i.estudiante_id]
                resultado.append(item)
            return resultado
        finally:
            db.close()

    def esta_inscrito_en_sesion(self, sesion_id: int | str, estudiante_id: int | str) -> bool:
        """Verifica si un estudiante está inscrito en una sesión."""
        db = self._get_db()
        try:
            inscripcion = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == int(sesion_id),
                InscripcionSesion.estudiante_id == int(estudiante_id),
            ).first()
            return inscripcion is not None
        finally:
            db.close()

    def listar_inscripciones_estudiante(
        self,
        estudiante_id: int | str,
    ) -> List[Dict[str, Any]]:
        """Lista todas las inscripciones de un estudiante."""
        db = self._get_db()
        try:
            inscripciones = db.query(InscripcionSesion).filter(
                InscripcionSesion.estudiante_id == int(estudiante_id)
            ).all()
            return [self._serializar_inscripcion(i) for i in inscripciones]
        finally:
            db.close()

    def listar_solicitudes_pendientes_docente(
        self,
        docente_id: int | str,
    ) -> List[Dict[str, Any]]:
        """Solicitudes asignadas al docente que están pendientes de aceptar."""
        db = self._get_db()
        try:
            solicitudes = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.docente_id == int(docente_id),
                SolicitudTutoria.estado.in_(["solicitada", "asignada"]),
            ).all()
            cache = self._build_caches(solicitudes)
            return [self._serializar_solicitud(s, cache) for s in solicitudes]
        finally:
            db.close()

    # ── Admin: crear tutoría por nombre ──────────────────────────

    def crear_sesion_admin(
        self,
        docente_id: int | str,
        estudiante_id: int | str | None = None,
        asignatura_id: int | str | None = None,
        tema: str = "",
        descripcion: str | None = None,
        capacidad_maxima: int = 20,
        fecha_agendada: str | None = None,
        usuario_id: str | None = None,
    ) -> Dict[str, Any]:
        """Admin crea directamente una sesión de tutoría grupal."""
        db = self._get_db()
        try:
            solicitud = SolicitudTutoria(
                estudiante_id=int(estudiante_id) if estudiante_id else 0,
                docente_id=int(docente_id),
                asignatura_id=int(asignatura_id) if asignatura_id else None,
                periodo_id=None,
                tema=tema,
                estado="confirmada",
                fecha_solicitud=_now(),
                fecha_actualizacion=_now(),
            )
            db.add(solicitud)
            db.flush()

            fa = None
            if fecha_agendada:
                try:
                    fa = datetime.fromisoformat(fecha_agendada)
                except ValueError:
                    pass

            sesion = SesionTutoria(
                solicitud_id=solicitud.id,
                docente_id=int(docente_id),
                asignatura_id=int(asignatura_id) if asignatura_id else None,
                tema=tema,
                descripcion=descripcion or f"Sesión creada por administrador",
                estado="abierta",
                fecha_creacion=_now(),
                fecha_agendada=fa,
                capacidad_maxima=capacidad_maxima,
                total_inscritos=0,
            )
            db.add(sesion)
            db.flush()

            solicitud.sesion_id = sesion.id

            self._crear_historial(db, solicitud.id, None, "confirmada",
                                  usuario_id=usuario_id, rol_usuario="admin",
                                  comentario="Sesión creada por administrador")
            self._registrar_auditoria(db, usuario_id, "CREAR_SESION_ADMIN",
                                      f"Sesión #{sesion.id} creada por admin: {tema}")

            db.commit()
            db.refresh(sesion)
            return self._serializar_sesion(sesion)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── Docente: bitácora y asistencia de sesión ─────────────────

    def registrar_bitacora_sesion(
        self,
        sesion_id: int | str,
        detalle: str,
        temas_detectados: str | None = None,
        usuario_id: str | None = None,
    ) -> Dict[str, Any]:
        """Docente registra una bitácora para una sesión."""
        db = self._get_db()
        try:
            sesion = db.query(SesionTutoria).filter(
                SesionTutoria.id == int(sesion_id)
            ).first()
            if not sesion:
                raise ValueError("No existe la sesión")

            bitacora = BitacoraAtencion(
                solicitud_id=sesion.solicitud_id,
                observaciones=detalle,
                temas_detectados=temas_detectados,
                fecha_registro=_now(),
            )
            db.add(bitacora)

            # Notificar al estudiante de la solicitud original
            solicitud = db.query(SolicitudTutoria).filter(
                SolicitudTutoria.id == sesion.solicitud_id
            ).first()
            if solicitud and solicitud.estudiante_id:
                self._crear_notificacion(db, sesion.solicitud_id, solicitud.estudiante_id, "estudiante",
                                         "bitacora", f"Se ha registrado una bitácora para la sesión #{sesion.id}.")
            # Notificar a los estudiantes inscritos en la sesión grupal
            inscripciones = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == sesion.id,
                InscripcionSesion.estudiante_id != (solicitud.estudiante_id if solicitud else None),
            ).all()
            for ins in inscripciones:
                self._crear_notificacion(db, sesion.solicitud_id, ins.estudiante_id, "estudiante",
                                         "bitacora", f"Se ha registrado una bitácora para la sesión grupal #{sesion.id} en la que participaste.")

            self._registrar_auditoria(db, usuario_id, "REGISTRAR_BITACORA_SESION",
                                      f"Bitácora registrada para sesión {sesion_id}")

            db.commit()
            db.refresh(bitacora)
            return {
                "id": bitacora.id,
                "sesion_id": int(sesion_id),
                "observaciones": bitacora.observaciones,
                "temas_detectados": bitacora.temas_detectados,
                "fecha_registro": bitacora.fecha_registro.isoformat() if bitacora.fecha_registro else None,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def registrar_asistencia_sesion(
        self,
        sesion_id: int | str,
        estudiante_id: int | str,
        asistio: bool,
        usuario_id: str | None = None,
    ) -> Dict[str, Any]:
        """Docente registra asistencia de un estudiante en una sesión."""
        db = self._get_db()
        try:
            inscripcion = db.query(InscripcionSesion).filter(
                InscripcionSesion.sesion_id == int(sesion_id),
                InscripcionSesion.estudiante_id == int(estudiante_id),
            ).first()
            if not inscripcion:
                raise ValueError("El estudiante no está inscrito en esta sesión")

            inscripcion.asistio = asistio

            self._registrar_auditoria(db, usuario_id, "REGISTRAR_ASISTENCIA_SESION",
                                      f"Asistencia de estudiante {estudiante_id} en sesión {sesion_id}: {'asistió' if asistio else 'no asistió'}")

            db.commit()
            return {
                "sesion_id": int(sesion_id),
                "estudiante_id": int(estudiante_id),
                "asistio": asistio,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SolicitudTutoria(Base):
    __tablename__ = "solicitudes_tutoria"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, nullable=False)
    docente_id = Column(Integer, nullable=True)
    asignatura_id = Column(Integer, nullable=True)
    periodo_id = Column(Integer, nullable=True)
    tema = Column(String(200), nullable=False)
    estado = Column(String(30), nullable=False, default="solicitada")
    fecha_solicitud = Column(DateTime, nullable=False, default=_utcnow)
    fecha_agendada = Column(DateTime, nullable=True)
    fecha_actualizacion = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
    motivo_cancelacion = Column(Text, nullable=True)
    motivo_rechazo = Column(Text, nullable=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_tutoria.id"), nullable=True)

    bitacoras = relationship("BitacoraAtencion", back_populates="solicitud", cascade="all, delete-orphan")
    historial = relationship("HistorialEstado", back_populates="solicitud", cascade="all, delete-orphan")
    notificaciones = relationship("Notificacion", back_populates="solicitud", cascade="all, delete-orphan")
    sesion = relationship("SesionTutoria", foreign_keys="[SolicitudTutoria.sesion_id]", viewonly=True)


class SesionTutoria(Base):
    __tablename__ = "sesiones_tutoria"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_tutoria.id"), nullable=False)
    docente_id = Column(Integer, nullable=False)
    asignatura_id = Column(Integer, nullable=True)
    tema = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(30), nullable=False, default="confirmada")
    fecha_creacion = Column(DateTime, nullable=False, default=_utcnow)
    fecha_agendada = Column(DateTime, nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    capacidad_maxima = Column(Integer, nullable=False, default=20)
    total_inscritos = Column(Integer, nullable=False, default=0)

    solicitud = relationship("SolicitudTutoria", foreign_keys="[SesionTutoria.solicitud_id]", viewonly=True)
    inscripciones = relationship("InscripcionSesion", back_populates="sesion", cascade="all, delete-orphan")


class InscripcionSesion(Base):
    __tablename__ = "inscripciones_sesion"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_tutoria.id"), nullable=False)
    estudiante_id = Column(Integer, nullable=False)
    fecha_inscripcion = Column(DateTime, nullable=False, default=_utcnow)
    asistio = Column(Boolean, nullable=True)
    observaciones = Column(Text, nullable=True)

    sesion = relationship("SesionTutoria", back_populates="inscripciones")


class BitacoraAtencion(Base):
    __tablename__ = "bitacoras_atencion"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_tutoria.id"), nullable=False)
    observaciones = Column(Text, nullable=True)
    asistio = Column(Boolean, nullable=True)
    temas_detectados = Column(Text, nullable=True)
    fecha_registro = Column(DateTime, nullable=False, default=_utcnow)

    solicitud = relationship("SolicitudTutoria", back_populates="bitacoras")


class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_tutoria.id"), nullable=False)
    estado_anterior = Column(String(30), nullable=True)
    estado_nuevo = Column(String(30), nullable=False)
    usuario_id = Column(String(50), nullable=True)
    rol_usuario = Column(String(30), nullable=True)
    fecha_cambio = Column(DateTime, nullable=False, default=_utcnow)
    comentario = Column(Text, nullable=True)

    solicitud = relationship("SolicitudTutoria", back_populates="historial")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes_tutoria.id"), nullable=True)
    destinatario_id = Column(Integer, nullable=False)
    destinatario_rol = Column(String(30), nullable=False)
    tipo = Column(String(50), nullable=False)
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, nullable=False, default=_utcnow)
    fecha_lectura = Column(DateTime, nullable=True)

    solicitud = relationship("SolicitudTutoria", back_populates="notificaciones")


class AuditoriaTutoria(Base):
    __tablename__ = "auditoria_tutorias"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(50), nullable=True)
    accion = Column(String(100), nullable=False)
    modulo = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha = Column(DateTime, nullable=False, default=_utcnow)


class CasoAcademicoDB(Base):
    __tablename__ = "casos_academicos"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, nullable=False)
    descripcion = Column(Text, nullable=False)
    severidad = Column(String(30), nullable=False, default="media")
    estado = Column(String(30), nullable=False, default="abierto")
    fecha_creacion = Column(DateTime, nullable=False, default=_utcnow)

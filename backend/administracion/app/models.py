from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Facultad(Base):
    __tablename__ = "facultades"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(255))
    estado = Column(Boolean, default=True)

    carreras = relationship("Carrera", back_populates="facultad")


class Carrera(Base):
    __tablename__ = "carreras"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    codigo = Column(String(20))
    facultad_id = Column(Integer, ForeignKey("facultades.id"), nullable=False)
    estado = Column(Boolean, default=True)

    facultad = relationship("Facultad", back_populates="carreras")
    asignaturas = relationship("Asignatura", back_populates="carrera")
    estudiantes = relationship("Estudiante", back_populates="carrera")
    paralelos = relationship("Paralelo", back_populates="carrera")


class Asignatura(Base):
    __tablename__ = "asignaturas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    codigo = Column(String(20))
    creditos = Column(Integer, nullable=False)
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False)
    estado = Column(Boolean, default=True)

    carrera = relationship("Carrera", back_populates="asignaturas")
    paralelos = relationship("Paralelo", back_populates="asignatura")


class PeriodoAcademico(Base):
    __tablename__ = "periodos_academicos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    fecha_inicio = Column(String(20), nullable=False)
    fecha_fin = Column(String(20), nullable=False)
    estado = Column(Boolean, default=True)

    paralelos = relationship("Paralelo", back_populates="periodo")


class Docente(Base):
    __tablename__ = "docentes"

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False)
    telefono = Column(String(20))
    especialidad = Column(String(120))
    estado = Column(Boolean, default=True)

    paralelos = relationship("Paralelo", back_populates="docente")


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False)
    matricula = Column(String(30))
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False)
    estado = Column(Boolean, default=True)

    carrera = relationship("Carrera", back_populates="estudiantes")


class Paralelo(Base):
    __tablename__ = "paralelos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=False)
    periodo_id = Column(Integer, ForeignKey("periodos_academicos.id"), nullable=False)
    estado = Column(Boolean, default=True)

    carrera = relationship("Carrera", back_populates="paralelos")
    asignatura = relationship("Asignatura", back_populates="paralelos")
    docente = relationship("Docente", back_populates="paralelos")
    periodo = relationship("PeriodoAcademico", back_populates="paralelos")
    horarios = relationship("HorarioAtencion", back_populates="paralelo")


class HorarioAtencion(Base):
    __tablename__ = "horarios_atencion"

    id = Column(Integer, primary_key=True, index=True)
    dia = Column(String(20), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    paralelo_id = Column(Integer, ForeignKey("paralelos.id"), nullable=False)
    estado = Column(Boolean, default=True)

    paralelo = relationship("Paralelo", back_populates="horarios")


class AuditoriaAdministracion(Base):
    __tablename__ = "auditoria_administracion"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String(50))
    accion = Column(String(100), nullable=False)
    modulo = Column(String(50), nullable=False)
    descripcion = Column(Text)
    fecha = Column(DateTime, default=datetime.utcnow)
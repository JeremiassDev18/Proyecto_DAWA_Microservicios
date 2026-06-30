from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Restaurante(Base):
    __tablename__ = "restaurantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    estado = Column(Boolean, default=True)

    sucursales = relationship("Sucursal", back_populates="restaurante")


class Sucursal(Base):
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20))
    restaurante_id = Column(Integer, ForeignKey("restaurantes.id"), nullable=False)
    estado = Column(Boolean, default=True)

    restaurante = relationship("Restaurante", back_populates="sucursales")
    mesas = relationship("Mesa", back_populates="sucursal")
    horarios = relationship("HorarioAtencion", back_populates="sucursal")
    promociones = relationship("Promocion", back_populates="sucursal")


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False)
    capacidad = Column(Integer, nullable=False)
    ubicacion = Column(String(50))
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    estado = Column(Boolean, default=True)

    sucursal = relationship("Sucursal", back_populates="mesas")


class HorarioAtencion(Base):
    __tablename__ = "horarios_atencion"

    id = Column(Integer, primary_key=True, index=True)
    dia = Column(String(20), nullable=False)
    hora_apertura = Column(Time, nullable=False)
    hora_cierre = Column(Time, nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    estado = Column(Boolean, default=True)

    sucursal = relationship("Sucursal", back_populates="horarios")


class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    descuento = Column(Numeric(5, 2), nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id"), nullable=False)
    estado = Column(Boolean, default=True)

    sucursal = relationship("Sucursal", back_populates="promociones")
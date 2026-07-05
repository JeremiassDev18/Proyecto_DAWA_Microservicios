from __future__ import annotations

from typing import Dict, List, Optional
from uuid import uuid4

from .models import CasoAcademico, Docente, Notificacion, Tutoria


class TutoriasService:
    def __init__(self) -> None:
        self.docentes: Dict[str, Docente] = {}
        self.tutorias: Dict[str, Tutoria] = {}
        self.casos_academicos: Dict[str, CasoAcademico] = {}
        self.notificaciones: Dict[str, Notificacion] = {}

    def registrar_docente(self, docente_id: str, nombre: str, disponibilidades: Optional[List[str]] = None) -> Dict[str, object]:
        docente = Docente(id=docente_id, nombre=nombre, disponibilidades=disponibilidades or [])
        self.docentes[docente_id] = docente
        return {"id": docente.id, "nombre": docente.nombre, "disponibilidades": docente.disponibilidades}

    def registrar_solicitud_tutoria(
        self,
        estudiante_id: str,
        carrera: str,
        tema: str,
        fecha_solicitud: str,
        hora_solicitud: str,
    ) -> Dict[str, object]:
        tutoria = Tutoria(
            id=str(uuid4())[:8],
            estudiante_id=estudiante_id,
            carrera=carrera,
            tema=tema,
            fecha_solicitud=fecha_solicitud,
            hora_solicitud=hora_solicitud,
        )
        self.tutorias[tutoria.id] = tutoria
        return self._serializar_tutoria(tutoria)

    def validar_disponibilidad_docente(self, docente_id: str, fecha: str) -> bool:
        docente = self.docentes.get(docente_id)
        if not docente:
            return False
        return fecha in docente.disponibilidades

    def asignar_tutoria(self, tutoria_id: str, docente_id: str) -> Dict[str, object]:
        tutoria = self.tutorias.get(tutoria_id)
        if not tutoria:
            raise ValueError("No existe la tutoría")
        if not self.validar_disponibilidad_docente(docente_id, tutoria.fecha_solicitud):
            return {"asignada": False, "docente_id": docente_id, "motivo": "Docente sin disponibilidad"}

        tutoria.docente_id = docente_id
        tutoria.estado = "asignada"
        return {"asignada": True, "docente_id": docente_id, "estado": tutoria.estado}

    def confirmar_o_cancelar_tutoria(self, tutoria_id: str, accion: str, motivo: Optional[str] = None) -> Dict[str, object]:
        tutoria = self.tutorias.get(tutoria_id)
        if not tutoria:
            raise ValueError("No existe la tutoría")
        if accion == "confirmar":
            tutoria.estado = "confirmada"
        elif accion == "cancelar":
            tutoria.estado = "cancelada"
            if motivo:
                tutoria.observaciones.append(motivo)
        else:
            raise ValueError("Acción no soportada")
        return self._serializar_tutoria(tutoria)

    def registrar_asistencia_estudiante(self, tutoria_id: str, asistio: bool) -> Dict[str, object]:
        tutoria = self.tutorias.get(tutoria_id)
        if not tutoria:
            raise ValueError("No existe la tutoría")
        tutoria.asistencia = asistio
        return {"tutoria_id": tutoria.id, "asistio": asistio, "estado": tutoria.estado}

    def registrar_bitacora_atencion(self, tutoria_id: str, detalle: str) -> Dict[str, object]:
        tutoria = self.tutorias.get(tutoria_id)
        if not tutoria:
            raise ValueError("No existe la tutoría")
        tutoria.bitacora.append(detalle)
        return {"tutoria_id": tutoria.id, "bitacora": tutoria.bitacora}

    def gestionar_estado_tutoria(self, tutoria_id: str, estado: str) -> Dict[str, object]:
        tutoria = self.tutorias.get(tutoria_id)
        if not tutoria:
            raise ValueError("No existe la tutoría")
        tutoria.estado = estado
        return self._serializar_tutoria(tutoria)

    def registrar_seguimiento_caso_academico(self, estudiante_id: str, descripcion: str, severidad: str) -> Dict[str, object]:
        caso = CasoAcademico(id=str(uuid4())[:8], estudiante_id=estudiante_id, descripcion=descripcion, severidad=severidad)
        self.casos_academicos[caso.id] = caso
        return {"id": caso.id, "estudiante_id": caso.estudiante_id, "estado": caso.estado, "severidad": caso.severidad}

    def generar_reporte_tutorias_por_docente(self, docente_id: str) -> Dict[str, object]:
        tutorias = [self._serializar_tutoria(t) for t in self.tutorias.values() if t.docente_id == docente_id]
        return {"docente_id": docente_id, "cantidad": len(tutorias), "tutorias": tutorias}

    def generar_reporte_estudiantes_atendidos(self) -> Dict[str, object]:
        estudiantes = {t.estudiante_id for t in self.tutorias.values() if t.asistencia is True}
        return {"cantidad": len(estudiantes), "estudiantes": sorted(estudiantes)}

    def generar_reporte_temas_recurrentes(self) -> Dict[str, object]:
        contador: Dict[str, int] = {}
        for tutoria in self.tutorias.values():
            contador[tutoria.tema] = contador.get(tutoria.tema, 0) + 1

        temas = [tema for tema, _ in sorted(contador.items())]
        detalle = [{"tema": tema, "cantidad": contador[tema]} for tema in temas]
        return {"temas": temas, "detalle": detalle}

    def notificar_cambio_estado(self, tutoria_id: str, estado: str) -> Dict[str, object]:
        notificacion = Notificacion(id=str(uuid4())[:8], tutoria_id=tutoria_id, mensaje=f"Cambio de estado: {estado}")
        self.notificaciones[notificacion.id] = notificacion
        return {"id": notificacion.id, "tutoria_id": notificacion.tutoria_id, "mensaje": notificacion.mensaje}

    def obtener_tutoria(self, tutoria_id: str) -> Dict[str, object]:
        return self._serializar_tutoria(self.tutorias[tutoria_id])

    def _serializar_tutoria(self, tutoria: Tutoria) -> Dict[str, object]:
        return {
            "id": tutoria.id,
            "estudiante_id": tutoria.estudiante_id,
            "carrera": tutoria.carrera,
            "tema": tutoria.tema,
            "fecha_solicitud": tutoria.fecha_solicitud,
            "hora_solicitud": tutoria.hora_solicitud,
            "estado": tutoria.estado,
            "docente_id": tutoria.docente_id,
            "asistencia": tutoria.asistencia,
            "bitacora": tutoria.bitacora,
            "observaciones": tutoria.observaciones,
        }

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

DIAS_SPANISH = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo"
}


class AdministracionClient:
    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            base_url = os.getenv(
                "ADMINISTRACION_URL",
                "http://administration-service:5002/api/administracion"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = 10

    def _get(self, path: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}{path}",
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    def validar_estudiante(self, estudiante_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/internos/validar-estudiante/{estudiante_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {"valido": False, "mensaje": "Estudiante no encontrado o inactivo"}
            logger.error(f"Error HTTP validando estudiante {estudiante_id}: {e}")
            return {"valido": False, "mensaje": f"Error del servicio: {e}"}
        except requests.RequestException as e:
            logger.error(f"Error de conexión validando estudiante {estudiante_id}: {e}")
            return {"valido": False, "mensaje": "No se pudo conectar con Administracionfix"}

    def obtener_docente(self, docente_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/docentes/{docente_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {}
            logger.error(f"Error HTTP obteniendo docente {docente_id}: {e}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Error de conexión obteniendo docente {docente_id}: {e}")
            return {}

    def obtener_disponibilidad_docente(self, docente_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/internos/disponibilidad-docente/{docente_id}")
        except requests.HTTPError as e:
            mensaje = ""
            if e.response is not None:
                try:
                    mensaje = e.response.json().get("mensaje", "")
                except Exception:
                    mensaje = str(e.response.status_code)
            logger.error(f"Error HTTP obteniendo disponibilidad docente {docente_id}: {mensaje}")
            return {"docente_id": docente_id, "horarios_disponibles": []}
        except requests.RequestException as e:
            logger.error(f"Error de conexión obteniendo disponibilidad docente {docente_id}: {e}")
            return {"docente_id": docente_id, "horarios_disponibles": []}

    def validar_disponibilidad_en_fecha(self, docente_id: int | str, fecha: str) -> bool:
        disponibilidad = self.obtener_disponibilidad_docente(docente_id)
        horarios = disponibilidad.get("horarios_disponibles", [])
        if not horarios:
            return False
        try:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            dia = DIAS_SPANISH[dt.weekday()]
        except (ValueError, KeyError):
            logger.warning(f"Fecha inválida: {fecha}")
            return False
        for h in horarios:
            if h.get("dia", "").strip().lower() == dia:
                return True
        return False

    def validar_asignatura(self, asignatura_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/internos/validar-asignatura/{asignatura_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {"valida": False, "mensaje": "Asignatura no encontrada o inactiva"}
            logger.error(f"Error HTTP validando asignatura {asignatura_id}: {e}")
            return {"valida": False, "mensaje": f"Error del servicio: {e}"}
        except requests.RequestException as e:
            logger.error(f"Error de conexión validando asignatura {asignatura_id}: {e}")
            return {"valida": False, "mensaje": "No se pudo conectar con Administracionfix"}

    def obtener_carrera(self, carrera_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/carreras/{carrera_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {}
            logger.error(f"Error HTTP obteniendo carrera {carrera_id}: {e}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Error de conexión obteniendo carrera {carrera_id}: {e}")
            return {}

    def validar_docente_existe(self, docente_id: int | str) -> Dict[str, Any]:
        try:
            docente = self._get(f"/docentes/{docente_id}")
            return {"valido": True, "docente": docente}
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {"valido": False, "mensaje": "Docente no encontrado o inactivo"}
            logger.error(f"Error HTTP validando docente {docente_id}: {e}")
            return {"valido": False, "mensaje": f"Error del servicio: {e}"}
        except requests.RequestException as e:
            logger.error(f"Error de conexión validando docente {docente_id}: {e}")
            return {"valido": False, "mensaje": "No se pudo conectar con Administracionfix"}

    def obtener_periodo(self, periodo_id: int | str) -> Dict[str, Any]:
        try:
            return self._get(f"/periodos/{periodo_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return {}
            logger.error(f"Error HTTP obteniendo periodo {periodo_id}: {e}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Error de conexión obteniendo periodo {periodo_id}: {e}")
            return {}

    def validar_periodo_activo(self, periodo_id: int | str) -> Dict[str, Any]:
        periodo = self.obtener_periodo(periodo_id)
        if not periodo:
            return {"valido": False, "mensaje": "Periodo académico no encontrado"}
        if periodo.get("estado_periodo") != "activo":
            return {"valido": False, "mensaje": "El periodo académico no está activo"}
        return {"valido": True, "periodo_id": periodo.get("id"), "nombre": periodo.get("nombre")}

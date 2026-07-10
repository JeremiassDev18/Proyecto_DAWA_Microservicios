"""
Adaptador de tutorías para el agente LLM.

Reutiliza TutoriasClient (RabbitMQ) para crear, cancelar y consultar tutorías.
Formatea la respuesta técnica como texto comprensible para el LLM.
"""

from app.services.microservice_client import get_tutorias_client, get_tutorias_rest_client
from app.utils.logger import logger


def _format_bitacora_resumen(row: tuple) -> str:
    """Formatea una fila de bitacora_resumen como texto legible."""
    solicitud_id = row[1]
    resumen = row[4]
    temas = row[5]
    fecha = row[6]
    partes = [f"Tutoría #{solicitud_id}: {resumen}"]
    if temas:
        partes.append(f"Temas: {temas}")
    if fecha:
        partes.append(f"Fecha: {fecha}")
    return " | ".join(partes)


class TutoriasAdapter:
    """Adaptador de operaciones de tutorías."""

    def __init__(self):
        self.tutorias = get_tutorias_client()

    def crear_tutoria(
        self,
        estudiante_id: int,
        asignatura_id: int,
        tema: str,
        periodo_id: int | None = None,
    ) -> tuple[str, dict]:
        """Crea una tutoría y devuelve el resultado como texto."""
        logger.info(
            f"[TutoriasAdapter] crear_tutoria estudiante_id={estudiante_id} "
            f"asignatura_id={asignatura_id} tema={tema}"
        )

        resultado = self.tutorias.registrar_solicitud(
            estudiante_id=estudiante_id,
            asignatura_id=asignatura_id,
            periodo_id=periodo_id,
            tema=tema,
        )

        if not resultado:
            return (
                "No se pudo registrar la tutoría en este momento. "
                "Verifica que los servicios de tutorías y RabbitMQ estén disponibles.",
                {},
            )

        content = (
            f"Tutoría registrada correctamente.\n"
            f"- ID: {resultado.get('id', 'N/A')}\n"
            f"- Tema: {resultado.get('tema', tema)}\n"
            f"- Estado: {resultado.get('estado', 'solicitada')}"
        )

        state_updates = {
            "ultima_tutoria": resultado.get("id"),
            "ultima_accion": "crear_tutoria",
            "materia_actual": tema,
        }

        return content, state_updates

    def cancelar_tutoria(
        self,
        tutoria_id: int,
        motivo: str,
        usuario_id: int,
    ) -> tuple[str, dict]:
        """Cancela una tutoría existente."""
        logger.info(f"[TutoriasAdapter] cancelar_tutoria tutoria_id={tutoria_id}")

        resultado = self.tutorias.cancelar_tutoria(
            tutoria_id=tutoria_id,
            motivo=motivo,
            usuario_id=usuario_id,
            rol_usuario="estudiante",
        )

        if not resultado:
            return (
                "No se pudo cancelar la tutoría. Verifica que el ID sea correcto "
                "y que la tutoría esté en un estado que permita cancelación.",
                {},
            )

        content = (
            f"Tutoría {tutoria_id} cancelada correctamente.\n"
            f"- Nuevo estado: {resultado.get('estado', 'cancelada')}\n"
            f"- Motivo: {motivo}"
        )

        state_updates = {
            "ultima_tutoria": tutoria_id,
            "ultima_accion": "cancelar_tutoria",
        }

        return content, state_updates

    def consultar_mis_tutorias(self, estudiante_id: int, periodo_id: int | None = None) -> tuple[str, dict]:
        """Lista las tutorías del estudiante."""
        logger.info(f"[TutoriasAdapter] consultar_mis_tutorias estudiante_id={estudiante_id}")

        tutorias = self.tutorias.consultar_mis_tutorias(estudiante_id, periodo_id)
        if not tutorias:
            return "No tienes tutorías registradas en este periodo.", {"ultima_accion": "consultar_tutorias"}

        lineas = ["Tus tutorías:"]
        for i, t in enumerate(tutorias, start=1):
            lineas.append(
                f"{i}. Tutoría #{t.get('id', 'N/A')} - "
                f"{t.get('tema', 'Sin tema')} - "
                f"Estado: {t.get('estado', 'desconocido')}"
            )

        state_updates = {
            "ultima_accion": "consultar_tutorias",
        }
        if tutorias:
            state_updates["ultima_tutoria"] = tutorias[-1].get("id")

        return "\n".join(lineas), state_updates

    def consultar_bitacoras_resumidas(
        self,
        estudiante_id: int,
        rol: str = "estudiante",
        periodo_id: int | None = None,
        solicitud_id: int | None = None,
        busqueda: str | None = None,
        db_conn=None,
    ) -> tuple[str, dict]:
        """
        Devuelve bitácoras del estudiante.
        - Si el rol es 'estudiante': resumen amigable, preferiblemente el
          precalculado por el worker RabbitMQ (Gap 5).
        - Si el rol es 'docente' o 'admin': detalle completo.
        - Si se provee solicitud_id, filtra por esa tutoría específica.
        - Si se provee busqueda, filtra por materia/tema que contenga el texto.
        """
        logger.info(f"[TutoriasAdapter] consultar_bitacoras estudiante={estudiante_id} rol={rol} solicitud_id={solicitud_id} busqueda={busqueda}")

        # Si hay solicitud_id específico, buscar por esa tutoría vía REST directo.
        if solicitud_id is not None:
            rest = get_tutorias_rest_client()
            bitacoras = rest.consultar_bitacoras_por_solicitud(solicitud_id)
            if not bitacoras:
                return f"No se encontraron bitácoras para la tutoría #{solicitud_id}.", {"ultima_accion": "consultar_bitacoras", "ultima_tutoria": solicitud_id}
            lineas = [f"Bitácora de la tutoría #{solicitud_id}:"]
            for b in bitacoras:
                obs = b.get("observaciones") or "Sesión registrada."
                temas = b.get("temas_detectados") or ""
                fecha = b.get("fecha_registro") or "N/A"
                partes = [f"Observaciones: {obs}"]
                if temas:
                    partes.append(f"Temas: {temas}")
                lineas.append(" | ".join(partes))
            return "\n".join(lineas), {"ultima_accion": "consultar_bitacoras", "ultima_tutoria": solicitud_id}

        # Para estudiantes, intentar usar resúmenes precalculados primero.
        if rol == "estudiante" and db_conn is not None:
            from app.db import queries
            try:
                resumenes = queries.get_bitacora_resumenes_by_estudiante(db_conn, estudiante_id)
                if resumenes:
                    lineas = ["Resumen de tus tutorías atendidas:"]
                    for r in resumenes:
                        lineas.append(_format_bitacora_resumen(r))
                    return "\n".join(lineas), {"ultima_accion": "consultar_bitacoras", "usando_resumenes_precalculados": True}
            except Exception as e:
                logger.warning(f"[TutoriasAdapter] error leyendo resúmenes precalculados: {e}")
                try:
                    db_conn.rollback()
                except Exception:
                    pass

        rest = get_tutorias_rest_client()
        bitacoras = rest.consultar_mis_bitacoras(estudiante_id)
        if periodo_id is not None:
            bitacoras = [b for b in bitacoras if b.get("periodo_id") == periodo_id]
        if busqueda:
            busqueda_lower = busqueda.lower()
            bitacoras = [
                b for b in bitacoras
                if busqueda_lower in (b.get("tema") or "").lower()
                or busqueda_lower in (b.get("temas_detectados") or "").lower()
            ]
        if not bitacoras:
            if busqueda:
                return f"No se encontraron bitácoras para '{busqueda}'.", {"ultima_accion": "consultar_bitacoras", "ultima_busqueda": busqueda}
            return "No tienes bitácoras de tutorías registradas.", {"ultima_accion": "consultar_bitacoras"}

        lineas = ["Bitácoras de tutorías:"]
        for i, b in enumerate(bitacoras, start=1):
            tema = b.get("tema", "Sin tema")
            estado = b.get("estado", "desconocido")
            fecha = b.get("fecha_registro", "N/A")
            if rol == "estudiante":
                obs = b.get("observaciones") or ""
                # Resumir: mostrar solo primeras palabras, sin detalles técnicos/docentes.
                resumen = obs.split(".")[0].strip() if obs else "Sesión registrada."
                lineas.append(
                    f"{i}. Tutoría #{b.get('solicitud_id', 'N/A')} - {tema} "
                    f"(Estado: {estado}, Fecha: {fecha}). Resumen: {resumen}"
                )
            else:
                lineas.append(
                    f"{i}. Tutoría #{b.get('solicitud_id', 'N/A')} - {tema} "
                    f"(Estado: {estado}, Fecha: {fecha}). Observaciones: {b.get('observaciones', 'N/A')} "
                    f"Temas: {b.get('temas_detectados', 'N/A')} | Asistió: {b.get('asistio', 'N/A')}"
                )

        state_updates = {
            "ultima_accion": "consultar_bitacoras",
            "total_bitacoras": len(bitacoras),
        }
        return "\n".join(lineas), state_updates

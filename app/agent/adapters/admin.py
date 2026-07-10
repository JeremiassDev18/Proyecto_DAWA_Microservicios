"""
Adaptador de administración académica para el agente LLM.

Expone consultas de asignaturas, carreras, docentes, etc.,
formateando los resultados técnicos como texto natural.
"""

from app.services.microservice_client import get_admin_client
from app.utils.logger import logger


class AdminAdapter:
    """Adaptador de operaciones de administración académica."""

    def __init__(self):
        self.admin = get_admin_client()

    def consultar_materias(self, estudiante_id: int) -> tuple[str, dict]:
        """Lista las materias del estudiante en texto plano."""
        logger.info(f"[AdminAdapter] consultar_materias estudiante_id={estudiante_id}")

        materias = self.admin.get_materias_estudiante(estudiante_id)
        if not materias:
            return (
                f"El estudiante {estudiante_id} no tiene materias asignadas "
                "en el periodo activo.",
                {},
            )

        lineas = ["Estas son tus materias actuales:"]
        nombres_materias = []
        for m in materias:
            nombre = m.get("nombre", "Sin nombre")
            codigo = m.get("codigo", "N/A")
            creditos = m.get("creditos", "N/A")
            asignatura_id = m.get("id")
            lineas.append(f"- {nombre} (ID: {asignatura_id}, código: {codigo}, créditos: {creditos})")
            nombres_materias.append(f"{nombre} ({codigo})")

        state_updates = {
            "ultimas_materias": ", ".join(nombres_materias),
        }

        return "\n".join(lineas), state_updates

    def listar_carreras(self) -> tuple[str, dict]:
        """Devuelve el listado de carreras disponibles."""
        carreras = self.admin.get_carreras()
        if not carreras:
            return "No pude obtener el listado de carreras en este momento.", {}

        lineas = ["Carreras disponibles:"]
        for c in carreras:
            lineas.append(f"- {c.get('nombre', 'N/A')} ({c.get('codigo', 'N/A')})")
        return "\n".join(lineas), {}

    def buscar_docentes(self, consulta: str, estudiante_id: int | None = None,
                        posesivo: str = "todos", materia: str | None = None) -> tuple[str, dict]:
        """Busca docentes según contexto: del estudiante o institucional.
        Si materia != None, busca docentes que imparten esa materia."""
        logger.info(f"[AdminAdapter] buscar_docentes query={consulta} posesivo={posesivo} materia={materia}")

        docentes = []
        if materia:
            docentes = self.admin.buscar_docentes_por_materia(materia)
        elif estudiante_id is not None and posesivo == "mios":
            docentes = self.admin.get_estudiante_docentes(estudiante_id)
            if consulta:
                consulta_lower = consulta.lower()
                docentes = [
                    d for d in docentes
                    if consulta_lower in (d.get("nombres", "") + " " + d.get("apellidos", "")).lower()
                    or consulta_lower in str(d.get("materia", "")).lower()
                    or consulta_lower in str(d.get("asignatura", "")).lower()
                ]
        else:
            docentes = self.admin.buscar_docentes(consulta)

        if not docentes:
            return "No encontré docentes que coincidan con tu búsqueda.", {}

        lineas = ["Docentes encontrados:"]
        for d in docentes:
            nombre = f"{d.get('nombres', '')} {d.get('apellidos', '')}".strip()
            if not nombre:
                nombre = d.get("nombre", "Sin nombre")
            materia = d.get("materia") or d.get("asignatura") or d.get("materia_nombre", "N/A")
            lineas.append(f"- {nombre} (ID: {d.get('id', 'N/A')}, materia: {materia})")

        return "\n".join(lineas), {"docentes_encontrados": len(docentes)}

    def sugerir_docente(self, estudiante_id: int, asignatura_id: int) -> tuple[str, dict]:
        """Sugiere el mejor docente para una materia según disponibilidad."""
        logger.info(f"[AdminAdapter] sugerir_docente estudiante={estudiante_id} asignatura={asignatura_id}")

        # Obtener docentes asignados al estudiante para esa asignatura.
        docentes_estudiante = self.admin.get_estudiante_docentes(estudiante_id)
        candidatos = [
            d for d in docentes_estudiante
            if d.get("asignatura_id") == asignatura_id or d.get("materia_id") == asignatura_id
        ]

        if not candidatos:
            # Fallback: buscar docentes institucionales para esa materia.
            asignatura = self.admin.get_asignatura(asignatura_id)
            nombre_asignatura = asignatura.get("nombre", "") if asignatura else ""
            candidatos = self.admin.buscar_docentes_por_materia(nombre_asignatura)

        if not candidatos:
            return (
                "No encontré docentes disponibles para esa materia en este momento.",
                {},
            )

        # Tomar el primero con disponibilidad; si no hay datos, el primero.
        elegido = candidatos[0]
        for d in candidatos:
            docente_id = d.get("id")
            if docente_id and self.admin.disponibilidad_docente(docente_id):
                elegido = d
                break

        nombre = f"{elegido.get('nombres', '')} {elegido.get('apellidos', '')}".strip()
        if not nombre:
            nombre = elegido.get("nombre", "Sin nombre")
        asignatura = elegido.get("materia") or elegido.get("asignatura") or elegido.get("materia_nombre", "N/A")

        content = (
            f"Te sugiero contactar al docente {nombre} para la materia {asignatura}. "
            f"Puedes solicitar una tutoría usando el ID de asignatura {asignatura_id}."
        )
        return content, {
            "docente_sugerido": elegido.get("id"),
            "asignatura_id": asignatura_id,
        }

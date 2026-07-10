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
        Si materia != None, busca docentes que imparten esa materia.
        Si la búsqueda por nombre no devuelve resultados, intenta buscar por materia."""
        logger.info(f"[AdminAdapter] buscar_docentes query={consulta} posesivo={posesivo} materia={materia}")

        if not materia:
            materia = None

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
                    or any(consulta_lower in a.get("nombre", "").lower() for a in d.get("asignaturas", []))
                ]
        else:
            docentes = self.admin.buscar_docentes(consulta)
            if not docentes and consulta:
                docentes = self.admin.buscar_docentes_por_materia(consulta)

        if not docentes:
            return "No encontré docentes que coincidan con tu búsqueda.", {}

        lineas = ["Docentes encontrados:"]
        for d in docentes:
            nombre = f"{d.get('nombres', '')} {d.get('apellidos', '')}".strip()
            if not nombre:
                nombre = d.get("nombre", "Sin nombre")
            asignaturas = d.get("asignaturas", [])
            if asignaturas:
                materias_str = ", ".join(a.get("nombre", "N/A") for a in asignaturas)
            else:
                materias_str = d.get("materia") or d.get("asignatura") or "N/A"
            lineas.append(f"- {nombre} (ID: {d.get('id', 'N/A')}, materias: {materias_str})")

        return "\n".join(lineas), {"docentes_encontrados": len(docentes)}

    def sugerir_docente(self, estudiante_id: int, asignatura_id: int) -> tuple[str, dict]:
        """Sugiere el mejor docente para una materia según disponibilidad."""
        logger.info(f"[AdminAdapter] sugerir_docente estudiante={estudiante_id} asignatura={asignatura_id}")

        docentes_estudiante = self.admin.get_estudiante_docentes(estudiante_id)
        candidatos = [
            d for d in docentes_estudiante
            if any(a.get("id") == asignatura_id for a in d.get("asignaturas", []))
        ]

        if not candidatos:
            asignatura = self.admin.get_asignatura(asignatura_id)
            nombre_asignatura = asignatura.get("nombre", "") if asignatura else ""
            candidatos = self.admin.buscar_docentes_por_materia(nombre_asignatura)

        if not candidatos:
            return (
                "No encontré docentes disponibles para esa materia en este momento.",
                {},
            )

        elegido = candidatos[0]
        for d in candidatos:
            docente_id = d.get("id")
            if docente_id and self.admin.disponibilidad_docente(docente_id):
                elegido = d
                break

        nombre = f"{elegido.get('nombres', '')} {elegido.get('apellidos', '')}".strip()
        if not nombre:
            nombre = elegido.get("nombre", "Sin nombre")
        asignaturas = elegido.get("asignaturas", [])
        if asignaturas:
            materias_str = ", ".join(a.get("nombre", "N/A") for a in asignaturas)
        else:
            materias_str = elegido.get("materia") or elegido.get("asignatura") or "N/A"

        content = (
            f"Te sugiero contactar al docente {nombre} para la materia {materias_str}. "
            f"Puedes solicitar una tutoría usando el ID de asignatura {asignatura_id}."
        )
        return content, {
            "docente_sugerido": elegido.get("id"),
            "asignatura_id": asignatura_id,
        }

    def listar_docentes_admin(self, consulta: str = "") -> tuple[str, dict]:
        """Lista todos los docentes del sistema (admin)."""
        logger.info(f"[AdminAdapter] listar_docentes_admin consulta={consulta}")

        if consulta:
            docentes = self.admin.buscar_docentes(consulta)
            if not docentes:
                docentes = self.admin.buscar_docentes_por_materia(consulta)
        else:
            docentes = self.admin.buscar_docentes("")

        if not docentes:
            return "No se encontraron docentes en el sistema.", {}

        lineas = [f"Total de docentes: {len(docentes)}"]
        for d in docentes:
            nombre = f"{d.get('nombres', '')} {d.get('apellidos', '')}".strip()
            if not nombre:
                nombre = d.get("nombre", "Sin nombre")
            asignaturas = d.get("asignaturas", [])
            materias_str = ", ".join(a.get("nombre", "N/A") for a in asignaturas) if asignaturas else "N/A"
            lineas.append(f"- {nombre} (ID: {d.get('id', 'N/A')}, materias: {materias_str})")

        return "\n".join(lineas), {"total_docentes": len(docentes)}

    def listar_estudiantes_admin(self, consulta: str = "") -> tuple[str, dict]:
        """Lista todos los estudiantes del sistema (admin)."""
        logger.info(f"[AdminAdapter] listar_estudiantes_admin consulta={consulta}")

        data = self.admin._get("/api/administracion/estudiantes/")
        estudiantes = data if isinstance(data, list) else []

        if not estudiantes:
            return "No se encontraron estudiantes en el sistema.", {}

        if consulta:
            q = consulta.lower()
            estudiantes = [
                e for e in estudiantes
                if q in (e.get("nombres", "") + " " + e.get("apellidos", "")).lower()
                or q in (e.get("correo", "")).lower()
            ]

        if not estudiantes:
            return f"No se encontraron estudiantes que coincidan con '{consulta}'.", {}

        lineas = [f"Total de estudiantes: {len(estudiantes)}"]
        for e in estudiantes[:20]:
            nombre = f"{e.get('nombres', '')} {e.get('apellidos', '')}".strip()
            correo = e.get("correo", "N/A")
            carrera = e.get("carrera_nombre", "N/A")
            lineas.append(f"- {nombre} ({correo}, {carrera})")

        if len(estudiantes) > 20:
            lineas.append(f"... y {len(estudiantes) - 20} más")

        return "\n".join(lineas), {"total_estudiantes": len(estudiantes)}

    def listar_tutorias_admin(self, consulta: str = "") -> tuple[str, dict]:
        """Lista todas las tutorías del sistema (admin)."""
        logger.info(f"[AdminAdapter] listar_tutorias_admin consulta={consulta}")

        rest = self.admin._get("/api/administracion/estudiantes/")  # fallback
        try:
            from app.services.microservice_client import get_tutorias_rest_client
            tutorias_rest = get_tutorias_rest_client()
            url = f"{tutorias_rest._base}/api/tutorias/solicitudes"
            import httpx
            resp = httpx.get(url, headers=tutorias_rest._headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                tutorias = data if isinstance(data, list) else data.get("solicitudes", [])
            else:
                tutorias = []
        except Exception as e:
            logger.warning(f"[AdminAdapter] listar_tutorias_admin falló: {e}")
            tutorias = []

        if not tutorias:
            return "No hay tutorías registradas en el sistema.", {}

        if consulta:
            q = consulta.lower()
            tutorias = [
                t for t in tutorias
                if q in (t.get("tema", "") or "").lower()
                or q in (t.get("estado", "") or "").lower()
            ]

        lineas = [f"Total de tutorías: {len(tutorias)}"]
        for t in tutorias[:15]:
            tid = t.get("id", "N/A")
            tema = t.get("tema", "Sin tema")
            estado = t.get("estado", "desconocido")
            fecha = t.get("fecha_solicitud", "N/A")
            eid = t.get("estudiante_id", "N/A")
            lineas.append(f"- Tutoría #{tid}: {tema} (Estado: {estado}, Estudiante: {eid}, Fecha: {fecha})")

        if len(tutorias) > 15:
            lineas.append(f"... y {len(tutorias) - 15} más")

        return "\n".join(lineas), {"total_tutorias": len(tutorias)}

    def estadisticas_sistema(self) -> tuple[str, dict]:
        """Devuelve estadísticas generales del sistema."""
        logger.info("[AdminAdapter] estadisticas_sistema")

        docentes = self.admin.buscar_docentes("")
        estudiantes_data = self.admin._get("/api/administracion/estudiantes/")
        estudiantes = estudiantes_data if isinstance(estudiantes_data, list) else []
        carreras = self.admin.get_carreras() or []
        facultades = self.admin.get_facultades() or []

        stats = {
            "total_docentes": len(docentes),
            "total_estudiantes": len(estudiantes),
            "total_carreras": len(carreras),
            "total_facultades": len(facultades),
        }

        content = (
            f"Estadísticas del sistema:\n"
            f"- Docentes: {stats['total_docentes']}\n"
            f"- Estudiantes: {stats['total_estudiantes']}\n"
            f"- Carreras: {stats['total_carreras']}\n"
            f"- Facultades: {stats['total_facultades']}"
        )

        return content, stats

    def listar_estudiantes_por_docente(self, usuario_id: int) -> tuple[str, dict]:
        """Lista las materias del docente y sus estudiantes asignados."""
        logger.info(f"[AdminAdapter] listar_estudiantes_por_docente usuario_id={usuario_id}")

        try:
            docentes = self.admin._get("/api/administracion/docentes/")
            docentes = docentes if isinstance(docentes, list) else []

            docente = None
            for d in docentes:
                uid = d.get("usuario_id") or (d.get("usuario", {}) or {}).get("id")
                if uid == usuario_id:
                    docente = d
                    break

            if not docente:
                return (
                    f"No se encontró el perfil del docente (usuario_id={usuario_id}).",
                    {},
                )
        except Exception as e:
            logger.error(f"[AdminAdapter] listar_estudiantes_por_docente error: {e}")
            return f"Error al obtener docente: {e}", {}

        nombre_completo = f"{docente.get('nombre', '')} {docente.get('apellidos', '') or docente.get('apellido', '')}".strip()
        asignaturas = docente.get("asignaturas", [])

        if not asignaturas:
            return (
                f"El docente {nombre_completo} no tiene materias asignadas actualmente.",
                {},
            )

        lineas = [f"Asignaturas de {nombre_completo}:\n"]

        for asig in asignaturas:
            nombre_materia = asig.get("nombre", "Sin nombre")
            materia_id = asig.get("id")
            semestre = asig.get("semestre", "")
            num_estudiantes = asig.get("total_estudiantes", asig.get("estudiantes", 0))
            paralelos = asig.get("paralelos", 0)
            seccion = asig.get("seccion", "")

            lineas.append(f"📚 {nombre_materia}")
            if semestre:
                lineas.append(f"   Semestre: {semestre}")
            if seccion:
                lineas.append(f"   Sección: {seccion}")
            if paralelos and isinstance(paralelos, int) and paralelos > 1:
                lineas.append(f"   Paralelos: {paralelos}")
            if num_estudiantes and isinstance(num_estudiantes, int):
                lineas.append(f"   Estudiantes asignados: {num_estudiantes}")
            lineas.append("")

        return "\n".join(lineas), {
            "docente": nombre_completo,
            "total_asignaturas": len(asignaturas),
        }

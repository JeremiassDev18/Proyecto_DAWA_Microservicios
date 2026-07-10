"""
Adaptador de seguridad/perfil para el agente LLM.

Reutiliza SecurityClient y AdminClient para construir una vista
unificada del perfil del estudiante.
"""

from app.services.microservice_client import (
    get_security_client,
    get_admin_client,
)
from app.utils.logger import logger


class SecurityAdapter:
    """Adaptador que expone operaciones de seguridad/perfil como herramientas."""

    def __init__(self):
        self.security = get_security_client()
        self.admin = get_admin_client()

    def consultar_perfil(self, estudiante_id: int) -> tuple[str, dict]:
        """
        Consulta y formatea el perfil académico completo de un estudiante.

        Combina datos del servicio de seguridad (usuario) y administración
        (estudiante, carrera, facultad).

        Returns:
            (texto_para_llm, state_updates)
        """
        logger.info(f"[SecurityAdapter] consultar_perfil estudiante_id={estudiante_id}")

        # 1. Datos académicos desde administración.
        estudiante = self.admin.get_estudiante(estudiante_id)
        if not estudiante:
            return (
                f"No encontré información académica para el estudiante {estudiante_id}. "
                "Verifica que el ID sea correcto.",
                {},
            )

        # 2. Datos de usuario desde seguridad (si aplica).
        usuario = None
        user_id = estudiante.get("usuario_id")
        if user_id:
            usuario = self.security.get_usuario(user_id)

        nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellidos', '')}".strip()

        # 3. Construir texto legible para el LLM.
        partes = ["Perfil del estudiante:"]
        partes.append(f"- Nombre: {nombre_completo}")
        email = estudiante.get("correo") or estudiante.get("email")
        if not email and usuario:
            email = usuario.get("email") or usuario.get("correo")
        partes.append(f"- Email: {email or 'N/A'}")
        partes.append(f"- Carrera: {estudiante.get('carrera_nombre', 'N/A')}")
        partes.append(f"- Facultad: {estudiante.get('facultad_nombre', 'N/A')}")
        partes.append(f"- Nivel/Semestre: {estudiante.get('nivel', 'N/A')}")
        partes.append(f"- Periodo activo: {estudiante.get('periodo_nombre', 'N/A')}")
        estado_val = estudiante.get('estado', True)
        partes.append(f"- Estado: {'Activo' if estado_val else 'Inactivo'}")

        state_updates = {
            "usuario": nombre_completo,
            "carrera": estudiante.get("carrera_nombre"),
            "periodo": estudiante.get("periodo_nombre"),
        }

        return "\n".join(partes), state_updates


    def consultar_perfil_completo(self, estudiante_id: int) -> tuple[str, dict]:
        """
        Perfil + materias + docentes en un solo llamado.

        Reutiliza el adaptador de administración para obtener materias y
        docentes asignados sin requerir múltiples tools.
        """
        from app.services.microservice_client import get_admin_client
        admin_client = get_admin_client()
        logger.info(f"[SecurityAdapter] consultar_perfil_completo estudiante_id={estudiante_id}")

        perfil_texto, perfil_state = self.consultar_perfil(estudiante_id)
        if not perfil_state:
            return perfil_texto, {}

        materias = admin_client.get_materias_estudiante(estudiante_id) or []
        docentes = admin_client.get_estudiante_docentes(estudiante_id) or []

        lineas = [perfil_texto, "", "Materias inscritas:"]
        for m in materias:
            lineas.append(
                f"- {m.get('nombre', 'Sin nombre')} (ID: {m.get('id', 'N/A')}, "
                f"código: {m.get('codigo', 'N/A')}, créditos: {m.get('creditos', 'N/A')})"
            )

        lineas.append("")
        lineas.append("Docentes asignados:")
        for d in docentes:
            nombre = f"{d.get('nombres', '')} {d.get('apellidos', '')}".strip()
            if not nombre:
                nombre = d.get("nombre", "Sin nombre")
            materia = d.get("materia") or d.get("asignatura") or d.get("materia_nombre", "N/A")
            lineas.append(f"- {nombre} (ID: {d.get('id', 'N/A')}) — materia: {materia}")

        state_updates = {
            **perfil_state,
            "materias": [
                {"id": m.get("id"), "nombre": m.get("nombre"), "codigo": m.get("codigo")}
                for m in materias
            ],
            "docentes": [
                {"id": d.get("id"), "nombre": f"{d.get('nombres', '')} {d.get('apellidos', '')}".strip() or d.get("nombre")}
                for d in docentes
            ],
        }

        return "\n".join(lineas), state_updates

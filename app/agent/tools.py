"""
Definiciones de herramientas para el agente LLM. Descripciones compactas para Qwen 3B.
"""

from .schemas import ToolDefinition, ToolParameter


def get_available_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="consultar_perfil",
            description="Perfil básico (nombres, carrera, email).",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
            ],
        ),
        ToolDefinition(
            name="consultar_perfil_completo",
            description="Perfil + materias + docentes.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
            ],
        ),
        ToolDefinition(
            name="consultar_materias",
            description="Materias del estudiante.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
            ],
        ),
        ToolDefinition(
            name="consultar_tutorias",
            description="Tutorías solicitadas/pendientes.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
            ],
        ),
        ToolDefinition(
            name="crear_tutoria",
            description="Crear nueva tutoría.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
                ToolParameter(name="asignatura_id", type="integer", description="ID de la materia", required=True),
                ToolParameter(name="tema", type="string", description="Tema de la tutoría", required=True),
                ToolParameter(name="periodo_id", type="integer", description="Periodo (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="cancelar_tutoria",
            description="Cancelar tutoría existente.",
            parameters=[
                ToolParameter(name="tutoria_id", type="integer", description="ID de la tutoría", required=True),
                ToolParameter(name="motivo", type="string", description="Motivo", required=True),
                ToolParameter(name="usuario_id", type="integer", description="ID usuario", required=True),
            ],
        ),
        ToolDefinition(
            name="buscar_docentes",
            description="SIEMPRE usa esto cuando el usuario pregunte por profesores, docentes, quién enseña algo, o materias de profesores. Param 'materia' con el nombre de la materia. Param 'posesivo'='mios' para profesores del estudiante.",
            parameters=[
                ToolParameter(name="consulta", type="string", description="Texto de búsqueda (nombre del profesor o materia)", required=True),
                ToolParameter(name="estudiante_id", type="integer", description="ID del estudiante", required=False),
                ToolParameter(name="posesivo", type="string", description="'mios' para profesores propios, 'todos' para todos", required=False),
                ToolParameter(name="materia", type="string", description="Nombre de la materia para buscar sus docentes", required=False),
            ],
        ),
        ToolDefinition(
            name="sugerir_docente",
            description="Recomendar profesor para una materia.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
                ToolParameter(name="asignatura_id", type="integer", description="ID de la materia", required=True),
            ],
        ),
        ToolDefinition(
            name="consultar_bitacoras",
            description="Tutorías atendidas, sesiones, historial, bitácoras.",
            parameters=[
                ToolParameter(name="estudiante_id", type="integer", description="ID estudiante", required=True),
                ToolParameter(name="periodo_id", type="integer", description="Periodo (opcional)", required=False),
                ToolParameter(name="solicitud_id", type="integer", description="ID tutoría específica (opcional)", required=False),
                ToolParameter(name="busqueda", type="string", description="Filtrar por tema (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="buscar_conocimiento",
            description="Reglamentos, políticas, normas institucionales.",
            parameters=[
                ToolParameter(name="consulta", type="string", description="Tema a buscar", required=True),
            ],
        ),
        ToolDefinition(
            name="escalar_conversacion",
            description="Atención humana, emergencia.",
            parameters=[
                ToolParameter(name="motivo", type="string", description="Motivo", required=True),
                ToolParameter(name="usuario_id", type="integer", description="ID usuario (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="listar_docentes",
            description="Listar todos los docentes del sistema. Opcionalmente buscar por nombre o materia.",
            parameters=[
                ToolParameter(name="consulta", type="string", description="Buscar por nombre o materia (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="listar_estudiantes",
            description="Listar todos los estudiantes del sistema. Opcionalmente buscar por nombre.",
            parameters=[
                ToolParameter(name="consulta", type="string", description="Buscar por nombre (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="listar_tutorias",
            description="Listar todas las tutorías del sistema con estado y tema.",
            parameters=[
                ToolParameter(name="consulta", type="string", description="Filtrar por tema (opcional)", required=False),
            ],
        ),
        ToolDefinition(
            name="estadisticas_sistema",
            description="Estadísticas generales: total docentes, estudiantes, tutorías, carreras.",
            parameters=[],
        ),
        ToolDefinition(
            name="listar_estudiantes_por_docente",
            description="Las materias que imparte el docente y cuántos estudiantes tiene en cada una. Úsalo cuando el docente pregunte por sus asignaturas o sus estudiantes.",
            parameters=[],
        ),
    ]

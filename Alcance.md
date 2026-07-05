Microservicio de Agente de Inteligencia Artificial
Descripción General
El Microservicio de Agente de Inteligencia Artificial constituye el componente inteligente de la plataforma. Su propósito es actuar como un primer punto de contacto entre el estudiante y el sistema de tutorías, brindando orientación inicial, resolviendo consultas frecuentes, clasificando solicitudes y apoyando labores administrativas mediante generación de resúmenes.
Es importante enfatizar que este microservicio no reemplaza el criterio del docente ni toma decisiones académicas definitivas. Su rol es de apoyo, orientación y automatización de tareas repetitivas, siempre bajo un esquema de respuestas basadas en información institucional validada, evitando que el agente genere contenido fuera de contexto o no autorizado.
El microservicio se apoya en un modelo de lenguaje (LLM), ya sea mediante consumo de una API externa o mediante un modelo desplegado localmente, combinado con una base de conocimiento institucional controlada (documentos, preguntas frecuentes, políticas académicas) que delimita el alcance de sus respuestas.
Objetivos del Microservicio

Brindar atención inicial automatizada a consultas frecuentes de los estudiantes, reduciendo la carga operativa de docentes y coordinadores.
Clasificar automáticamente las solicitudes de tutoría según tema, asignatura o urgencia, facilitando su asignación.
Sugerir el docente tutor más adecuado en función de la asignatura y disponibilidad registrada en el Microservicio de Administración Académica.
Generar resúmenes automáticos de solicitudes y bitácoras para facilitar el seguimiento por parte de docentes y coordinadores.
Escalar de forma controlada los casos que el agente no pueda resolver con seguridad hacia un docente o coordinador.
Mantener trazabilidad completa de todas las interacciones para fines de auditoría y mejora continua.

Arquitectura y Enfoque Técnico

Modelo de lenguaje (LLM): puede integrarse mediante API de un proveedor externo o mediante un modelo local, según las capacidades técnicas y de infraestructura del equipo de desarrollo.
Base de conocimiento controlada (RAG): se recomienda implementar un enfoque de Retrieval-Augmented Generation, donde el agente consulta primero una base documental institucional (FAQs, reglamentos, información de horarios y procesos) antes de generar una respuesta, minimizando el riesgo de alucinaciones o respuestas fuera de contexto.
Capa de validación de respuestas: antes de entregar una respuesta al usuario, el sistema debe verificar que la información no exponga datos sensibles ni contradiga las políticas institucionales.
Mecanismo de escalamiento: cuando el nivel de confianza de la respuesta sea bajo, o el tema esté fuera del alcance de la base de conocimiento, el sistema debe derivar automáticamente el caso a un docente o coordinador, notificando mediante el Microservicio de Tutorías.
Comunicación interna: este microservicio debe consumir datos del Microservicio de Administración Académica (asignaturas, docentes, disponibilidad) y del Microservicio de Tutorías (estado de solicitudes) mediante API REST o mensajería asíncrona.

Entidades Principales

Conversación: sesión de interacción entre un estudiante y el agente de IA.
Mensaje: cada intervención dentro de una conversación (usuario o agente).
Base de Conocimiento: conjunto de documentos, FAQs y políticas parametrizadas por los administradores.
Clasificación de Solicitud: categoría asignada automáticamente a una consulta (tema, asignatura, urgencia).
Escalamiento: registro de un caso derivado a un humano, con motivo y destinatario.
Feedback: valoración del usuario sobre la utilidad de una respuesta.

Reglas de Negocio Específicas

El agente de IA solo podrá responder con base en información registrada o parametrizada en el sistema (base de conocimiento institucional).
Toda respuesta generada por el agente deberá presentarse explícitamente como una orientación, no como una decisión académica definitiva.
Cuando el nivel de confianza de la respuesta sea insuficiente, el sistema deberá escalar automáticamente la consulta a un docente o coordinador.
Todas las conversaciones e interacciones con el agente deberán quedar registradas de forma íntegra para fines de auditoría.
El agente no podrá acceder ni exponer información académica sensible de un estudiante distinto al que inició la conversación.
Los documentos y FAQs que alimentan la base de conocimiento solo podrán ser gestionados por usuarios con permisos administrativos.

Detalle de Requerimientos Funcionales
IDDescripciónDetalle AmpliadoAIA-R01Chat académico para consultas frecuentesInterfaz conversacional donde el estudiante puede preguntar sobre horarios, procesos, requisitos, etc.AIA-R02Clasificación automática de solicitudesEl agente etiqueta cada solicitud según tema, asignatura o nivel de urgencia, apoyándose en NLP.AIA-R03Sugerencia de docente tutorRecomendación basada en asignatura solicitada y disponibilidad horaria consultada al Microservicio de Administración Académica.AIA-R04Generación de resumen de solicitudesResumen automático del historial de una solicitud para facilitar la revisión del docente/coordinador.AIA-R05Generación de resumen de bitácorasConsolidación automática de observaciones registradas en múltiples sesiones de atención.AIA-R06Búsqueda en base de conocimiento institucionalConsulta semántica sobre documentos, reglamentos y FAQs cargados por administradores (enfoque RAG).AIA-R07Escalamiento de consultas no resueltasDerivación automática a un docente/coordinador cuando el agente no tenga suficiente certeza o la consulta lo requiera.AIA-R08Registro histórico de conversacionesAlmacenamiento completo de cada conversación, con marca de tiempo, usuario y contenido.AIA-R09Evaluación de utilidad de la respuesta (feedback)Mecanismo tipo "¿te fue útil esta respuesta?" que retroalimenta la mejora del sistema.AIA-R10Configuración de FAQs y documentos basePanel administrativo para cargar, editar o eliminar documentos y preguntas frecuentes.AIA-R11Validación de respuestas no autorizadasFiltro que impide que el agente exponga datos sensibles o responda fuera del alcance institucional.AIA-R12Panel de métricas de uso del agenteDashboard con indicadores: número de conversaciones, temas más consultados, tasa de escalamiento, satisfacción promedio.
Consideraciones Técnicas y de Seguridad

Se recomienda limitar el contexto del modelo de lenguaje exclusivamente a la información institucional cargada, evitando respuestas generadas con conocimiento general no verificado.
Las conversaciones deben almacenarse cifradas o con control de acceso restringido, dado que pueden contener información académica personal.
Se debe definir un umbral de confianza (score) a partir del cual una respuesta se considera "segura" para ser entregada directamente al usuario; por debajo de dicho umbral, el caso se escala automáticamente.
El panel de métricas (AIA-R12) debe ser accesible únicamente para coordinadores y administradores, en línea con las reglas de negocio sobre visualización de reportes.
Se sugiere versionar la base de conocimiento para poder auditar qué documentos estaban vigentes cuando se generó una respuesta específica.
-- ============================================================
-- TutorBot AI — Base de Datos del Agente de IA (v1.0)
-- Motor: PostgreSQL 16
-- Microservicio: agente-ia  |  Puerto BD: 5435
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. INTENCIONES (clasificación semántica)
-- ============================================================

CREATE TABLE chatbot_intencion (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL UNIQUE,
    descripcion TEXT,
    activo      BOOLEAN DEFAULT TRUE,
    creado_en   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. DATASET DE ENTRENAMIENTO (SetFit + Búsqueda Híbrida)
-- ============================================================

CREATE TABLE chatbot_dataset (
    id              SERIAL PRIMARY KEY,
    texto           TEXT NOT NULL,
    id_intencion    INT NOT NULL REFERENCES chatbot_intencion(id),
    embedding       VECTOR(384),
    validado        BOOLEAN DEFAULT FALSE,
    origen          VARCHAR(20) DEFAULT 'manual' 
                    CHECK (origen IN ('manual', 'usuario', 'auto')),
    activo          BOOLEAN DEFAULT TRUE,
    creado_en       TIMESTAMP DEFAULT NOW(),
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dataset_trgm ON chatbot_dataset USING GIN (texto gin_trgm_ops);
-- CREATE INDEX idx_dataset_vector ON chatbot_dataset USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- ============================================================
-- 3. RESPUESTAS (asociadas a una intención)
-- ============================================================

CREATE TABLE chatbot_respuesta (
    id              SERIAL PRIMARY KEY,
    id_intencion    INT NOT NULL REFERENCES chatbot_intencion(id),
    respuesta_texto TEXT NOT NULL,
    tipo            VARCHAR(20) DEFAULT 'texto' 
                    CHECK (tipo IN ('texto', 'accion', 'mixto')),
    fuente          VARCHAR(20) DEFAULT 'manual' 
                    CHECK (fuente IN ('manual', 'dinamica', 'logica')),
    prioridad       SMALLINT DEFAULT 1,
    activa          BOOLEAN DEFAULT TRUE,
    veces_usada     INT DEFAULT 0,
    creado_en       TIMESTAMP DEFAULT NOW(),
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. PREGUNTAS PENDIENTES (con embedding)
-- ============================================================

CREATE TABLE chatbot_pregunta_pendiente (
    id              SERIAL PRIMARY KEY,
    contenido       TEXT NOT NULL,
    embedding       VECTOR(384),
    veces_repetida  INT DEFAULT 1,
    resuelta        BOOLEAN DEFAULT FALSE,
    aprendida       BOOLEAN DEFAULT FALSE,
    creado_en       TIMESTAMP DEFAULT NOW(),
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. BASE DE CONOCIMIENTO (documentos, reglamentos, FAQs)
-- ============================================================

CREATE TABLE documento_base (
    id              SERIAL PRIMARY KEY,
    titulo          VARCHAR(255) NOT NULL,
    contenido       TEXT NOT NULL,
    embedding       VECTOR(384),
    categoria       VARCHAR(50),            -- 'reglamento', 'manual', 'faq', 'normativa'
    fuente          VARCHAR(100),           -- Ej: 'Reglamento.pdf'
    archivo_pdf     VARCHAR(255),           -- URL o path del archivo
    fecha_publicacion DATE,
    activo          BOOLEAN DEFAULT TRUE,
    creado_en       TIMESTAMP DEFAULT NOW(),
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documento_trgm ON documento_base USING GIN (contenido gin_trgm_ops);
-- CREATE INDEX idx_documento_vector ON documento_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- ============================================================
-- 6. CONVERSACIONES Y MENSAJES
-- ============================================================

CREATE TABLE chatbot_conversacion (
    id              SERIAL PRIMARY KEY,
    id_usuario      INT,
    nombre_cliente  VARCHAR(150),
    iniciado_en     TIMESTAMP DEFAULT NOW(),
    finalizado_en   TIMESTAMP,
    activa          BOOLEAN DEFAULT TRUE
);

CREATE TABLE chatbot_mensaje (
    id                  SERIAL PRIMARY KEY,
    id_conversacion     INT REFERENCES chatbot_conversacion(id),
    rol                 VARCHAR(10) CHECK (rol IN ('usuario', 'bot')),
    contenido           TEXT NOT NULL,
    tipo_resolucion     VARCHAR(20) CHECK (tipo_resolucion IN ('estatica', 'dinamica', 'logica', 'sin_respuesta')),
    respondido_por_ia   BOOLEAN DEFAULT FALSE,
    score_similitud     NUMERIC(5,4),
    id_intencion        INT REFERENCES chatbot_intencion(id),
    confianza_ml        NUMERIC(5,2),
    modelo_usado        VARCHAR(30),
    enviado_en          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. FEEDBACK DEL USUARIO
-- ============================================================

CREATE TABLE chatbot_feedback (
    id          SERIAL PRIMARY KEY,
    id_mensaje  INT REFERENCES chatbot_mensaje(id),
    fue_util    BOOLEAN,
    comentario  TEXT,
    creado_en   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 8. REGISTRO DE PREDICCIONES (para aprendizaje continuo)
-- ============================================================

CREATE TABLE chatbot_prediccion (
    id                  SERIAL PRIMARY KEY,
    texto_usuario       TEXT NOT NULL,
    intencion_predicha  VARCHAR(80),
    confianza           NUMERIC(5,2),
    correcta            BOOLEAN,
    fecha               TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 9. COLA DE ENTRENAMIENTO (cuando se validan nuevos ejemplos)
-- ============================================================

CREATE TABLE entrenamiento_pendiente (
    id              SERIAL PRIMARY KEY,
    id_dataset      INT REFERENCES chatbot_dataset(id),
    procesado       BOOLEAN DEFAULT FALSE,
    fecha           TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 10. HISTORIAL DE MODELOS ML (versionado)
-- ============================================================

CREATE TABLE modelo_ml (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    version             VARCHAR(20) UNIQUE,           -- Ahora UNIQUE para FK
    accuracy            NUMERIC(5,2),
    precision           NUMERIC(5,2),
    recall              NUMERIC(5,2),
    f1_score            NUMERIC(5,2),
    loss                NUMERIC(5,4),
    fecha_entrenamiento TIMESTAMP DEFAULT NOW(),
    activo              BOOLEAN DEFAULT FALSE,
    observacion         TEXT
);

-- ============================================================
-- 11. REGISTRO DETALLADO DE ENTRENAMIENTOS
-- ============================================================

CREATE TABLE chatbot_training (
    id                SERIAL PRIMARY KEY,
    fecha             TIMESTAMP DEFAULT NOW(),
    modelo_version    VARCHAR(50) REFERENCES modelo_ml(version), -- Ahora funciona
    ejemplos_usados   INT,
    accuracy          NUMERIC(5,2),
    precision         NUMERIC(5,2),
    recall            NUMERIC(5,2),
    f1_score          NUMERIC(5,2),
    loss              NUMERIC(5,4),
    estado            VARCHAR(20) DEFAULT 'completado' 
                      CHECK (estado IN ('en_progreso', 'completado', 'fallido')),
    observacion       TEXT
);

-- ============================================================
-- DATOS INICIALES
-- ============================================================

INSERT INTO chatbot_intencion (nombre, descripcion) VALUES
('CREAR_SOLICITUD',       'El estudiante quiere crear una nueva solicitud de tutoría'),
('CANCELAR_SOLICITUD',    'El estudiante desea cancelar una tutoría existente'),
('CAMBIAR_HORARIO',       'El estudiante quiere reprogramar una tutoría'),
('BUSCAR_DOCENTE',        'El estudiante busca información sobre docentes'),
('CONSULTAR_ASIGNATURA',  'Consulta sobre asignaturas, horarios, contenidos'),
('CONSULTAR_REGLAMENTO',  'Preguntas sobre normas, políticas o reglamentos'),
('CONSULTAR_FAQ',         'Preguntas frecuentes y respuestas estándar'),
('ESCALAR_DOCENTE',       'Derivar un problema a un docente o coordinador'),
('RESUMEN_SOLICITUD',     'Solicitar resumen de tutorías o bitácoras'),
('SIN_INTENCION',         'Catch-all para frases no clasificadas'),
('SOLICITAR_TUTORIA',     'El estudiante solicita un tutor o apoyo académico en una materia'),
('CONSULTAR_MIS_TUTORIAS','El estudiante consulta sus tutorías registradas o activas'),
('HORARIO_TUTORIAS',      'Preguntas sobre horarios, modalidad o disponibilidad de tutorías'),
('CONTACTAR_DOCENTE',     'El estudiante quiere contactar a un docente específico'),
('DISPONIBILIDAD_DOCENTE','El estudiante pregunta si hay tutores disponibles para una materia');

-- ---- Dataset de entrenamiento inicial (validado) ----
-- Aprox. 140 ejemplos distribuidos en las 11 intenciones
INSERT INTO chatbot_dataset (id_intencion, texto, validado, origen) VALUES

-- SOLICITAR_TUTORIA (18) — antes era CONSULTAR_TUTORIA
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito tutoría de Matemáticas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero una tutoría de Programación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'No entiendo Cálculo, necesito ayuda', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito ayuda en Física', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), '¿Cómo solicito una tutoría?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Me gustaría recibir tutoría de Álgebra Lineal', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Estoy atrasado en Redes, necesito un tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito reforzar mis conocimientos de Química', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Tengo dudas de Ingeniería de Software, qué hago', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito ayuda urgente con mi tesis', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), '¿Pueden darme tutoría de inglés técnico?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), '¿Cómo hago para que me asignen un tutor?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un tutor de Programación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Busco un tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero un docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito apoyo académico', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero hablar con un tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un especialista en programación', TRUE, 'manual'),

-- CONSULTAR_MIS_TUTORIAS (8) — nueva
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), '¿Cuántas tutorías tengo registradas?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consulta mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), '¿Qué tutorías tengo activas?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Mis tutorías programadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Lista de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), '¿En qué tutorías estoy inscrito?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Muéstrame mis sesiones de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), '¿Tengo tutorías pendientes?', TRUE, 'manual'),

-- HORARIO_TUTORIAS (8) — nueva
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿En qué horarios hay tutorías?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿Las tutorías son presenciales o virtuales?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿Dan tutorías de Estadística?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿Hay apoyo para el curso de Algoritmos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de tutorías disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿A qué hora son las tutorías?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿Las tutorías son en línea o presenciales?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), '¿Hay tutorías los fines de semana?', TRUE, 'manual'),

-- CONTACTAR_DOCENTE (6) — nueva
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Muéstrame el correo del rector', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), '¿Cómo contacto a mi tutor?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero el correo del profesor García', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Correo del docente de Redes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Número de contacto del tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), '¿Cómo escribo al coordinador?', TRUE, 'manual'),

-- DISPONIBILIDAD_DOCENTE (6) — nueva
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor disponibles para Sistemas Operativos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), '¿Puedo conseguir tutoría para Estructura de Datos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), '¿Hay tutorías de Base de Datos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), '¿Qué profesor está disponible para tutorías?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), '¿Hay tutores disponibles esta semana?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), '¿Quién puede ayudarme con Álgebra Lineal?', TRUE, 'manual'),

-- CREAR_SOLICITUD (15)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Quiero crear una solicitud de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Necesito agendar una tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Solicitar tutoría para POO', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Registra una tutoría para mí', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Quiero inscribirme en una tutoría de Cálculo II', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Agenda una sesión de tutoría para esta semana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Necesito reservar un espacio con un tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Aparta una tutoría de Física para el jueves', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Quiero pedir una tutoría de Base de Datos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Solicita una tutoría para el examen final', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Puedes crear una solicitud para tutoría grupal', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Necesito que me asignen un tutor de Estadística', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Registra mi interés en tutoría de Programación Web', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Quiero tomar tutorías regulares de Álgebra', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Agéndame una tutoría con el profe de Física', TRUE, 'manual'),

-- CANCELAR_SOLICITUD (12)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Quiero cancelar mi tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Cancelar la tutoría de mañana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Ya no necesito la tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Anula mi solicitud de tutoría por favor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Cancelar todas mis tutorías programadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Quiero dar de baja mi tutoría del lunes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Elimina la tutoría que pedí ayer', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'No podré asistir, cancela la sesión', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Deja sin efecto mi solicitud de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Cancelar la cita con el tutor de Cálculo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Quiero anular la reserva de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Ya resolví mis dudas, cancela la tutoría', TRUE, 'manual'),

-- CAMBIAR_HORARIO (12)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Quiero reprogramar mi tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Cambiar la hora de la tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), '¿Puedo mover la tutoría a otro día?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Necesito cambiar el horario de mi tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), '¿Se puede pasar la tutoría al viernes?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Adelantar la tutoría de las 4 a las 2', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), '¿Hay disponibilidad para mover la tutoría a la mañana?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Recorre la tutoría media hora más tarde', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Atrasa la tutoría 1 hora por favor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Cambiar la fecha de la tutoría del miércoles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Necesito reagendar urgente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), '¿Puedo tener la tutoría más temprano?', TRUE, 'manual'),

-- BUSCAR_DOCENTE (12)
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Quién dicta Programación?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Qué profesor está disponible?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Docente de Matemáticas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Quién es el profesor de Álgebra Lineal?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Necesito saber el correo del docente de Redes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Qué tutor me recomiendas para Física?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Muéstrame los docentes disponibles para tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Quién da Tutoría de Base de Datos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿El profesor García tiene horario libre?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Horario de atención del docente de POO', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Quisiera contactar al tutor de Cálculo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), '¿Quién es el coordinador de la carrera?', TRUE, 'manual'),

-- CONSULTAR_ASIGNATURA (15)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuándo es el examen de Cálculo?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), 'Horario de Programación Avanzada', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Qué temas abarca POO?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuál es el sílabo de Análisis Numérico?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuántos créditos tiene Estructura de Datos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), 'Prerrequisitos para cursar Base de Datos II', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿En qué aula se dicta Física III?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuándo empiezan las inscripciones?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Qué asignaturas tiene el ciclo 3?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuál es el plan de estudios de la carrera?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿La asignatura de Inglés es obligatoria?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), 'Horario de atención del curso de Tesis', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuánto dura el curso de Álgebra Lineal?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Qué profesor dicta Sistemas Operativos?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), '¿Cuándo cierran las matrículas?', TRUE, 'manual'),

-- CONSULTAR_REGLAMENTO (12)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Explícame el reglamento de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Cuáles son las normas?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Política de cancelación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Puedo faltar a una tutoría sin avisar?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Cuántas faltas están permitidas?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Normas para tutorías virtuales', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Se puede recuperar una tutoría perdida?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Política de uso de la plataforma', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Qué sanciones hay por no asistir?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Los tutores son evaluados por los estudiantes?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Reglamento de tutorías entre pares', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), '¿Existe un código de conducta para tutorías?', TRUE, 'manual'),

-- CONSULTAR_FAQ (12)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), 'Preguntas frecuentes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Cómo funciona el sistema?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Cuánto dura una tutoría?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Las tutorías tienen costo?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Cuántas tutorías puedo tomar por semana?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Cómo sé qué tutor me asignaron?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Qué hago si no encuentro a mi tutor?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿La tutoría queda registrada en mi historial?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Puedo pedir tutoría de más de una materia?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Hay límite de tutorías por día?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Qué beneficios tienen las tutorías?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), '¿Cuánto tiempo antes debo solicitar una tutoría?', TRUE, 'manual'),

-- ESCALAR_DOCENTE (10)
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Necesito hablar con el profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Escalar este problema al docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Quiero contactar al coordinador', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Mi tutor no se presentó, quiero reportarlo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Necesito que un docente revise mi caso', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'No estoy de acuerdo con la evaluación, quiero escalar', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Comunícame con el coordinador académico', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Derivar este reclamo al área correspondiente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Quiero presentar una queja sobre mi tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Necesito una reunión con el jefe de departamento', TRUE, 'manual'),

-- RESUMEN_SOLICITUD (10)
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Resumen de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), '¿Cuántas tutorías he tenido?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Ver bitácora de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Quiero ver el historial de mis sesiones', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), '¿Puedes darme un resumen de mi progreso?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Muéstrame las observaciones de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), '¿Cuántas horas de tutoría he completado?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Resumen semanal de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), '¿Qué temas he cubierto en tutorías?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Necesito un reporte de asistencia a tutorías', TRUE, 'manual'),

-- SIN_INTENCION (8)
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Hola', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Buenos días', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Gracias', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), '¿Qué tal?', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Chau', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Buenas tardes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Adiós', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Hola, cómo estás', TRUE, 'manual'),
-- SIN_INTENCION (adicionales)
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Buenas noches', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Qué onda', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Cómo va', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Todo bien', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'De nada', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Hasta luego', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Nos vemos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Hasta pronto', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Buen finde', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Claro', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'OK', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Perfecto', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Entendido', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Vale', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'De acuerdo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Qué cuentas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Dime', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Escucha', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Oye', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Disculpa', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Perdón', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Una consulta', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Puedes ayudarme', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Tengo una duda', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Quién ganó el mundial', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Cómo está el clima', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Cuál es la capital de Perú', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Quién es el presidente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Dame la hora', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Cuánto es 2 más 2', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Qué día es hoy', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SIN_INTENCION'), 'Quién descubrió América', TRUE, 'manual'),

-- SOLICITAR_TUTORIA (adicionales hasta ~50)
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Busco un tutor particular', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Requiero asesoría académica', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Podrían darme tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quisiera recibir clases de apoyo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito que me enseñen', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Alguien que me explique', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Me gustaría aprender más', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Ayúdame a entender', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito nivelarme', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Estoy perdido en clase', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'No entiendo el tema', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un tutor de Física cuántica', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero un mentor académico', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Podrían asignarme un tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito clases de refuerzo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Alguien que me ayude con la tarea', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Resolver dudas académicas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un tutor de inglés', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero reforzar Matemáticas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Busco quien me enseñe Programación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito ayuda con mi tesis', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero prepararme para el examen', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito un tutor particular de Estadística', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Requiero clases personalizadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Alguien que me guíe en el curso', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito apoyo para el parcial', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Reforzamiento de lo visto en clase', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Un profe que me explique bien', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Quiero que me ayuden a estudiar', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Necesito acompañamiento académico', TRUE, 'manual'),

-- CONSULTAR_MIS_TUTORIAS (adicionales hasta ~50)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cómo van mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Estado de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Tutorías que he solicitado', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consultar estado de solicitud', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'En qué tutorías estoy', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver el estado de mi solicitud', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Revisar mis tutorías activas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cuántas tutorías he pedido', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cuál es el estado de mi tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver solicitud de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Mis solicitudes de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Lista de tutorías solicitadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Dónde veo mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cómo consulto mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Mostrar mis tutorías pendientes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Tutorías asignadas a mi nombre', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver historial de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cuántas tutorías tengo este mes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Tutorías registradas este ciclo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consultar bitácora de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Revisar tutorías programadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Estado de mis solicitudes de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver si tengo tutorías activas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Tutorías que me asignaron', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Lista de sesiones de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver tutorías del usuario', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consultar mis tutorías registradas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Cómo saber si tengo tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Mostrar tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Dame el listado de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Información de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver las tutorías que tengo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'En qué tutorías estoy registrado', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consultar tutorías del estudiante', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Tutorías asignadas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver solicitudes pendientes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Estado de mis tutorías activas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Revisar el estado de mis tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Consultar progreso de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Ver si tengo tutorías programadas', TRUE, 'manual'),

-- HORARIO_TUTORIAS (adicionales hasta ~50)
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuál es el horario de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Hay tutorías los sábados', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías son virtuales', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Días de tutorías disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'En qué horario dan tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de atención de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuándo hay tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías son por la mañana o tarde', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Hay tutorías en la noche', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuánto dura cada tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías duran una hora', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Modalidad de las tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Son presenciales o virtuales', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Hay tutorías en horario nocturno', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Se puede tener tutoría virtual', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario disponible para tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuándo están disponibles los tutores', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Tutorías en la mañana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Hay tutorías por la tarde', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuánto tiempo dura una sesión', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario extendido de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías tienen horario fijo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Puedo elegir el horario de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'A qué hora empiezan las tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'A qué hora terminan las tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Tutorías de lunes a viernes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de tutorías virtuales', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de tutorías presenciales', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuándo dan tutorías de Matemáticas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Hay tutorías en vacaciones', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Tutorías en horario de clases', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías son después de clase', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Se puede agendar tutoría fuera del horario', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Tutorías los fines de semana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de verano de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Cuál es el cronograma de tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'En qué días hay tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Tutorías disponibles esta semana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Próximas fechas de tutoría', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Horario de tutorías del ciclo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Dónde veo los horarios de tutoría', TRUE, 'manual'),

-- CONTACTAR_DOCENTE (adicionales hasta ~50)
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo contacto al profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero escribir al docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Correo del profesor de Física', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Necesito el teléfono del tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo me comunico con el tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Datos de contacto del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo localizar al profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero hablar con el coordinador', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo ubico a mi tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Correo electrónico del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Teléfono del profesor de Álgebra', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo enviar un mensaje al tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Medios de contacto del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Oficina del profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Dirección del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Email del tutor asignado', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo contactar al coordinador académico', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero el correo del director', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo escribir al profesor de Programación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Número de oficina del tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Dónde encuentro al profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cuál es el correo del rector', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo contacto al jefe de departamento', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero la dirección del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Teléfono del coordinador', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo hablar con el profesor tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Correo del profesor de Base de Datos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Información de contacto del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo le escribo a mi tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Dónde está la oficina del profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero contactar al docente de Redes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo llamar al profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Correo del jefe de carrera', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo contactar al tutor asignado', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Quiero la extensión telefónica del tutor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo llegar a la oficina del profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Redes sociales del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Perfil del profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Dónde atiende el profesor', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Horario de oficina del docente', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Cómo le envío un mensaje al coordinador', TRUE, 'manual'),

-- DISPONIBILIDAD_DOCENTE (adicionales hasta ~50)
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutores disponibles ahora', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Qué tutores están disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay profesor de Física disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Cuándo hay tutor disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Matemáticas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Está disponible el profesor García', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Quién está disponible para tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay cupo para tutorías', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores disponibles esta tarde', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor libre', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay disponibilidad con el tutor de Cálculo', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores de Programación disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay profesor para Química', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Disponibilidad de tutores esta semana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Álgebra Lineal', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores con horario libre', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores disponibles en la mañana', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Estadística', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Quién da tutorías de Programación', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutores de Física disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Disponibilidad de tutores de Redes', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Base de Datos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores de inglés disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay profesor de Estructura de Datos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor disponible para Análisis Numérico', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Disponibilidad de tutores de Sistemas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Ingeniería de Software', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores de POO disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Álgebra', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay profesor de Inglés Técnico disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Cálculo disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Qué tutores hay para el curso de Algoritmos', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay disponibilidad de tutores de Física', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores de Química disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay profesor de Literatura', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Contabilidad', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay docentes disponibles ahora', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Profesores disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de matemáticas disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Tutores con cupo disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay espacio para tutorías nuevas', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Disponibilidad de tutores de Álgebra Lineal', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Docentes de Programación disponibles', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Hay tutor de Estadística disponible', TRUE, 'manual'),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Quién puede dar tutorías de Base de Datos', TRUE, 'manual');

-- ---- Respuestas para cada intención (ejemplos) ----
INSERT INTO chatbot_respuesta (id_intencion, respuesta_texto, tipo, prioridad) VALUES
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Perfecto. ¿De qué asignatura necesitas tutoría?', 'texto', 2),
((SELECT id FROM chatbot_intencion WHERE nombre = 'SOLICITAR_TUTORIA'), 'Puedo ayudarte con tutorías. Dime la materia y el tema.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_MIS_TUTORIAS'), 'Estoy consultando tus tutorías registradas...', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Las tutorías se realizan en horario académico regular, de lunes a viernes de 8:00 a 18:00. Algunas también están disponibles en modalidad virtual.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'HORARIO_TUTORIAS'), 'Puedes consultar los horarios disponibles en el sistema académico.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONTACTAR_DOCENTE'), 'Puedes contactar al docente a través del sistema de mensajería interna o solicitar sus datos de contacto en la secretaría académica.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Te recomiendo al docente más adecuado para esa asignatura.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'DISPONIBILIDAD_DOCENTE'), 'Los docentes disponibles para esa área son...', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Voy a crear tu solicitud. Dame la asignatura y tu disponibilidad.', 'accion', 2),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CREAR_SOLICITUD'), 'Excelente. ¿Para qué asignatura y qué día prefieres?', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), 'Dame el ID de tu tutoría para cancelarla.', 'accion', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CANCELAR_SOLICITUD'), '¿Cuál es el código de la tutoría que deseas cancelar?', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Necesito el código de la tutoría y la nueva fecha/hora.', 'accion', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CAMBIAR_HORARIO'), 'Dime qué tutoría quieres reprogramar.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Te recomiendo al docente más adecuado para esa asignatura.', 'texto', 2),
((SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE'), 'Los docentes disponibles son...', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), 'La información de la asignatura se encuentra en el sistema académico.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_ASIGNATURA'), 'Puedes consultar el horario y contenido en el portal.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Según el reglamento, las cancelaciones deben hacerse con 24h de anticipación.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_REGLAMENTO'), 'Las tutorías tienen una duración máxima de 90 minutos.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), 'Las tutorías duran 60 minutos y son gratuitas para estudiantes.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'CONSULTAR_FAQ'), 'Puedes solicitar hasta 3 tutorías por semana.', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'He creado un ticket para el coordinador. Te contactarán pronto.', 'accion', 2),
((SELECT id FROM chatbot_intencion WHERE nombre = 'ESCALAR_DOCENTE'), 'Voy a escalar tu consulta al docente responsable.', 'accion', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Aquí tienes el resumen de tus tutorías...', 'texto', 1),
((SELECT id FROM chatbot_intencion WHERE nombre = 'RESUMEN_SOLICITUD'), 'Tienes 3 tutorías realizadas y 1 pendiente.', 'texto', 1);

-- ---- Documentos base (reglamentos, FAQs) ----
INSERT INTO documento_base (titulo, contenido, categoria, fuente) VALUES
('Reglamento de Tutorías', 
 'Las tutorías son gratuitas, tienen duración de 60 minutos y se pueden cancelar con 24 horas de anticipación.', 
 'reglamento', 'Reglamento_Tutorias.pdf'),
('Política de Cancelación',
 'Las cancelaciones con menos de 24 horas serán registradas como falta justificada solo si se presenta certificado médico.',
 'reglamento', 'Politica_Cancelacion.pdf'),
('Preguntas Frecuentes',
 '¿Cómo solicito una tutoría? Ingresa al sistema y selecciona "Solicitar Tutoría". ¿Cuántas tutorías puedo tener? Máximo 3 por semana.',
 'faq', 'FAQ_Tutorias.pdf'),
('Manual del Estudiante',
 'El estudiante debe inscribirse en el portal para acceder a las tutorías. Las sesiones se registran en bitácora.',
 'manual', 'Manual_Estudiante.docx');

-- ============================================================
-- FUNCIONES PL/pgSQL
-- ============================================================

-- Búsqueda híbrida en el dataset (pgvector + pg_trgm)
CREATE OR REPLACE FUNCTION buscar_respuesta_hibrida(
    p_texto     TEXT,
    p_vector    VECTOR(384),
    p_umbral    FLOAT DEFAULT 0.20,
    p_w_vector  FLOAT DEFAULT 0.70,
    p_w_trgm    FLOAT DEFAULT 0.30
)
RETURNS TABLE (
    id_respuesta    INT,
    respuesta_texto TEXT,
    score           FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cr.id,
        cr.respuesta_texto,
        (
            (1 - (cd.embedding <=> p_vector)) * p_w_vector
            + similarity(cd.texto, p_texto) * p_w_trgm
        )::FLOAT AS score
    FROM chatbot_dataset cd
    JOIN chatbot_respuesta cr ON cr.id_intencion = cd.id_intencion
    WHERE cd.activo = TRUE
      AND cd.validado = TRUE
      AND cd.embedding IS NOT NULL
      AND (
            (1 - (cd.embedding <=> p_vector)) * p_w_vector
            + similarity(cd.texto, p_texto) * p_w_trgm
          ) > p_umbral
    ORDER BY score DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Fallback con pg_trgm
CREATE OR REPLACE FUNCTION buscar_respuesta_trgm(
    p_texto  TEXT,
    p_umbral FLOAT DEFAULT 0.20
)
RETURNS TABLE (
    id_respuesta    INT,
    respuesta_texto TEXT,
    score           FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cr.id,
        cr.respuesta_texto,
        similarity(cd.texto, p_texto)::FLOAT AS score
    FROM chatbot_dataset cd
    JOIN chatbot_respuesta cr ON cr.id_intencion = cd.id_intencion
    WHERE cd.activo = TRUE
      AND cd.validado = TRUE
      AND similarity(cd.texto, p_texto) > p_umbral
    ORDER BY score DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Búsqueda semántica en documentos base (RAG)
CREATE OR REPLACE FUNCTION buscar_documento(
    p_vector    VECTOR(384),
    p_umbral    FLOAT DEFAULT 0.30
)
RETURNS TABLE (
    id_doc      INT,
    titulo      TEXT,
    contenido   TEXT,
    score       FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        db.id,
        db.titulo,
        db.contenido,
        (1 - (db.embedding <=> p_vector))::FLOAT AS score
    FROM documento_base db
    WHERE db.activo = TRUE
      AND db.embedding IS NOT NULL
      AND (1 - (db.embedding <=> p_vector)) > p_umbral
    ORDER BY score DESC
    LIMIT 3;
END;
$$ LANGUAGE plpgsql;

-- Registrar pregunta pendiente (con embedding)
CREATE OR REPLACE FUNCTION registrar_pendiente(
    p_contenido TEXT,
    p_embedding  VECTOR(384) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM chatbot_pregunta_pendiente
        WHERE contenido ILIKE p_contenido AND resuelta = FALSE
    ) THEN
        UPDATE chatbot_pregunta_pendiente
        SET veces_repetida = veces_repetida + 1,
            actualizado_en = NOW(),
            embedding = COALESCE(p_embedding, embedding)
        WHERE contenido ILIKE p_contenido AND resuelta = FALSE;
    ELSE
        INSERT INTO chatbot_pregunta_pendiente (contenido, embedding)
        VALUES (p_contenido, p_embedding);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Incrementar uso de una respuesta
CREATE OR REPLACE FUNCTION incrementar_uso(p_id_respuesta INT)
RETURNS VOID AS $$
BEGIN
    UPDATE chatbot_respuesta
    SET veces_usada = veces_usada + 1,
        actualizado_en = NOW()
    WHERE id = p_id_respuesta;
END;
$$ LANGUAGE plpgsql;

-- Registrar predicción (para aprendizaje continuo)
CREATE OR REPLACE FUNCTION registrar_prediccion(
    p_texto     TEXT,
    p_intencion VARCHAR(80),
    p_confianza NUMERIC(5,2)
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO chatbot_prediccion (texto_usuario, intencion_predicha, confianza)
    VALUES (p_texto, p_intencion, p_confianza);
END;
$$ LANGUAGE plpgsql;

-- Marcar predicción como correcta/incorrecta (administrador)
CREATE OR REPLACE FUNCTION marcar_prediccion(
    p_id_prediccion INT,
    p_correcta BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE chatbot_prediccion
    SET correcta = p_correcta
    WHERE id = p_id_prediccion;
END;
$$ LANGUAGE plpgsql;

-- Trigger: cuando se valida un dataset, se encola para entrenamiento
CREATE OR REPLACE FUNCTION encolar_entrenamiento()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.validado = TRUE AND OLD.validado = FALSE THEN
        INSERT INTO entrenamiento_pendiente (id_dataset) VALUES (NEW.id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_encolar_entrenamiento
AFTER UPDATE OF validado ON chatbot_dataset
FOR EACH ROW
EXECUTE FUNCTION encolar_entrenamiento();

-- ============================================================
-- VISTAS ÚTILES
-- ============================================================

CREATE VIEW v_respuestas_activas AS
SELECT 
    i.nombre AS intencion,
    r.respuesta_texto,
    r.prioridad,
    r.veces_usada
FROM chatbot_respuesta r
JOIN chatbot_intencion i ON i.id = r.id_intencion
WHERE r.activa = TRUE
ORDER BY i.nombre, r.prioridad DESC, r.veces_usada DESC;

CREATE VIEW v_pendientes_con_embedding AS
SELECT id, contenido, veces_repetida, creado_en
FROM chatbot_pregunta_pendiente
WHERE resuelta = FALSE AND embedding IS NOT NULL
ORDER BY veces_repetida DESC;

CREATE VIEW v_dataset_validado AS
SELECT cd.texto, i.nombre AS intencion, cd.origen
FROM chatbot_dataset cd
JOIN chatbot_intencion i ON i.id = cd.id_intencion
WHERE cd.validado = TRUE AND cd.activo = TRUE;

CREATE VIEW v_predicciones_incorrectas AS
SELECT *
FROM chatbot_prediccion
WHERE correcta = FALSE
ORDER BY fecha DESC;

CREATE VIEW v_modelo_activo AS
SELECT *
FROM modelo_ml
WHERE activo = TRUE
LIMIT 1;

CREATE VIEW v_entrenamientos_pendientes AS
SELECT 
    ep.id,
    cd.texto,
    i.nombre AS intencion
FROM entrenamiento_pendiente ep
JOIN chatbot_dataset cd ON cd.id = ep.id_dataset
JOIN chatbot_intencion i ON i.id = cd.id_intencion
WHERE ep.procesado = FALSE;

-- ============================================================
-- Migración: separar intents transaccionales de documentales
-- ============================================================

-- 1. Fusionar CONTACTAR_DOCENTE y DISPONIBILIDAD_DOCENTE en BUSCAR_DOCENTE
UPDATE chatbot_dataset cd
SET id_intencion = (SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE')
WHERE cd.id_intencion IN (
    SELECT id FROM chatbot_intencion
    WHERE nombre IN ('CONTACTAR_DOCENTE', 'DISPONIBILIDAD_DOCENTE')
);

UPDATE chatbot_respuesta cr
SET id_intencion = (SELECT id FROM chatbot_intencion WHERE nombre = 'BUSCAR_DOCENTE')
WHERE cr.id_intencion IN (
    SELECT id FROM chatbot_intencion
    WHERE nombre IN ('CONTACTAR_DOCENTE', 'DISPONIBILIDAD_DOCENTE')
);

UPDATE chatbot_intencion SET activo = FALSE
WHERE nombre IN ('CONTACTAR_DOCENTE', 'DISPONIBILIDAD_DOCENTE');

-- 2. Desactivar intents documentales (respondidas vía RAG, no SetFit)
UPDATE chatbot_intencion SET activo = FALSE
WHERE nombre IN (
    'CONSULTAR_REGLAMENTO',
    'CONSULTAR_FAQ',
    'CONSULTAR_ASIGNATURA',
    'HORARIO_TUTORIAS'
);
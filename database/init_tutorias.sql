CREATE TABLE IF NOT EXISTS solicitudes_tutoria (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL,
    docente_id INTEGER,
    asignatura_id INTEGER,
    periodo_id INTEGER,
    tema VARCHAR(200) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'solicitada',
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_agendada TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo_cancelacion TEXT
);

CREATE TABLE IF NOT EXISTS bitacoras_atencion (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL,
    observaciones TEXT,
    asistio BOOLEAN,
    temas_detectados TEXT,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bitacora_solicitud
        FOREIGN KEY (solicitud_id)
        REFERENCES solicitudes_tutoria(id)
);

CREATE TABLE IF NOT EXISTS historial_estados (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30) NOT NULL,
    usuario_id VARCHAR(50),
    rol_usuario VARCHAR(30),
    fecha_cambio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    comentario TEXT,
    CONSTRAINT fk_historial_solicitud
        FOREIGN KEY (solicitud_id)
        REFERENCES solicitudes_tutoria(id)
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id SERIAL PRIMARY KEY,
    solicitud_id INTEGER,
    destinatario_id INTEGER NOT NULL,
    destinatario_rol VARCHAR(30) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_lectura TIMESTAMP,
    CONSTRAINT fk_notificacion_solicitud
        FOREIGN KEY (solicitud_id)
        REFERENCES solicitudes_tutoria(id)
);

CREATE TABLE IF NOT EXISTS auditoria_tutorias (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(50),
    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solicitudes_estudiante ON solicitudes_tutoria(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_docente ON solicitudes_tutoria(docente_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes_tutoria(estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_periodo ON solicitudes_tutoria(periodo_id);
CREATE INDEX IF NOT EXISTS idx_bitacoras_solicitud ON bitacoras_atencion(solicitud_id);
CREATE INDEX IF NOT EXISTS idx_historial_solicitud ON historial_estados(solicitud_id);
CREATE TABLE IF NOT EXISTS casos_academicos (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    severidad VARCHAR(30) NOT NULL DEFAULT 'media',
    estado VARCHAR(30) NOT NULL DEFAULT 'abierto',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notificaciones_destinatario ON notificaciones(destinatario_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_leida ON notificaciones(leida);
CREATE INDEX IF NOT EXISTS idx_casos_estudiante ON casos_academicos(estudiante_id);

-- ── Seed data ────────────────────────────────────────────────────────
-- Mapeo contra Administración (ids de sus tablas):
--   Periodos:   1=Periodo 2025-2026 (activo), 2=Periodo 2026-2027 (planificado)
--   Docentes:   1=Carlos Docente, 2=Carlos Mendoza López, 3=María González Ruiz,
--               4=José Martínez Vera, 5=Ana López Torres
--   Estudiantes: 1=Jeremías Prueba (carrera 1, periodo 1),
--                2=Luis Andrade (carrera 1, periodo 2), 3=Sofía Cárdenas (carrera 1, periodo 2),
--                4=Andrés Muñoz (carrera 2, periodo 2), 5=Camila Torres (carrera 2, periodo 2)
--   Asignaturas: 1=Introducción a la Programación (carrera 1, periodo 1),
--                2=Programación I (carrera 1, periodo 2), 3=Base de Datos (carrera 1, periodo 2),
--                4=Cálculo I (carrera 2, periodo 2), 7=Matemáticas Discretas (carrera 1, periodo 1),
--                8=Fundamentos de Computación (carrera 1, periodo 1),
--                12=Programación II (carrera 2, periodo 2), 13=Circuitos Digitales (carrera 2, periodo 2)

INSERT INTO solicitudes_tutoria (id, estudiante_id, docente_id, asignatura_id, periodo_id, tema, estado, fecha_solicitud, fecha_agendada, fecha_actualizacion, motivo_cancelacion)
VALUES
(1, 1, NULL,  1, 1, 'Estructuras de control',              'solicitada',  '2026-07-01 09:00:00', NULL,                        '2026-07-01 09:00:00', NULL),
(2, 2, 2,     2, 2, 'Modelo entidad-relación',             'asignada',    '2026-07-02 10:30:00', '2026-07-10 14:00:00',     '2026-07-02 11:00:00', NULL),
(3, 3, 3,     3, 2, 'Límites y derivadas',                 'confirmada',  '2026-07-03 08:00:00', '2026-07-12 09:00:00',     '2026-07-04 09:00:00', NULL),
(4, 1, 1,     7, 1, 'Programación orientada a objetos',    'atendida',    '2026-06-15 14:00:00', '2026-06-20 10:00:00',     '2026-06-20 11:30:00', NULL),
(5, 4, NULL,  4, 2, 'Arreglos y matrices',                 'cancelada',   '2026-07-05 16:00:00', NULL,                        '2026-07-06 10:00:00', 'Problemas personales del estudiante'),
(6, 5, 2,     12, 2, 'SQL avanzado',                       'no_asistida', '2026-06-25 11:00:00', '2026-07-01 08:00:00',     '2026-07-01 09:00:00', NULL),
(7, 4, NULL,  13, 2, 'Derivadas parciales',                'solicitada',  '2026-07-07 13:00:00', NULL,                        '2026-07-07 13:00:00', NULL),
(8, 3, 1,     2, 2, 'Normalización de bases de datos',     'atendida',    '2026-04-10 09:30:00', '2026-04-15 11:00:00',     '2026-04-15 12:00:00', NULL),
(9, 2, 3,     3, 2, 'Integrales indefinidas',              'asignada',    '2026-07-08 15:00:00', '2026-07-18 10:00:00',     '2026-07-08 16:00:00', NULL),
(10, 5, NULL, 4, 2, 'Funciones y procedimientos',          'solicitada',  '2026-07-09 07:30:00', NULL,                        '2026-07-09 07:30:00', NULL),
(11, 1, 1,    8, 1, 'Manejo de archivos',                  'atendida',    '2026-05-05 10:00:00', '2026-05-10 09:00:00',     '2026-05-10 10:30:00', NULL),
(12, 4, 2,    12, 2, 'Consultas SQL complejas',             'confirmada',  '2026-07-06 12:00:00', '2026-07-16 14:00:00',     '2026-07-07 10:00:00', NULL);
SELECT setval('solicitudes_tutoria_id_seq', (SELECT MAX(id) FROM solicitudes_tutoria));

INSERT INTO historial_estados (solicitud_id, estado_anterior, estado_nuevo, usuario_id, rol_usuario, fecha_cambio, comentario)
VALUES
(1, NULL,         'solicitada', '1', 'estudiante',  '2026-07-01 09:00:00', NULL),
(2, NULL,         'solicitada', '2', 'estudiante',  '2026-07-02 10:30:00', NULL),
(2, 'solicitada', 'asignada',   '99', 'coordinador', '2026-07-02 11:00:00', 'Asignada a Carlos Mendoza López'),
(3, NULL,         'solicitada', '3', 'estudiante',  '2026-07-03 08:00:00', NULL),
(3, 'solicitada', 'asignada',   '99', 'coordinador', '2026-07-03 09:00:00', 'Asignada a María González Ruiz'),
(3, 'asignada',   'confirmada', '3', 'estudiante',  '2026-07-04 09:00:00', 'Confirmo mi asistencia'),
(4, NULL,         'solicitada', '1', 'estudiante',  '2026-06-15 14:00:00', NULL),
(4, 'solicitada', 'asignada',   '99', 'coordinador', '2026-06-16 09:00:00', 'Asignada a Carlos Docente'),
(4, 'asignada',   'confirmada', '1', 'estudiante',  '2026-06-17 10:00:00', NULL),
(4, 'confirmada', 'atendida',   '1', 'docente',     '2026-06-20 11:30:00', 'Estudiante atendido, buen desempeño'),
(5, NULL,         'solicitada', '4', 'estudiante',  '2026-07-05 16:00:00', NULL),
(5, 'solicitada', 'cancelada',  '4', 'estudiante',  '2026-07-06 10:00:00', 'Problemas personales del estudiante'),
(6, NULL,         'solicitada', '5', 'estudiante',  '2026-06-25 11:00:00', NULL),
(6, 'solicitada', 'asignada',   '99', 'coordinador', '2026-06-26 08:00:00', 'Asignada a Carlos Mendoza López'),
(6, 'asignada',   'no_asistida','1', 'docente',     '2026-07-01 09:00:00', 'Estudiante no se presentó a la tutoría'),
(7, NULL,         'solicitada', '4', 'estudiante',  '2026-07-07 13:00:00', NULL),
(8, NULL,         'solicitada', '3', 'estudiante',  '2026-04-10 09:30:00', NULL),
(8, 'solicitada', 'asignada',   '99', 'coordinador', '2026-04-11 10:00:00', 'Asignada a Carlos Docente'),
(8, 'asignada',   'confirmada', '3', 'estudiante',  '2026-04-12 11:00:00', NULL),
(8, 'confirmada', 'atendida',   '1', 'docente',     '2026-04-15 12:00:00', 'Tutoría completada'),
(9, NULL,         'solicitada', '2', 'estudiante',  '2026-07-08 15:00:00', NULL),
(9, 'solicitada', 'asignada',   '99', 'coordinador', '2026-07-08 16:00:00', 'Asignada a María González Ruiz'),
(10, NULL,        'solicitada', '5', 'estudiante',  '2026-07-09 07:30:00', NULL),
(11, NULL,        'solicitada', '1', 'estudiante',  '2026-05-05 10:00:00', NULL),
(11, 'solicitada','asignada',   '99', 'coordinador','2026-05-06 09:00:00', 'Asignada a Carlos Docente'),
(11, 'asignada',  'confirmada', '1', 'estudiante',  '2026-05-07 10:00:00', NULL),
(11, 'confirmada','atendida',   '1', 'docente',     '2026-05-10 10:30:00', 'Tutoría completada satisfactoriamente'),
(12, NULL,        'solicitada', '4', 'estudiante',  '2026-07-06 12:00:00', NULL),
(12, 'solicitada','asignada',   '99', 'coordinador','2026-07-06 14:00:00', 'Asignada a Carlos Mendoza López'),
(12, 'asignada',  'confirmada', '4', 'estudiante',  '2026-07-07 10:00:00', 'Confirmada por el estudiante');
SELECT setval('historial_estados_id_seq', (SELECT MAX(id) FROM historial_estados));

INSERT INTO bitacoras_atencion (solicitud_id, observaciones, asistio, temas_detectados, fecha_registro)
VALUES
(4,  'Se revisaron conceptos de POO: clases, herencia y polimorfismo. El estudiante implementó ejemplos correctamente.',  TRUE,  'Clases, herencia, polimorfismo, encapsulamiento',  '2026-06-20 11:30:00'),
(6,  'El estudiante no asistió a la tutoría programada. Se esperó 15 minutos.',                                          FALSE, NULL,                                                 '2026-07-01 09:00:00'),
(8,  'Se explicó el proceso de normalización hasta 3FN. El estudiante resolvió ejercicios de forma correcta.',           TRUE,  '1FN, 2FN, 3FN, dependencias funcionales',            '2026-04-15 12:00:00'),
(11, 'Se trabajó lectura y escritura de archivos en Python. Buen progreso del estudiante.',                              TRUE,  'Archivos, serialización, excepciones',               '2026-05-10 10:30:00');
SELECT setval('bitacoras_atencion_id_seq', (SELECT MAX(id) FROM bitacoras_atencion));

INSERT INTO notificaciones (solicitud_id, destinatario_id, destinatario_rol, tipo, mensaje, leida, fecha_creacion, fecha_lectura)
VALUES
(2, 2, 'docente',    'asignacion',   'Se te ha asignado la tutoría #2',                    TRUE,  '2026-07-02 11:00:00', '2026-07-02 11:30:00'),
(3, 3, 'docente',    'asignacion',   'Se te ha asignado la tutoría #3',                    TRUE,  '2026-07-03 09:00:00', '2026-07-03 09:15:00'),
(3, 3, 'estudiante', 'cambio_estado','Tu tutoría #3 ha sido confirmada',                    TRUE,  '2026-07-04 09:00:00', '2026-07-04 09:05:00'),
(4, 1, 'docente',    'asignacion',   'Se te ha asignado la tutoría #4',                    TRUE,  '2026-06-16 09:00:00', '2026-06-16 09:10:00'),
(5, 4, 'estudiante', 'cambio_estado','Tu tutoría #5 ha sido cancelada',                    TRUE,  '2026-07-06 10:00:00', '2026-07-06 10:01:00'),
(6, 2, 'docente',    'asignacion',   'Se te ha asignado la tutoría #6',                    TRUE,  '2026-06-26 08:00:00', '2026-06-26 08:30:00'),
(8, 1, 'docente',    'asignacion',   'Se te ha asignado la tutoría #8',                    TRUE,  '2026-04-11 10:00:00', '2026-04-11 10:05:00'),
(9, 3, 'docente',    'asignacion',   'Se te ha asignado la tutoría #9',                    FALSE, '2026-07-08 16:00:00', NULL),
(11, 1, 'docente',   'asignacion',   'Se te ha asignado la tutoría #11',                   TRUE,  '2026-05-06 09:00:00', '2026-05-06 09:20:00'),
(12, 2, 'docente',   'asignacion',   'Se te ha asignado la tutoría #12',                   FALSE, '2026-07-06 14:00:00', NULL),
(12, 4, 'estudiante','cambio_estado','Tu tutoría #12 ha sido confirmada',                  FALSE, '2026-07-07 10:00:00', NULL);
SELECT setval('notificaciones_id_seq', (SELECT MAX(id) FROM notificaciones));

INSERT INTO auditoria_tutorias (usuario_id, accion, modulo, descripcion, fecha)
VALUES
('1',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 1 (Jeremías Prueba)',  '2026-07-01 09:00:00'),
('2',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 2 (Luis Andrade)',      '2026-07-02 10:30:00'),
('99', 'ASIGNAR_TUTORIA',   'TUTORIAS', 'Tutoría 2 asignada a docente 2 (Carlos Mendoza)',                  '2026-07-02 11:00:00'),
('3',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 3 (Sofía Cárdenas)',   '2026-07-03 08:00:00'),
('99', 'ASIGNAR_TUTORIA',   'TUTORIAS', 'Tutoría 3 asignada a docente 3 (María González)',                  '2026-07-03 09:00:00'),
('3',  'CONFIRMAR_TUTORIA', 'TUTORIAS', 'Tutoría 3 confirmada',                                              '2026-07-04 09:00:00'),
('1',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 1 (Jeremías Prueba)',  '2026-06-15 14:00:00'),
('99', 'ASIGNAR_TUTORIA',   'TUTORIAS', 'Tutoría 4 asignada a docente 1 (Carlos Docente)',                  '2026-06-16 09:00:00'),
('1',  'REGISTRAR_ASISTENCIA','TUTORIAS','Asistencia de tutoría 4: asistió',                                '2026-06-20 11:30:00'),
('4',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 4 (Andrés Muñoz)',     '2026-07-05 16:00:00'),
('4',  'CANCELAR_TUTORIA',  'TUTORIAS', 'Tutoría 5 cancelada',                                              '2026-07-06 10:00:00'),
('5',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 5 (Camila Torres)',    '2026-06-25 11:00:00'),
('4',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 4 (Andrés Muñoz)',     '2026-07-07 13:00:00'),
('3',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 3 (Sofía Cárdenas)',   '2026-04-10 09:30:00'),
('2',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 2 (Luis Andrade)',      '2026-07-08 15:00:00'),
('99', 'ASIGNAR_TUTORIA',   'TUTORIAS', 'Tutoría 9 asignada a docente 3 (María González)',                  '2026-07-08 16:00:00'),
('5',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 5 (Camila Torres)',    '2026-07-09 07:30:00'),
('1',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 1 (Jeremías Prueba)',  '2026-05-05 10:00:00'),
('4',  'CREAR_SOLICITUD',   'TUTORIAS', 'Solicitud de tutoría creada por estudiante 4 (Andrés Muñoz)',     '2026-07-06 12:00:00');
SELECT setval('auditoria_tutorias_id_seq', (SELECT MAX(id) FROM auditoria_tutorias));

INSERT INTO casos_academicos (estudiante_id, descripcion, severidad, estado, fecha_creacion)
VALUES
(5, 'Bajo rendimiento sostenido en Programación I. Promedio por debajo de 10.',                                        'alta',  'abierto', '2026-07-01 10:00:00'),
(1, 'Dificultad recurrente con conceptos de programación orientada a objetos. Requiere refuerzo adicional.',             'media', 'abierto', '2026-05-20 14:00:00'),
(4, 'Inasistencia frecuente a tutorías programadas. Se recomienda seguimiento por parte de bienestar estudiantil.',      'media', 'abierto', '2026-07-07 14:00:00'),
(2, 'Excelente desempeño académico en Base de Datos. Participación activa en clase. Sin novedades.',                     'baja',  'cerrado', '2026-06-30 16:00:00'),
(3, 'Problemas de comprensión de conceptos matemáticos avanzados en Cálculo I. Derivado a apoyo académico.',            'alta',  'abierto', '2026-04-20 11:00:00');
SELECT setval('casos_academicos_id_seq', (SELECT MAX(id) FROM casos_academicos));

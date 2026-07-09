CREATE TABLE IF NOT EXISTS facultades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(20) UNIQUE,
    descripcion VARCHAR(255),
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS carreras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(20) UNIQUE,
    modalidad VARCHAR(50) NOT NULL,
    facultad_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_facultad
        FOREIGN KEY (facultad_id)
        REFERENCES facultades(id)
);

CREATE TABLE IF NOT EXISTS periodos_academicos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha_inicio VARCHAR(20) NOT NULL,
    fecha_fin VARCHAR(20) NOT NULL,
    estado_periodo VARCHAR(20) DEFAULT 'planificado',
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asignaturas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(20) UNIQUE,
    creditos INTEGER NOT NULL,
    nivel VARCHAR(50),
    carrera_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrera_asignatura
        FOREIGN KEY (carrera_id)
        REFERENCES carreras(id),
    CONSTRAINT fk_periodo_asignatura
        FOREIGN KEY (periodo_id)
        REFERENCES periodos_academicos(id)
);

CREATE TABLE IF NOT EXISTS docentes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    especialidad VARCHAR(120),
    facultad_id INTEGER NOT NULL,
    carga_horaria_maxima INTEGER DEFAULT 40,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_facultad_docente
        FOREIGN KEY (facultad_id)
        REFERENCES facultades(id)
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    matricula VARCHAR(30) UNIQUE,
    carrera_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    estado_academico VARCHAR(30) DEFAULT 'activo',
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrera_estudiante
        FOREIGN KEY (carrera_id)
        REFERENCES carreras(id),
    CONSTRAINT fk_periodo_estudiante
        FOREIGN KEY (periodo_id)
        REFERENCES periodos_academicos(id)
);

CREATE TABLE IF NOT EXISTS paralelos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    carrera_id INTEGER NOT NULL,
    asignatura_id INTEGER NOT NULL,
    docente_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_paralelo_carrera
        FOREIGN KEY (carrera_id)
        REFERENCES carreras(id),
    CONSTRAINT fk_paralelo_asignatura
        FOREIGN KEY (asignatura_id)
        REFERENCES asignaturas(id),
    CONSTRAINT fk_paralelo_docente
        FOREIGN KEY (docente_id)
        REFERENCES docentes(id),
    CONSTRAINT fk_paralelo_periodo
        FOREIGN KEY (periodo_id)
        REFERENCES periodos_academicos(id)
);

CREATE TABLE IF NOT EXISTS horarios_atencion (
    id SERIAL PRIMARY KEY,
    docente_id INTEGER NOT NULL,
    dia VARCHAR(20) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_docente_horario
        FOREIGN KEY (docente_id)
        REFERENCES docentes(id)
);

CREATE TABLE IF NOT EXISTS auditoria_administracion (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(50),
    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Seed data ────────────────────────────────────────────────────────

INSERT INTO facultades (nombre, codigo, descripcion)
VALUES ('Facultad de Ciencias Matemáticas y Físicas', 'FCMF', 'Facultad principal de ejemplo')
ON CONFLICT DO NOTHING;

INSERT INTO facultades (nombre, codigo, descripcion)
VALUES ('Facultad de Ingeniería', 'FI', 'Facultad de Ingeniería')
ON CONFLICT DO NOTHING;

INSERT INTO facultades (nombre, codigo, descripcion)
VALUES ('Facultad de Ciencias Empresariales', 'FCE', 'Facultad de Ciencias Empresariales')
ON CONFLICT DO NOTHING;

INSERT INTO facultades (nombre, codigo, descripcion)
VALUES ('Facultad de Ciencias de la Salud', 'FCS', 'Facultad de Ciencias de la Salud')
ON CONFLICT DO NOTHING;

INSERT INTO periodos_academicos (nombre, fecha_inicio, fecha_fin, estado_periodo, estado)
VALUES ('Periodo 2025-2026', '2025-09-01', '2026-07-31', 'activo', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO periodos_academicos (nombre, fecha_inicio, fecha_fin, estado_periodo, estado)
VALUES ('Periodo 2026-2027', '2026-05-01', '2027-02-28', 'planificado', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO carreras (nombre, codigo, modalidad, facultad_id)
VALUES ('Ingeniería de Software', 'IS', 'presencial', 1)
ON CONFLICT DO NOTHING;

INSERT INTO carreras (nombre, codigo, modalidad, facultad_id)
VALUES ('Ingeniería en Sistemas', 'INS', 'Presencial', 2)
ON CONFLICT DO NOTHING;

INSERT INTO carreras (nombre, codigo, modalidad, facultad_id)
VALUES ('Ingeniería Civil', 'IC', 'Presencial', 2)
ON CONFLICT DO NOTHING;

INSERT INTO carreras (nombre, codigo, modalidad, facultad_id)
VALUES ('Administración de Empresas', 'ADE', 'Presencial', 4)
ON CONFLICT DO NOTHING;

INSERT INTO carreras (nombre, codigo, modalidad, facultad_id)
VALUES ('Contabilidad y Auditoría', 'CA', 'Presencial', 4)
ON CONFLICT DO NOTHING;

INSERT INTO docentes (nombres, apellidos, correo, especialidad, facultad_id)
VALUES ('Carlos', 'Docente', 'carlos@test.com', 'Tutorías', 1)
ON CONFLICT DO NOTHING;

INSERT INTO docentes (nombres, apellidos, correo, telefono, especialidad, facultad_id)
VALUES ('Carlos', 'Mendoza López', 'carlos.mendoza@universidad.edu.ec', '0991234567', 'Desarrollo de Software', 2)
ON CONFLICT DO NOTHING;

INSERT INTO docentes (nombres, apellidos, correo, telefono, especialidad, facultad_id)
VALUES ('María', 'González Ruiz', 'maria.gonzalez@universidad.edu.ec', '0992345678', 'Estructuras', 2)
ON CONFLICT DO NOTHING;

INSERT INTO docentes (nombres, apellidos, correo, telefono, especialidad, facultad_id)
VALUES ('José', 'Martínez Vera', 'jose.martinez@universidad.edu.ec', '0993456789', 'Gestión Empresarial', 4)
ON CONFLICT DO NOTHING;

INSERT INTO docentes (nombres, apellidos, correo, telefono, especialidad, facultad_id)
VALUES ('Ana', 'López Torres', 'ana.lopez@universidad.edu.ec', '0994567890', 'Auditoría Financiera', 4)
ON CONFLICT DO NOTHING;

INSERT INTO asignaturas (id, nombre, codigo, creditos, nivel, carrera_id, periodo_id) VALUES
    (1,  'Introducción a la Programación', 'INTRO1', 4, 'Primero', 1, 1),
    (2,  'Programación I',                 'PROG1',  5, 'Primero', 1, 2),
    (3,  'Base de Datos',                  'BD1',    4, 'Segundo', 1, 2),
    (4,  'Cálculo I',                      'CAL1',   5, 'Primero', 2, 2),
    (5,  'Marketing',                      'MKT1',   4, 'Tercero', 4, 2),
    (6,  'Contabilidad General',           'CONT1',  5, 'Primero', 5, 2),
    (7,  'Matemáticas Discretas',          'MD1',    4, 'Primero', 1, 1),
    (8,  'Fundamentos de Computación',     'FC1',    3, 'Primero', 1, 1),
    (9,  'Estructuras de Datos',           'ED1',    4, 'Segundo', 1, 2),
    (10, 'Álgebra Lineal',                 'AL1',    4, 'Primero', 2, 1),
    (11, 'Física I',                       'FI1',    4, 'Primero', 2, 1),
    (12, 'Programación II',                'PROG2',  4, 'Segundo', 2, 2),
    (13, 'Circuitos Digitales',            'CD1',    4, 'Segundo', 2, 2),
    (14, 'Estática',                       'EST1',   4, 'Segundo', 3, 2),
    (15, 'Materiales de Construcción',     'MC1',    3, 'Segundo', 3, 2),
    (16, 'Gestión de Recursos Humanos',    'RRHH1',  3, 'Tercero', 4, 2),
    (17, 'Economía I',                     'ECO1',   3, 'Primero', 4, 1),
    (18, 'Auditoría I',                    'AUD1',   4, 'Tercero', 5, 2),
    (19, 'Matemáticas Financieras',        'MF1',    3, 'Primero', 5, 1)
ON CONFLICT (codigo) DO UPDATE SET
    nombre = EXCLUDED.nombre, creditos = EXCLUDED.creditos,
    nivel = EXCLUDED.nivel, carrera_id = EXCLUDED.carrera_id,
    periodo_id = EXCLUDED.periodo_id;
SELECT setval('asignaturas_id_seq', (SELECT MAX(id) FROM asignaturas));

INSERT INTO paralelos (nombre, carrera_id, asignatura_id, docente_id, periodo_id) VALUES
    ('A', 1, 1,  2, 2),
    ('B', 1, 2,  3, 2),
    ('A', 2, 4,  2, 2),
    ('A', 3, 14, 4, 2),
    ('A', 4, 5,  5, 2),
    ('B', 2, 11, 2, 1),
    ('A', 1, 9,  3, 2),
    ('A', 5, 18, 5, 2),
    ('A', 2, 10, 2, 1),
    ('B', 1, 8,  1, 1),
    ('A', 2, 12, 2, 2),
    ('A', 1, 7,  1, 1),
    ('A', 4, 16, 4, 2),
    ('B', 2, 13, 3, 2),
    ('A', 3, 15, 3, 2),
    ('A', 5, 19, 5, 1),
    ('A', 4, 17, 4, 1)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Jeremías', 'Prueba', 'jeremias@test.com', 'MAT001', 1, 1)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Luis', 'Andrade Jiménez', 'luis.andrade@universidad.edu.ec', '2025001', 1, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Sofía', 'Cárdenas Paz', 'sofia.cardenas@universidad.edu.ec', '2025002', 1, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Andrés', 'Muñoz Rivera', 'andres.munoz@universidad.edu.ec', '2025003', 2, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Camila', 'Torres Medina', 'camila.torres@universidad.edu.ec', '2025004', 2, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Diego', 'Herrera Silva', 'diego.herrera@universidad.edu.ec', '2025005', 3, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Valentina', 'Ortiz Castro', 'valentina.ortiz@universidad.edu.ec', '2025006', 3, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Gabriel', 'Flores Vargas', 'gabriel.flores@universidad.edu.ec', '2025007', 4, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Isabella', 'Reyes Suárez', 'isabella.reyes@universidad.edu.ec', '2025008', 4, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Mateo', 'Castillo Núñez', 'mateo.castillo@universidad.edu.ec', '2025009', 5, 2)
ON CONFLICT DO NOTHING;

INSERT INTO estudiantes (nombres, apellidos, correo, matricula, carrera_id, periodo_id)
VALUES ('Gabriela', 'Romero Vera', 'gabriela.romero@universidad.edu.ec', '2025010', 5, 2)
ON CONFLICT DO NOTHING;

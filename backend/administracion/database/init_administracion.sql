CREATE TABLE IF NOT EXISTS facultades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),
    estado BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS carreras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(20),
    facultad_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_facultad
        FOREIGN KEY (facultad_id)
        REFERENCES facultades(id)
);

CREATE TABLE IF NOT EXISTS asignaturas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(20),
    creditos INTEGER NOT NULL,
    carrera_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_carrera_asignatura
        FOREIGN KEY (carrera_id)
        REFERENCES carreras(id)
);

CREATE TABLE IF NOT EXISTS periodos_academicos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha_inicio VARCHAR(20) NOT NULL,
    fecha_fin VARCHAR(20) NOT NULL,
    estado BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS docentes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(120) NOT NULL,
    telefono VARCHAR(20),
    especialidad VARCHAR(120),
    estado BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(120) NOT NULL,
    matricula VARCHAR(30),
    carrera_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_carrera_estudiante
        FOREIGN KEY (carrera_id)
        REFERENCES carreras(id)
);

CREATE TABLE IF NOT EXISTS paralelos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    carrera_id INTEGER NOT NULL,
    asignatura_id INTEGER NOT NULL,
    docente_id INTEGER NOT NULL,
    periodo_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
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
    dia VARCHAR(20) NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    paralelo_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_paralelo_horario
        FOREIGN KEY (paralelo_id)
        REFERENCES paralelos(id)
);

CREATE TABLE IF NOT EXISTS auditoria_administracion (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(50),
    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO facultades (nombre, descripcion)
VALUES ('Facultad de Ciencias Matemáticas y Físicas', 'Facultad principal de ejemplo')
ON CONFLICT DO NOTHING;
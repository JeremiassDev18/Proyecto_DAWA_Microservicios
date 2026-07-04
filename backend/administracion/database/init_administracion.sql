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

INSERT INTO facultades (nombre, codigo, descripcion)
VALUES ('Facultad de Ciencias Matemáticas y Físicas', 'FCMF', 'Facultad principal de ejemplo')
ON CONFLICT DO NOTHING;
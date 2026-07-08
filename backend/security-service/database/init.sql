-- SeguridadDB: esquema base para el microservicio de seguridad

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS permisos (
    id SERIAL PRIMARY KEY,
    nombre_permiso VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuarios_roles (
    usuario_id INTEGER NOT NULL,
    rol_id INTEGER NOT NULL,
    asignado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (usuario_id, rol_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS roles_permisos (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL,
    asignado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permiso_id) REFERENCES permisos (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS auditoria (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    direccion_ip VARCHAR(45),
    detalles JSONB DEFAULT '{}'::jsonb,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    utilizado BOOLEAN NOT NULL DEFAULT FALSE,
    utilizado_en TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR(255) NOT NULL UNIQUE,
    usuario_id INTEGER,
    bloqueado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    razon VARCHAR(255),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);

-- Index for efficient token blacklist lookups
CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti ON token_blacklist(token_jti);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expira ON token_blacklist(expira_en);

-- Sessions table to persist issued tokens (JTIs) for session management
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR(255) NOT NULL UNIQUE,
    usuario_id INTEGER NOT NULL,
    user_agent TEXT,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    revocado BOOLEAN NOT NULL DEFAULT FALSE,
    revocado_en TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expira_en TIMESTAMP WITH TIME ZONE NOT NULL,
    revocado BOOLEAN NOT NULL DEFAULT FALSE,
    revocado_en TIMESTAMP WITH TIME ZONE,
    razon VARCHAR(255),
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expira ON refresh_tokens(expira_en);

CREATE INDEX IF NOT EXISTS idx_sessions_usuario_id ON sessions(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expira_en ON sessions(expira_en);

INSERT INTO roles (nombre_rol, descripcion)
VALUES
    ('admin', 'Administrador del sistema'),
    ('manager', 'Gestor de operaciones'),
    ('viewer', 'Usuario con permisos de lectura')
ON CONFLICT (nombre_rol) DO NOTHING;

INSERT INTO permisos (nombre_permiso, descripcion)
VALUES
    ('read_users', 'Permiso para leer usuarios'),
    ('write_users', 'Permiso para crear o editar usuarios'),
    ('read_reports', 'Permiso para leer reportes')
ON CONFLICT (nombre_permiso) DO NOTHING;

INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r
JOIN permisos p ON p.nombre_permiso = 'read_users'
WHERE r.nombre_rol = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO roles_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r
JOIN permisos p ON p.nombre_permiso = 'read_reports'
WHERE r.nombre_rol IN ('admin', 'manager', 'viewer')
ON CONFLICT DO NOTHING;

-- Roles del dominio académico
INSERT INTO roles (nombre_rol, descripcion)
VALUES
    ('estudiante', 'Estudiante — puede solicitar tutorías, ver su historial'),
    ('profesor',   'Profesor / tutor — puede atender tutorías, ver bitácoras')
ON CONFLICT (nombre_rol) DO NOTHING;

-- Usuarios semilla (passwords hasheadas con Argon2 — mismo algoritmo que auth.py)
INSERT INTO usuarios (email, password_hash, nombre)
VALUES
    ('admin@sistema.com',  '$argon2id$v=19$m=65536,t=3,p=4$jandSQ0pGTLCWyLQv2+WlA$KIPMWE8F5wSBEmjrMPHr6LQIFqDI2aBonEB+lof3m8Q', 'Admin Sistema'),
    ('jeremias@test.com',  '$argon2id$v=19$m=65536,t=3,p=4$PE2E+C8J7t0c6tk+UYuY2g$Hr0Tvr07HyBEae3m2oyHOkIT5F6LsG3hi4FzOhZ4RSk', 'Jeremías Prueba'),
    ('profesor@test.com',  '$argon2id$v=19$m=65536,t=3,p=4$ypCpKdHuhcrQBWm/28SW9A$yDB3KsJ7r8/RofDJiEHI3Q4MgoNipUcmpP1eHk9bI4E', 'Profesor Prueba')
ON CONFLICT (email) DO NOTHING;

-- Asignar roles a los usuarios semilla
INSERT INTO usuarios_roles (usuario_id, rol_id)
SELECT u.id, r.id FROM usuarios u, roles r
WHERE u.email = 'admin@sistema.com' AND r.nombre_rol = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO usuarios_roles (usuario_id, rol_id)
SELECT u.id, r.id FROM usuarios u, roles r
WHERE u.email = 'admin@sistema.com' AND r.nombre_rol = 'profesor'
ON CONFLICT DO NOTHING;

INSERT INTO usuarios_roles (usuario_id, rol_id)
SELECT u.id, r.id FROM usuarios u, roles r
WHERE u.email = 'jeremias@test.com' AND r.nombre_rol = 'estudiante'
ON CONFLICT DO NOTHING;

INSERT INTO usuarios_roles (usuario_id, rol_id)
SELECT u.id, r.id FROM usuarios u, roles r
WHERE u.email = 'profesor@test.com' AND r.nombre_rol = 'profesor'
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS restaurantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    restaurante_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_restaurante
        FOREIGN KEY (restaurante_id)
        REFERENCES restaurantes(id)
);

CREATE TABLE IF NOT EXISTS mesas (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL,
    capacidad INTEGER NOT NULL,
    ubicacion VARCHAR(50),
    sucursal_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_sucursal_mesa
        FOREIGN KEY (sucursal_id)
        REFERENCES sucursales(id)
);

CREATE TABLE IF NOT EXISTS horarios_atencion (
    id SERIAL PRIMARY KEY,
    dia VARCHAR(20) NOT NULL,
    hora_apertura TIME NOT NULL,
    hora_cierre TIME NOT NULL,
    sucursal_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_sucursal_horario
        FOREIGN KEY (sucursal_id)
        REFERENCES sucursales(id)
);

CREATE TABLE IF NOT EXISTS promociones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    descuento NUMERIC(5,2) NOT NULL,
    sucursal_id INTEGER NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_sucursal_promocion
        FOREIGN KEY (sucursal_id)
        REFERENCES sucursales(id)
);

CREATE TABLE IF NOT EXISTS auditoria_administracion (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(50),
    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO restaurantes (nombre, descripcion)
VALUES 
('XYZ Restaurant', 'Restaurante principal del sistema')
ON CONFLICT DO NOTHING;
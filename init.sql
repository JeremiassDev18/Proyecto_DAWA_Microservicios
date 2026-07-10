-- ============================================================
-- TutorBot AI — Base de Datos del Agente LLM
-- Motor: PostgreSQL 16 + pgvector + pg_trgm
-- Puerto BD: 5435
--
-- NOTA: SetFit fue eliminado. Este esquema mantiene solo lo
-- necesario para el agente conversacional basado en Qwen/Ollama:
-- conversaciones, mensajes, feedback, pendientes, RAG y memoria.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. CONVERSACIONES Y MENSAJES
-- ============================================================

CREATE TABLE IF NOT EXISTS chatbot_conversacion (
    id              SERIAL PRIMARY KEY,
    id_usuario      INT,
    nombre_cliente  VARCHAR(150),
    iniciado_en     TIMESTAMP DEFAULT NOW(),
    finalizado_en   TIMESTAMP,
    activa          BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS chatbot_mensaje (
    id                  SERIAL PRIMARY KEY,
    id_conversacion     INT REFERENCES chatbot_conversacion(id),
    rol                 VARCHAR(10) CHECK (rol IN ('usuario', 'bot')),
    contenido           TEXT NOT NULL,
    tipo_resolucion     VARCHAR(20) CHECK (tipo_resolucion IN ('estatica', 'dinamica', 'logica', 'sin_respuesta', 'saludo', 'hibrida', 'agente')),
    respondido_por_ia   BOOLEAN DEFAULT FALSE,
    score_similitud     NUMERIC(5,4),
    id_intencion        INT,
    confianza_ml        NUMERIC(5,2),
    modelo_usado        VARCHAR(30),
    enviado_en          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. FEEDBACK DEL USUARIO
-- ============================================================

CREATE TABLE IF NOT EXISTS chatbot_feedback (
    id          SERIAL PRIMARY KEY,
    id_mensaje  INT REFERENCES chatbot_mensaje(id),
    fue_util    BOOLEAN,
    comentario  TEXT,
    creado_en   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. PREGUNTAS PENDIENTES
-- ============================================================

CREATE TABLE IF NOT EXISTS chatbot_pregunta_pendiente (
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
-- 4. CENTRO DE CONOCIMIENTO (Agentic RAG)
-- ============================================================

CREATE TABLE IF NOT EXISTS centro_conocimiento (
    id                  SERIAL PRIMARY KEY,
    titulo              VARCHAR(255) NOT NULL,
    contenido           TEXT NOT NULL,
    embedding           VECTOR(384),
    tags                TEXT[] DEFAULT '{}',
    activo              BOOLEAN DEFAULT TRUE,
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conocimiento_trgm ON centro_conocimiento USING GIN (contenido gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_conocimiento_vector ON centro_conocimiento USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- ============================================================
-- 5. MEMORIA DEL AGENTE LLM
-- ============================================================

CREATE TABLE IF NOT EXISTS agente_memoria (
    id_conversacion INT PRIMARY KEY REFERENCES chatbot_conversacion(id),
    contexto        JSONB NOT NULL DEFAULT '{}',
    resumen         TEXT,
    total_mensajes  INT DEFAULT 0,
    actualizado_en  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5.1 RESÚMENES DE BITÁCORAS (Gap 5: worker RabbitMQ)
-- ============================================================

CREATE TABLE IF NOT EXISTS bitacora_resumen (
    id              SERIAL PRIMARY KEY,
    solicitud_id    INT NOT NULL,
    estudiante_id   INT NOT NULL,
    observaciones   TEXT,
    resumen         TEXT NOT NULL,
    temas_detectados TEXT,
    generado_en     TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bitacora_resumen_estudiante ON bitacora_resumen(estudiante_id);
CREATE INDEX IF NOT EXISTS idx_bitacora_resumen_solicitud ON bitacora_resumen(solicitud_id);

CREATE TABLE IF NOT EXISTS worker_evento_procesado (
    evento_id       VARCHAR(255) PRIMARY KEY,
    tipo_evento     VARCHAR(100) NOT NULL,
    datos           JSONB,
    procesado_en    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 6. DATOS INICIALES RAG
-- ============================================================

INSERT INTO centro_conocimiento (titulo, contenido, tags) VALUES
('Reglamento de Tutorías',
 'Las tutorías son gratuitas, tienen duración de 60 minutos y se pueden cancelar con 24 horas de anticipación.',
 ARRAY['tutorías', 'reglamento']),
('Política de Cancelación',
 'Las cancelaciones con menos de 24 horas serán registradas como falta justificada solo si se presenta certificado médico.',
 ARRAY['tutorías', 'cancelación', 'reglamento']),
('Preguntas Frecuentes',
 '¿Cómo solicito una tutoría? Ingresa al sistema y selecciona "Solicitar Tutoría". ¿Cuántas tutorías puedo tener? Máximo 3 por semana.',
 ARRAY['tutorías', 'faq']),
('Manual del Estudiante',
 'El estudiante debe inscribirse en el portal para acceder a las tutorías. Las sesiones se registran en bitácora.',
 ARRAY['tutorías', 'manual', 'estudiante'])
ON CONFLICT DO NOTHING;

-- ============================================================
-- 7. FUNCIONES AUXILIARES
-- ============================================================

CREATE OR REPLACE FUNCTION buscar_conocimiento_hibrido(
    p_texto     TEXT,
    p_vector    VECTOR(384),
    p_candidatos INT DEFAULT 20,
    p_w_vector  FLOAT DEFAULT 0.80,
    p_w_trgm    FLOAT DEFAULT 0.20
)
RETURNS TABLE (
    id          INT,
    titulo      TEXT,
    contenido   TEXT,
    score       FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ck.id,
        ck.titulo,
        ck.contenido,
        (
            (1 - (ck.embedding <=> p_vector)) * p_w_vector
            + similarity(ck.contenido, p_texto) * p_w_trgm
        )::FLOAT AS score
    FROM centro_conocimiento ck
    WHERE ck.activo = TRUE
      AND ck.embedding IS NOT NULL
    ORDER BY score DESC
    LIMIT p_candidatos;
END;
$$ LANGUAGE plpgsql;

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

-- ============================================================
-- 8. VISTAS ÚTILES
-- ============================================================

CREATE OR REPLACE VIEW v_pendientes_con_embedding AS
SELECT id, contenido, veces_repetida, creado_en
FROM chatbot_pregunta_pendiente
WHERE resuelta = FALSE AND embedding IS NOT NULL
ORDER BY veces_repetida DESC;

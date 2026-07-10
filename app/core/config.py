from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5435
    DB_NAME: str = "chatbotdb"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin123"

    # URLs microservicios HTTP
    SECURITY_SERVICE_URL: str = "http://security-service:5001"
    ADMIN_SERVICE_URL: str = "http://administration-service:5002"
    TUTORIAS_SERVICE_URL: str = "http://tutorias-service:5003"

    # RabbitMQ (tutorias-service comandos vía AMQP)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    RABBITMQ_QUEUE_SOLICITUDES: str = "tutorias.solicitudes"
    RABBITMQ_QUEUE_EVENTOS: str = "tutorias.eventos"
    RABBITMQ_RESPONSE_TIMEOUT: int = 30

    # Seguridad interna
    INTERNAL_TOKEN: str = "internal_secret_token_xyz"

    # Motor de IA: "setfit" (legacy) o "qwen" (agente LLM)
    AI_ENGINE: str = "qwen"

    # Configuración Ollama / agente LLM
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT: int = 30
    OLLAMA_MAX_TOOL_ITERATIONS: int = 3

    # Embeddings (MiniLM para RAG)
    MODEL_NAME: str = "all-MiniLM-L6-v2"

    # RAG (Agentic RAG)
    RAG_TOP_K: int = 5                # documentos finales que recibe el LLM
    RAG_CANDIDATES: int = 20          # candidatos a recuperar de pgvector
    RAG_MIN_SCORE: float = 0.35       # umbral de corte por calidad
    RAG_VECTOR_WEIGHT: float = 0.80   # peso del embedding
    RAG_TEXT_WEIGHT: float = 0.20     # peso de pg_trgm

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
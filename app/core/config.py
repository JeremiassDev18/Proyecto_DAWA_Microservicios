from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5435
    DB_NAME: str = "chatbotdb"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin123"

    # URLs microservicios
    SECURITY_SERVICE_URL: str = "http://security-service:5001"
    ADMIN_SERVICE_URL: str = "http://administration-service:5002"
    RESERVATION_SERVICE_URL: str = "http://reservation-service:5003"

    # Seguridad interna
    INTERNAL_TOKEN: str = "internal_secret_token_xyz"

    # Configuración ML
    SIMILARITY_THRESHOLD: float = 0.25
    VECTOR_WEIGHT: float = 0.70
    TRGM_WEIGHT: float = 0.30
    MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Umbral de confianza para respuesta directa vs escalamiento
    CONFIDENCE_THRESHOLD: float = 0.60
    ESCALATION_ENABLED: bool = True

    # Reentrenamiento inteligente
    AUTO_TRAIN: bool = True
    AUTO_TRAIN_THRESHOLD: int = 100

    # RAG
    RAG_TOP_K: int = 3
    RAG_SIMILARITY_THRESHOLD: float = 0.25
    RAG_HIGH_CONFIDENCE: float = 0.35

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
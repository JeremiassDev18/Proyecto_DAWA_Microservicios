from datetime import datetime

from pydantic import BaseModel


class ChatResponse(BaseModel):
    respuesta: str
    intencion: str
    confianza: float
    tipo_resolucion: str
    id_conversacion: int
    id_mensaje: int


class FeedbackResponse(BaseModel):
    id: int
    mensaje: str = "Feedback registrado"
    already_exists: bool = False


class FeedbackStatusResponse(BaseModel):
    id_mensaje: int
    feedback_exists: bool
    fue_util: bool | None = None


class PendingItem(BaseModel):
    id: int
    texto: str
    intencion_sugerida: str | None
    creado_en: datetime


class PendingListResponse(BaseModel):
    pendientes: list[PendingItem]
    total: int


class HealthResponse(BaseModel):
    status: str


class KnowledgeResponse(BaseModel):
    id: int
    titulo: str
    contenido: str
    tags: list[str]
    activo: bool
    fecha_actualizacion: datetime


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeResponse]
    total: int


class UsageMetricsResponse(BaseModel):
    total_conversaciones: int
    conversaciones_activas: int
    total_mensajes: int
    pendientes_sin_resolver: int
    top_tipos_resolucion: list[dict]
    resolucion_por_tipo: list[dict]
    feedback_utiles: int
    feedback_no_utiles: int
    feedback_total: int


class ConversationSummary(BaseModel):
    id_conversacion: int
    id_usuario: int
    nombre_cliente: str | None
    iniciado_en: datetime
    activa: bool
    total_mensajes: int
    resumen: str


class MessageResponse(BaseModel):
    id: int
    id_conversacion: int
    rol: str
    contenido: str
    tipo_resolucion: str | None = None
    confianza_ml: float | None = None
    modelo_usado: str | None = None
    enviado_en: datetime


class ConversationResponse(BaseModel):
    id: int
    id_usuario: int
    nombre_cliente: str | None = None
    activa: bool
    iniciado_en: datetime
    finalizado_en: datetime | None = None

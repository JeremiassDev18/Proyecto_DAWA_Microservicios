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


class PendingList(BaseModel):
    pendientes: list[PendingItem]
    total: int


class ModelMetrics(BaseModel):
    nombre: str
    version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    activo: bool


class PredictionItem(BaseModel):
    id: int
    texto_usuario: str
    intencion_predicha: str
    confianza: float
    correcta: bool | None
    creado_en: datetime


class TrainingStatus(BaseModel):
    mensaje: str
    modelo_version: str
    metricas: dict


class HealthResponse(BaseModel):
    status: str


class DatasetResponse(BaseModel):
    id: int
    texto: str
    id_intencion: int
    intencion: str
    validado: bool
    origen: str
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int


class PendingConvertResponse(BaseModel):
    id_pendiente: int
    id_dataset: int
    dataset: DatasetResponse


class TaskInfo(BaseModel):
    task_id: int
    status: str
    modelo_version: str = ""
    metricas: dict = {}
    mensaje: str = ""


class DocumentResponse(BaseModel):
    id: int
    titulo: str
    contenido: str
    categoria: str | None
    fuente: str | None
    archivo_pdf: str | None
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class UsageMetricsResponse(BaseModel):
    total_conversaciones: int
    conversaciones_activas: int
    total_mensajes: int
    pendientes_sin_resolver: int
    top_intenciones: list[dict]
    resolucion_por_tipo: list[dict]
    feedback_utiles: int
    feedback_no_utiles: int
    feedback_total: int


class IntentResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool
    creado_en: datetime


class IntentListResponse(BaseModel):
    items: list[IntentResponse]
    total: int


class ResponseResponse(BaseModel):
    id: int
    id_intencion: int
    intencion: str
    respuesta_texto: str
    tipo: str
    prioridad: int
    activa: bool
    veces_usada: int


class ResponseListResponse(BaseModel):
    items: list[ResponseResponse]
    total: int


class ConversationSummary(BaseModel):
    id_conversacion: int
    id_usuario: int
    nombre_cliente: str | None
    iniciado_en: datetime
    activa: bool
    total_mensajes: int
    resumen: str

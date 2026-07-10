from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    usuario_id: int
    mensaje: str = Field(..., min_length=1, max_length=1000)
    nombre: str = ""
    id_conversacion: int | None = None
    nueva_conversacion: bool = False
    estudiante_id: int | None = None
    carrera_id: int | None = None
    periodo_id: int | None = None


class FeedbackRequest(BaseModel):
    id_mensaje: int
    util: bool

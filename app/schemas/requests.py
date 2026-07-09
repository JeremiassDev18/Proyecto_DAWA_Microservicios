from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    usuario_id: int
    mensaje: str = Field(..., min_length=1, max_length=1000)
    nombre: str = ""
    id_conversacion: int | None = None
    estudiante_id: int | None = None


class FeedbackRequest(BaseModel):
    id_mensaje: int
    util: bool


class DatasetCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)
    id_intencion: int
    origen: str = "manual"


class DatasetUpdate(BaseModel):
    texto: str | None = Field(None, min_length=1, max_length=2000)
    id_intencion: int | None = None


class PendingConvertRequest(BaseModel):
    id_intencion: int
    validar: bool = True


class DocumentCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    contenido: str = Field(..., min_length=1)
    categoria: str = ""
    fuente: str = ""
    archivo_pdf: str = ""


class DocumentUpdate(BaseModel):
    titulo: str | None = Field(None, min_length=1, max_length=255)
    contenido: str | None = None
    categoria: str | None = None
    fuente: str | None = None
    archivo_pdf: str | None = None


class IntentCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=80)
    descripcion: str = ""


class IntentUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=80)
    descripcion: str | None = None
    activo: bool | None = None


class ResponseCreate(BaseModel):
    id_intencion: int
    respuesta_texto: str = Field(..., min_length=1)
    tipo: str = "texto"
    prioridad: int = 1


class ResponseUpdate(BaseModel):
    respuesta_texto: str | None = None
    tipo: str | None = None
    prioridad: int | None = None
    activa: bool | None = None

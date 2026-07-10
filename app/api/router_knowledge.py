from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import requerir_admin
from app.core.dependencies import get_db
from app.controllers import knowledge_controller as ctrl
from app.services.agent_orchestrator import clear_agent_cache
from app.agent.adapters.rag import RAGAdapter
from app.schemas.responses import KnowledgeListResponse, KnowledgeResponse
from app.utils.logger import logger
from app.utils.pagination import paginate

router = APIRouter(tags=["Centro de Conocimiento"])


class KnowledgeCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    contenido: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class KnowledgeUpdate(BaseModel):
    titulo: str | None = Field(None, min_length=1, max_length=255)
    contenido: str | None = Field(None, min_length=1)
    tags: list[str] | None = None


class KnowledgeTestRequest(BaseModel):
    consulta: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=10)


class KnowledgeTestItem(BaseModel):
    titulo: str
    contenido: str
    score: float


class KnowledgeTestResponse(BaseModel):
    consulta: str
    documentos: list[KnowledgeTestItem]
    respuesta: str


@router.get("/knowledge", response_model=KnowledgeListResponse)
def list_knowledge(
    query: str = Query("", description="Buscar por título o contenido"),
    tag: str = Query("", description="Filtrar por tag"),
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
    _auth=Depends(requerir_admin),
):
    tags = [t.strip() for t in tag.split(",") if t.strip()] if tag else None
    items = ctrl.list_knowledge(conn, texto_query=query, tags=tags, activo=activo)
    paged, total = paginate(items, page, page_size)
    return KnowledgeListResponse(items=[KnowledgeResponse(**i) for i in paged], total=total)


@router.get("/knowledge/{id}", response_model=KnowledgeResponse)
def get_knowledge(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.get_knowledge(conn, id)
    if not item:
        raise HTTPException(status_code=404, detail="Conocimiento no encontrado")
    return KnowledgeResponse(**item)


@router.post("/knowledge", response_model=KnowledgeResponse, status_code=201)
def create_knowledge(req: KnowledgeCreate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.create_knowledge(conn, req.titulo, req.contenido, req.tags)
    logger.info(f"Conocimiento creado id={item['id']}: {req.titulo}")
    return KnowledgeResponse(**item)


@router.put("/knowledge/{id}", response_model=KnowledgeResponse)
def update_knowledge(id: int, req: KnowledgeUpdate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.update_knowledge(
        conn, id,
        titulo=req.titulo,
        contenido=req.contenido,
        tags=req.tags,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Conocimiento no encontrado")
    logger.info(f"Conocimiento actualizado id={id}")
    clear_agent_cache()  # invalida caché para que el RAG se actualice
    return KnowledgeResponse(**item)


@router.delete("/knowledge/{id}")
def delete_knowledge(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    ok = ctrl.delete_knowledge(conn, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conocimiento no encontrado")
    clear_agent_cache()
    return {"mensaje": "Conocimiento desactivado", "id": id}


@router.post("/knowledge/test", response_model=KnowledgeTestResponse)
def test_knowledge(payload: KnowledgeTestRequest, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    """
    Permite al administrador probar qué documentos recupera el RAG
    y qué respondería el agente con esa información.
    """
    adapter = RAGAdapter()
    resultados = adapter.buscar_conocimiento(
        conn, payload.consulta, top_k=payload.top_k, return_scores=True,
    )

    documentos = [
        KnowledgeTestItem(titulo=r["titulo"], contenido=r["contenido"], score=r["score"])
        for r in resultados
    ]

    if not resultados:
        return KnowledgeTestResponse(
            consulta=payload.consulta,
            documentos=[],
            respuesta="No encontré información relevante en el centro de conocimiento.",
        )

    # Generar respuesta con el LLM usando solo el contexto recuperado.
    respuesta = adapter.responder_con_contexto(payload.consulta, resultados)

    return KnowledgeTestResponse(
        consulta=payload.consulta,
        documentos=documentos,
        respuesta=respuesta,
    )

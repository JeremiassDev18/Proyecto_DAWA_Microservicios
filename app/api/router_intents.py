from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_db
from app.core.auth import requerir_admin
from app.schemas.requests import IntentCreate, IntentUpdate, ResponseCreate, ResponseUpdate
from app.schemas.responses import (
    IntentListResponse, IntentResponse,
    ResponseListResponse, ResponseResponse,
)
from app.db import queries as db_queries
from app.utils.logger import logger
from app.utils.pagination import paginate

router = APIRouter(tags=["intents"])


# ── Intenciones ─────────────────────────────────────────────────────────

@router.get("/intents", response_model=IntentListResponse)
def list_intents(
    activo: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
    _auth=Depends(requerir_admin),
):
    rows = db_queries.get_all_intenciones(conn)
    if activo is not None:
        rows = [r for r in rows if r[3] == activo]
    items, total = paginate(rows, page, page_size)
    return IntentListResponse(
        items=[IntentResponse(id=r[0], nombre=r[1], descripcion=r[2],
                              activo=r[3], creado_en=r[4]) for r in items],
        total=total,
    )


@router.get("/intents/{id}", response_model=IntentResponse)
def get_intent(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    row = db_queries.get_intencion_by_id(conn, id)
    if not row:
        raise HTTPException(status_code=404, detail="Intención no encontrada")
    return IntentResponse(id=row[0], nombre=row[1], descripcion=row[2],
                          activo=row[3], creado_en=row[4])


@router.post("/intents", response_model=IntentResponse, status_code=201)
def create_intent(req: IntentCreate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    existing = db_queries.get_intencion_by_nombre(conn, req.nombre)
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe una intención con ese nombre")
    new_id = db_queries.create_intencion(conn, req.nombre, req.descripcion)
    row = db_queries.get_intencion_by_id(conn, new_id)
    logger.info(f"Intención creada id={new_id}: {req.nombre}")
    return IntentResponse(id=row[0], nombre=row[1], descripcion=row[2],
                          activo=row[3], creado_en=row[4])


@router.put("/intents/{id}", response_model=IntentResponse)
def update_intent(id: int, req: IntentUpdate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    existing = db_queries.get_intencion_by_id(conn, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Intención no encontrada")
    db_queries.update_intencion(
        conn, id,
        nombre=req.nombre if req.nombre is not None else existing[1],
        descripcion=req.descripcion if req.descripcion is not None else (existing[2] or ""),
        activo=req.activo,
    )
    row = db_queries.get_intencion_by_id(conn, id)
    logger.info(f"Intención actualizada id={id}")
    return IntentResponse(id=row[0], nombre=row[1], descripcion=row[2],
                          activo=row[3], creado_en=row[4])


@router.delete("/intents/{id}")
def delete_intent(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    existing = db_queries.get_intencion_by_id(conn, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Intención no encontrada")
    db_queries.soft_delete_intencion(conn, id)
    logger.info(f"Intención desactivada id={id}")
    return {"mensaje": "Intención desactivada", "id": id}


# ── Respuestas ──────────────────────────────────────────────────────────

@router.get("/responses", response_model=ResponseListResponse)
def list_responses(
    id_intencion: int | None = Query(None, description="Filter by intent ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
    _auth=Depends(requerir_admin),
):
    rows = db_queries.get_all_respuestas(conn)
    if id_intencion is not None:
        rows = [r for r in rows if r[7] == id_intencion]
    items, total = paginate(rows, page, page_size)
    return ResponseListResponse(
        items=[ResponseResponse(
            id=r[0], respuesta_texto=r[1], tipo=r[2], prioridad=r[3],
            activa=r[4], veces_usada=r[5], intencion=r[6], id_intencion=r[7],
        ) for r in items],
        total=total,
    )


@router.get("/responses/{id}", response_model=ResponseResponse)
def get_response(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    row = db_queries.get_respuesta_by_id(conn, id)
    if not row:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    return ResponseResponse(
        id=row[0], respuesta_texto=row[1], tipo=row[2], prioridad=row[3],
        activa=row[4], veces_usada=row[5], intencion=row[6], id_intencion=row[7],
    )


@router.post("/responses", response_model=ResponseResponse, status_code=201)
def create_response(req: ResponseCreate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    intent = db_queries.get_intencion_by_id(conn, req.id_intencion)
    if not intent:
        raise HTTPException(status_code=404, detail="Intención no encontrada")
    new_id = db_queries.create_respuesta(
        conn, req.id_intencion, req.respuesta_texto, req.tipo, req.prioridad,
    )
    row = db_queries.get_respuesta_by_id(conn, new_id)
    logger.info(f"Respuesta creada id={new_id} para intención {req.id_intencion}")
    return ResponseResponse(
        id=row[0], respuesta_texto=row[1], tipo=row[2], prioridad=row[3],
        activa=row[4], veces_usada=row[5], intencion=row[6], id_intencion=row[7],
    )


@router.put("/responses/{id}", response_model=ResponseResponse)
def update_response(id: int, req: ResponseUpdate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    existing = db_queries.get_respuesta_by_id(conn, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    db_queries.update_respuesta(
        conn, id,
        respuesta_texto=req.respuesta_texto if req.respuesta_texto is not None else existing[1],
        tipo=req.tipo if req.tipo is not None else existing[2],
        prioridad=req.prioridad if req.prioridad is not None else existing[3],
        activa=req.activa,
    )
    row = db_queries.get_respuesta_by_id(conn, id)
    logger.info(f"Respuesta actualizada id={id}")
    return ResponseResponse(
        id=row[0], respuesta_texto=row[1], tipo=row[2], prioridad=row[3],
        activa=row[4], veces_usada=row[5], intencion=row[6], id_intencion=row[7],
    )


@router.delete("/responses/{id}")
def delete_response(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    existing = db_queries.get_respuesta_by_id(conn, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    db_queries.soft_delete_respuesta(conn, id)
    logger.info(f"Respuesta desactivada id={id}")
    return {"mensaje": "Respuesta desactivada", "id": id}

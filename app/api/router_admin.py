from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_db
from app.core.auth import requerir_admin
from app.schemas.responses import (
    ConversationSummary, PendingItem, PendingListResponse, UsageMetricsResponse,
)
from app.db import queries as db_queries

from app.utils.pagination import paginate
from app.utils.logger import logger

router = APIRouter(tags=["admin"])


@router.get("/pending", response_model=PendingListResponse)
def list_pending(
    resuelta: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    rows = db_queries.get_pendientes(conn, resuelta=resuelta)
    paged, total = paginate(rows, page, page_size)
    items = [
        PendingItem(
            id=r[0], texto=r[1],
            intencion_sugerida=None,
            creado_en=r[3],
        )
        for r in paged
    ]
    return PendingListResponse(pendientes=items, total=total)


@router.get("/metrics/usage", response_model=UsageMetricsResponse)
def usage_metrics(conn=Depends(get_db), _auth=Depends(requerir_admin)):
    total_conv = db_queries.count_conversaciones(conn)
    activas = db_queries.count_conversaciones(conn, activa=True)
    total_msgs = db_queries.count_mensajes(conn)
    pendientes = db_queries.count_pendientes(conn, resuelta=False)

    top_tipos = [
        {"tipo_resolucion": r[0], "total": r[1]}
        for r in db_queries.top_tipos_resolucion(conn)
    ]
    resolucion = [
        {"tipo": r[0], "total": r[1]}
        for r in db_queries.resolucion_por_tipo(conn)
    ]
    fb_row = db_queries.feedback_summary(conn)
    fb_utiles = fb_row[0] if fb_row else 0
    fb_no_utiles = fb_row[1] if fb_row else 0
    fb_total = fb_row[2] if fb_row else 0

    return UsageMetricsResponse(
        total_conversaciones=total_conv,
        conversaciones_activas=activas,
        total_mensajes=total_msgs,
        pendientes_sin_resolver=pendientes,
        top_tipos_resolucion=top_tipos,
        resolucion_por_tipo=resolucion,
        feedback_utiles=fb_utiles,
        feedback_no_utiles=fb_no_utiles,
        feedback_total=fb_total,
    )


@router.get("/summary/conversations", response_model=list[ConversationSummary])
def list_conversation_summaries(
    limit: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
    _auth=Depends(requerir_admin),
):
    rows = db_queries.get_conversaciones_by_date_range(
        conn, "1970-01-01", "2100-01-01", limit=limit,
    )
    result = []
    for r in rows:
        conv, mensajes = db_queries.get_conversacion_with_mensajes(conn, r[0])
        total_msgs = len(mensajes) if mensajes else 0
        resumen = _generar_resumen(mensajes) if mensajes else "Sin mensajes"
        result.append(ConversationSummary(
            id_conversacion=r[0],
            id_usuario=r[1],
            nombre_cliente=r[2],
            iniciado_en=r[3],
            activa=r[4],
            total_mensajes=total_msgs,
            resumen=resumen,
        ))
    return result


def _generar_resumen(mensajes) -> str:
    usuario_msgs = [m for m in mensajes if m[1] == "usuario"]
    bot_msgs = [m for m in mensajes if m[1] == "bot"]

    partes = []
    total = len(mensajes)

    if usuario_msgs:
        primera = usuario_msgs[0][2][:120]
        partes.append(f"Pregunta: {primera}")

    if bot_msgs:
        ultima = bot_msgs[-1]
        ultima_respuesta = ultima[2][:120]
        tipo_resol = ultima[3] if len(ultima) > 3 and ultima[3] else ""
        partes.append(f"Respuesta: {ultima_respuesta}")
        if tipo_resol:
            partes.append(f"Tipo: {tipo_resol}")

    confianzas = [float(m[5]) for m in bot_msgs if len(m) > 5 and m[5] is not None]
    if confianzas:
        conf_max = max(confianzas)
        partes.append(f"Confianza: {conf_max:.0%}")

    partes.append(f"Mensajes: {total}")

    return " | ".join(partes) if partes else "Conversación sin contenido"


@router.patch("/pending/{id}/resolver")
def resolve_pending(id: int, conn=Depends(get_db)):
    pending = db_queries.get_pendiente_by_id(conn, id)
    if not pending:
        raise HTTPException(status_code=404, detail="Pendiente no encontrado")
    if pending[2]:
        raise HTTPException(status_code=400, detail="El pendiente ya está resuelto")
    db_queries.resolver_pendiente(conn, id)
    logger.info(f"Pendiente {id} resuelto")
    return {"mensaje": "Pendiente resuelto", "id": id}

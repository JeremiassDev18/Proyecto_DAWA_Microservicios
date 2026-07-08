from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_db
from app.core.auth import requerir_admin
from app.schemas.requests import PendingConvertRequest
from app.schemas.responses import (
    ConversationSummary, DatasetResponse, ModelMetrics, PendingConvertResponse,
    PendingItem, PendingList, PredictionItem, TaskInfo, UsageMetricsResponse,
)
from app.db import queries as db_queries
from app.db.training_repository import get_training_data
from app.controllers.dataset_controller import create_dataset
from app.services.training_queue import enqueue_training, get_task_status
from app.services.admin_sync_service import sync as sync_admin_data
from app.utils.logger import logger
from app.utils.pagination import paginate

router = APIRouter(tags=["admin"])


@router.post("/train", status_code=202, response_model=TaskInfo)
def train(conn=Depends(get_db)):
    texts, labels = get_training_data(conn)
    if not texts:
        return TaskInfo(
            task_id=0,
            status="no_data",
            mensaje="No hay datos de entrenamiento validados",
        )

    task_id = enqueue_training(texts, labels)
    if task_id is None:
        return TaskInfo(
            task_id=0,
            status="already_training",
            mensaje="Ya hay un entrenamiento en progreso. Espera a que termine.",
        )
    logger.info(f"Entrenamiento encolado: task_id={task_id}, {len(texts)} ejemplos")
    return TaskInfo(
        task_id=task_id,
        status="pending",
        mensaje=f"Entrenamiento encolado con {len(texts)} ejemplos",
    )


@router.post("/internal/sync-admin-data")
def run_sync_admin():
    stats = sync_admin_data()
    return stats


@router.get("/train/status/{task_id}", response_model=TaskInfo)
def training_status(task_id: int):
    task = get_task_status(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return TaskInfo(
        task_id=task_id,
        status=task["status"],
        modelo_version=task.get("modelo_version", ""),
        metricas=task.get("metricas", {}),
        mensaje=_status_message(task),
    )


def _status_message(task: dict) -> str:
    s = task["status"]
    if s == "pending":
        return "Entrenamiento en progreso..."
    if s == "completed":
        return f"Entrenamiento completado: {task.get('modelo_version', '')}"
    if s == "failed":
        return f"Entrenamiento fallido: {task.get('error', '')}"
    return s


@router.get("/pending", response_model=PendingList)
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
    return PendingList(pendientes=items, total=total)


@router.get("/metrics/predictions", response_model=list[PredictionItem])
def predictions_incorrectas(limit: int = 100, conn=Depends(get_db)):
    rows = db_queries.get_predicciones(conn, incorrectas=True, limit=limit)
    return [
        PredictionItem(
            id=r[0], texto_usuario=r[1],
            intencion_predicha=r[2], confianza=float(r[3]),
            correcta=r[4], creado_en=r[5],
        )
        for r in rows
    ]


@router.get("/metrics/model", response_model=ModelMetrics | None)
def model_metrics(conn=Depends(get_db)):
    row = db_queries.get_modelo_activo(conn)
    if not row:
        return None
    return ModelMetrics(
        nombre=row[1], version=row[2],
        accuracy=float(row[3]), precision=float(row[4]),
        recall=float(row[5]), f1_score=float(row[6]),
        activo=row[7],
    )


@router.get("/modelos", response_model=list[ModelMetrics])
def list_modelos(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    rows = db_queries.get_historial_modelos(conn, limit=limit)
    paged, total = paginate(rows, page, page_size)
    return [
        ModelMetrics(
            nombre=r[1], version=r[2],
            accuracy=float(r[3]), precision=float(r[4]),
            recall=float(r[5]), f1_score=float(r[6]),
            activo=r[7],
        )
        for r in paged
    ]


@router.get("/metrics/usage", response_model=UsageMetricsResponse)
def usage_metrics(conn=Depends(get_db), _auth=Depends(requerir_admin)):
    total_conv = db_queries.count_conversaciones(conn)
    activas = db_queries.count_conversaciones(conn, activa=True)
    total_msgs = db_queries.count_mensajes(conn)
    pendientes = db_queries.count_pendientes(conn, resuelta=False)

    top_int = [
        {"intencion": r[0], "total": r[1]}
        for r in db_queries.top_intenciones(conn)
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
        top_intenciones=top_int,
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





@router.post("/pending/{id}/convert", response_model=PendingConvertResponse)
def convert_pending(id: int, req: PendingConvertRequest, conn=Depends(get_db)):
    pending = db_queries.get_pendiente_by_id(conn, id)
    if not pending:
        raise HTTPException(status_code=404, detail="Pendiente no encontrado")
    if pending[2]:
        raise HTTPException(status_code=400, detail="El pendiente ya está resuelto")

    item = create_dataset(conn, pending[1], req.id_intencion)
    ds_id = item["id"]

    if req.validar:
        from app.controllers.dataset_controller import validate_dataset
        item = validate_dataset(conn, ds_id)

    db_queries.marcar_pendiente_resuelta(conn, id)
    logger.info(f"Pendiente {id} convertido a dataset {ds_id}")

    return PendingConvertResponse(
        id_pendiente=id,
        id_dataset=ds_id,
        dataset=DatasetResponse(**item),
    )


@router.patch("/pending/{id}/resolver")
def resolve_pending(id: int, conn=Depends(get_db)):
    pending = db_queries.get_pendiente_by_id(conn, id)
    if not pending:
        raise HTTPException(status_code=404, detail="Pendiente no encontrado")
    if pending[2]:
        raise HTTPException(status_code=400, detail="El pendiente ya está resuelto")
    db_queries.resolver_pendiente(conn, id)
    logger.info(f"Pendiente {id} resuelto sin convertir")
    return {"mensaje": "Pendiente resuelto", "id": id}

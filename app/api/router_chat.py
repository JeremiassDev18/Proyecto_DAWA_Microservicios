from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db
from app.schemas.requests import ChatRequest, FeedbackRequest
from app.schemas.responses import (
    ChatResponse, FeedbackResponse, FeedbackStatusResponse,
)
from app.db import queries as db_queries
from app.services.chat_orchestrator import process_message
from app.services.microservice_client import get_security_client
from app.utils.logger import logger

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, conn=Depends(get_db)):
    logger.info(f"Chat desde usuario {req.usuario_id}: {req.mensaje[:50]}...")

    user_context = {}
    try:
        client = get_security_client()
        user_data = client.get_usuario(req.usuario_id)
        if user_data:
            user_context["nombre"] = user_data.get("nombre") or user_data.get("nombres", "")
            user_context["carrera"] = user_data.get("carrera", "")
    except Exception as e:
        logger.warning(f"No se pudo obtener datos del usuario {req.usuario_id}: {e}")

    result = process_message(
        conn, req.usuario_id, req.mensaje, req.id_conversacion,
        nombre_cliente=user_context.get("nombre", req.nombre),
    )

    return ChatResponse(**result)


@router.post("/chat/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest, conn=Depends(get_db)):
    msg = db_queries.get_mensaje_by_id(conn, req.id_mensaje)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    existing = db_queries.get_feedback_by_mensaje(conn, req.id_mensaje)
    if existing:
        logger.info(f"Feedback duplicado para mensaje {req.id_mensaje}, ya existe id={existing[0]}")
        return FeedbackResponse(
            id=existing[0],
            mensaje="Ya registraste feedback para este mensaje",
            already_exists=True,
        )

    fb_id = db_queries.insert_feedback(conn, req.id_mensaje, req.util)
    action = "útil" if req.util else "no útil"
    logger.info(f"Feedback {fb_id}: mensaje {req.id_mensaje}, {action}")
    return FeedbackResponse(id=fb_id, mensaje=f"Feedback registrado como {action}")


@router.get("/chat/feedback/{id_mensaje}", response_model=FeedbackStatusResponse)
def feedback_status(id_mensaje: int, conn=Depends(get_db)):
    msg = db_queries.get_mensaje_by_id(conn, id_mensaje)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    existing = db_queries.get_feedback_by_mensaje(conn, id_mensaje)
    if existing:
        return FeedbackStatusResponse(
            id_mensaje=id_mensaje,
            feedback_exists=True,
            fue_util=bool(existing[1]),
        )
    return FeedbackStatusResponse(
        id_mensaje=id_mensaje,
        feedback_exists=False,
    )

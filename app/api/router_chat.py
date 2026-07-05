from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db
from app.schemas.requests import ChatRequest, FeedbackRequest
from app.schemas.responses import ChatResponse, FeedbackResponse
from app.db import queries as db_queries
from app.services.chat_orchestrator import process_message
from app.utils.logger import logger

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, conn=Depends(get_db)):
    logger.info(f"Chat desde usuario {req.usuario_id}: {req.mensaje[:50]}...")

    result = process_message(
        conn, req.usuario_id, req.mensaje, req.id_conversacion
    )

    return ChatResponse(**result)


@router.post("/chat/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest, conn=Depends(get_db)):
    msg = db_queries.get_mensaje_by_id(conn, req.id_mensaje)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    fb_id = db_queries.insert_feedback(conn, req.id_mensaje, req.util)
    logger.info(f"Feedback {fb_id}: mensaje {req.id_mensaje}, util={req.util}")
    return FeedbackResponse(id=fb_id)

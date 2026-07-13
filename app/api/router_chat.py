from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import verificar_token, AuthContext
from app.core.dependencies import get_db
from app.core.context import estudiante_id_ctx
from app.schemas.requests import ChatRequest, FeedbackRequest
from app.schemas.responses import (
    ChatResponse, FeedbackResponse, FeedbackStatusResponse, MessageResponse,
    ConversationResponse,
)
from app.db import queries as db_queries
from app.services.agent_orchestrator import process_message_agent
from app.utils.logger import logger

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    conn=Depends(get_db),
    auth: AuthContext = Depends(verificar_token),
):
    logger.info(f"Chat desde usuario {req.usuario_id}: {req.mensaje[:50]}...")

    # Auto-resolver estudiante_id si no viene en el request pero el usuario es estudiante.
    estudiante_id = req.estudiante_id
    if estudiante_id is None and auth.tipo == "estudiante" and auth.email:
        try:
            from app.services.microservice_client import get_admin_client
            admin = get_admin_client()
            estudiantes = admin._get("/api/administracion/estudiantes/") or []
            for est in estudiantes:
                if est.get("correo", "").lower() == auth.email.lower():
                    estudiante_id = est.get("id")
                    logger.info(f"[ChatRouter] estudiante_id auto-resuelto: {estudiante_id} para email {auth.email}")
                    break
        except Exception as e:
            logger.warning(f"[ChatRouter] no se pudo auto-resolver estudiante_id: {e}")

    token = estudiante_id_ctx.set(estudiante_id)
    try:
        # Normalizar rol desde JWT: estudiante, admin, docente u otro.
        rol = auth.tipo if auth.tipo in ("estudiante", "admin", "docente") else "estudiante"
        result = process_message_agent(
            conn,
            usuario_id=req.usuario_id,
            mensaje=req.mensaje,
            id_conversacion=req.id_conversacion,
            nombre_cliente=req.nombre,
            nueva_conversacion=req.nueva_conversacion,
            estudiante_id=estudiante_id,
            carrera_id=req.carrera_id,
            periodo_id=req.periodo_id,
            rol=rol,
            email=auth.email or "",
        )

        return ChatResponse(**result)
    finally:
        estudiante_id_ctx.reset(token)


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


@router.get("/conversations", response_model=list[ConversationResponse])
def get_user_conversations(usuario_id: int, conn=Depends(get_db)):
    rows = db_queries.get_conversaciones_by_usuario(conn, usuario_id, limit=5)
    return [
        ConversationResponse(
            id=row[0],
            id_usuario=row[1],
            nombre_cliente=row[2],
            activa=row[3],
            iniciado_en=row[4],
            finalizado_en=row[5],
        )
        for row in rows
    ]


@router.get("/conversations/{id_conversacion}/messages", response_model=list[MessageResponse])
def get_conversation_messages(id_conversacion: int, conn=Depends(get_db)):
    conv = db_queries.get_conversacion(conn, id_conversacion)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    rows = db_queries.get_mensajes_by_conversacion(conn, id_conversacion)
    return [
        MessageResponse(
            id=row[0],
            id_conversacion=id_conversacion,
            rol=row[1],
            contenido=row[2],
            tipo_resolucion=row[3] if len(row) > 3 else None,
            enviado_en=row[4] if len(row) > 4 else None,
        )
        for row in rows
    ]

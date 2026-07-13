"""
Orquestador del Agente LLM para el endpoint de chat.

Responsabilidades:
- Resolver o crear la conversación.
- Insertar el mensaje del usuario.
- Cargar/crear el Agent en memoria (RAM) y persistir su memoria en PostgreSQL.
- Ejecutar Agent.process().
- Guardar la memoria actualizada.
- Insertar la respuesta del bot en chatbot_mensaje.
- Retornar la respuesta en formato ChatResponse.
"""

import json
from typing import Any

from app.agent.agent import Agent
from app.agent.memory import ConversationMemory
from app.agent.schemas import AgentResponse
from app.db import queries
from app.utils.logger import logger


# Caché RAM de instancias de Agent por conversación.
_agent_cache: dict[int, Agent] = {}


def process_message_agent(
    conn,
    usuario_id: int,
    mensaje: str,
    id_conversacion: int | None = None,
    nombre_cliente: str = "",
    nueva_conversacion: bool = False,
    estudiante_id: int | None = None,
    carrera_id: int | None = None,
    periodo_id: int | None = None,
    rol: str = "estudiante",
    email: str = "",
) -> dict:
    """
    Procesa un mensaje usando el agente LLM y persiste todo en DB.

    Returns:
        dict con los campos esperados por ChatResponse.
    """
    logger.info(
        f"[AgentOrchestrator] usuario={usuario_id} estudiante={estudiante_id} "
        f"mensaje={mensaje[:50]}..."
    )

    # 1. Resolver/crear conversación.
    conv_id = _resolve_conversation(conn, usuario_id, id_conversacion, nombre_cliente,
                                    finalizar_anterior=nueva_conversacion)

    # 2. Insertar mensaje del usuario.
    queries.insert_mensaje(conn, conv_id, "usuario", mensaje)

    # 3. Obtener o crear Agent con memoria persistente.
    agent = _get_agent(
        conn, conv_id,
        estudiante_id=estudiante_id,
        usuario_id=usuario_id,
        carrera_id=carrera_id,
        periodo_id=periodo_id,
        rol=rol,
        email=email,
    )

    # 4. Procesar con el LLM.
    try:
        result = agent.process(mensaje, db_conn=conn)
    except Exception as e:
        logger.error(f"[AgentOrchestrator] error en Agent.process: {e}")
        result = AgentResponse(
            mensaje="Lo siento, ocurrió un error al procesar tu mensaje. Intenta de nuevo.",
            intencion_detectada="error",
            herramientas_usadas=[],
        )

    # 5. Persistir memoria del agente.
    try:
        _save_agent_memory(conn, conv_id, agent)
    except Exception as e:
        logger.error(f"[AgentOrchestrator] error guardando memoria: {e}")

    # 6. Insertar respuesta del bot.
    bot_msg_id = queries.insert_mensaje(
        conn, conv_id, "bot", result.mensaje, "agente",
    )

    return {
        "respuesta": result.mensaje,
        "intencion": result.intencion_detectada or "agente_llm",
        "confianza": 1.0,
        "tipo_resolucion": "agente",
        "id_conversacion": conv_id,
        "id_mensaje": bot_msg_id,
    }


def clear_agent_cache(conv_id: int | None = None) -> None:
    """Limpia la caché RAM de Agents. Útil para tests o reinicio."""
    global _agent_cache
    if conv_id is None:
        _agent_cache.clear()
    else:
        _agent_cache.pop(conv_id, None)


def _resolve_conversation(conn, usuario_id: int,
                          id_conversacion: int | None,
                          nombre_cliente: str = "",
                          finalizar_anterior: bool = False) -> int:
    if finalizar_anterior:
        # Finalizar la conversación activa actual y forzar una nueva.
        convs_activas = queries.get_conversaciones_by_usuario(conn, usuario_id, limit=5)
        for conv in convs_activas:
            if conv[3]:  # columna activa (0: id, 1: id_usuario, 2: nombre_cliente, 3: activa, 4: iniciado_en, 5: finalizado_en)
                logger.info(f"[AgentOrchestrator] finalizando conversación activa conv_id={conv[0]}")
                queries.update_conversacion_estado(conn, conv[0], activa=False)
        id_conversacion = None

    if id_conversacion:
        conv = queries.get_conversacion(conn, id_conversacion)
        if conv:
            if nombre_cliente:
                queries.update_conversacion_nombre(conn, id_conversacion, nombre_cliente)
            return id_conversacion

    convs = queries.get_conversaciones_by_usuario(conn, usuario_id, limit=1)
    if convs and convs[0][3]:  # activa
        conv_id = convs[0][0]
        if nombre_cliente:
            queries.update_conversacion_nombre(conn, conv_id, nombre_cliente)
        return conv_id

    # Crear nueva conversación y limpiar antiguas (máx 5 por usuario).
    new_id = queries.create_conversacion(conn, usuario_id, nombre_cliente)
    try:
        deleted = queries.delete_old_conversations(conn, usuario_id, keep=5)
        if deleted:
            logger.info(f"[AgentOrchestrator] {deleted} conversaciones antiguas eliminadas para usuario {usuario_id}")
    except Exception as e:
        logger.warning(f"[AgentOrchestrator] no se pudieron limpiar conversaciones antiguas: {e}")
    return new_id


def _get_agent(
    conn,
    conv_id: int,
    estudiante_id: int | None,
    usuario_id: int | None,
    carrera_id: int | None,
    periodo_id: int | None,
    rol: str = "estudiante",
    email: str = "",
) -> Agent:
    """Obtiene un Agent de la caché RAM o lo reconstruye desde PostgreSQL."""
    if conv_id in _agent_cache:
        logger.info(f"[AgentOrchestrator] Agent cache hit conv_id={conv_id}")
        agent = _agent_cache[conv_id]
        # Actualizar contexto si el usuario aportó nuevos datos en esta petición.
        if estudiante_id is not None:
            agent.estudiante_id = estudiante_id
        if usuario_id is not None:
            agent.usuario_id = usuario_id
        if carrera_id is not None:
            agent.carrera_id = carrera_id
        if periodo_id is not None:
            agent.periodo_id = periodo_id
        if rol is not None:
            agent.rol = rol
        if email:
            agent.email = email
        return agent

    memory = _load_agent_memory(conn, conv_id)

    agent = Agent(
        estudiante_id=estudiante_id,
        usuario_id=usuario_id,
        carrera_id=carrera_id,
        periodo_id=periodo_id,
        rol=rol,
        email=email,
        memory=memory,
    )
    _agent_cache[conv_id] = agent
    return agent


def _load_agent_memory(conn, conv_id: int) -> ConversationMemory:
    """Carga la memoria del agente desde PostgreSQL."""
    row = queries.get_agent_memory(conn, conv_id)
    if row:
        try:
            raw = row[0]
            data = raw if isinstance(raw, dict) else json.loads(raw)
            memory = ConversationMemory.from_dict(data, max_messages=3)
            memory.state.setdefault("id_conversacion", conv_id)
            logger.info(f"[AgentOrchestrator] memoria cargada conv_id={conv_id}")
            return memory
        except Exception as e:
            logger.warning(f"[AgentOrchestrator] error parseando memoria conv_id={conv_id}: {e}")

    memory = ConversationMemory(max_messages=3)
    memory.state["id_conversacion"] = conv_id
    return memory


def _save_agent_memory(conn, conv_id: int, agent: Agent) -> None:
    """Guarda la memoria del agente en PostgreSQL."""
    memory = agent.get_memory()
    data = memory.to_dict()
    queries.upsert_agent_memory(
        conn, conv_id,
        contexto=json.dumps(data, ensure_ascii=False),
        resumen=data["state"].get("resumen", ""),
        total_mensajes=data["total_messages"],
    )
    logger.info(f"[AgentOrchestrator] memoria guardada conv_id={conv_id}")

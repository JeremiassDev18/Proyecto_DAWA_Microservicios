from fastapi import FastAPI

from app.api.router_chat import router as chat_router
from app.api.router_admin import router as admin_router
from app.api.router_knowledge import router as knowledge_router
from app.api.router_agent import router as agent_router

from app.core.config import settings
from app.db.postgres_client import init_pool, close_pool
from app.utils.logger import logger

app = FastAPI(
    title="Chatbot Service",
    description="Microservicio de chatbot con agente LLM académico",
    version="2.0.0",
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    logger.info("Inicializando pool de conexiones...")
    init_pool()
    logger.info(f"Motor de IA configurado: {settings.AI_ENGINE}")
    logger.info("Chatbot Service iniciado.")


@app.on_event("shutdown")
def shutdown():
    logger.info("Cerrando pool de conexiones...")
    close_pool()


@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router_chat import router as chat_router
from app.api.router_admin import router as admin_router
from app.api.router_dataset import router as dataset_router
from app.api.router_documents import router as documents_router
from app.api.router_intents import router as intents_router
import threading
import time

from app.db.postgres_client import init_pool, close_pool, get_connection, release_connection
from app.db.training_repository import auto_train_if_needed
from app.ml.setfit_trainer import models_exist, load_model
from app.ml import predictor as ml_predictor
from app.utils.logger import logger

app = FastAPI(
    title="Chatbot Service",
    description="Microservicio de chatbot con clasificación ML y búsqueda híbrida",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(dataset_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(intents_router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    logger.info("Inicializando pool de conexiones...")
    init_pool()

    if models_exist():
        try:
            model = load_model()
            ml_predictor.set_cached_model(model)
            logger.info("Modelo SetFit cargado desde disco exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo SetFit: {e}")
    else:
        logger.warning(
            "No se encontró modelo entrenado en data/setfit_model/. "
            "Ejecuta POST /api/v1/train o scripts/train_setfit.py primero."
        )

    _start_training_checker()

    logger.info("Chatbot Service iniciado.")


def _periodic_training_check():
    while True:
        time.sleep(300)
        try:
            conn = get_connection()
            trained = auto_train_if_needed(conn)
            release_connection(conn)
            if trained:
                logger.info("Auto-entrenamiento periódico completado.")
        except Exception as e:
            logger.error(f"Error en training checker: {e}")


def _start_training_checker():
    thread = threading.Thread(target=_periodic_training_check, daemon=True)
    thread.start()
    logger.info("Training checker iniciado (cada 300s).")


@app.on_event("shutdown")
def shutdown():
    logger.info("Cerrando pool de conexiones...")
    close_pool()


@app.get("/health")
def health():
    return {"status": "ok"}

"""FastAPI application entrypoint for the Insurance Cross-Sell Predictor."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app import model as model_mod
from app.routes import router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Boot even if the model is unavailable: the container must start and
    # listen so the platform health check passes. /predict returns 503 until
    # a model is loaded.
    try:
        model_mod.state["model"] = model_mod.load_model()
        logger.info(
            "Model loaded (env=%s, version=%s)",
            config.APP_ENV,
            config.MODEL_VERSION,
        )
    except Exception as e:  # noqa: BLE001 - never crash on startup
        model_mod.state["model"] = None
        logger.error("Model load failed at startup (serving 503 until fixed): %s", e)
    yield
    model_mod.state["model"] = None


app = FastAPI(title="Insurance Cross-Sell Predictor", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # nanti bisa dipersempit ke domain Vercel-mu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
async def read_root():
    return {
        "health_check": "OK",
        "model_version": config.MODEL_VERSION,
        "env": config.APP_ENV,
        "model_loaded": model_mod.state["model"] is not None,
    }
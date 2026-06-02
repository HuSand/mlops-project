"""FastAPI application entrypoint for the Insurance Cross-Sell Predictor."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config
from app import model as model_mod
from app.routes import router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    model_mod.state["model"] = model_mod.load_model()
    logger.info(
        "Model loaded (env=%s, version=%s)", config.APP_ENV, config.MODEL_VERSION
    )
    yield
    model_mod.state["model"] = None


app = FastAPI(title="Insurance Cross-Sell Predictor", lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def read_root():
    return {
        "health_check": "OK",
        "model_version": config.MODEL_VERSION,
        "env": config.APP_ENV,
        "model_loaded": model_mod.state["model"] is not None,
    }

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model.pkl"))
GCS_MODEL_URI = os.getenv("GCS_MODEL_URI")  # e.g. gs://pso-mlops-dvc-sandy/models/model.pkl
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")
APP_ENV = os.getenv("APP_ENV", "local")

state = {"model": None}


def _download_from_gcs(gcs_uri: str, dest: Path) -> None:
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")
    _, _, rest = gcs_uri.partition("gs://")
    bucket_name, _, blob_name = rest.partition("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    client.bucket(bucket_name).blob(blob_name).download_to_filename(str(dest))
    logger.info("Downloaded model from %s to %s", gcs_uri, dest)


def _load_model():
    if not MODEL_PATH.exists() and GCS_MODEL_URI:
        logger.info("Model not found locally, fetching from GCS")
        _download_from_gcs(GCS_MODEL_URI, MODEL_PATH)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


@asynccontextmanager
async def lifespan(_: FastAPI):
    state["model"] = _load_model()
    logger.info("Model loaded (env=%s, version=%s)", APP_ENV, MODEL_VERSION)
    yield
    state["model"] = None


app = FastAPI(title="Insurance Cross-Sell Predictor", lifespan=lifespan)


class InputData(BaseModel):
    Gender: str
    Age: int
    HasDrivingLicense: int
    RegionID: float
    Switch: int
    PastAccident: str
    AnnualPremium: float


@app.get("/")
async def read_root():
    return {
        "health_check": "OK",
        "model_version": MODEL_VERSION,
        "env": APP_ENV,
        "model_loaded": state["model"] is not None,
    }


@app.post("/predict")
async def predict(input_data: InputData):
    model = state["model"]
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    df = pd.DataFrame([input_data.model_dump()])
    pred = model.predict(df)
    return {"predicted_class": int(pred[0]), "model_version": MODEL_VERSION}

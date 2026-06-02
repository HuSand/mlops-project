"""API routes for predictions."""

import pandas as pd
from fastapi import APIRouter, HTTPException

from app import bq_logger, config
from app import model as model_mod
from app.schemas import InputData

router = APIRouter()


@router.post("/predict")
async def predict(input_data: InputData):
    model = model_mod.get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    payload = input_data.model_dump()
    df = pd.DataFrame([payload])
    pred = int(model.predict(df)[0])
    bq_logger.log_prediction(payload, pred)
    bq_logger.notify_discord(payload, pred) 
    return {"predicted_class": pred, "model_version": config.MODEL_VERSION}

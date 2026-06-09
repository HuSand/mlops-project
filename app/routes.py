"""API routes for predictions."""

import json
import pandas as pd
from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

from app import bq_logger, config
from app import model as model_mod
from app.schemas import InputData

router = APIRouter()

@router.get("/api/v1/monitoring/latest")
async def get_latest_monitoring():
    """Fetch the latest drift metrics from BigQuery for the dashboard."""
    client = bigquery.Client(project=config.BQ_PROJECT)
    
    table_id = f"{config.BQ_PROJECT}.{config.BQ_DATASET}.{config.BQ_MONITOR_TABLE}"
    query = f"SELECT * FROM `{table_id}` ORDER BY timestamp DESC LIMIT 1"
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        
        if not results:
            return {"status": "error", "message": "No monitoring data found"}
            
        row = results[0]
        
        # Parse drifted_features from JSON string to list
        drifted_features = []
        if row.drifted_features:
            try:
                drifted_features = json.loads(row.drifted_features)
            except Exception:
                drifted_features = []

        return {
            "status": "success",
            "data": {
                "execution_date": str(row.date),
                "timestamp": row.timestamp.isoformat(),
                "summary": {
                    "drift_detected": bool(row.dataset_drift),
                    "drift_share": float(row.drift_share) if row.drift_share else 0.0,
                    "number_of_columns": int(row.number_of_columns) if row.number_of_columns else 0,
                    "drifted_columns_count": int(row.number_of_drifted_columns) if row.number_of_drifted_columns else 0
                },
                "drift_details": drifted_features,
                "report_url": f"https://storage.googleapis.com/mlops-monitoring-reports/reports/drift_report_{row.date}.html"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")

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

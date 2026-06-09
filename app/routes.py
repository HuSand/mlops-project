"""API routes for predictions."""

import json
import pandas as pd
from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

from app import bq_logger, config
from app import model as model_mod
from app.schemas import InputData

router = APIRouter()


def _predlog_table() -> str:
    """Fully-qualified prediction_logs table id."""
    return f"{config.BQ_PROJECT}.{config.BQ_DATASET}.{config.BQ_TABLE}"


def _norm_cte() -> str:
    """SQL ``WITH norm AS (...)`` that normalizes both payload formats.

    Production predictions use ``Gender/Age/...`` keys while older seeds use
    ``feature_0..6`` (same order/meaning). COALESCE bridges both so the analytics
    queries work regardless of which writer produced the row.
    """
    return f"""
WITH norm AS (
  SELECT
    COALESCE(JSON_EXTRACT_SCALAR(input_payload, '$.Gender'),
             JSON_EXTRACT_SCALAR(input_payload, '$.feature_0')) AS gender,
    SAFE_CAST(COALESCE(JSON_EXTRACT_SCALAR(input_payload, '$.Age'),
             JSON_EXTRACT_SCALAR(input_payload, '$.feature_1')) AS FLOAT64) AS age,
    SAFE_CAST(COALESCE(JSON_EXTRACT_SCALAR(input_payload, '$.AnnualPremium'),
             JSON_EXTRACT_SCALAR(input_payload, '$.feature_6')) AS FLOAT64) AS premium,
    COALESCE(JSON_EXTRACT_SCALAR(input_payload, '$.PastAccident'),
             JSON_EXTRACT_SCALAR(input_payload, '$.feature_5')) AS past_accident,
    prediction,
    timestamp
  FROM `{_predlog_table()}`
)
"""


@router.get("/api/v1/insights/business")
async def get_business_insights():
    """Aggregate prediction_logs into cross-sell business insights (mgmt/marketing)."""
    client = bigquery.Client(project=config.BQ_PROJECT)
    norm = _norm_cte()
    try:
        kpis = dict(list(client.query(norm + """
            SELECT
              COUNT(*) AS total_scored,
              ROUND(AVG(prediction) * 100, 1) AS interest_rate,
              ROUND(AVG(premium), 0) AS avg_premium,
              COUNTIF(prediction = 1) AS interested_leads,
              ROUND(AVG(IF(prediction = 1, premium, NULL)), 0) AS avg_premium_interested
            FROM norm
        """).result())[0])

        by_gender = [dict(r) for r in client.query(norm + """
            SELECT COALESCE(gender, 'Unknown') AS gender, COUNT(*) AS n,
                   ROUND(AVG(prediction) * 100, 1) AS interest_pct,
                   ROUND(AVG(premium), 0) AS avg_premium
            FROM norm GROUP BY gender ORDER BY gender
        """).result()]

        by_age_band = [dict(r) for r in client.query(norm + """
            SELECT CASE WHEN age < 30 THEN '<30' WHEN age < 45 THEN '30-44'
                        WHEN age < 60 THEN '45-59' ELSE '60+' END AS band,
                   COUNT(*) AS n, ROUND(AVG(prediction) * 100, 1) AS interest_pct
            FROM norm GROUP BY band ORDER BY MIN(age)
        """).result()]

        by_premium_band = [dict(r) for r in client.query(norm + """
            SELECT CASE WHEN premium < 5000 THEN '<5k' WHEN premium < 15000 THEN '5-15k'
                        WHEN premium < 30000 THEN '15-30k' ELSE '30k+' END AS band,
                   COUNT(*) AS n, ROUND(AVG(prediction) * 100, 1) AS interest_pct
            FROM norm GROUP BY band ORDER BY MIN(premium)
        """).result()]

        by_past_accident = [dict(r) for r in client.query(norm + """
            SELECT COALESCE(past_accident, 'Unknown') AS value, COUNT(*) AS n,
                   ROUND(AVG(prediction) * 100, 1) AS interest_pct
            FROM norm GROUP BY value ORDER BY value
        """).result()]

        trend = [dict(r) for r in client.query(norm + """
            SELECT DATE(timestamp) AS date, COUNT(*) AS total,
                   COUNTIF(prediction = 1) AS interested,
                   ROUND(AVG(prediction) * 100, 1) AS interest_pct
            FROM norm GROUP BY date ORDER BY date DESC LIMIT 30
        """).result()]
        trend.reverse()
        for r in trend:
            r["date"] = str(r["date"])

        bq_logger.log_api_hit("/api/v1/insights/business")

        return {
            "status": "success",
            "data": {
                "kpis": kpis,
                "by_gender": by_gender,
                "by_age_band": by_age_band,
                "by_premium_band": by_premium_band,
                "by_past_accident": by_past_accident,
                "trend": trend,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")


@router.get("/api/v1/monitoring/ops")
async def get_monitoring_ops():
    """Operational model metrics (throughput) from prediction_logs."""
    client = bigquery.Client(project=config.BQ_PROJECT)
    table = _predlog_table()
    try:
        summary = dict(list(client.query(f"""
            SELECT COUNT(*) AS total_predictions, MAX(timestamp) AS last_prediction_ts
            FROM `{table}`
        """).result())[0])

        volume_by_day = [dict(r) for r in client.query(f"""
            SELECT DATE(timestamp) AS date, COUNT(*) AS n
            FROM `{table}` GROUP BY date ORDER BY date DESC LIMIT 30
        """).result()]
        volume_by_day.reverse()
        for r in volume_by_day:
            r["date"] = str(r["date"])

        by_model_version = [dict(r) for r in client.query(f"""
            SELECT model_version, COUNT(*) AS n
            FROM `{table}` GROUP BY model_version ORDER BY n DESC
        """).result()]

        bq_logger.log_api_hit("/api/v1/monitoring/ops")

        last_ts = summary.get("last_prediction_ts")
        return {
            "status": "success",
            "data": {
                "total_predictions": int(summary["total_predictions"]),
                "last_prediction_ts": last_ts.isoformat() if last_ts else None,
                "volume_by_day": volume_by_day,
                "by_model_version": by_model_version,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")


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

        bq_logger.log_api_hit("/api/v1/monitoring/latest")

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
                "data_health": {
                    "missing_values_count": int(row.missing_values_count) if row.missing_values_count is not None else 0,
                    "total_predictions": int(row.total_rows) if row.total_rows is not None else 0
                },
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

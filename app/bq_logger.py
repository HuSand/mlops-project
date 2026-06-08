"""Best-effort prediction logging to BigQuery.

Writes rows to ``{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`` (default
``mlops.prediction_logs``) matching the schema consumed by the CM pipeline
(``monitoring/fetch_production_data.py``): an ``input_payload`` JSON string and
a ``timestamp`` column. Logging never blocks or breaks a prediction request.
"""

import os
import requests
import json
import logging
from datetime import datetime, timezone

from app import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from google.cloud import bigquery

        _client = bigquery.Client(project=config.BQ_PROJECT)
    return _client


def log_prediction(payload: dict, prediction: int | None = None) -> None:
    """Insert a single prediction log row. No-op when logging is disabled.

    Any failure is swallowed (logged as a warning) so the prediction path keeps
    working even if BigQuery is unreachable or not yet provisioned.
    """
    if not config.ENABLE_BQ_LOGGING:
        return
    try:
        client = _get_client()
        table_id = f"{config.BQ_PROJECT}.{config.BQ_DATASET}.{config.BQ_TABLE}"
        row = {
            "input_payload": json.dumps(payload),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prediction": prediction,
            "model_version": config.MODEL_VERSION,
        }
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            logger.warning("BQ prediction log insert errors: %s", errors)
    except Exception as e:  # noqa: BLE001 - logging must never break /predict
        logger.warning("BQ prediction logging failed (non-fatal): %s", e)

def notify_discord(payload: dict, prediction: int) -> None:
    """Kirim notifikasi ke Discord setiap ada prediksi masuk."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_PREDICT")
    if not webhook_url:
        return
    try:
        label = "Tertarik Beli" if prediction == 1 else "Tidak Tertarik"
        color = 3066993 if prediction == 1 else 15158332
        embed = {
            "embeds": [{
                "title": f"Prediksi Baru - {label}",
                "color": color,
                "fields": [
                    {"name": "Gender", "value": str(payload.get("Gender", "-")), "inline": True},
                    {"name": "Age", "value": str(payload.get("Age", "-")), "inline": True},
                    {"name": "Annual Premium", "value": str(payload.get("AnnualPremium", "-")), "inline": True},
                    {"name": "Past Accident", "value": str(payload.get("PastAccident", "-")), "inline": True},
                    {"name": "Has Driving License", "value": str(payload.get("HasDrivingLicense", "-")), "inline": True},
                    {"name": "Result", "value": label, "inline": True},
                ],
                "footer": {"text": f"Model version: {config.MODEL_VERSION}"}
            }]
        }
        requests.post(webhook_url, json=embed, timeout=5)
    except Exception as e:
        logger.warning("Discord notification failed (non-fatal): %s", e)
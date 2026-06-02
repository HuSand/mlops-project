"""Best-effort prediction logging to BigQuery.

Writes rows to ``{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`` (default
``mlops.prediction_logs``) matching the schema consumed by the CM pipeline
(``monitoring/fetch_production_data.py``): an ``input_payload`` JSON string and
a ``timestamp`` column. Logging never blocks or breaks a prediction request.
"""

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

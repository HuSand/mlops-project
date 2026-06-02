"""Centralized configuration read from environment variables."""

import os
from pathlib import Path

# --- Model loading ---
MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model.pkl"))
GCS_MODEL_URI = os.getenv("GCS_MODEL_URI")  # e.g. gs://bucket/models/model.pkl
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")
APP_ENV = os.getenv("APP_ENV", "local")

# --- BigQuery prediction logging (consumed by CM / monitor.yml) ---
ENABLE_BQ_LOGGING = os.getenv("ENABLE_BQ_LOGGING", "false").lower() == "true"
BQ_PROJECT = os.getenv("BQ_PROJECT")  # defaults to ADC project when None
BQ_DATASET = os.getenv("BQ_DATASET", "mlops")
BQ_TABLE = os.getenv("BQ_TABLE", "prediction_logs")

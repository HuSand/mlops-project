"""Model loading: fetch from GCS if needed, then load with joblib."""

import logging
from pathlib import Path

import joblib

from app import config

logger = logging.getLogger(__name__)

# In-memory holder shared across the app lifespan.
state = {"model": None}


def download_from_gcs(gcs_uri: str, dest: Path) -> None:
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")
    _, _, rest = gcs_uri.partition("gs://")
    bucket_name, _, blob_name = rest.partition("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    client.bucket(bucket_name).blob(blob_name).download_to_filename(str(dest))
    logger.info("Downloaded model from %s to %s", gcs_uri, dest)


def load_model():
    if not config.MODEL_PATH.exists() and config.GCS_MODEL_URI:
        logger.info("Model not found locally, fetching from GCS")
        download_from_gcs(config.GCS_MODEL_URI, config.MODEL_PATH)
    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {config.MODEL_PATH}")
    return joblib.load(config.MODEL_PATH)


def get_model():
    return state["model"]

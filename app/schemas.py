"""Pydantic request/response models for the prediction API."""

from pydantic import BaseModel, ConfigDict


class InputData(BaseModel):
    # The deployed model (CT pipeline) is trained on dataset.py's synthetic
    # make_classification output: 10 numeric features named feature_0..feature_9.
    # The serving contract must match those column names exactly.
    feature_0: float
    feature_1: float
    feature_2: float
    feature_3: float
    feature_4: float
    feature_5: float
    feature_6: float
    feature_7: float
    feature_8: float
    feature_9: float


class PredictResponse(BaseModel):
    # ``model_version`` would otherwise clash with pydantic's protected
    # ``model_`` namespace; disable that guard for this response schema.
    model_config = ConfigDict(protected_namespaces=())

    predicted_class: int
    model_version: str

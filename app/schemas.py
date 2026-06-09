"""Pydantic request/response models for the prediction API."""

from pydantic import BaseModel, ConfigDict


class InputData(BaseModel):
    # Matches the CT-trained insurance model's feature contract.
    Gender: str
    Age: int
    HasDrivingLicense: int
    RegionID: float
    Switch: int
    PastAccident: str
    AnnualPremium: float


class PredictResponse(BaseModel):
    # ``model_version`` would otherwise clash with pydantic's protected
    # ``model_`` namespace; disable that guard for this response schema.
    model_config = ConfigDict(protected_namespaces=())

    predicted_class: int
    model_version: str

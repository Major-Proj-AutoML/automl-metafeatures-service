from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MetaFeaturesResponse(BaseModel):
    dataset_id: int
    features: dict
    computed_at: datetime
    cached: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["connected", "unreachable"]
    data_service: Literal["reachable", "unreachable", "unknown"]

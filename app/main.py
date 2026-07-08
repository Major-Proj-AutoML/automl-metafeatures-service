"""FastAPI entry point for the automl-metafeatures-service."""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.data_service_client import DataServiceClient
from app.db import get_session
from app.schemas import HealthResponse, MetaFeaturesResponse
from app.service import compute_and_cache, delete_cached, fetch_cached

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="automl-metafeatures-service",
    version="0.1.0",
    description="Meta-feature extraction for tabular datasets. Given a dataset id, "
    "computes and caches simple/distributional/information/landmarking meta-features.",
)


def get_data_client() -> DataServiceClient:
    return DataServiceClient()


@app.get("/health", response_model=HealthResponse)
def health(
    session: Session = Depends(get_session),
    client: DataServiceClient = Depends(get_data_client),
) -> HealthResponse:
    db_ok = False
    try:
        session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    ds_ok = client.ping()
    if db_ok and ds_ok:
        return HealthResponse(status="ok", database="connected", data_service="reachable")
    return HealthResponse(
        status="degraded",
        database="connected" if db_ok else "unreachable",
        data_service="reachable" if ds_ok else "unreachable",
    )


@app.post("/meta-features/{dataset_id}", response_model=MetaFeaturesResponse, status_code=201)
def compute(
    dataset_id: int,
    force: bool = Query(False, description="Recompute even if cached."),
    session: Session = Depends(get_session),
    client: DataServiceClient = Depends(get_data_client),
) -> MetaFeaturesResponse:
    rec, cached = compute_and_cache(session, dataset_id, client, force=force)
    return MetaFeaturesResponse(
        dataset_id=rec.dataset_id,
        features=rec.features,
        computed_at=rec.computed_at,
        cached=cached,
    )


@app.get("/meta-features/{dataset_id}", response_model=MetaFeaturesResponse)
def get(
    dataset_id: int, session: Session = Depends(get_session)
) -> MetaFeaturesResponse:
    rec = fetch_cached(session, dataset_id)
    return MetaFeaturesResponse(
        dataset_id=rec.dataset_id,
        features=rec.features,
        computed_at=rec.computed_at,
        cached=True,
    )


@app.delete("/meta-features/{dataset_id}", status_code=204)
def delete(dataset_id: int, session: Session = Depends(get_session)) -> None:
    delete_cached(session, dataset_id)

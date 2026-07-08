"""Business logic. Thin wrapper over ``src.meta_features.extractor.extract``."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.contracts import TaskType
from src.meta_features.extractor import extract as extract_meta

from app.data_service_client import DataServiceClient
from app.models import MetaFeaturesRecord


def _load_train_df(train_path: str) -> pd.DataFrame:
    p = Path(train_path)
    if not p.exists():
        raise HTTPException(
            status_code=410,
            detail=f"Training CSV no longer exists on disk: {train_path}",
        )
    return pd.read_csv(p)


def compute_and_cache(
    session: Session,
    dataset_id: int,
    client: DataServiceClient,
    *,
    force: bool = False,
) -> tuple[MetaFeaturesRecord, bool]:
    """Return (record, cached).

    ``cached=True`` means the DB already had a valid row and we didn't recompute.
    ``force=True`` recomputes and overwrites."""
    if not force:
        existing = session.scalar(
            select(MetaFeaturesRecord).where(MetaFeaturesRecord.dataset_id == dataset_id)
        )
        if existing is not None:
            return existing, True

    ds = client.get_dataset(dataset_id)
    df_train = _load_train_df(ds["train_path"])

    meta = extract_meta(
        df_train,
        target_col=ds["target_col"],
        dataset_id=ds["name"],
        task_type=TaskType(ds["task_type"]),
    )
    features_dict = json.loads(meta.model_dump_json())

    existing = session.scalar(
        select(MetaFeaturesRecord).where(MetaFeaturesRecord.dataset_id == dataset_id)
    )
    if existing is not None:
        existing.features = features_dict
        record = existing
    else:
        record = MetaFeaturesRecord(dataset_id=dataset_id, features=features_dict)
        session.add(record)
    session.commit()
    session.refresh(record)
    return record, False


def fetch_cached(session: Session, dataset_id: int) -> MetaFeaturesRecord:
    rec = session.scalar(
        select(MetaFeaturesRecord).where(MetaFeaturesRecord.dataset_id == dataset_id)
    )
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached meta-features for dataset {dataset_id}. "
            "POST /meta-features/{dataset_id} to compute.",
        )
    return rec


def delete_cached(session: Session, dataset_id: int) -> None:
    rec = fetch_cached(session, dataset_id)
    session.delete(rec)
    session.commit()

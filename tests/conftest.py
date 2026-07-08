"""Pytest fixtures for automl-metafeatures-service.

Uses SQLite in-memory instead of Postgres, and a stub for the DataServiceClient
so tests don't need automl-data-service or an actual CSV on disk beyond a
throwaway one we write per-test."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DATA_SERVICE_URL", "http://stub-data-service")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.data_service_client import DataServiceClient  # noqa: E402
from app.db import Base, get_session  # noqa: E402
from app.main import app, get_data_client  # noqa: E402
from app import models  # noqa: F401, E402  register table


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class _StubDataServiceClient(DataServiceClient):
    """Overrides HTTP calls with in-memory dict lookups."""

    def __init__(self, datasets: dict[int, dict]) -> None:
        self._datasets = datasets
        self.base_url = "stub"
        self.timeout = 1.0

    def get_dataset(self, dataset_id: int):
        from fastapi import HTTPException

        if dataset_id not in self._datasets:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        return self._datasets[dataset_id]

    def ping(self) -> bool:  # type: ignore[override]
        return True


@pytest.fixture(scope="function")
def make_dataset(tmp_path):
    """Factory: writes a small CSV to disk and returns a dataset-service-shaped dict."""

    def _factory(
        dataset_id: int = 1, target: str = "label", n_rows: int = 60
    ) -> dict:
        csv = tmp_path / f"train_{dataset_id}.csv"
        header = f"a,b,{target}\n"
        rows = "\n".join(f"{i % 3},{i * 0.1:.3f},{i % 2}" for i in range(n_rows))
        csv.write_text(header + rows, encoding="utf-8")

        return {
            "id": dataset_id,
            "name": f"ds_{dataset_id}",
            "source": "custom",
            "openml_id": None,
            "target_col": target,
            "task_type": "binary_classification",
            "train_path": str(csv),
            "test_path": str(csv),  # reuse; not read
            "n_rows": n_rows,
            "n_cols": 3,
        }

    return _factory


@pytest.fixture(scope="function")
def client(db_session, make_dataset):
    datasets_by_id: dict[int, dict] = {}
    stub = _StubDataServiceClient(datasets_by_id)

    def _override_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_data_client] = lambda: stub
    with TestClient(app) as c:
        c._datasets = datasets_by_id  # type: ignore[attr-defined]
        c._make = make_dataset  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()

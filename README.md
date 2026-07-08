# automl-metafeatures-service

Meta-feature extraction microservice. Port **8002**.

## Responsibilities

- Given a `dataset_id`, fetches dataset metadata from `automl-data-service`.
- Reads the training CSV from disk (shared volume).
- Computes the four meta-feature groups: simple, distributional, information, landmarking (from `automl-reusables`).
- Caches the result in Postgres. Second call returns cached result unless `?force=true`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + DB + data-service reachability |
| POST | `/meta-features/{dataset_id}` | Compute & cache. `?force=true` to recompute |
| GET | `/meta-features/{dataset_id}` | Fetch cached result (404 if never computed) |
| DELETE | `/meta-features/{dataset_id}` | Drop cached result |

Interactive docs at `http://localhost:8002/docs`.

## Depends on

- `automl-reusables` (installed editable from `../automl-reusables`)
- `automl-data-service` reachable via HTTP for dataset metadata (`DATA_SERVICE_URL` env var)
- Postgres from `automl-infra`

## Local run

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools
pip install -e ../automl-reusables
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8002
```

## Tests

Uses SQLite in-memory + a stubbed data-service client. No infra required:

```bash
pytest -v
```

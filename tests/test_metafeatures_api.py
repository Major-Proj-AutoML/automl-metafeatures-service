from __future__ import annotations


def _register(client, dataset_id: int = 1):
    ds = client._make(dataset_id=dataset_id)  # type: ignore[attr-defined]
    client._datasets[dataset_id] = ds  # type: ignore[attr-defined]
    return ds


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["database"] == "connected"
    assert body["data_service"] == "reachable"


def test_compute_and_cache(client):
    _register(client, 1)
    r = client.post("/meta-features/1")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["dataset_id"] == 1
    assert body["cached"] is False
    features = body["features"]
    # sanity: known keys from MetaFeatures Pydantic model
    for key in ("simple", "distributional", "information", "landmarks", "task_type"):
        assert key in features


def test_second_call_returns_cached(client):
    _register(client, 1)
    r1 = client.post("/meta-features/1")
    assert r1.json()["cached"] is False
    r2 = client.post("/meta-features/1")
    assert r2.status_code == 201
    assert r2.json()["cached"] is True


def test_force_recomputes(client):
    _register(client, 1)
    client.post("/meta-features/1")
    r = client.post("/meta-features/1?force=true")
    assert r.status_code == 201
    assert r.json()["cached"] is False


def test_get_before_compute_returns_404(client):
    _register(client, 1)
    r = client.get("/meta-features/1")
    assert r.status_code == 404


def test_get_after_compute(client):
    _register(client, 1)
    client.post("/meta-features/1")
    r = client.get("/meta-features/1")
    assert r.status_code == 200
    assert r.json()["cached"] is True


def test_unknown_dataset_returns_404(client):
    r = client.post("/meta-features/999")
    assert r.status_code == 404


def test_delete_cached(client):
    _register(client, 1)
    client.post("/meta-features/1")
    r = client.delete("/meta-features/1")
    assert r.status_code == 204
    r = client.get("/meta-features/1")
    assert r.status_code == 404

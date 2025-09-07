from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard import build_app


def test_metrics_protected(monkeypatch):
    monkeypatch.setenv("OW_SC_METRICS_PROTECT", "1")
    monkeypatch.setenv("OW_SC_API_TOKEN", "secret")
    app = build_app()
    client = TestClient(app)

    r = client.get("/metrics")
    assert r.status_code == 401

    r2 = client.get("/metrics", headers={"Authorization": "Bearer secret"})
    assert r2.status_code == 200 and "stream_buffer_len" in r2.text


def test_metrics_token_separate(monkeypatch):
    monkeypatch.setenv("OW_SC_METRICS_PROTECT", "1")
    monkeypatch.setenv("OW_SC_API_TOKEN", "api-token")
    monkeypatch.setenv("OW_SC_METRICS_TOKEN", "metrics-token")
    app = build_app()
    client = TestClient(app)

    # API token should not work for metrics if metrics token is set
    r = client.get("/metrics", headers={"Authorization": "Bearer api-token"})
    assert r.status_code == 401

    # Metrics token works
    r2 = client.get("/metrics", headers={"Authorization": "Bearer metrics-token"})
    assert r2.status_code == 200

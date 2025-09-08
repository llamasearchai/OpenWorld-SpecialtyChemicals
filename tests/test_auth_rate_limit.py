from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard import build_app


def test_api_token_auth_http(monkeypatch):
    monkeypatch.setenv("OW_SC_API_TOKEN", "secret")
    app = build_app()
    client = TestClient(app)

    # Missing token -> 401
    r = client.get("/api/status")
    assert r.status_code == 401

    # With token -> 200
    r2 = client.get("/api/status", headers={"Authorization": "Bearer secret"})
    assert r2.status_code == 200


def test_rate_limit_http(monkeypatch):
    # Very small limit to trigger 429
    monkeypatch.setenv("OW_SC_RL_PER_SEC", "2")
    app = build_app()
    client = TestClient(app)
    # Send multiple requests quickly; third should be 429
    client.get("/api/status")
    client.get("/api/status")
    r = client.get("/api/status")
    assert r.status_code == 429


def test_ws_token_auth(monkeypatch):
    monkeypatch.setenv("OW_SC_API_TOKEN", "secret")
    app = build_app()
    client = TestClient(app)

    # Missing token -> policy close
    failed = False
    try:
        with client.websocket_connect("/ws/effluent") as ws:
            pass
    except Exception:
        failed = True
    assert failed

    # With token -> accepted
    with client.websocket_connect("/ws/effluent", headers={"Authorization": "Bearer secret"}) as ws:
        ws.send_json({"species": "SO4", "time": 0, "concentration": 1.0})

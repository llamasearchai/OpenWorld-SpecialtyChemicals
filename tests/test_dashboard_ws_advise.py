from typing import Any, Dict

from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard import build_app


def test_health_streams_and_observability():
    app = build_app(max_buffer=8)
    c = TestClient(app)
    assert c.get("/health").json()["status"] == "ok"
    assert c.get("/livez").json()["status"] == "live"
    assert c.get("/readyz").json()["status"] == "ready"
    # Metrics returns text with a known metric name
    m = c.get("/metrics").text
    assert "stream_buffer_len" in m
    # No streams yet
    assert c.get("/streams").json() == []


def test_ws_buffer_and_advise():
    app = build_app(max_buffer=4)
    c = TestClient(app)
    with c.websocket_connect("/ws/effluent") as ws:
        ws.send_json({"time": 0, "species": "SO4", "concentration": 10.0})
        ws.send_json({"time": 1, "species": "SO4", "concentration": 9.5})
    # Buffer contains sent items
    items = c.get("/streams").json()
    assert len(items) == 2 and items[-1]["concentration"] == 9.5

    payload = {
        "alerts": [
            {"time": 1, "species": "SO4", "value": 260.0, "limit": 250.0},
            {"time": 2, "species": "As", "value": 0.02, "limit": 0.01},
        ]
    }
    r = c.post("/advise", json=payload)
    data: Dict[str, Any] = r.json()
    assert r.status_code == 200 and isinstance(data.get("actions"), list)
    assert any("SO4" in a for a in data["actions"]) or any("As" in a for a in data["actions"])



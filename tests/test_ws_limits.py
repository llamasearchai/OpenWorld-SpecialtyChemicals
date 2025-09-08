from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard import build_app


def test_ws_message_size_limit(monkeypatch):
    # Set a very low limit to trigger violation
    monkeypatch.setenv("OW_SC_WS_MAX_MESSAGE_BYTES", "10")
    app = build_app()
    client = TestClient(app)

    with client.websocket_connect("/ws/effluent") as ws:
        # Create a message larger than 10 bytes
        msg = {"species": "SO4", "concentration": 123.456, "time": 0}
        ws.send_json(msg)

    # Check metrics for errors count > 0
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "ws_errors_total" in body
    # value after the metric name indicates increment occurred
    # can't be zero if the message was oversized and counted
    lines = [ln for ln in body.splitlines() if ln.startswith("ws_errors_total ")]
    assert lines, body
    val = float(lines[0].split()[1])
    assert val >= 1.0


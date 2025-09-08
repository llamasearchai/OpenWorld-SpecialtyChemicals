import asyncio

from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard.server import app, broadcaster


def test_dashboard_health_and_ws():
    c = TestClient(app)
    assert c.get("/api/health").json()["status"] == "ok"
    with c.websocket_connect("/ws/effluent") as ws:
        # publish a message
        asyncio.get_event_loop().run_until_complete(broadcaster.publish({"seq":0,"pH":7.2}))
        data = ws.receive_json()
        assert "pH" in data



from fastapi.testclient import TestClient

from openworld_specialty_chemicals.dashboard import build_app


def test_security_headers_present():
    app = build_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    # Basic security headers
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "Content-Security-Policy" in r.headers


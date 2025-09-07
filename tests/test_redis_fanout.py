import pytest
from openworld_specialty_chemicals.dashboard import build_app


def test_redis_channel_config(monkeypatch: pytest.MonkeyPatch):
    # Guarded: only checks configuration wiring without requiring Redis
    monkeypatch.setenv("OW_SC_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OW_SC_REDIS_CHANNEL", "test-chan")
    app = build_app()
    assert getattr(app.state, "redis_channel", None) == "test-chan"


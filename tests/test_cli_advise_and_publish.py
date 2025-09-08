import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from typer.testing import CliRunner

from openworld_specialty_chemicals.cli import app

runner = CliRunner()


def test_cli_advise_command(tmp_path: Path):
    alerts = {
        "alerts": [
            {"time": 0, "species": "SO4", "value": 260.0, "limit": 250.0}
        ]
    }
    p = tmp_path / "alerts.json"
    p.write_text(json.dumps(alerts), encoding="utf-8")
    res = runner.invoke(app, [
        "advise",
        "--alerts", str(p),
        "--site", "Plant A",
    ])
    assert res.exit_code == 0, res.output
    out = json.loads(res.stdout)
    assert out["site"] == "Plant A" and isinstance(out["actions"], list)


def test_cli_simulate_stream_publish_ws_stub(tmp_path: Path, monkeypatch):
    # Create a small batch file
    df = pd.DataFrame({"time": [0, 1], "species": ["SO4", "SO4"], "concentration": [10.0, 9.5]})
    p = tmp_path / "batch.csv"
    df.to_csv(p, index=False)

    sent = []

    class _StubConn:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def send_json(self, obj):  # exercised _pub path
            sent.append(("json", obj))

        async def send(self, s):  # exercised _pub_fallback path when forced
            sent.append(("text", s))

    class _Connect:
        def __call__(self, url):
            return self

        async def __aenter__(self):
            return _StubConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    # Inject stub websockets module into CLI namespace
    monkeypatch.setitem(
        __import__("sys").modules,
        "websockets",
        SimpleNamespace(connect=_Connect())
    )

    res = runner.invoke(app, [
        "simulate-stream",
        "--source", str(p),
        "--delay", "0.0",
        "--publish-ws", "ws://stub/effluent",
    ])
    assert res.exit_code == 0, res.output
    assert len(sent) >= 2



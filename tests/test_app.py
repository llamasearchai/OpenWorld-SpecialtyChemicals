import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from openworld_specialty_chemicals import chemistry, dashboard, io as io_mod, reporting, rules, streaming
from openworld_specialty_chemicals.cli import app as cli_app


runner = CliRunner()


def make_batch_df() -> pd.DataFrame:
    # Exponential-ish decay for SO4
    t = np.arange(0, 6, dtype=float)
    c0 = 20.0
    k_true = 0.2
    c = c0 * np.exp(-k_true * t)
    return pd.DataFrame({"time": t, "species": ["SO4"] * len(t), "concentration": c})


def test_io_read_write_json(tmp_path: Path):
    data = {"x": 1, "y": [1, 2, 3]}
    p = tmp_path / "out.json"
    io_mod.write_json(p, data)
    back = io_mod.read_json(p)
    assert back == data


def test_io_jsonl(tmp_path: Path):
    recs = [{"a": 1}, {"a": 2}]
    p = tmp_path / "out.jsonl"
    io_mod.write_jsonl(p, recs)
    back = io_mod.read_jsonl(p)
    assert back == recs


def test_io_read_batch_csv_and_errors(tmp_path: Path):
    # Missing file error
    with pytest.raises(FileNotFoundError):
        io_mod.read_batch_csv(tmp_path / "missing.csv")

    # Missing columns error
    p = tmp_path / "bad.csv"
    pd.DataFrame({"time": [0], "species": ["SO4"]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        io_mod.read_batch_csv(p)

    # Good file
    p2 = tmp_path / "good.csv"
    make_batch_df().to_csv(p2, index=False)
    df = io_mod.read_batch_csv(p2)
    assert set(df.columns) == {"time", "species", "concentration"}


def test_chemistry_fit_parameters_paths():
    df = make_batch_df()
    res = chemistry.fit_parameters(df, "SO4")
    assert res.species == "SO4"
    assert res.k >= 0 and res.kd > 0
    d = res.to_dict()
    assert set(d.keys()) == {"species", "k", "Kd"}

    # Species not found
    with pytest.raises(ValueError):
        chemistry.fit_parameters(df, "NO3")

    # Not enough points branch
    df2 = df.iloc[:1]
    res2 = chemistry.fit_parameters(df2, "SO4")
    assert res2.k == 0 and res2.kd == 0


def test_rules_alerts_and_suggestions():
    df = make_batch_df()
    permit = {"limits": {"SO4": float(df["concentration"].min() - 1)}}
    alerts = rules.check_permit(df, permit)
    assert isinstance(alerts, list) and len(alerts) > 0
    sugg = rules.suggest_remediation(alerts)
    assert len(sugg) == len(alerts) and sugg[0]["suggestion"].startswith("Increase")

    # No alerts branch
    permit2 = {"limits": {"SO4": float(df["concentration"].max() + 1)}}
    alerts2 = rules.check_permit(df, permit2)
    assert alerts2 == []


def test_streaming_simulate_and_errors(tmp_path: Path):
    df = make_batch_df()
    p = tmp_path / "stream.csv"
    df.to_csv(p, index=False)
    rows = list(streaming.simulate_stream(p, delay=0.0))
    assert len(rows) == len(df)

    # Missing columns error path
    p2 = tmp_path / "bad.csv"
    pd.DataFrame({"time": [0], "species": ["SO4"]}).to_csv(p2, index=False)
    with pytest.raises(ValueError):
        list(streaming.simulate_stream(p2))


def test_dashboard_app_health():
    app = dashboard.build_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"
    r2 = client.get("/api/streams")
    assert r2.status_code == 200 and r2.json()["count"] == 0


def test_reporting_certificate():
    html = reporting.generate_certificate([], site="Plant A")
    assert "COMPLIANT" in html and "Plant A" in html
    html2 = reporting.generate_certificate([{"time": 0, "species": "SO4", "value": 5, "limit": 1}], site="B")
    assert "NON-COMPLIANT" in html2 and "SO4" in html2


def test_cli_commands_end_to_end(tmp_path: Path):
    df = make_batch_df()
    batch = tmp_path / "batch.csv"
    df.to_csv(batch, index=False)
    permit = tmp_path / "permit.json"
    limits = {"limits": {"SO4": float(df["concentration"].mean())}}
    permit.write_text(json.dumps(limits), encoding="utf-8")

    # process-chemistry
    out_fit = tmp_path / "fit.json"
    res = runner.invoke(cli_app, [
        "process-chemistry",
        "--input", str(batch),
        "--species", "SO4",
        "--out", str(out_fit),
    ])
    assert res.exit_code == 0, res.output
    fit = json.loads(out_fit.read_text(encoding="utf-8"))
    assert set(fit.keys()) == {"species", "k", "Kd"}

    # monitor-batch
    out_alerts = tmp_path / "alerts.json"
    res2 = runner.invoke(cli_app, [
        "monitor-batch",
        "--input", str(batch),
        "--permit", str(permit),
        "--out", str(out_alerts),
    ])
    assert res2.exit_code == 0, res2.output
    payload = json.loads(out_alerts.read_text(encoding="utf-8"))
    assert "count" in payload and "alerts" in payload

    # cert
    out_html = tmp_path / "cert.html"
    res3 = runner.invoke(cli_app, [
        "cert",
        "--alerts", str(out_alerts),
        "--site", "Plant A",
        "--out", str(out_html),
    ])
    assert res3.exit_code == 0, res3.output
    assert "Compliance Certificate" in out_html.read_text(encoding="utf-8")

    # dashboard (no serve)
    res4 = runner.invoke(cli_app, ["dashboard", "--serve", "False"])
    assert res4.exit_code == 0, res4.output

    # simulate-stream (stdout) and (jsonl)
    res5 = runner.invoke(cli_app, [
        "simulate-stream",
        "--source", str(batch),
        "--delay", "0.0",
    ])
    assert res5.exit_code == 0, res5.output

    out_jsonl = tmp_path / "stream.jsonl"
    res6 = runner.invoke(cli_app, [
        "simulate-stream",
        "--source", str(batch),
        "--delay", "0.0",
        "--out", str(out_jsonl),
    ])
    assert res6.exit_code == 0, res6.output
    assert out_jsonl.exists() and out_jsonl.read_text(encoding="utf-8").strip() != ""


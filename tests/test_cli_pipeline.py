import os, json
import pandas as pd
from typer.testing import CliRunner
from openworld_specialty_chemicals.cli import app

def test_cli_e2e(tmp_path, monkeypatch):
    runner = CliRunner()
    data_dir = tmp_path / "data"
    artifacts = tmp_path / "artifacts"
    reports = tmp_path / "reports"
    os.makedirs(data_dir, exist_ok=True)

    df = pd.DataFrame({"time_h":[0,1,2,3], "SO4_mgL":[220,210,205,260], "As_mgL":[0.005,0.006,0.007,0.008]})
    p = data_dir/"lab.csv"; df.to_csv(p, index=False)

    r1 = runner.invoke(app, ["process-chemistry","--input", str(p), "--species","SO4","--out", str(artifacts/"so4_fit.json")])
    assert r1.exit_code == 0 and (artifacts/"so4_fit.json").exists()

    r2 = runner.invoke(app, ["monitor-batch","--input", str(p), "--out", str(artifacts/"alerts.json")])
    assert r2.exit_code == 0 and (artifacts/"alerts.json").exists()

    r3 = runner.invoke(app, ["cert","--alerts", str(artifacts/"alerts.json"), "--site", "Plant A", "--out", str(reports/"cert.html")])
    assert r3.exit_code == 0 and (reports/"cert.html").exists()

    r4 = runner.invoke(app, ["advise","--alerts", str(artifacts/"alerts.json"), "--site", "Plant A"])
    assert r4.exit_code == 0



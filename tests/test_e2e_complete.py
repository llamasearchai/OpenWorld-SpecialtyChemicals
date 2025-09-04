import json
import tempfile
import os
from pathlib import Path
import pandas as pd
from typer.testing import CliRunner

from openworld_specialty_chemicals.cli import app
from openworld_specialty_chemicals.chemistry import fit_parameters
from openworld_specialty_chemicals.rules import check_permit
from openworld_specialty_chemicals.reporting import generate_certificate
from openworld_specialty_chemicals.agents.fake_agent import FakeAdviceAgent


runner = CliRunner()


def create_sample_data():
    """Create sample batch data for testing."""
    df = pd.DataFrame({
        "time": [0, 1, 2, 3, 4],
        "species": ["SO4"] * 5,
        "concentration": [100, 110, 120, 130, 140]
    })
    return df


def test_complete_e2e_pipeline(tmp_path: Path):
    """Test the complete end-to-end pipeline from data to certificate."""
    # Create sample data
    df = create_sample_data()
    batch_file = tmp_path / "batch.csv"
    df.to_csv(batch_file, index=False)

    # Create permit file
    permit_data = {"limits": {"SO4": 120.0}, "rolling_window": 3}
    permit_file = tmp_path / "permit.json"
    permit_file.write_text(json.dumps(permit_data))

    # Test chemistry fitting
    result = fit_parameters(df, "SO4")
    assert result.species == "SO4"
    assert result.k >= 0
    assert result.kd > 0

    # Test rule evaluation
    alerts = check_permit(df, permit_data)
    assert len(alerts) > 0
    assert any(a["species"] == "SO4" for a in alerts)

    # Test certificate generation
    html = generate_certificate(alerts, "Test Site")
    assert "Test Site" in html
    assert "NON-COMPLIANT" in html

    # Test CLI commands
    # 1. process-chemistry
    fit_out = tmp_path / "fit.json"
    res1 = runner.invoke(app, [
        "process-chemistry",
        "--input", str(batch_file),
        "--species", "SO4",
        "--out", str(fit_out)
    ])
    assert res1.exit_code == 0
    assert fit_out.exists()

    # 2. monitor-batch
    alerts_out = tmp_path / "alerts.json"
    res2 = runner.invoke(app, [
        "monitor-batch",
        "--input", str(batch_file),
        "--permit", str(permit_file),
        "--out", str(alerts_out)
    ])
    assert res2.exit_code == 0
    assert alerts_out.exists()

    # 3. cert
    cert_out = tmp_path / "cert.html"
    res3 = runner.invoke(app, [
        "cert",
        "--alerts", str(alerts_out),
        "--site", "Test Site",
        "--out", str(cert_out)
    ])
    assert res3.exit_code == 0
    assert cert_out.exists()

    # 4. advise
    res4 = runner.invoke(app, [
        "advise",
        "--alerts", str(alerts_out),
        "--site", "Test Site"
    ])
    assert res4.exit_code == 0
    output = json.loads(res4.stdout)
    assert "site" in output
    assert "actions" in output


def test_agent_integration():
    """Test the advice agent integration."""
    alerts = [
        {"species": "SO4", "value": 260.0, "limit": 250.0},
        {"species": "As", "value": 0.02, "limit": 0.01}
    ]

    agent = FakeAdviceAgent()
    result = agent.advise(alerts)

    assert "actions" in result
    assert "rationale" in result
    assert len(result["actions"]) > 0
    assert any("SO4" in action for action in result["actions"])


def test_streaming_functionality(tmp_path: Path):
    """Test streaming functionality."""
    df = create_sample_data()
    csv_file = tmp_path / "stream.csv"
    df.to_csv(csv_file, index=False)

    # Test streaming simulation
    from openworld_specialty_chemicals.streaming import simulate_stream
    rows = list(simulate_stream(str(csv_file), delay=0.0))
    assert len(rows) == len(df)
    assert all("time" in row for row in rows)
    assert all("species" in row for row in rows)
    assert all("concentration" in row for row in rows)

from pathlib import Path

from typer.testing import CliRunner

from openworld_specialty_chemicals.cli import app

runner = CliRunner()


def test_dry_run_skips_writes(tmp_path: Path):
    # Prepare CSV
    p = tmp_path / "batch.csv"
    p.write_text("time,species,concentration\n0,SO4,1\n", encoding="utf-8")

    out_fit = tmp_path / "fit.json"
    res = runner.invoke(app, [
        "--dry-run",
        "process-chemistry",
        "--input", str(p),
        "--species", "SO4",
        "--out", str(out_fit),
    ])
    assert res.exit_code == 0, res.output
    assert not out_fit.exists()

    out_alerts = tmp_path / "alerts.json"
    res2 = runner.invoke(app, [
        "--dry-run",
        "monitor-batch",
        "--input", str(p),
        "--out", str(out_alerts),
    ])
    assert res2.exit_code == 0, res2.output
    assert not out_alerts.exists()


from pathlib import Path
import json
from typer.testing import CliRunner

from openworld_specialty_chemicals.cli import app


runner = CliRunner()


def test_missing_input_file_exit_code(tmp_path: Path):
    # process-chemistry with missing input -> NOT_FOUND (3)
    res = runner.invoke(app, [
        "process-chemistry",
        "--input", str(tmp_path / "missing.csv"),
        "--species", "SO4",
    ])
    assert res.exit_code == 3, res.output


def test_invalid_alerts_format_exit_code(tmp_path: Path):
    # cert with invalid JSON shape -> VALIDATION (4)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not_alerts": []}), encoding="utf-8")
    res = runner.invoke(app, [
        "cert",
        "--alerts", str(bad),
        "--site", "X",
    ])
    assert res.exit_code == 4, res.output


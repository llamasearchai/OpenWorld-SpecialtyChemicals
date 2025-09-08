from pathlib import Path

import pandas as pd
import pytest

from openworld_specialty_chemicals import io as io_mod


def test_row_limit_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OW_SC_MAX_CSV_ROWS", "1")
    p = tmp_path / "rows.csv"
    pd.DataFrame({
        "time": [0, 1],
        "species": ["SO4", "SO4"],
        "concentration": [1.0, 2.0],
    }).to_csv(p, index=False)
    with pytest.raises(ValueError):
        io_mod.read_batch_csv(p)


def test_file_size_limit_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OW_SC_MAX_CSV_BYTES", "10")
    p = tmp_path / "size.csv"
    # This CSV will exceed 10 bytes
    pd.DataFrame({
        "time": [0],
        "species": ["SO4"],
        "concentration": [1.0],
    }).to_csv(p, index=False)
    with pytest.raises(ValueError):
        io_mod.read_batch_csv(p)


def test_dtype_and_nan_validation(tmp_path: Path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({
        "time": [0, 1],
        "species": ["SO4", "SO4"],
        "concentration": ["nope", 2.0],
    }).to_csv(p, index=False)
    with pytest.raises(ValueError):
        io_mod.read_batch_csv(p)


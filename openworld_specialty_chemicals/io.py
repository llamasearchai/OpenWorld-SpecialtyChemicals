from __future__ import annotations
import json
from pathlib import Path
import os
import numpy as np
import pandas as pd


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def read_batch_csv(path: Path) -> pd.DataFrame:
    """Read a batch CSV with schema and size limits.

    Env overrides:
      - OW_SC_MAX_CSV_BYTES (default: 10_485_760 bytes)
      - OW_SC_MAX_CSV_ROWS (default: 1_000_000 rows)
    """
    if not path.exists():
        raise FileNotFoundError(str(path))

    max_bytes = int(os.getenv("OW_SC_MAX_CSV_BYTES", "10485760"))
    max_rows = int(os.getenv("OW_SC_MAX_CSV_ROWS", "1000000"))

    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"CSV file too large: {size} bytes > limit {max_bytes}")

    # Read and validate
    df = pd.read_csv(path)
    required = {"time", "species", "concentration"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV missing required columns: {required}")

    # Row limit
    if len(df) > max_rows:
        raise ValueError(f"CSV has too many rows: {len(df)} > limit {max_rows}")

    # Type checks and coercion
    try:
        df["time"] = pd.to_numeric(df["time"], errors="raise")
        df["concentration"] = pd.to_numeric(df["concentration"], errors="raise")
    except Exception as e:
        raise ValueError(f"CSV contains non-numeric values in time/concentration: {e}")

    # Basic sanity checks
    if np.isnan(df["time"]).any() or np.isnan(df["concentration"]).any():
        raise ValueError("CSV contains NaN in time or concentration")

    return df

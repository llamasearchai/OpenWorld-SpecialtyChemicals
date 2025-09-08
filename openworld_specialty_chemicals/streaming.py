from __future__ import annotations

import time as _time
from pathlib import Path
from typing import Dict, Generator, Iterable

import pandas as pd


def stream_rows(df: pd.DataFrame, delay: float = 0.0) -> Generator[Dict, None, None]:
    for _, row in df.iterrows():
        yield {
            "time": float(row["time"]),
            "species": row["species"],
            "concentration": float(row["concentration"])
        }
        if delay > 0:
            _time.sleep(delay)

def simulate_stream(source_csv: str | Path, delay: float = 0.0) -> Iterable[Dict]:
    df = pd.read_csv(source_csv)
    required = {"time", "species", "concentration"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    return stream_rows(df, delay=delay)

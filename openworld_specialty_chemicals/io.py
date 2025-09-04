from __future__ import annotations
import json
from pathlib import Path
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
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path)
    required = {"time", "species", "concentration"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV missing required columns: {required}")
    return df


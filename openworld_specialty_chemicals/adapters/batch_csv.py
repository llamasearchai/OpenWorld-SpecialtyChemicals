from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def ingest_batch_csv(path: str) -> Dict[str, Any]:
    df = pd.read_csv(path)
    return {"type": "batch", "data": df, "metadata": {"source": path}}



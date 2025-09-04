from __future__ import annotations
import pandas as pd
from typing import Dict, Any

def ingest_batch_csv(path: str) -> Dict[str, Any]:
    df = pd.read_csv(path)
    return {"type": "batch", "data": df, "metadata": {"source": path}}



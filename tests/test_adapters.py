import asyncio

import pandas as pd

from openworld_specialty_chemicals.adapters.batch_csv import ingest_batch_csv
from openworld_specialty_chemicals.adapters.streaming import stream_csv_rows


def test_ingest_batch_csv(tmp_path):
    p = tmp_path / "b.csv"
    pd.DataFrame({"time_h":[0,1], "SO4_mgL":[200,198]}).to_csv(p, index=False)
    out = ingest_batch_csv(str(p))
    assert out["type"] == "batch" and len(out["data"]) == 2

def test_stream_csv_rows(tmp_path):
    p = tmp_path / "s.csv"
    pd.DataFrame({"seq":[0,1], "flow_lps":[10,11]}).to_csv(p, index=False)
    async def collect():
        rows = []
        async for row in stream_csv_rows(str(p), delay_s=0):
            rows.append(row)
        return rows
    rows = asyncio.run(collect())
    assert len(rows) == 2 and "flow_lps" in rows[0]



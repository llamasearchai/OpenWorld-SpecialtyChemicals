from __future__ import annotations

import asyncio
import csv
from typing import AsyncIterator


async def stream_csv_rows(path: str, delay_s: float = 0.1) -> AsyncIterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: (float(v) if v.replace('.','',1).isdigit() else v) for k, v in row.items()}
            await asyncio.sleep(delay_s)

class StreamBroadcaster:
    def __init__(self) -> None:
        self._subs: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    async def publish(self, item: dict) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                # drop for slow consumers
                pass



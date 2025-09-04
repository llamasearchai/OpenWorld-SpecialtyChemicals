from __future__ import annotations
import os, json, asyncio
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from ..adapters.streaming import StreamBroadcaster

app = FastAPI(title="OpenWorld Specialty Chemicals Dashboard")
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

broadcaster = StreamBroadcaster()

def _ensure_event_loop() -> None:
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:  # no loop set for this thread
        pass
    if loop is None or not loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

_ensure_event_loop()

# Make asyncio.get_event_loop() always return a usable loop for sync test contexts
_orig_get_event_loop = asyncio.get_event_loop
def _get_event_loop_safe():  # pragma: no cover
    try:
        return _orig_get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
asyncio.get_event_loop = _get_event_loop_safe  # type: ignore[assignment]

# Install a tolerant event loop policy so asyncio.get_event_loop() never fails
class _TolerantPolicy(asyncio.DefaultEventLoopPolicy):  # type: ignore[attr-defined]
    def get_event_loop(self):  # type: ignore[override]
        try:
            return super().get_event_loop()
        except RuntimeError:
            loop = self.new_event_loop()
            self.set_event_loop(loop)
            return loop

try:  # pragma: no cover
    asyncio.set_event_loop_policy(_TolerantPolicy())
except Exception:
    pass

@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.websocket("/ws/effluent")
async def ws_effluent(ws: WebSocket):
    await ws.accept()
    q = broadcaster.subscribe()
    try:
        while True:
            item = await q.get()
            await ws.send_json(item)
    except WebSocketDisconnect:
        broadcaster.unsubscribe(q)



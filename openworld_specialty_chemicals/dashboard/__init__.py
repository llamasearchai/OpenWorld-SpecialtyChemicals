from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


def build_app(max_buffer: int = 1024) -> FastAPI:
    """Build and configure the dashboard FastAPI application with enhanced monitoring."""
    app = FastAPI(
        title="OpenWorld Specialty Chemicals Dashboard API",
        description="Environmental compliance monitoring and real-time data streaming API",
        version="1.0.0"
    )

    # CORS configuration
    import os as _os
    origins_env = _os.getenv("OW_SC_CORS_ORIGINS", "*")
    origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers and request logging middleware
    # Simple in-memory HTTP rate limiter state
    _rl_state: Dict[str, Dict[str, float | int]] = {}

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        # Ensure X-Request-ID present
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            from uuid import uuid4 as _uuid4
            req_id = _uuid4().hex[:8]
        import time as _time
        start = _time.time()
        # Auth (if token configured) for /api/* endpoints
        token = _os.getenv("OW_SC_API_TOKEN")
        path = request.url.path
        if token and (path.startswith("/api/") or path.startswith("/ws/")):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != token:
                # Short-circuit unauthorized
                resp = JSONResponse({"detail": "Unauthorized"}, status_code=401)
                resp.headers.setdefault("X-Request-ID", req_id)
                return resp

        # Basic HTTP rate limiting for /api/* endpoints
        if path.startswith("/api/"):
            per_sec = int(_os.getenv("OW_SC_RL_PER_SEC", "10"))
            now = _time.time()
            ip = (request.client.host if request.client else "unknown")  # type: ignore[attr-defined]
            key = f"{ip}:{path}"
            state = _rl_state.get(key)
            if not state or now - float(state.get("start", 0.0)) >= 1.0:
                _rl_state[key] = {"start": now, "count": 1}
            else:
                count = int(state.get("count", 0)) + 1
                state["count"] = count
                if count > per_sec:
                    resp = JSONResponse({"detail": "Too Many Requests"}, status_code=429)
                    resp.headers.setdefault("Retry-After", "1")
                    resp.headers.setdefault("X-Request-ID", req_id)
                    return resp

        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", req_id)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        # Basic CSP suited for this app; adjust as needed
        csp = (
            "default-src 'self'; img-src 'self' data:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        # Request logging
        try:
            from ..logging import get_logger, set_correlation_id
            set_correlation_id(req_id)
            log = get_logger("api")
            duration_ms = int((_time.time() - start) * 1000)
            log.info(f"HTTP {request.method} {path} -> {response.status_code} {duration_ms}ms")
        except Exception:
            pass
        return response

    # Application state for streaming buffer and metrics
    app.state.buffer: List[Dict[str, Any]] = []
    app.state.max_buffer = int(max_buffer)
    app.state.registry = CollectorRegistry()
    app.state.buf_gauge = Gauge(
        "stream_buffer_len",
        "Number of items in stream buffer",
        registry=app.state.registry,
    )
    app.state.connections: Dict[str, WebSocket] = {}  # Active WebSocket connections
    app.state.conn_gauge = Gauge(
        "ws_active_connections",
        "Number of active WebSocket connections",
        registry=app.state.registry,
    )
    app.state.conn_total = Counter(
        "ws_connections_total",
        "Total WebSocket connections accepted",
        registry=app.state.registry,
    )
    app.state.msg_recv_total = Counter(
        "ws_messages_received_total",
        "Total WebSocket messages received",
        registry=app.state.registry,
    )
    app.state.msg_broadcast_total = Counter(
        "ws_messages_broadcast_total",
        "Total WebSocket messages broadcast to clients",
        registry=app.state.registry,
    )
    app.state.ws_errors_total = Counter(
        "ws_errors_total",
        "Total WebSocket errors encountered",
        registry=app.state.registry,
    )
    app.state.msg_size_bytes = Histogram(
        "ws_message_size_bytes",
        "WebSocket message payload size in bytes",
        buckets=(64, 128, 256, 512, 1024, 2048, 4096, 8192, float("inf")),
        registry=app.state.registry,
    )

    # Optional Redis fan-out for multi-instance deployments
    app.state.redis = None  # set on startup if configured
    app.state.redis_channel = _os.getenv("OW_SC_REDIS_CHANNEL", "owsc:effluent")
    app.state.instance_id = __import__('uuid').uuid4().hex[:8]

    async def _start_redis_subscriber():
        url = _os.getenv("OW_SC_REDIS_URL")
        if not url:
            return
        try:
            import redis.asyncio as redis  # type: ignore
        except Exception:
            print("Redis not available; install 'redis' to enable fan-out")
            return
        try:
            app.state.redis = redis.from_url(url)
            pubsub = app.state.redis.pubsub()
            await pubsub.subscribe(app.state.redis_channel)
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    import json as _json
                    data = _json.loads(message.get("data").decode("utf-8"))
                    if data.get("origin") == app.state.instance_id:
                        continue
                    disconnected = []
                    for conn_id, ws in app.state.connections.items():
                        try:
                            await ws.send_json(data.get("payload", data))
                            app.state.msg_broadcast_total.inc()
                        except Exception:
                            app.state.ws_errors_total.inc()
                            disconnected.append(conn_id)
                    for cid in disconnected:
                        app.state.connections.pop(cid, None)
                        app.state.conn_gauge.set(len(app.state.connections))
                except Exception:
                    app.state.ws_errors_total.inc()
                    continue
        except Exception as e:
            print(f"Redis subscriber error: {e}")

    @app.on_event("startup")
    async def _startup_redis():
        if _os.getenv("OW_SC_REDIS_URL"):
            import asyncio as _asyncio
            _asyncio.create_task(_start_redis_subscriber())

    @app.get("/health")
    def health():
        """Health check endpoint for load balancer."""
        return {"status": "healthy", "service": "openworld-specialty-chemicals"}

    @app.get("/livez")
    def livez():
        """Kubernetes liveness probe."""
        return {"status": "live", "timestamp": __import__('time').time()}

    @app.get("/readyz")
    def readyz():
        """Kubernetes readiness probe."""
        return {"status": "ready", "buffer_size": len(app.state.buffer)}

    @app.get("/metrics")
    def metrics(request: Request):
        """Prometheus metrics endpoint."""
        # Optional protection for metrics
        protect = _os.getenv("OW_SC_METRICS_PROTECT", "0") == "1"
        if protect:
            api_token = _os.getenv("OW_SC_API_TOKEN")
            m_token = _os.getenv("OW_SC_METRICS_TOKEN") or api_token
            auth = request.headers.get("Authorization", "")
            if not m_token or not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != m_token:
                return PlainTextResponse("Unauthorized", status_code=401)
        app.state.buf_gauge.set(len(app.state.buffer))
        app.state.conn_gauge.set(len(app.state.connections))
        data = generate_latest(app.state.registry)
        return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/streams")
    def get_streams():
        """Get current stream buffer contents."""
        return JSONResponse({
            "count": len(app.state.buffer),
            "data": app.state.buffer[-100:]  # Return last 100 records
        })

    @app.get("/api/status")
    def get_status():
        """Get system status and statistics."""
        return {
            "status": "operational",
            "buffer_size": len(app.state.buffer),
            "max_buffer": app.state.max_buffer,
            "active_connections": len(app.state.connections),
            "uptime": __import__('time').time()
        }

    @app.post("/api/advise")
    def advise_endpoint(payload: Dict[str, Any]):
        """Generate remediation recommendations from alert data."""
        alerts = payload.get("alerts", [])
        actions: List[str] = []

        for alert in alerts:
            species = alert.get("species", "")
            level = alert.get("level", "info")

            if species == "SO4":
                action = "Increase lime dosing; verify gypsum precipitation; reduce discharge rate"
            elif species == "As":
                action = "Adjust pH to 7-8; add ferric coagulant; check filter performance"
            elif species == "Ni":
                action = (
                    "Increase ion exchange cycle; ensure resin regeneration; "
                    "check chelation dosing"
                )
            else:
                action = (
                    f"Review {species} treatment process and verify setpoints"
                    if species
                    else "Increase treatment intensity"
                )

            actions.append(f"[{level.upper()}] {species}: {action}")

        return {
            "alert_count": len(alerts),
            "actions": actions,
            "recommendations": [
                {"species": a.get("species"), "action": actions[i]}
                for i, a in enumerate(alerts)
            ]
        }

    @app.websocket("/ws/effluent")
    async def websocket_effluent(websocket: WebSocket):
        """WebSocket endpoint for real-time effluent data streaming."""
        # Auth (if token configured)
        token = _os.getenv("OW_SC_API_TOKEN")
        if token:
            auth = websocket.headers.get("authorization") or ""
            if not auth.lower().startswith("bearer ") or auth.split(" ", 1)[1] != token:
                await websocket.close(code=1008)  # Policy violation
                return
        client_id = f"client_{id(websocket)}"
        await websocket.accept()
        app.state.connections[client_id] = websocket
        app.state.conn_total.inc()
        app.state.conn_gauge.set(len(app.state.connections))

        try:
            while True:
                # Receive data from client
                data = await websocket.receive_json()
                app.state.msg_recv_total.inc()

                # Add timestamp if not present
                if "timestamp" not in data:
                    data["timestamp"] = __import__('time').time()

                # Enforce WS message size cap and per-connection rate limit
                max_msg = int(_os.getenv("OW_SC_WS_MAX_MESSAGE_BYTES", "8192"))
                msgs_per_sec = int(_os.getenv("OW_SC_WS_MSGS_PER_SEC", "20"))
                import json as _json
                enc = _json.dumps(data).encode("utf-8")
                size = len(enc)
                if size > max_msg:
                    app.state.ws_errors_total.inc()
                    # Skip oversize message
                    continue

                # Simple per-connection fixed window rate limiter
                now = __import__('time').time()
                win = getattr(websocket, "_rl_win_start", None)
                _ = getattr(websocket, "_rl_win_cnt", 0)
                if not win or now - win >= 1.0:
                    websocket._rl_win_start = now
                    websocket._rl_win_cnt = 0
                websocket._rl_win_cnt = getattr(websocket, "_rl_win_cnt", 0) + 1
                if websocket._rl_win_cnt > msgs_per_sec:
                    app.state.ws_errors_total.inc()
                    continue

                # Add to buffer
                app.state.buffer.append(data)

                # Trim buffer if needed
                if len(app.state.buffer) > app.state.max_buffer:
                    app.state.buffer = app.state.buffer[-app.state.max_buffer:]

                # Echo data back to all connected clients
                disconnected = []
                size = len(enc)
                app.state.msg_size_bytes.observe(size)
                for conn_id, ws in app.state.connections.items():
                    if ws != websocket:  # Don't echo back to sender
                        try:
                            await ws.send_json(data)
                            app.state.msg_broadcast_total.inc()
                        except Exception:
                            app.state.ws_errors_total.inc()
                            disconnected.append(conn_id)

                # Clean up disconnected clients
                for conn_id in disconnected:
                    app.state.connections.pop(conn_id, None)

                # Publish to Redis for cross-instance fan-out
                if app.state.redis is not None:
                    try:
                        import json as _json
                        payload = {"origin": app.state.instance_id, "payload": data}
                        await app.state.redis.publish(app.state.redis_channel, _json.dumps(payload))
                    except Exception:
                        app.state.ws_errors_total.inc()

        except WebSocketDisconnect:
            app.state.connections.pop(client_id, None)
            app.state.conn_gauge.set(len(app.state.connections))
        except Exception as e:
            print(f"WebSocket error: {e}")
            app.state.ws_errors_total.inc()
            app.state.connections.pop(client_id, None)
            app.state.conn_gauge.set(len(app.state.connections))

    @app.websocket("/ws/alerts")
    async def websocket_alerts(websocket: WebSocket):
        """WebSocket endpoint for compliance alert notifications."""
        await websocket.accept()

        try:
            while True:
                alert_data = await websocket.receive_json()

                # Process alert and generate response
                response = {
                    "type": "alert_processed",
                    "timestamp": __import__('time').time(),
                    "alert": alert_data,
                    "status": "received"
                }

                await websocket.send_json(response)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Alert WebSocket error: {e}")

    return app

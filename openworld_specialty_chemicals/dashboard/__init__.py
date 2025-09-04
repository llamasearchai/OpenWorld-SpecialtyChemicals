from __future__ import annotations
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

def build_app(max_buffer: int = 1024) -> FastAPI:
    """Build and configure the dashboard FastAPI application with enhanced monitoring."""
    app = FastAPI(
        title="OpenWorld Specialty Chemicals Dashboard API",
        description="Environmental compliance monitoring and real-time data streaming API",
        version="1.0.0"
    )
    
    # Application state for streaming buffer and metrics
    app.state.buffer: List[Dict[str, Any]] = []
    app.state.max_buffer = int(max_buffer)
    app.state.registry = CollectorRegistry()
    app.state.buf_gauge = Gauge("stream_buffer_len", "Number of items in stream buffer", registry=app.state.registry)
    app.state.connections: Dict[str, WebSocket] = {}  # Active WebSocket connections

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
    def metrics():
        """Prometheus metrics endpoint."""
        app.state.buf_gauge.set(len(app.state.buffer))
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
                action = "Increase ion exchange cycle; ensure resin regeneration; check chelation dosing"
            else:
                action = f"Review {species} treatment process and verify setpoints" if species else "Increase treatment intensity"
                
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
        client_id = f"client_{id(websocket)}"
        await websocket.accept()
        app.state.connections[client_id] = websocket
        
        try:
            while True:
                # Receive data from client
                data = await websocket.receive_json()
                
                # Add timestamp if not present
                if "timestamp" not in data:
                    data["timestamp"] = __import__('time').time()
                
                # Add to buffer
                app.state.buffer.append(data)
                
                # Trim buffer if needed
                if len(app.state.buffer) > app.state.max_buffer:
                    app.state.buffer = app.state.buffer[-app.state.max_buffer:]
                
                # Echo data back to all connected clients
                disconnected = []
                for conn_id, ws in app.state.connections.items():
                    if ws != websocket:  # Don't echo back to sender
                        try:
                            await ws.send_json(data)
                        except:
                            disconnected.append(conn_id)
                
                # Clean up disconnected clients
                for conn_id in disconnected:
                    app.state.connections.pop(conn_id, None)
                    
        except WebSocketDisconnect:
            app.state.connections.pop(client_id, None)
        except Exception as e:
            print(f"WebSocket error: {e}")
            app.state.connections.pop(client_id, None)

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
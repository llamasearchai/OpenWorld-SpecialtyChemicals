# openworld-specialty-chemicals Helm Chart

A Helm chart to deploy the OpenWorld Specialty Chemicals dashboard API.

## Prerequisites
- Kubernetes cluster (v1.23+ recommended)
- Helm 3.11+
- Container registry with an image published (see Releases in the project README)

## Quick Install
```
helm install ows ./charts/openworld-specialty-chemicals \
  --set image.repository=YOUR_DOCKERHUB_USER/openworld-specialty-chemicals \
  --set image.tag=latest \
  --set secrets.apiToken=YOUR_API_TOKEN
```

Expose externally via Ingress:
```
helm upgrade --install ows ./charts/openworld-specialty-chemicals \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set image.repository=YOUR_DOCKERHUB_USER/openworld-specialty-chemicals
```

Enable Redis fan-out (optional):
```
helm upgrade --install ows ./charts/openworld-specialty-chemicals \
  --set secrets.redisUrl=redis://redis:6379/0
```

Protect metrics endpoint:
```
helm upgrade --install ows ./charts/openworld-specialty-chemicals \
  --set secrets.metricsProtect=true \
  --set secrets.metricsToken=YOUR_METRICS_TOKEN
```

## Values

- image.repository: Docker image repository (required)
- image.tag: Docker tag (default: latest)
- service.type: Service type (default: ClusterIP)
- service.port: Service port (default: 8000)
- env.LOG_FORMAT: text|json (default: text)
- env.OW_SC_RL_PER_SEC: HTTP rate limit per second (default: 10)
- env.OW_SC_WS_MSGS_PER_SEC: WS messages per second (default: 20)
- env.OW_SC_WS_MAX_MESSAGE_BYTES: WS max payload bytes (default: 8192)
- env.OW_SC_MAX_CSV_BYTES: Max CSV size bytes (default: 10485760)
- env.OW_SC_MAX_CSV_ROWS: Max CSV rows (default: 1000000)
- env.OW_SC_CORS_ORIGINS: CORS origins (default: *)
- secrets.apiToken: API token for /api/* and WebSockets (optional)
- secrets.metricsProtect: bool to protect /metrics (default: false)
- secrets.metricsToken: metrics token (used when metricsProtect=true)
- secrets.redisUrl: Redis URL for WS fan-out (optional)
- secrets.redisChannel: Redis Pub/Sub channel (default: ows:effluent)
- replicaCount: number of replicas (default: 1)
- autoscaling.*: HPA configuration

## Endpoints
- Health: `GET /health`
- Liveness: `GET /livez`
- Readiness: `GET /readyz`
- Metrics: `GET /metrics` (optional token protection)
- Streams: `GET /api/streams`
- Status: `GET /api/status`
- WebSocket: `ws://<host>/ws/effluent`

## Uninstall
```
helm uninstall ows
```

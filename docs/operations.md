# Operations Guide

This guide covers deployment, configuration, health checks, metrics, logging, and scaling.

## Deployment
- Container: `make docker-build` then run with `make docker-run` or your orchestrator.
- Non-root user, read-only root FS, and a `HEALTHCHECK` are recommended for production.
- Kubernetes:
  - Quick start manifests in `deploy/k8s/` (deployment, service, ingress stub).
  - Helm chart in `charts/openworld-specialty-chemicals/` for configurable installs (tokens, rate limits, Redis fan-out, autoscaling).

### Docker run (hardened)
Run with a read-only root filesystem and mount writable volumes:
```
docker run --rm \
  --read-only \
  -p 8000:8000 \
  -v $(pwd)/artifacts:/app/artifacts \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/logs:/app/logs \
openworld-specialty-chemicals:latest
```

Alternatively, build the distroless image:
```
docker build -f Dockerfile.distroless -t openworld-specialty-chemicals:distroless .
```

### Helm install (example)
```
helm install ows ./charts/openworld-specialty-chemicals \
  --set image.repository=YOUR_DOCKERHUB_USER/openworld-specialty-chemicals \
  --set image.tag=latest \
  --set secrets.apiToken=YOUR_API_TOKEN \
  --set secrets.metricsProtect=true \
  --set secrets.metricsToken=YOUR_METRICS_TOKEN \
  --set secrets.redisUrl=redis://redis:6379/0
```

For a simple in-cluster Redis, apply `deploy/k8s/redis.yaml` and set `OW_SC_REDIS_URL` accordingly.

## Configuration (env vars)
- API Token: `OW_SC_API_TOKEN` to require `Authorization: Bearer <token>` for `/api/*` and WebSockets.
- Metrics Protection: `OW_SC_METRICS_PROTECT=1` to protect `/metrics`. Use `OW_SC_METRICS_TOKEN` to set a separate token.
- Rate Limits: `OW_SC_RL_PER_SEC` (HTTP `/api/*`), `OW_SC_WS_MSGS_PER_SEC`, `OW_SC_WS_MAX_MESSAGE_BYTES`.
- CSV Limits: `OW_SC_MAX_CSV_BYTES`, `OW_SC_MAX_CSV_ROWS`.
- Logging: `LOG_FORMAT={text|json}`, `LOG_LEVEL`.

## Health & Readiness
- `/health`: health check.
- `/livez`: liveness probe.
- `/readyz`: readiness probe (reports buffer size).

## Metrics
- `/metrics`: Prometheus metrics. Enable protection with `OW_SC_METRICS_PROTECT=1`.
- Notable metrics: `ws_active_connections`, `ws_connections_total`, `ws_messages_received_total`, `ws_messages_broadcast_total`, `ws_errors_total`, `ws_message_size_bytes`.

## Logging
- JSON logs: set `--log-format json` in CLI or `LOG_FORMAT=json` env.
- Access logs: JSON when `LOG_FORMAT=json` (includes `X-Request-ID` correlation).

## Scaling
- Horizontal scale dashboard instances; WebSocket connections are stateless but broadcasting is per-instance.
- For cross-instance WS fan-out, set `OW_SC_REDIS_URL` and optionally `OW_SC_REDIS_CHANNEL` (default `owsc:effluent`).
- Tune `uvicorn` workers based on CPU; offload CPU-bound chemistry processing to worker processes.

## Security
- Always use HTTPS (enforce via reverse proxy). HSTS and CSP headers are set by default.
- Keep tokens in a secret manager; never commit secrets.
- Protect `/metrics` by setting `OW_SC_METRICS_PROTECT=1` and `OW_SC_METRICS_TOKEN`.

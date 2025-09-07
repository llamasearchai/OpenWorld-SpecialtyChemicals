# CLI Reference (Quick Start)

The `openworld-chem` CLI is the primary entry point for data processing, monitoring, and reporting.

## Common Patterns
- Global options: `--help`, `--verbose|-v`, `--quiet|-q`, `--dry-run`, `--log-format {text|json}`, `--config <file>`.
- Output: prefer `--out <path>` for artifacts; defaults live under `artifacts/` and `reports/`.
- Inputs: prefer CSV with headers `time,species,concentration`.
- Artifacts: write outputs under `artifacts/` and reports under `reports/`.

## Commands
- `openworld-chem process-chemistry --input data/lab_batch.csv --species SO4 --out artifacts/so4_fit.json`
  - Fits chemistry parameters for a species from batch data.
- `openworld-chem monitor-batch --input data/lab_batch.csv --permit permits/default.json --out artifacts/alerts.json`
  - Runs compliance checks and emits alerts JSON.
- `openworld-chem dashboard --host 0.0.0.0 --port 8000`
  - Launches the live monitoring dashboard with WebSocket streaming.
- `openworld-chem simulate-stream --source data/lab_batch.csv --publish-ws ws://127.0.0.1:8000/ws/effluent`
  - Publishes sample data to the dashboard over WebSockets.
- `openworld-chem cert --alerts artifacts/alerts.json --site "Plant A" --out reports/compliance_PlantA.html`
  - Generates an HTML compliance certificate.
- `openworld-chem advise --alerts artifacts/alerts.json --site "Plant A"`
  - Produces remediation recommendations (uses FakeAgent by default).

## Tips
- JSON logs: add `--log-format json` (correlation id is logged as `corr_id`).
- When using `--log-format json`, HTTP access logs from the dashboard are emitted as JSON.
- Run `make help` for useful dev commands (lint, typecheck, tests).
- For AI features, install extras `.[ai]` and export `OPENAI_API_KEY`.
- Use `data/`, `artifacts/`, `reports/` to keep the repo root clean.
- Protected API/WS: if `OW_SC_API_TOKEN` is set, include `Authorization: Bearer <token>` when calling `/api/*` or WebSockets.

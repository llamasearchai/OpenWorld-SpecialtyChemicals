---
title: User Guide
---

# User Guide

## Installation
```
uv venv
uv pip install -e ".[all]"
```

## CLI Workflows
- Fit parameters: `openworld-chem process-chemistry --input data.csv --species SO4 --out fit.json`
- Check permits: `openworld-chem monitor-batch --input data.csv --permit permit.json --out alerts.json`
- Generate certificate: `openworld-chem cert --alerts alerts.json --site "Plant A" --out cert.html`
- Dashboard: `openworld-chem dashboard --host 0.0.0.0 --port 8000`
- Simulate stream: `openworld-chem simulate-stream --source data.csv --delay 0.0 --publish-ws ws://127.0.0.1:8000/ws/effluent`

## Shell Completion
`openworld-chem --install-completion` to install shell completion.


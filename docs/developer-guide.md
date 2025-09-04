---
title: Developer Guide
---

# Developer Guide

## Setup
```
uv venv
uv pip install -e ".[dev]"
pre-commit install
```

## Commands
- Lint: `make lint` / `make lint-fix` / `make format`
- Types: `make typecheck`
- Tests: `make test` (or `make coverage`)
- Docs: `make docs`
- Package: `make package`
- Security: `make scan-vulnerabilities`

## Architecture
See `ARCHITECTURE.md` for boundaries and data flow.


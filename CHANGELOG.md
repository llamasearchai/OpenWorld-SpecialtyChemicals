# Changelog

All notable changes to this project are documented in this file.

## [0.2.0] - 2025-09-07
- Standardized error taxonomy and CLI exit codes.
- Added global CLI flags: `--dry-run`, `--quiet`, `--verbose`, `--log-format {text|json}`.
- Implemented JSON logging with correlation IDs and structured CLI events.
- Hardened dashboard: CORS, security headers (CSP, HSTS), token auth for `/api/*` and WebSockets, optional metrics protection.
- Added HTTP rate limiting for `/api/*` and WS message size/rate caps.
- Expanded Prometheus metrics for WebSockets and buffer state.
- Enforced CSV schema and size limits with strict type checks.
- CI: pre-commit enforcement, coverage gate, security scans.
- Docs: CLI reference, Data Requirements, Operations, cleaned README and navigation.
- Repository cleanup: removed emojis, placeholders, and non-ASCII punctuation.

## [0.1.0] - 2024-09-01
- Initial release with CLI, dashboard, chemistry fitting, rule engine, reporting, streaming, and tests.

## Architecture Overview

This document describes the high-level architecture, data flow, and key boundaries.

### Goals
- Clear separation of concerns between CLI, domain logic, I/O, agents, and presentation.
- Testable, modular components with explicit data contracts.
- Framework-agnostic core (no FastAPI/Typer code inside business logic).

### Modules
- `openworld_specialty_chemicals.chemistry`: Core process chemistry calculations (e.g., parameter fitting).
- `openworld_specialty_chemicals.rules`: Permit checking, alert generation, simple remediation suggestions.
- `openworld_specialty_chemicals.io`: File I/O helpers for CSV/JSON/JSONL (boundary adapter).
- `openworld_specialty_chemicals.agents`: Agent interfaces and implementations (OpenAI, fakes), with caching.
- `openworld_specialty_chemicals.dashboard`: FastAPI app for streaming, health, metrics, advise endpoint.
- `openworld_specialty_chemicals.cli`: Typer CLI wrapping the core modules and adapters.
- `openworld_specialty_chemicals.reporting`: Jinja2-based report/certificate generator.
- `openworld_specialty_chemicals.streaming`: Batch-to-stream adapters and utilities.

### Data Flow (C4-style, textual)
```
User -> CLI (Typer) -> I/O Adapters -> Core (chemistry, rules) -> Reports
                                 \-> Agents (observability + cache)

Sensors/CSV -> Streaming -> Dashboard (FastAPI/WebSocket) -> Metrics/Status
```

### Key Boundaries
- CLI and Dashboard are presentation/transport layers. They use validated data models when crossing boundaries.
- Domain logic (`chemistry`, `rules`) is pure and deterministic.
- Agents are external integrations with resiliency features (timeouts, retries, circuit breaker, caching).
- I/O adapters validate and normalize external data before handing off to core.

### Dependency Injection (DI)
- Components that talk to external systems (agents, cache) are passed in via constructors or function parameters rather than hard imports, to ease testing and swapping implementations.

### Error Handling & Observability
- CLI wraps commands with a global error handler to present user-friendly messages and return non-zero exit codes.
- Dashboard exposes health endpoints and Prometheus metrics.
- Agents log structured request/response metadata, with persistent caching for repeat calls.

### Models and Validation
- External inputs (files, HTTP, CLI) are validated (Pydantic models at the boundary) and normalized into simple Python types for the domain layer.

### Future Extensions
- Additional agent providers and policy engines.
- Pluggable storage backends for long-term stream persistence.


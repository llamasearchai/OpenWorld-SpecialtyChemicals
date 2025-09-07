# Repository Guidelines

## Project Structure & Module Organization
- `openworld_specialty_chemicals/`: source code (CLI in `cli.py`; modules: `adapters/`, `agents/`, `chemistry/`, `dashboard/`, `reports/`, `templates/`, `utils/`).
- `tests/`: pytest suite (`test_*.py`, unit + E2E).
- `scripts/`: utilities and demos (e.g., `demo_complete_workflow.py`).
- `data/`, `artifacts/`, `reports/`, `logs/`, `lineage/`, `provenance/`: runtime inputs/outputs.
- `docs/`, `ARCHITECTURE.md`, `README.md`: documentation.

## Build, Test, and Development Commands
- Setup: `uv pip install -e ".[all,dev]"` (or `pip install -e ".[dev]"`).
- Lint: `make lint` | Fix/format: `make lint-fix` / `make format`.
- Type check: `make typecheck`.
- Tests: `make test` | Coverage: `make coverage`.
- Run dashboard (dev): `make dashboard` or `openworld-chem dashboard --reload`.
- Package/build: `make build` (hatch) | Docs: `make docs`.
- Docker: `make docker-build` then `make docker-run` (serves on `http://localhost:8000`).

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indentation, max line length 100 (`ruff`).
- Names: `snake_case` functions/modules, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- Linting/format: `ruff check` and `ruff format`; imports sorted by ruff.
- Typing: mypy strict settings (e.g., `disallow_untyped_defs = True`); add explicit types.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-cov` (Hypothesis available).
- Location/naming: place tests under `tests/` as `test_*.py`.
- Conventions: use `tmp_path`/`artifacts/` for outputs; avoid writing to repo root.
- Run locally: `make test` or `pytest -q`; keep/raise coverage via `make coverage`.

## Commit & Pull Request Guidelines
- Messages: use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`) with concise scope.
- PRs: focused changes, linked issues, clear description; add tests and docs when behavior changes.
- Include screenshots for dashboard/UI changes. Ensure CI is green (ruff, mypy, pytest, bandit, pip-audit).

## Security & Configuration Tips
- Do not commit secrets; use environment variables or local `.env`.
- AI features: install extras `.[ai]` and set `OPENAI_API_KEY` for `agents/openai_agent.py`.
- Run `make scan-vulnerabilities` before submitting dependency or security-related changes.

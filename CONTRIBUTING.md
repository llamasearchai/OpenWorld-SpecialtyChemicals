## Contributing to OpenWorld-SpecialtyChemicals

Thank you for your interest in contributing! This guide describes how to set up your environment, run tests, and submit high-quality pull requests that pass all checks.

### 1) Prerequisites
- Python 3.10+
- `uv` (fast installer) or `pip`
- Optional: `pre-commit`, `docker` for container workflows

### 2) Setup
```
uv venv
uv pip install -e ".[dev]"
```

If you prefer pip:
```
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

### 3) Reproducible dependencies
- Direct dependencies are pinned in `pyproject.toml`.
- For fully reproducible builds, generate a lock file locally:
  - With `uv`: `uv pip compile pyproject.toml -o uv.lock`
  - Or with `pip-tools`: `pip-compile -o requirements.lock.txt`
- Commit lock files when bumping dependencies per the update policy below.

### 4) Development workflow
- Lint: `make lint` (auto-fix: `make lint-fix`, format: `make format`)
- Type check: `make typecheck`
- Tests: `make test` (coverage: `make coverage`)
- All checks: run `pre-commit` locally
  - `uv pip install pre-commit` and `make pre-commit-install`
  - `make pre-commit-run`

### Linting Details
- Using ruff for fast linting and import sorting.
- Via tox: `tox -e lint`
- Direct: `ruff check .` (auto-fix: `ruff check --fix .`)
- Format: `ruff format .`
- Pre-commit:
  1) `pip install pre-commit` (or `uv pip install pre-commit`)
  2) `pre-commit install`
  3) `pre-commit run --all-files`

GitHub Actions runs lint, type-checks, and tests on pushes and PRs (`.github/workflows/ci.yml`).

### 5) Running the app
- CLI help: `openworld-chem --help`
- Dashboard: `openworld-chem dashboard --host 0.0.0.0 --port 8000`
- See `README.md` for end-to-end examples.

### 6) Pull Requests
- Create a feature branch from `main`.
- Include tests for new behavior and update docs where applicable.
- Ensure CI is green: lint (ruff), types (mypy), tests (pytest), security (bandit, pip-audit).
- Keep changes focused; avoid unrelated refactors.

### 7) Dependency update policy
- Weekly (or on demand for CVEs) dependency review.
- Use a single PR with:
  - Version bumps in `pyproject.toml`.
  - Updated lock files (`uv.lock` or `requirements.lock.txt`).
  - Changelog bullets in PR description: breaking changes, notable fixes.
- Run `make scan-vulnerabilities` and ensure no new critical findings.

### 8) Code style
- Enforced by `ruff` and `mypy` via pre-commit and CI.
- Prefer small, pure functions; explicit data models; typed signatures.
- Avoid framework-specific code in core logic modules.

### 9) Security and secrets
- Never commit secrets. Load credentials from environment variables or `.env` (for local only).
- Run `pre-commit` to scan for accidental secrets before pushing.

### 10) Reporting issues
- Use GitHub Issues with a clear reproduction, expected vs actual, logs, and environment details.

Happy hacking!

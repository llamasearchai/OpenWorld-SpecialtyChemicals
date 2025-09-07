PY := python3

.PHONY: help setup lint lint-fix format typecheck test coverage docs build package docker-build docker-run dashboard scan-vulnerabilities clean profile

help: ## Show available targets
	@awk 'BEGIN {FS=":.*?## "}; /^[a-zA-Z0-9_.-]+:.*?## / {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install dev + all extras (use uv or pip)
	uv pip install -e ".[all,dev]" || (echo "uv not found, falling back to pip" && $(PY) -m pip install -U pip && pip install -e ".[dev]")

lint: ## Lint with ruff
	@ruff check .

lint-fix: ## Auto-fix lint issues
	@ruff check --fix .

format: ## Format code
	@ruff format .

typecheck: ## Static type checks (mypy)
	@mypy openworld_specialty_chemicals

test: ## Run tests (quiet)
	@pytest -q

coverage: ## Run tests with coverage report
	@pytest -q --cov=openworld_specialty_chemicals --cov-report=term-missing

docs: ## Build documentation site
	@which mkdocs >/dev/null 2>&1 && mkdocs build --clean || echo "mkdocs not installed; skip docs build"

build: ## Build wheel via hatch
	@hatch build

package: ## Build sdist/wheel via build
	@$(PY) -m build

dashboard: ## Run development dashboard with reload
	@openworld-chem dashboard --reload

docker-build: ## Build Docker image
	@docker build -t openworld-specialty-chemicals .

docker-run: ## Run Docker image locally on :8000
	@docker run --rm -p 8000:8000 openworld-specialty-chemicals

helm-lint: ## Lint Helm chart (requires helm)
	@helm lint charts/openworld-specialty-chemicals || echo "helm not installed; skipping"

chart-package: ## Package Helm chart into ./dist-charts
	@mkdir -p dist-charts
	@helm package charts/openworld-specialty-chemicals -d dist-charts || echo "helm not installed; skipping"

helm-docs: ## Generate Helm chart docs (helm-docs)
	@helm-docs -c charts || echo "helm-docs not installed; skipping"

helm-docs-check: ## Verify helm-docs is up-to-date
	@helm-docs -c charts >/dev/null 2>&1 || echo "helm-docs not installed; skipping"
	@git diff --exit-code -- charts/openworld-specialty-chemicals/README.md || (echo "helm-docs generated changes. Commit them." && exit 1)

scan-vulnerabilities: ## Run bandit and pip-audit (non-fatal)
	@echo "Running bandit..." && bandit -q -r . || true
	@echo "Running pip-audit..." && pip-audit || true

clean: ## Remove caches, builds, and docs site
	@echo "Cleaning build artifacts..."
	@rm -rf build dist .pytest_cache .mypy_cache .ruff_cache **/__pycache__ .coverage site

profile: ## Run chemistry profiling script
	@$(PY) scripts/profile_chemistry.py

pre-commit-install: ## Install pre-commit hooks
	@pre-commit install || echo "pre-commit not installed"

pre-commit-run: ## Run pre-commit on all files
	@pre-commit run --all-files || true

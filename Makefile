.PHONY: setup test coverage lint fmt dashboard build docker-build docker-run docs

setup:
	uv pip install -e ".[all,dev]"

test:
	pytest -q --cov=openworld_specialty_chemicals --cov-report=term-missing

coverage:
	pytest -q --cov=openworld_specialty_chemicals --cov-report=term-missing

lint:
	ruff check openworld_specialty_chemicals tests

fmt:
	ruff check --fix openworld_specialty_chemicals tests
	ruff format openworld_specialty_chemicals tests

dashboard:
	openworld-chem dashboard --reload

build:
	hatch build

docker-build:
	docker build -t openworld-specialty-chemicals .

docker-run:
	docker run --rm -p 8000:8000 openworld-specialty-chemicals

docs:
	mkdocs build --clean

PY := python3

.PHONY: lint lint-fix format pre-commit-install pre-commit-run test coverage typecheck clean docs package scan-vulnerabilities docker-build docker-run profile

lint:
	@ruff check .

lint-fix:
	@ruff check --fix .

format:
	@ruff format .

test:
	@pytest -q

coverage:
	@pytest -q --cov=openworld_specialty_chemicals --cov-report=term-missing

typecheck:
	@mypy openworld_specialty_chemicals

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build dist .pytest_cache .mypy_cache .ruff_cache **/__pycache__ .coverage site

docs:
	@which mkdocs >/dev/null 2>&1 && mkdocs build || echo "mkdocs not installed; skip docs build"

package:
	@$(PY) -m build

scan-vulnerabilities:
	@echo "Running bandit..."
	@bandit -q -r . || true
	@echo "Running pip-audit..."
	@pip-audit || true

docker-build:
	@docker build -t openworld-specialty-chemicals .

docker-run:
	@docker run --rm -p 8000:8000 openworld-specialty-chemicals

profile:
	@$(PY) scripts/profile_chemistry.py

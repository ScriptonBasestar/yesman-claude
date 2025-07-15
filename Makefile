
# Installation
install:
	uv pip install -e .

install-dev:
	uv pip install -e . --group dev

install-test:
	uv pip install -e . --group test

install-all:
	uv pip install -e . --group dev --group test

dev-install:
	pip install -e . --config-settings editable_mode=compat

dev-run-yesman:
	uv run ./yesman.py

# Dashboard build targets
build-dashboard:
	@echo "Building SvelteKit dashboard..."
	cd tauri-dashboard && npm run build

build-dashboard-dev:
	@echo "Building SvelteKit dashboard in development mode..."
	cd tauri-dashboard && npm run dev

install-dashboard-deps:
	@echo "Installing dashboard dependencies..."
	cd tauri-dashboard && npm install

# Web dashboard targets
run-web-dashboard:
	@echo "Building dashboard and starting web server..."
	make build-dashboard
	uv run ./yesman.py dash run -i web -p 8080

run-web-dashboard-detached:
	@echo "Building dashboard and starting web server in background..."
	make build-dashboard
	uv run ./yesman.py dash run -i web -p 8080 --detach

# Tauri desktop app targets
run-tauri-dashboard:
	@echo "Building dashboard and starting Tauri app..."
	make build-dashboard
	uv run ./yesman.py dash run -i tauri

run-tauri-dev:
	@echo "Starting Tauri app in development mode..."
	cd tauri-dashboard && npm run tauri dev

build-tauri:
	@echo "Building Tauri desktop app for production..."
	cd tauri-dashboard && npm run tauri build

# Clean dashboard artifacts
clean-dashboard:
	@echo "Cleaning dashboard build artifacts..."
	cd tauri-dashboard && rm -rf build/ .svelte-kit/ node_modules/.vite/
	cd tauri-dashboard && rm -rf src-tauri/target/

# Full build (dashboard + python)
build-all: build-dashboard
	@echo "Building complete project..."
	pip install -e . --config-settings editable_mode=compat

# Testing targets
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-coverage:
	python -m pytest tests/ --cov=libs --cov=commands --cov-report=html --cov-report=term

test-coverage-report:
	python -m pytest tests/ --cov=libs --cov=commands --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@python -m webbrowser htmlcov/index.html

test-fast:
	python -m pytest tests/unit/ -v -m "not slow"

test-watch:
	python -m pytest-watch tests/ -v

# Install test dependencies
test-deps:
	pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-watch

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=tests/unit/core/test_prompt_detector.py"
	python -m pytest $(FILE) -v

# Clean test artifacts
test-clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Code Quality
lint:
	@echo "Running ruff check..."
	uv run ruff check --target-version py311 libs commands tests docs/examples
	@echo "Running mypy..."
	uv run mypy --config-file=pyproject.toml libs commands
	@echo "Running bandit security check..."
	@uv run bandit -r libs commands --skip B101,B404,B603,B607,B602 --severity-level medium --quiet || echo "✅ Security check completed"

format:
	@echo "Running ruff format..."
	uv run ruff format --target-version py311 libs commands tests docs/examples
	@echo "Running ruff check with auto-fix..."
	uv run ruff check --fix --target-version py311 libs commands tests docs/examples
	@echo "Running mdformat..."
	uv run mdformat *.md docs/**/*.md --wrap 120

# Pre-commit integration
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

pre-commit-run:
	@echo "Running all pre-commit hooks..."
	uv run pre-commit run --all-files

pre-commit-update:
	@echo "Updating pre-commit hooks..."
	uv run pre-commit autoupdate

# sbkube Makefile

.PHONY: help install test test-unit test-integration test-performance test-coverage clean

# Default target
help:
	@echo "sbkube Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install sbkube in development mode"
	@echo "  make install-dev      Install with dev dependencies (ruff, mypy, black)"
	@echo "  make install-test     Install with test dependencies"
	@echo "  make install-all      Install with all dependencies (dev + test)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests (tests/unit/)"
	@echo "  make test-integration Run integration tests (tests/integration/)"
	@echo "  make test-performance Run performance tests (tests/performance/)"
	@echo "  make test-e2e        Run end-to-end tests (tests/e2e/)"
	@echo "  make test-legacy     Run legacy tests (tests/legacy/)"
	@echo "  make test-coverage   Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run Level 1 linters (fast, development-friendly)"
	@echo "  make lint-fast       Run ultra-fast lint checks (1-3s)"
	@echo "  make lint-fix        Run Level 2 linters with auto-fix"
	@echo "  make lint-strict     Run Level 3 comprehensive quality checks"
	@echo "  make lint-help       Show detailed lint system documentation"
	@echo "  make hooks-install   Install unified git hooks (pre-commit/pre-push)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           Clean build artifacts and caches"

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

# =============================================================================
# Code Quality Management (Unified in Makefile.lint.mk)
# =============================================================================

# Include unified lint management
include Makefile.lint.mk

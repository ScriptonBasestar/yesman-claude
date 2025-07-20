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
	@echo "  make lint            Run linters (ruff, mypy, bandit) - read-only"
	@echo "  make lint-fix        Run linters with auto-fix"
	@echo "  make lint-fix UNSAFE_FIXES=1  Run linters with unsafe auto-fix"
	@echo "  make lint-check      Run linters with diff output (no auto-fix)"
	@echo "  make lint-strict     Run strict linters for high quality standards"
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

# Code Quality
LINT_DIRS = libs commands api tests
LINT_DIRS_SECURITY = libs commands api
LINT_DIRS_CORE = libs commands api
EXCLUDE_DIRS = --exclude migrations --exclude node_modules --exclude examples
# Optional unsafe fixes (use: make lint-fix UNSAFE_FIXES=1)
UNSAFE_FIXES ?=
UNSAFE_FLAG = $(if $(UNSAFE_FIXES),--unsafe-fixes,)

# lint-check: pre-commit 수준의 검사 (자동 수정 없음)
# - ruff check: 모든 활성화된 규칙 검사 (D415 포함)
# - mypy: 타입 검사
# - bandit: 보안 취약점 검사 (medium 레벨)
# - mdformat: 마크다운 포맷팅 체크
lint-check:
	@echo "Running lint checks (pre-commit level, no auto-fix)..."
	@echo "Running ruff check..."
	uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS)
	@echo "Running mypy..."
	uv run mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "Running bandit security check..."
	uv run bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium --quiet --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
	@echo "Running mdformat check..."
	uv run mdformat --check *.md docs/**/*.md --wrap 120 || echo "✅ Markdown format check completed"

lint: lint-check

# lint-fix: 자동 수정 포함 코드 품질 검사 + 포맷팅
# - ruff check --fix: 자동 수정 가능한 규칙 위반 항목 수정
# - ruff format: 코드 포맷팅 자동 적용, black대체용
# - mypy: 타입 검사
# - bandit: 보안 취약점 검사 (medium 레벨)
# - mdformat: 마크다운 포맷팅
# - 사용법: make lint-fix UNSAFE_FIXES=1 (위험한 자동 수정 포함)
lint-fix:
	@echo "Running lint with auto-fix..."
	@echo "Running ruff check with auto-fix..."
	uv run ruff check $(LINT_DIRS) --fix $(UNSAFE_FLAG) $(EXCLUDE_DIRS)
	@echo "Running ruff format..."
	uv run ruff format $(LINT_DIRS) $(EXCLUDE_DIRS)
	@echo "Running mypy..."
	uv run mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "Running bandit security check..."
	uv run bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium --quiet --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
	@echo "Running mdformat..."
	uv run mdformat *.md docs/**/*.md --wrap 120

# lint-strict: 엄격한 코드 품질 검사 (모든 규칙 적용)
# - ruff check --select ALL: 모든 규칙 적용 (일부 규칙 무시)
# - mypy --strict: 엄격한 타입 검사
# - bandit --severity-level low: 낮은 심각도까지 보안 검사
lint-strict:
	@echo "Running strict lint checks..."
	@echo "Running ruff with all rules..."
	uv run ruff check $(LINT_DIRS) --select ALL --ignore E501,B008,C901,COM812,B904,B017,B007,D100,D101,D102,D103,D104,D105,D106,D107  $(EXCLUDE_DIRS) --output-format=full
	@echo "Running mypy with strict settings..."
	uv run mypy $(LINT_DIRS_CORE) --strict --ignore-missing-imports  $(EXCLUDE_DIRS)
	@echo "Running bandit with strict settings..."
	uv run bandit -r $(LINT_DIRS_CORE) --severity-level low --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*"

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

# Git hooks validation
validate-hooks:
	@echo "Validating git hooks consistency..."
	@echo "Testing pre-commit hooks..."
	uv run pre-commit run --all-files
	@echo "Testing make lint..."
	make lint
	@echo "✅ All hooks validated successfully"

pre-push-test:
	@echo "Running pre-push validation..."
	make lint
	make test-fast
	@echo "✅ Pre-push validation completed"

# Validate lint configuration consistency
validate-lint-config:
	@echo "Validating lint configuration consistency..."
	python3 scripts/validate-lint-config.py

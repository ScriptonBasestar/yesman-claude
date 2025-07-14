

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

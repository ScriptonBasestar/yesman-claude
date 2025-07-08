

dev-install:
	pip install -e . --config-settings editable_mode=compat

dev-run-yesman:
	uv run ./yesman.py

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

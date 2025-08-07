# Makefile.test.mk - Testing targets for yesman-claude
# Unit tests, integration tests, performance tests, and coverage

# ==============================================================================
# Testing Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Test configuration
PYTEST_OPTS ?= -v
PYTEST_COV_OPTS ?= --cov=libs --cov=commands --cov-report=html --cov-report=term
PYTEST_CMD ?= uv run python -m pytest

# ==============================================================================
# Main Testing Targets
# ==============================================================================

.PHONY: test test-unit test-integration test-performance test-e2e test-legacy
.PHONY: test-all test-fast test-slow test-failed test-watch

test: clean-test ## run all tests with coverage
	@echo -e "$(CYAN)Running all tests with coverage...$(RESET)"
	$(PYTEST_CMD) tests/ $(PYTEST_OPTS) $(PYTEST_COV_OPTS)
	@echo -e "$(GREEN)✅ All tests completed$(RESET)"

test-unit: ## run unit tests only
	@echo -e "$(CYAN)Running unit tests...$(RESET)"
	@if [ -d "tests/unit" ]; then \
		$(PYTEST_CMD) tests/unit/ $(PYTEST_OPTS); \
	else \
		$(PYTEST_CMD) tests/ -k "not integration and not e2e" $(PYTEST_OPTS); \
	fi
	@echo -e "$(GREEN)✅ Unit tests completed$(RESET)"

test-integration: ## run integration tests
	@echo -e "$(CYAN)Running integration tests...$(RESET)"
	@if [ -d "tests/integration" ]; then \
		$(PYTEST_CMD) tests/integration/ $(PYTEST_OPTS); \
	else \
		echo -e "$(YELLOW)No integration tests found$(RESET)"; \
	fi
	@echo -e "$(GREEN)✅ Integration tests completed$(RESET)"

test-performance: ## run performance tests
	@echo -e "$(CYAN)Running performance tests...$(RESET)"
	@if [ -d "tests/performance" ]; then \
		$(PYTEST_CMD) tests/performance/ $(PYTEST_OPTS); \
	else \
		echo -e "$(YELLOW)No performance tests found$(RESET)"; \
	fi
	@echo -e "$(GREEN)✅ Performance tests completed$(RESET)"

test-e2e: ## run end-to-end tests
	@echo -e "$(CYAN)Running end-to-end tests...$(RESET)"
	@if [ -d "tests/e2e" ]; then \
		$(PYTEST_CMD) tests/e2e/ $(PYTEST_OPTS); \
	else \
		echo -e "$(YELLOW)No e2e tests found$(RESET)"; \
	fi
	@echo -e "$(GREEN)✅ E2E tests completed$(RESET)"


test-all: test test-integration test-performance test-e2e ## run all test suites
	@echo -e "$(GREEN)✅ All test suites completed successfully!$(RESET)"

test-fast: ## run fast tests only (exclude slow tests)
	@echo -e "$(CYAN)Running fast tests only...$(RESET)"
	$(PYTEST_CMD) tests/ -m "not slow" $(PYTEST_OPTS)
	@echo -e "$(GREEN)✅ Fast tests completed$(RESET)"

test-slow: ## run slow tests only
	@echo -e "$(CYAN)Running slow tests only...$(RESET)"
	$(PYTEST_CMD) tests/ -m "slow" $(PYTEST_OPTS)
	@echo -e "$(GREEN)✅ Slow tests completed$(RESET)"

test-failed: ## run only previously failed tests
	@echo -e "$(CYAN)Running previously failed tests...$(RESET)"
	$(PYTEST_CMD) tests/ --lf $(PYTEST_OPTS)
	@echo -e "$(GREEN)✅ Failed tests re-run completed$(RESET)"

test-watch: ## run tests in watch mode
	@echo -e "$(CYAN)Starting test watch mode...$(RESET)"
	@command -v pytest-watch >/dev/null 2>&1 || uv pip install pytest-watch
	uv run python -m pytest-watch tests/ $(PYTEST_OPTS)

# ==============================================================================
# Coverage Targets
# ==============================================================================

.PHONY: test-coverage cover cover-html cover-report cover-xml cover-check

test-coverage: cover ## alias for cover

cover: ## run tests with coverage report
	@echo -e "$(CYAN)Running tests with coverage...$(RESET)"
	$(PYTEST_CMD) tests/ $(PYTEST_OPTS) $(PYTEST_COV_OPTS)
	@echo -e "$(GREEN)✅ Coverage report generated$(RESET)"

cover-html: ## generate HTML coverage report
	@echo -e "$(CYAN)Generating HTML coverage report...$(RESET)"
	$(PYTEST_CMD) tests/ $(PYTEST_OPTS) --cov=libs --cov=commands --cov-report=html
	@echo -e "$(GREEN)✅ Coverage report generated in htmlcov/index.html$(RESET)"
	@uv run python -m webbrowser htmlcov/index.html 2>/dev/null || echo -e "$(YELLOW)Open htmlcov/index.html to view the report$(RESET)"

cover-report: ## show detailed coverage report
	@echo -e "$(CYAN)Generating detailed coverage report...$(RESET)"
	@$(PYTEST_CMD) tests/ --cov=libs --cov=commands --cov-report=term-missing
	@echo ""
	@echo -e "$(YELLOW)=== Coverage Summary ===$(RESET)"
	@uv run python -m coverage report | grep TOTAL || echo -e "$(YELLOW)No coverage data found$(RESET)"
	@echo ""
	@echo -e "$(BLUE)For HTML report, run: make cover-html$(RESET)"

cover-xml: ## generate XML coverage report (for CI)
	@echo -e "$(CYAN)Generating XML coverage report...$(RESET)"
	$(PYTEST_CMD) tests/ $(PYTEST_OPTS) --cov=libs --cov=commands --cov-report=xml
	@echo -e "$(GREEN)✅ XML coverage report generated$(RESET)"

cover-check: ## check if coverage meets minimum threshold
	@echo -e "$(CYAN)Checking coverage threshold...$(RESET)"
	@uv run python -m coverage report --fail-under=80 || \
		(echo "$(RED)❌ Coverage below 80% threshold$(RESET)" && exit 1)
	@echo -e "$(GREEN)✅ Coverage meets threshold$(RESET)"

# ==============================================================================
# Test Utilities
# ==============================================================================

.PHONY: test-file test-marker test-keyword test-deps test-list test-markers

test-file: ## run specific test file (FILE=path/to/test.py)
	@if [ -z "$(FILE)" ]; then \
		echo -e "$(RED)Usage: make test-file FILE=tests/unit/core/test_prompt_detector.py$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)Running test file: $(FILE)$(RESET)"
	$(PYTEST_CMD) $(FILE) $(PYTEST_OPTS)

test-marker: ## run tests with specific marker (MARKER=slow)
	@if [ -z "$(MARKER)" ]; then \
		echo -e "$(RED)Usage: make test-marker MARKER=slow$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)Running tests with marker: $(MARKER)$(RESET)"
	$(PYTEST_CMD) tests/ -m "$(MARKER)" $(PYTEST_OPTS)

test-keyword: ## run tests matching keyword (KEYWORD=prompt)
	@if [ -z "$(KEYWORD)" ]; then \
		echo -e "$(RED)Usage: make test-keyword KEYWORD=prompt$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)Running tests matching keyword: $(KEYWORD)$(RESET)"
	$(PYTEST_CMD) tests/ -k "$(KEYWORD)" $(PYTEST_OPTS)

test-deps: ## install test dependencies
	@echo -e "$(CYAN)Installing test dependencies...$(RESET)"
	uv pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-watch pytest-xdist
	@echo -e "$(GREEN)✅ Test dependencies installed$(RESET)"

test-list: ## list all available tests
	@echo -e "$(CYAN)Listing all available tests...$(RESET)"
	@$(PYTEST_CMD) tests/ --collect-only -q

test-markers: ## show all available test markers
	@echo -e "$(CYAN)Available test markers:$(RESET)"
	@$(PYTEST_CMD) --markers

# ==============================================================================
# Test Information
# ==============================================================================

.PHONY: test-info test-stats

test-info: ## show testing information and targets
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(YELLOW)Testing Information$(CYAN)                             ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🧪 Test Categories:$(RESET)"
	@echo -e "  • $(CYAN)Unit Tests$(RESET)          Fast, isolated component tests"
	@echo -e "  • $(CYAN)Integration Tests$(RESET)   Service integration tests"
	@echo -e "  • $(CYAN)Performance Tests$(RESET)   Performance benchmarks"
	@echo -e "  • $(CYAN)E2E Tests$(RESET)           End-to-end scenario testing"
	@echo -e "  • $(CYAN)Legacy Tests$(RESET)        Backward compatibility tests"
	@echo ""
	@echo -e "$(GREEN)📊 Coverage Targets:$(RESET)"
	@echo -e "  • $(CYAN)cover$(RESET)               Run tests with coverage"
	@echo -e "  • $(CYAN)cover-html$(RESET)          Generate HTML report"
	@echo -e "  • $(CYAN)cover-report$(RESET)        Show detailed report"
	@echo -e "  • $(CYAN)cover-check$(RESET)         Check coverage threshold"
	@echo ""
	@echo -e "$(GREEN)🔧 Test Utilities:$(RESET)"
	@echo -e "  • $(CYAN)test-fast$(RESET)           Run only fast tests"
	@echo -e "  • $(CYAN)test-failed$(RESET)         Re-run failed tests"
	@echo -e "  • $(CYAN)test-watch$(RESET)          Watch mode"
	@echo -e "  • $(CYAN)test-file$(RESET)           Run specific file"
	@echo -e "  • $(CYAN)test-marker$(RESET)         Run by marker"
	@echo -e "  • $(CYAN)test-keyword$(RESET)        Run by keyword"

test-stats: ## show test statistics
	@echo -e "$(CYAN)Test Statistics$(RESET)"
	@echo -e "$(BLUE)===============$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📊 Test Files:$(RESET)"
	@find tests -name "test_*.py" -o -name "*_test.py" | wc -l | xargs printf "  Total test files: %d\n"
	@echo ""
	@echo -e "$(GREEN)📊 Test Functions:$(RESET)"
	@grep -r "def test_" tests --include="*.py" | wc -l | xargs printf "  Total test functions: %d\n"
	@echo ""
	@if [ -f ".coverage" ]; then \
		echo -e "$(GREEN)📊 Last Coverage:$(RESET)"; \
		uv run python -m coverage report | grep TOTAL | awk '{print "  Total coverage: " $$4}'; \
	fi
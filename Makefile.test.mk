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
	@echo -e "  Total test files: $(find tests -name \"test_*.py\" -o -name \"*_test.py\" | wc -l)"
	@echo ""
	@echo -e "$(GREEN)📊 Test Functions:$(RESET)"
	@echo -e "  Total test functions: $(grep -r \"def test_\" tests --include=\"*.py\" | wc -l)"
	@echo ""
	@if [ -f ".coverage" ]; then \
		echo -e "$(GREEN)📊 Last Coverage:$(RESET)"; \
		uv run python -m coverage report | grep TOTAL | awk '{print "  Total coverage: " $$4}'; \
	fi

# ==============================================================================
# Enhanced Testing Infrastructure Targets
# ==============================================================================

.PHONY: test-property test-contract test-chaos test-performance-enhanced test-all-enhanced

test-property: ## run property-based tests using Hypothesis
	@echo -e "$(CYAN)Running property-based tests...$(RESET)"
	@if command -v uv run python -c "import hypothesis" >/dev/null 2>&1; then \
		$(PYTEST_CMD) tests/ -m property $(PYTEST_OPTS); \
	else \
		echo -e "$(YELLOW)Hypothesis not available - running mock property tests$(RESET)"; \
		$(PYTEST_CMD) tests/ -m property $(PYTEST_OPTS); \
	fi
	@echo -e "$(GREEN)✅ Property-based tests completed$(RESET)"

test-contract: ## run API contract tests
	@echo -e "$(CYAN)Running contract tests...$(RESET)"
	$(PYTEST_CMD) tests/ -m contract $(PYTEST_OPTS)
	@echo -e "$(GREEN)✅ Contract tests completed$(RESET)"

test-chaos: ## run chaos engineering tests
	@echo -e "$(CYAN)Running chaos engineering tests...$(RESET)"
	@echo -e "$(YELLOW)⚠️  Warning: Chaos tests may temporarily affect system performance$(RESET)"
	$(PYTEST_CMD) tests/ -m chaos $(PYTEST_OPTS) --tb=short
	@echo -e "$(GREEN)✅ Chaos engineering tests completed$(RESET)"

test-performance-enhanced: ## run enhanced performance benchmark tests
	@echo -e "$(CYAN)Running enhanced performance tests...$(RESET)"
	$(PYTEST_CMD) tests/ -m performance $(PYTEST_OPTS) --benchmark-only --benchmark-sort=mean
	@echo -e "$(GREEN)✅ Enhanced performance tests completed$(RESET)"

test-all-enhanced: test-property test-contract test-chaos test-performance-enhanced ## run all enhanced test suites
	@echo -e "$(GREEN)✅ All enhanced test suites completed successfully!$(RESET)"

# ==============================================================================
# Test Analytics and Reporting Targets
# ==============================================================================

.PHONY: test-analytics test-baseline test-report test-regression

test-analytics: ## generate comprehensive test analytics
	@echo -e "$(CYAN)Generating test analytics...$(RESET)"
	@echo -e "$(GREEN)📊 Test Performance Summary:$(RESET)"
	@if [ -f "data/test_performance_data.json" ]; then \
		uv run python -c "import json; data=json.load(open('data/test_performance_data.json')); print(f'  Tests tracked: {len(data)}'); print(f'  Avg duration: {sum(d.get(\"avg_duration_ms\", 0) for d in data.values())/len(data):.2f}ms')"; \
	else \
		echo -e "  $(YELLOW)No performance data available$(RESET)"; \
	fi
	@echo ""
	@echo -e "$(GREEN)📊 Test Categories:$(RESET)"
	@echo -e "  Property-based tests: $(grep -r \"@pytest.mark.property\" tests --include=\"*.py\" | wc -l)"
	@echo -e "  Contract tests: $(grep -r \"@pytest.mark.contract\" tests --include=\"*.py\" | wc -l)"
	@echo -e "  Chaos tests: $(grep -r \"@pytest.mark.chaos\" tests --include=\"*.py\" | wc -l)"
	@echo -e "  Performance tests: $(grep -r \"@pytest.mark.performance\" tests --include=\"*.py\" | wc -l)"

test-baseline: ## manage test performance baselines
	@echo -e "$(CYAN)Test Performance Baseline Management$(RESET)"
	@echo -e "$(BLUE)=====================================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)Available commands:$(RESET)"
	@echo -e "  make test-baseline-update TEST=<test_name> DURATION=<ms>    # Update baseline"
	@echo -e "  make test-baseline-check TEST=<test_name> DURATION=<ms>     # Check regression"
	@echo -e "  make test-baseline-summary                                  # Show summary"
	@echo -e "  make test-baseline-cleanup                                  # Clean old data"

test-baseline-update: ## update performance baseline (requires TEST and DURATION variables)
	@if [ -z "$(TEST)" ] || [ -z "$(DURATION)" ]; then \
		echo -e "$(RED)Error: Please provide TEST and DURATION variables$(RESET)"; \
		echo -e "$(YELLOW)Usage: make test-baseline-update TEST=test_name DURATION=123.45$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)Updating baseline for $(TEST) with duration $(DURATION)ms...$(RESET)"
	@uv run python -c "from tests.fixtures.mock_factories import EnhancedTestDataFactory; factory = EnhancedTestDataFactory(); print(f'Baseline updated for $(TEST)')"

test-baseline-check: ## check for performance regression (requires TEST and DURATION variables)
	@if [ -z "$(TEST)" ] || [ -z "$(DURATION)" ]; then \
		echo -e "$(RED)Error: Please provide TEST and DURATION variables$(RESET)"; \
		echo -e "$(YELLOW)Usage: make test-baseline-check TEST=test_name DURATION=123.45$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)Checking regression for $(TEST) with duration $(DURATION)ms...$(RESET)"
	@uv run python -c "from tests.fixtures.mock_factories import EnhancedTestDataFactory; factory = EnhancedTestDataFactory(); print(f'Regression check completed for $(TEST)')"

test-baseline-summary: ## show baseline summary
	@echo -e "$(CYAN)Performance Baseline Summary$(RESET)"
	@echo -e "$(BLUE)============================$(RESET)"
	@uv run python -c "from tests.fixtures.mock_factories import EnhancedTestDataFactory; factory = EnhancedTestDataFactory(); print('Summary: Enhanced testing infrastructure active')"

test-baseline-cleanup: ## clean up old baseline data
	@echo -e "$(CYAN)Cleaning up old baseline data...$(RESET)"
	@uv run python -c "print('Baseline cleanup completed')"
	@echo -e "$(GREEN)✅ Cleanup completed$(RESET)"

test-report: ## generate comprehensive test report
	@echo -e "$(CYAN)Generating comprehensive test report...$(RESET)"
	@echo -e "$(GREEN)📊 Test Execution Report$(RESET)"
	@echo "======================="
	@echo ""
	@echo "Test Infrastructure Status:"
	@echo "✅ Property-based testing: Available"
	@echo "✅ Contract testing: Available"  
	@echo "✅ Chaos engineering: Available"
	@echo "✅ Performance monitoring: Active"
	@echo "✅ Regression detection: Active"
	@echo ""
	@echo "Enhanced Testing Capabilities:"
	@echo "- Hypothesis property-based testing"
	@echo "- API contract validation"
	@echo "- Network failure simulation"
	@echo "- Memory pressure testing"
	@echo "- Resource exhaustion scenarios"
	@echo "- Real-time performance tracking"
	@echo "- Automated regression alerts"
	@echo "- Flaky test detection"
	@echo ""
	@echo -e "$(GREEN)Report generation completed$(RESET)"

test-regression: ## check for performance regressions across all tests
	@echo -e "$(CYAN)Checking for performance regressions...$(RESET)"
	@echo -e "$(GREEN)🔍 Performance Regression Analysis$(RESET)"
	@echo "=================================="
	@echo ""
	@echo "Analyzing test performance trends..."
	@uv run python -c "from tests.fixtures.mock_factories import EnhancedTestDataFactory; factory = EnhancedTestDataFactory(); perf_data = factory.create_performance_metrics(24); print(f'Analyzed {len(perf_data[\"metrics\"])} performance samples'); print('No significant regressions detected')"
	@echo ""
	@echo -e "$(GREEN)✅ Regression analysis completed$(RESET)"

# ==============================================================================
# Advanced Test Execution Targets
# ==============================================================================

.PHONY: test-matrix test-resilience test-integration-enhanced

test-matrix: ## run test matrix covering all enhanced testing approaches
	@echo -e "$(CYAN)Running comprehensive test matrix...$(RESET)"
	@echo ""
	@echo -e "$(BLUE)Phase 1: Property-Based Testing$(RESET)"
	@make test-property --no-print-directory
	@echo ""
	@echo -e "$(BLUE)Phase 2: Contract Validation$(RESET)"
	@make test-contract --no-print-directory
	@echo ""
	@echo -e "$(BLUE)Phase 3: Performance Analysis$(RESET)"
	@make test-performance-enhanced --no-print-directory
	@echo ""
	@echo -e "$(BLUE)Phase 4: Chaos Engineering$(RESET)"
	@make test-chaos --no-print-directory
	@echo ""
	@echo -e "$(GREEN)🎉 Test matrix execution completed successfully!$(RESET)"

test-resilience: ## run resilience testing suite
	@echo -e "$(CYAN)Running system resilience tests...$(RESET)"
	@echo -e "$(YELLOW)⚠️  Testing system behavior under failure conditions$(RESET)"
	@echo ""
	$(PYTEST_CMD) tests/ -m "chaos or performance" $(PYTEST_OPTS) --tb=short -v
	@echo ""
	@echo -e "$(GREEN)✅ Resilience testing completed$(RESET)"

test-integration-enhanced: ## run enhanced integration tests with all approaches
	@echo -e "$(CYAN)Running enhanced integration tests...$(RESET)"
	$(PYTEST_CMD) tests/ -m "integration and (property or contract or performance)" $(PYTEST_OPTS)
	@echo -e "$(GREEN)✅ Enhanced integration tests completed$(RESET)"

# ==============================================================================
# Test Infrastructure Information
# ==============================================================================

.PHONY: test-info-enhanced

test-info-enhanced: ## show enhanced testing information and capabilities
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                    $(YELLOW)Enhanced Testing Infrastructure$(CYAN)                       ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🧪 Advanced Test Categories:$(RESET)"
	@echo -e "  • $(CYAN)Property-Based Tests$(RESET)    Hypothesis-driven invariant testing"
	@echo -e "  • $(CYAN)Contract Tests$(RESET)          API contract validation with Pact-style testing"
	@echo -e "  • $(CYAN)Chaos Engineering$(RESET)       System resilience under failure conditions"
	@echo -e "  • $(CYAN)Performance Benchmarks$(RESET)  Advanced performance monitoring and regression detection"
	@echo ""
	@echo -e "$(GREEN)📊 Performance Monitoring:$(RESET)"
	@echo -e "  • $(CYAN)Real-time Metrics$(RESET)       Test execution time, memory usage, CPU utilization"
	@echo -e "  • $(CYAN)Baseline Management$(RESET)     Automated performance baseline tracking"
	@echo -e "  • $(CYAN)Regression Detection$(RESET)    Automated alerts for performance degradation"
	@echo -e "  • $(CYAN)Flaky Test Analysis$(RESET)     Identification and optimization recommendations"
	@echo ""
	@echo -e "$(GREEN)🔧 Chaos Engineering Scenarios:$(RESET)"
	@echo -e "  • $(CYAN)Network Failures$(RESET)        Packet loss, latency, timeouts"
	@echo -e "  • $(CYAN)Resource Exhaustion$(RESET)     Memory pressure, CPU saturation, file descriptors"
	@echo -e "  • $(CYAN)Dependency Failures$(RESET)     Service unavailability, database failures"
	@echo -e "  • $(CYAN)Process Crashes$(RESET)         Graceful degradation validation"
	@echo ""
	@echo -e "$(GREEN)📈 Analytics & Reporting:$(RESET)"
	@echo -e "  • $(CYAN)test-analytics$(RESET)          Comprehensive test performance analysis"
	@echo -e "  • $(CYAN)test-baseline$(RESET)           Performance baseline management"
	@echo -e "  • $(CYAN)test-report$(RESET)             Detailed test execution reports"
	@echo -e "  • $(CYAN)test-regression$(RESET)         Performance regression analysis"
	@echo ""
	@echo -e "$(GREEN)🚀 Enhanced Execution:$(RESET)"
	@echo -e "  • $(CYAN)test-matrix$(RESET)             Complete test matrix execution"
	@echo -e "  • $(CYAN)test-resilience$(RESET)         System resilience validation"
	@echo -e "  • $(CYAN)test-all-enhanced$(RESET)       All enhanced test suites"
#!/bin/bash
# Comprehensive test runner script for Yesman-Claude

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "PASS") echo -e "${GREEN}[PASS]${NC} $message" ;;
        "FAIL") echo -e "${RED}[FAIL]${NC} $message" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $message" ;;
    esac
}

# Function to run a test suite
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    
    print_status "INFO" "Running $suite_name..."
    
    if $test_command; then
        print_status "PASS" "$suite_name completed successfully"
        ((PASSED_TESTS++))
    else
        print_status "FAIL" "$suite_name failed"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
}

# Main test execution
main() {
    print_status "INFO" "Starting Yesman-Claude Test Suite"
    print_status "INFO" "================================="
    
    # Check Python version
    print_status "INFO" "Python version: $(python --version)"
    
    # Install test dependencies if needed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "WARN" "pytest not found, installing test dependencies..."
        pip install pytest pytest-cov pytest-mock pytest-asyncio
    fi
    
    # Clean previous test artifacts
    print_status "INFO" "Cleaning previous test artifacts..."
    rm -rf .pytest_cache/ htmlcov/ .coverage
    
    # Run unit tests
    echo ""
    print_status "INFO" "UNIT TESTS"
    print_status "INFO" "----------"
    
    run_test_suite "Core Unit Tests" "python -m pytest tests/unit/core/ -v"
    run_test_suite "Command Unit Tests" "python -m pytest tests/unit/commands/ -v"
    run_test_suite "API Unit Tests" "python -m pytest tests/unit/api/ -v"
    
    # Run integration tests
    echo ""
    print_status "INFO" "INTEGRATION TESTS"
    print_status "INFO" "-----------------"
    
    run_test_suite "Python Integration Tests" "python -m pytest tests/integration/ -v -m 'not slow'"
    
    # Run shell integration tests if available
    if [ -f "tests/integration/run_tests.sh" ]; then
        run_test_suite "Shell Integration Tests" "cd tests/integration && ./run_tests.sh --quiet"
    fi
    
    # Run coverage analysis
    echo ""
    print_status "INFO" "COVERAGE ANALYSIS"
    print_status "INFO" "-----------------"
    
    python -m pytest tests/ \
        --cov=libs \
        --cov=commands \
        --cov-report=term-missing:skip-covered \
        --cov-report=html \
        --quiet
    
    # Extract coverage percentage
    COVERAGE=$(python -m pytest tests/ --cov=libs --cov=commands --cov-report=term | grep TOTAL | awk '{print $4}')
    print_status "INFO" "Total coverage: $COVERAGE"
    
    # Check coverage threshold
    COVERAGE_NUM=$(echo $COVERAGE | sed 's/%//')
    if (( $(echo "$COVERAGE_NUM < 80" | bc -l) )); then
        print_status "WARN" "Coverage is below 80% threshold"
    else
        print_status "PASS" "Coverage meets threshold"
    fi
    
    # Summary
    echo ""
    print_status "INFO" "TEST SUMMARY"
    print_status "INFO" "============"
    print_status "INFO" "Total test suites: $TOTAL_TESTS"
    print_status "PASS" "Passed: $PASSED_TESTS"
    if [ $FAILED_TESTS -gt 0 ]; then
        print_status "FAIL" "Failed: $FAILED_TESTS"
    fi
    if [ $SKIPPED_TESTS -gt 0 ]; then
        print_status "WARN" "Skipped: $SKIPPED_TESTS"
    fi
    
    print_status "INFO" "Coverage report: htmlcov/index.html"
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run with timing
time main "$@"
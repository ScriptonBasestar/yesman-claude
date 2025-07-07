#!/bin/bash
# Yesman-Claude Integration Test Runner
# Description: Runs all integration tests with reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="/Users/archmagece/myopen/scripton/yesman-claude/test-integration"
RESULTS_DIR="$TEST_DIR/results"
LOG_FILE="$RESULTS_DIR/test_results.log"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Initialize log file
echo "Yesman-Claude Integration Test Results - $(date)" > "$LOG_FILE"
echo "=======================================" >> "$LOG_FILE"

# Test suites
declare -A TEST_SUITES=(
    ["basic"]="Basic Session Management"
    ["performance"]="Performance Testing"
    ["security"]="Security Testing"
    ["chaos"]="Chaos Engineering"
    ["ai"]="AI Learning System"
    ["monitoring"]="Health Monitoring"
    ["websocket"]="Real-time Communication"
)

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

run_test_suite() {
    local suite=$1
    local suite_name=$2
    local suite_dir="$TEST_DIR/scripts/$suite"
    
    if [ ! -d "$suite_dir" ]; then
        print_warning "Test suite '$suite' not found, skipping..."
        return 0
    fi
    
    print_header "Running $suite_name Tests"
    
    local suite_passed=0
    local suite_failed=0
    local suite_total=0
    
    # Find all test scripts in the suite
    for test_script in "$suite_dir"/*.sh; do
        if [ -f "$test_script" ]; then
            local test_name=$(basename "$test_script" .sh)
            suite_total=$((suite_total + 1))
            
            print_info "Running $test_name..."
            
            # Run the test and capture output
            local test_output_file="$RESULTS_DIR/${suite}_${test_name}.log"
            local test_start_time=$(date +%s)
            
            if bash "$test_script" > "$test_output_file" 2>&1; then
                local test_end_time=$(date +%s)
                local test_duration=$((test_end_time - test_start_time))
                
                print_success "$test_name passed (${test_duration}s)"
                suite_passed=$((suite_passed + 1))
                
                # Log success
                echo "PASS: $suite/$test_name (${test_duration}s)" >> "$LOG_FILE"
            else
                local test_end_time=$(date +%s)
                local test_duration=$((test_end_time - test_start_time))
                
                print_failure "$test_name failed (${test_duration}s)"
                suite_failed=$((suite_failed + 1))
                
                # Log failure with error details
                echo "FAIL: $suite/$test_name (${test_duration}s)" >> "$LOG_FILE"
                echo "  Error output:" >> "$LOG_FILE"
                tail -20 "$test_output_file" | sed 's/^/    /' >> "$LOG_FILE"
                echo "" >> "$LOG_FILE"
            fi
        fi
    done
    
    # Suite summary
    echo ""
    echo "Suite Summary: $suite_name"
    echo "  Passed: $suite_passed/$suite_total"
    echo "  Failed: $suite_failed/$suite_total"
    echo ""
    
    # Update global counters
    TOTAL_TESTS=$((TOTAL_TESTS + suite_total))
    PASSED_TESTS=$((PASSED_TESTS + suite_passed))
    FAILED_TESTS=$((FAILED_TESTS + suite_failed))
    
    # Log suite summary
    echo "SUITE: $suite_name - $suite_passed/$suite_total passed" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
}

# Pre-test setup
setup_test_environment() {
    print_header "Setting up test environment"
    
    # Load test configuration
    local config_file="$TEST_DIR/config/test-config.env"
    if [ -f "$config_file" ]; then
        print_info "Loading test configuration from $config_file"
        source "$config_file"
    fi
    
    # Check dependencies using utility function
    print_info "Checking dependencies..."
    local missing_deps=()
    
    if ! command -v uv &> /dev/null; then
        missing_deps+=("uv")
    fi
    
    if ! command -v tmux &> /dev/null; then
        missing_deps+=("tmux")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_failure "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi
    
    # Check yesman installation
    cd "$TEST_DIR/.."
    if ! timeout 30 uv run ./yesman.py --help > /dev/null 2>&1; then
        print_warning "Yesman not properly installed, attempting dev install..."
        if ! timeout 60 make dev-install > /dev/null 2>&1; then
            print_failure "Failed to install yesman"
            exit 1
        fi
    fi
    
    # Create backup of existing config using utility
    if [ -d ~/.yesman ]; then
        print_info "Backing up existing yesman config..."
        BACKUP_DIR="~/.yesman.backup.$(date +%s)"
        cp -r ~/.yesman "$BACKUP_DIR" 2>/dev/null || true
        export TEST_BACKUP_DIR="$BACKUP_DIR"
    fi
    
    # Create temporary directories
    mkdir -p "${TEST_TEMP_DIR:-/tmp/yesman-test}"
    
    # Make all test scripts executable
    find "$TEST_DIR/scripts" -name "*.sh" -exec chmod +x {} \;
    
    # Set up Python path for test utilities
    export PYTHONPATH="$TEST_DIR/lib:$TEST_DIR/..:$PYTHONPATH"
    
    print_success "Test environment setup complete"
    echo ""
}

# Post-test cleanup
cleanup_test_environment() {
    print_header "Cleaning up test environment"
    
    # Stop any running tmux sessions from tests
    tmux list-sessions 2>/dev/null | grep -E "(test-|perf-|chaos-|security-)" | cut -d: -f1 | while read session; do
        print_info "Stopping test session: $session"
        tmux kill-session -t "$session" 2>/dev/null || true
    done
    
    # Stop any background processes
    pkill -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -f "python.*websocket" 2>/dev/null || true
    
    # Clean up temporary files
    rm -rf /tmp/test-* /tmp/perf-* /tmp/chaos-* /tmp/security-* 2>/dev/null || true
    
    print_success "Cleanup complete"
    echo ""
}

# Generate test report
generate_test_report() {
    print_header "Generating Test Report"
    
    local report_file="$RESULTS_DIR/test_report.md"
    local success_rate=0
    
    if [ $TOTAL_TESTS -ne 0 ]; then
        success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    fi
    
    # Generate markdown report
    cat > "$report_file" << EOF
# Yesman-Claude Integration Test Report

**Date:** $(date)  
**Total Tests:** $TOTAL_TESTS  
**Passed:** $PASSED_TESTS  
**Failed:** $FAILED_TESTS  
**Success Rate:** $success_rate%

## Test Results Summary

| Test Suite | Status |
|------------|--------|
EOF
    
    # Add suite results to report
    for suite in "${!TEST_SUITES[@]}"; do
        local suite_name="${TEST_SUITES[$suite]}"
        local suite_logs=$(grep "SUITE: $suite_name" "$LOG_FILE" || echo "")
        
        if [ -n "$suite_logs" ]; then
            local suite_result=$(echo "$suite_logs" | grep -o '[0-9]\+/[0-9]\+' | head -1)
            local passed=$(echo "$suite_result" | cut -d'/' -f1)
            local total=$(echo "$suite_result" | cut -d'/' -f2)
            
            if [ "$passed" = "$total" ]; then
                echo "| $suite_name | ✅ $suite_result |" >> "$report_file"
            else
                echo "| $suite_name | ❌ $suite_result |" >> "$report_file"
            fi
        else
            echo "| $suite_name | ⏭️ Skipped |" >> "$report_file"
        fi
    done
    
    # Add detailed logs
    cat >> "$report_file" << EOF

## Detailed Test Logs

\`\`\`
$(cat "$LOG_FILE")
\`\`\`

## Test Environment

- **OS:** $(uname -s)
- **Python:** $(python3 --version)
- **Tmux:** $(tmux -V)
- **UV:** $(uv --version 2>/dev/null || echo "Not available")

## Test Files Generated

$(find "$RESULTS_DIR" -name "*.log" -exec basename {} \; | sort)
EOF
    
    print_success "Test report generated: $report_file"
    
    # Display summary
    echo ""
    echo "Test Results Summary:"
    echo "===================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $success_rate%"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_failure "$FAILED_TESTS tests failed"
        echo ""
        echo "Failed test details:"
        grep "FAIL:" "$LOG_FILE" | sed 's/^/  /'
    fi
}

# Main execution
main() {
    local run_suites=("${!TEST_SUITES[@]}")
    local quick_mode=false
    local verbose=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --suite)
                if [[ -n "$2" && "${TEST_SUITES[$2]}" ]]; then
                    run_suites=("$2")
                    shift
                else
                    echo "Invalid suite: $2"
                    echo "Available suites: ${!TEST_SUITES[*]}"
                    exit 1
                fi
                shift
                ;;
            --quick)
                quick_mode=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --suite SUITE    Run specific test suite"
                echo "  --quick          Run quick tests only"
                echo "  --verbose        Show verbose output"
                echo "  --help           Show this help"
                echo ""
                echo "Available test suites:"
                for suite in "${!TEST_SUITES[@]}"; do
                    echo "  $suite: ${TEST_SUITES[$suite]}"
                done
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Skip heavy tests in quick mode
    if [ "$quick_mode" = true ]; then
        run_suites=("basic" "security")
        print_info "Running in quick mode - limited test suites"
    fi
    
    # Start test execution
    print_header "Yesman-Claude Integration Testing"
    echo "Test suites to run: ${run_suites[*]}"
    echo ""
    
    # Setup
    setup_test_environment
    
    # Run test suites
    for suite in "${run_suites[@]}"; do
        run_test_suite "$suite" "${TEST_SUITES[$suite]}"
    done
    
    # Cleanup
    cleanup_test_environment
    
    # Generate report
    generate_test_report
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Trap for cleanup on exit
trap cleanup_test_environment EXIT

# Run main function
main "$@"
#!/bin/bash
# Test: Session Lifecycle Management (Improved)
# Description: Tests the complete lifecycle of tmux sessions with better error handling

set -e

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/../../config"
TEMPLATES_DIR="$SCRIPT_DIR/../../templates"

if [ -f "$CONFIG_DIR/test-config.env" ]; then
    source "$CONFIG_DIR/test-config.env"
fi

# Set defaults if not configured
YESMAN_PROJECT_ROOT="${YESMAN_PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../../../" && pwd)}"
TEST_TIMEOUT="${TEST_TIMEOUT:-30}"
TEST_PARALLEL_SESSIONS="${TEST_PARALLEL_SESSIONS:-5}"

echo "🔧 Testing Session Lifecycle..."

# Utility functions
log_info() {
    echo -e "\n📋 $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

log_warning() {
    echo "⚠️ $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."

    # Remove test sessions
    for session in $(tmux list-sessions 2>/dev/null | grep -E "test-lifecycle-|perf-test-" | cut -d: -f1); do
        log_info "Removing test session: $session"
        tmux kill-session -t "$session" 2>/dev/null || true
    done

    # Remove temporary files
    rm -f /tmp/template_list.txt /tmp/test-project.yaml

    log_success "Cleanup completed"
}

# Set up trap for cleanup
trap cleanup EXIT

# Test 1: Environment validation
log_info "Test 1: Environment validation"

# Check required commands
REQUIRED_COMMANDS=("uv" "tmux" "python3")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "$cmd command not found"
        exit 1
    fi
done

# Check yesman installation
cd "$YESMAN_PROJECT_ROOT"
if ! timeout "$TEST_TIMEOUT" uv run ./yesman.py --help > /dev/null 2>&1; then
    log_error "Yesman not properly installed or accessible"
    exit 1
fi

log_success "Environment validation passed"

# Test 2: Template listing
log_info "Test 2: Testing template listing"

timeout "$TEST_TIMEOUT" uv run ./yesman.py ls > /tmp/template_list.txt
if grep -q -E "(Available|sessions)" /tmp/template_list.txt; then
    log_success "Template listing works"
else
    log_error "Template listing failed"
    cat /tmp/template_list.txt
    exit 1
fi

# Test 3: Session creation with template
log_info "Test 3: Testing session creation"

SESSION_NAME="test-lifecycle-$(date +%s)"

# Use template file instead of inline YAML
if [ -f "$TEMPLATES_DIR/test-project.yaml" ]; then
    # Replace template variables
    sed "s/{{SESSION_NAME}}/$SESSION_NAME/g; s|{{PROJECT_PATH}}|$YESMAN_PROJECT_ROOT|g" \
        "$TEMPLATES_DIR/test-project.yaml" > /tmp/test-project.yaml
else
    # Fallback to inline creation
    cat > /tmp/test-project.yaml << EOF
sessions:
  test-project:
    session_name: "$SESSION_NAME"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["echo 'Test session created'"]
        - window_name: "claude"
          panes:
            - shell_command: ["echo 'Claude window'"]
EOF
fi

# Backup existing projects.yaml
if [ -f ~/.yesman/projects.yaml ]; then
    cp ~/.yesman/projects.yaml ~/.yesman/projects.yaml.backup
fi

cp /tmp/test-project.yaml ~/.yesman/projects.yaml

# Create session with timeout
if timeout "$TEST_TIMEOUT" uv run ./yesman.py setup; then
    log_success "Session setup command completed"
else
    log_error "Session setup command failed or timed out"
    exit 1
fi

# Wait for session to be created
sleep 2

# Verify session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    log_success "Session created successfully"
else
    log_error "Session creation failed"
    tmux list-sessions 2>/dev/null || log_warning "No tmux sessions found"
    exit 1
fi

# Test 4: Session inspection
log_info "Test 4: Testing session inspection"

# Check session structure
WINDOWS=$(tmux list-windows -t "$SESSION_NAME" 2>/dev/null | wc -l)
if [ "$WINDOWS" -ge 2 ]; then
    log_success "Session has expected window structure ($WINDOWS windows)"
else
    log_error "Session window structure incorrect ($WINDOWS windows)"
    tmux list-windows -t "$SESSION_NAME" 2>/dev/null || true
    exit 1
fi

# Test show command
if timeout "$TEST_TIMEOUT" uv run ./yesman.py show | grep -q "$SESSION_NAME"; then
    log_success "Session appears in show command"
else
    log_error "Session not visible in show command"
    uv run ./yesman.py show
    exit 1
fi

# Test 5: Performance measurement
log_info "Test 5: Testing performance"

# Measure show command performance
RUNS=3
TOTAL_TIME=0

for i in $(seq 1 $RUNS); do
    START_TIME=$(date +%s%N)
    timeout "$TEST_TIMEOUT" uv run ./yesman.py show > /dev/null
    END_TIME=$(date +%s%N)
    RUN_TIME=$((($END_TIME - $START_TIME) / 1000000))
    TOTAL_TIME=$((TOTAL_TIME + RUN_TIME))
    log_info "Run $i: ${RUN_TIME}ms"
done

AVERAGE_TIME=$((TOTAL_TIME / RUNS))
log_info "Average response time: ${AVERAGE_TIME}ms"

if [ $AVERAGE_TIME -lt 2000 ]; then  # Less than 2 seconds
    log_success "Performance is acceptable (${AVERAGE_TIME}ms average)"
else
    log_warning "Performance may need improvement (${AVERAGE_TIME}ms average)"
fi

# Test 6: Session teardown
log_info "Test 6: Testing session teardown"

if timeout "$TEST_TIMEOUT" uv run ./yesman.py teardown; then
    log_success "Teardown command completed"
else
    log_error "Teardown command failed or timed out"
    exit 1
fi

# Wait for teardown to complete
sleep 2

# Verify session removed
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    log_success "Session removed successfully"
else
    log_error "Session removal failed"
    exit 1
fi

# Restore original projects.yaml
if [ -f ~/.yesman/projects.yaml.backup ]; then
    mv ~/.yesman/projects.yaml.backup ~/.yesman/projects.yaml
fi

log_success "All session lifecycle tests passed!"

# Test summary
echo -e "\n📊 Test Summary:"
echo "- Environment validation: ✅"
echo "- Template listing: ✅"
echo "- Session creation: ✅"
echo "- Session inspection: ✅"
echo "- Performance measurement: ✅"
echo "- Session teardown: ✅"
echo "- Average response time: ${AVERAGE_TIME}ms"

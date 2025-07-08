#!/bin/bash
# Test: Health Monitoring (Improved)
# Description: Tests project health monitoring with better structure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_LIB_DIR="$SCRIPT_DIR/../../lib"
export PYTHONPATH="$TEST_LIB_DIR:$PYTHONPATH"

echo "🏥 Testing Health Monitoring..."

# Check dependencies
echo -e "\n🔍 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git not found"
    exit 1
fi

# Check if test utils are available
if [ ! -f "$TEST_LIB_DIR/test_utils.py" ]; then
    echo "❌ Test utilities not found at $TEST_LIB_DIR/test_utils.py"
    exit 1
fi

if [ ! -f "$TEST_LIB_DIR/health_tests.py" ]; then
    echo "❌ Health test module not found at $TEST_LIB_DIR/health_tests.py"
    exit 1
fi

echo "✅ Dependencies checked"

# Run health monitoring tests using the dedicated Python module
echo -e "\n🚀 Running health monitoring tests..."
cd "$TEST_LIB_DIR"
python3 health_tests.py

# Capture exit code
HEALTH_TEST_EXIT_CODE=$?

if [ $HEALTH_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All health monitoring tests completed successfully!"
    exit 0
else
    echo -e "\n❌ Health monitoring tests failed!"
    exit 1
fi
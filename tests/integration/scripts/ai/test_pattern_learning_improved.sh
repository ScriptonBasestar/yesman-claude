#!/bin/bash
# Test: AI Pattern Learning (Improved)
# Description: Tests AI learning system accuracy and adaptation with better structure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_LIB_DIR="$SCRIPT_DIR/../../lib"
export PYTHONPATH="$TEST_LIB_DIR:$PYTHONPATH"

echo "🧠 Testing AI Pattern Learning..."

# Check dependencies
echo -e "\n🔍 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check if test utils are available
if [ ! -f "$TEST_LIB_DIR/test_utils.py" ]; then
    echo "❌ Test utilities not found at $TEST_LIB_DIR/test_utils.py"
    exit 1
fi

if [ ! -f "$TEST_LIB_DIR/ai_tests.py" ]; then
    echo "❌ AI test module not found at $TEST_LIB_DIR/ai_tests.py"
    exit 1
fi

echo "✅ Dependencies checked"

# Run AI tests using the dedicated Python module
echo -e "\n🚀 Running AI pattern learning tests..."
cd "$TEST_LIB_DIR"
python3 ai_tests.py

# Capture exit code
AI_TEST_EXIT_CODE=$?

if [ $AI_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All AI pattern learning tests completed successfully!"
    exit 0
else
    echo -e "\n❌ AI pattern learning tests failed!"
    exit 1
fi

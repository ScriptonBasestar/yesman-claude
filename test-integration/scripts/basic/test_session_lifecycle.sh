#!/bin/bash
# Test: Session Lifecycle Management
# Description: Tests the complete lifecycle of tmux sessions

set -e

echo "🔧 Testing Session Lifecycle..."

# Test 1: List templates
echo -e "\n📋 Test 1: Listing templates"
uv run ./yesman.py ls > /tmp/template_list.txt
if grep -q "Available" /tmp/template_list.txt; then
    echo "✅ Template listing works"
else
    echo "❌ Template listing failed"
    exit 1
fi

# Test 2: Create session
echo -e "\n🏗️ Test 2: Creating session"
SESSION_NAME="test-lifecycle-$(date +%s)"
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

cp /tmp/test-project.yaml ~/.yesman/projects.yaml
uv run ./yesman.py setup

# Verify session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "✅ Session created successfully"
else
    echo "❌ Session creation failed"
    exit 1
fi

# Test 3: Show sessions
echo -e "\n👀 Test 3: Showing sessions"
uv run ./yesman.py show | grep -q "$SESSION_NAME"
if [ $? -eq 0 ]; then
    echo "✅ Session appears in show command"
else
    echo "❌ Session not visible in show command"
    exit 1
fi

# Test 4: Session caching
echo -e "\n💾 Test 4: Testing session cache"
START_TIME=$(date +%s%N)
uv run ./yesman.py show > /dev/null
END_TIME=$(date +%s%N)
FIRST_RUN=$((($END_TIME - $START_TIME) / 1000000))

START_TIME=$(date +%s%N)
uv run ./yesman.py show > /dev/null
END_TIME=$(date +%s%N)
SECOND_RUN=$((($END_TIME - $START_TIME) / 1000000))

echo "First run: ${FIRST_RUN}ms, Second run: ${SECOND_RUN}ms"
if [ $SECOND_RUN -lt $FIRST_RUN ]; then
    echo "✅ Cache appears to be working (faster second run)"
else
    echo "⚠️ Cache may not be working effectively"
fi

# Test 5: Teardown session
echo -e "\n🗑️ Test 5: Tearing down session"
uv run ./yesman.py teardown

# Verify session removed
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "✅ Session removed successfully"
else
    echo "❌ Session removal failed"
    exit 1
fi

echo -e "\n✅ All session lifecycle tests passed!"
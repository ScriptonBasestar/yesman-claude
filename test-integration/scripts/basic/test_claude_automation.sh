#!/bin/bash
# Test: Claude Automation
# Description: Tests auto-response functionality for Claude prompts

set -e

echo "🤖 Testing Claude Automation..."

# Setup test session with Claude
SESSION_NAME="test-claude-$(date +%s)"
cat > /tmp/test-claude.yaml << EOF
sessions:
  claude-test:
    session_name: "$SESSION_NAME"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["pwd"]
        - window_name: "claude"
          panes:
            - shell_command: ["sleep 2", "echo 'Simulating Claude prompt...'", "echo 'Do you trust this workspace? (y/n)'", "read response", "echo \"You selected: \$response\""]
EOF

cp /tmp/test-claude.yaml ~/.yesman/projects.yaml

# Test 1: Start session with claude manager
echo -e "\n🚀 Test 1: Starting session with Claude manager"
uv run ./yesman.py setup

# Give claude manager time to start
sleep 3

# Test 2: Check claude manager status
echo -e "\n📊 Test 2: Checking Claude manager status"
if ps aux | grep -v grep | grep -q "claude_manager"; then
    echo "✅ Claude manager is running"
else
    echo "⚠️ Claude manager may not be running"
fi

# Test 3: Verify auto-response
echo -e "\n🔍 Test 3: Checking auto-response"
tmux capture-pane -t "$SESSION_NAME:claude" -p > /tmp/claude_output.txt

if grep -q "You selected: y" /tmp/claude_output.txt; then
    echo "✅ Auto-response worked!"
    cat /tmp/claude_output.txt
else
    echo "❌ Auto-response may not have worked"
    echo "Output:"
    cat /tmp/claude_output.txt
fi

# Test 4: Pattern detection
echo -e "\n🎯 Test 4: Testing pattern detection"
python3 -c "
from libs.core.prompt_detector import ClaudePromptDetector
detector = ClaudePromptDetector()

test_prompts = [
    'Do you trust this workspace? (y/n)',
    'Continue? [Y/n]',
    'Select option: 1) Option A  2) Option B  3) Option C',
    'Press Enter to continue...'
]

for prompt in test_prompts:
    prompt_type = detector.detect_prompt_type(prompt)
    print(f'Prompt: {prompt[:50]}... -> Type: {prompt_type}')
"

# Cleanup
echo -e "\n🧹 Cleaning up..."
uv run ./yesman.py teardown

echo -e "\n✅ Claude automation tests completed!"

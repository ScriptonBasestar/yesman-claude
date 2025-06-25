#!/usr/bin/env python3
"""Test script for dashboard controller functionality"""

import time
import libtmux
import subprocess
import sys

def test_controller():
    """Test the dashboard controller with test1 session"""
    
    server = libtmux.Server()
    session = server.find_where({"session_name": "test1"})
    
    if not session:
        print("❌ test1 session not found")
        return
    
    # Find claude pane
    claude_pane = None
    for window in session.list_windows():
        for pane in window.list_panes():
            cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
            if "claude" in cmd.lower():
                claude_pane = pane
                break
        if claude_pane:
            break
    
    if not claude_pane:
        print("❌ Claude pane not found in test1 session")
        return
    
    print("✅ Found claude pane in test1 session")
    
    # Test scenarios
    print("\n📋 Testing Dashboard Controller Features:")
    print("1. Start dashboard with: uv run yesman.py dashboard")
    print("2. Select 'test1' session from the left panel")
    print("3. Test the following features:")
    print("   - Start Controller button")
    print("   - Model selection (Default, Opus4, Sonnet4)")
    print("   - Auto switch (ON/OFF)")
    print("   - Restart Claude button")
    
    print("\n🔍 Current Claude pane status:")
    content = claude_pane.cmd("capture-pane", "-p").stdout
    last_lines = "\n".join(content[-10:]) if len(content) > 10 else "\n".join(content)
    print(last_lines)
    
    print("\n💡 To trigger test prompts in Claude:")
    print("1. Navigate to a directory with code files")
    print("2. Claude should show trust prompt automatically")
    print("3. Controller should auto-respond with '1'")
    
    print("\n📝 Pattern detection test commands:")
    print("- For trust prompt: cd to a new directory in Claude")
    print("- For selection: Use Claude commands that require choices")
    print("- For yes/no: Commands that ask for confirmation")

if __name__ == "__main__":
    test_controller()
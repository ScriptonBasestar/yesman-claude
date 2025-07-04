#!/usr/bin/env python3
"""Test prompt detection and auto-response"""

import time
from libs.core.claude_manager import ClaudeManager

def main():
    print("🚀 Testing prompt detection...")
    
    # Create manager and get controller
    manager = ClaudeManager()
    controller = manager.get_controller("proxynd")
    
    print(f"Controller found: {controller}")
    print(f"Auto-next enabled: {controller.is_auto_next_enabled}")
    print(f"Claude pane: {controller.claude_pane}")
    
    # Test 1: Capture content
    print("\n📋 Testing content capture...")
    content = controller.capture_pane_content()
    print(f"Content length: {len(content)}")
    print(f"Content preview: {repr(content[:200])}")
    
    # Test 2: Prompt detection
    print("\n🔍 Testing prompt detection...")
    prompt_info = controller.check_for_prompt(content)
    if prompt_info:
        print(f"✅ Prompt detected!")
        print(f"  Type: {prompt_info.type}")
        print(f"  Question: {prompt_info.question}")
        print(f"  Options: {prompt_info.options}")
        print(f"  Confidence: {prompt_info.confidence}")
        
        # Test 3: Auto-response
        print("\n🤖 Testing auto-response...")
        success = controller.auto_respond_to_selection(prompt_info)
        print(f"Auto-response success: {success}")
        
        if success:
            print("✅ Auto-response sent! Checking result...")
            time.sleep(2)
            new_content = controller.capture_pane_content()
            print(f"New content preview: {repr(new_content[:200])}")
        
    else:
        print("❌ No prompt detected")
        print("Content analysis:")
        print(f"  Waiting for input: {controller.is_waiting_for_input()}")

if __name__ == "__main__":
    main()
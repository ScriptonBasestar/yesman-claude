#!/usr/bin/env python3
"""Test full automation workflow."""

import time

from libs.core.claude_manager import ClaudeManager


def main():
    print("🚀 Testing full automation workflow...")

    # Create manager and get controller
    manager = ClaudeManager()
    controller = manager.get_controller("proxynd")

    print(f"Controller found: {controller}")
    print(f"Auto-next enabled: {controller.is_auto_next_enabled}")
    print(f"Claude pane: {controller.claude_pane}")

    # Start the controller
    print("\n📡 Starting controller...")
    if controller.start():
        print("✅ Controller started successfully!")

        try:
            # Let it run for 10 seconds to handle all prompts
            print("🔍 Monitoring for 10 seconds...")
            for i in range(10):
                time.sleep(1)
                print(f"  {i + 1}/10s", end="\r")

            print("\n\n📋 Final content check:")
            content = controller.capture_pane_content()
            if "Welcome to Claude Code!" in content:
                print("✅ SUCCESS: Claude completed startup sequence!")
                print("✅ Auto-response workflow is fully functional!")
            elif "continue" in content.lower() or "press enter" in content.lower():
                print("⏳ PARTIAL: Claude still waiting for input")
                print(f"Current prompt: {repr(content[-100:])}")
            else:
                print("❓ UNKNOWN: Claude state unclear")
                print(f"Content preview: {repr(content[:200])}")

        except KeyboardInterrupt:
            print("\n⏹️ Stopping controller...")
        finally:
            controller.stop()
            print("Controller stopped.")

    else:
        print("❌ Failed to start controller")

#!/usr/bin/env python3
"""Debug content capture and prompt detection."""

from libs.core.claude_manager import ClaudeManager


def main():
    print("🔍 Debugging content and prompt detection...")

    # Create manager and get controller
    manager = ClaudeManager()
    controller = manager.get_controller("proxynd")

    # Capture content
    content = controller.capture_pane_content()
    print(f"Content length: {len(content)}")
    print("=" * 50)
    print("FULL CONTENT:")
    print(repr(content))
    print("=" * 50)
    print("VISUAL CONTENT:")
    print(content)
    print("=" * 50)

    # Test prompt detection step by step
    prompt_detector = controller.prompt_detector
    prompt_info = prompt_detector.detect_prompt(content)

    if prompt_info:
        print("✅ Prompt detected!")
        print(f"  Type: {prompt_info.type}")
        print(f"  Question: {prompt_info.question}")
        print(f"  Options: {prompt_info.options}")
        print(f"  Confidence: {prompt_info.confidence}")
    else:
        print("❌ No prompt detected")

    # Check waiting for input
    waiting = prompt_detector.is_waiting_for_input(content)
    print(f"Waiting for input: {waiting}")


if __name__ == "__main__":
    main()

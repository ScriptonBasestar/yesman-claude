#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test full automation workflow."""

import time

from libs.core.claude_manager import ClaudeManager


def main() -> None:

    # Create manager and get controller
    manager = ClaudeManager()
    controller = manager.get_controller("proxynd")


    # Start the controller
    if controller.start():

        try:
            # Let it run for 10 seconds to handle all prompts
            for i in range(10):
                time.sleep(1)

            content = controller.capture_pane_content()
            if "Welcome to Claude Code!" in content or "continue" in content.lower() or "press enter" in content.lower():
                pass
            else:
                pass

        except KeyboardInterrupt:
            pass
        finally:
            controller.stop()

    else:
        pass

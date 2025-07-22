# Copyright notice.

import unittest
from unittest.mock import patch

from libs.core.claude_manager import DashboardController

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test auto response functionality."""


class TestAutoResponse(unittest.TestCase):
    def setUp(self) -> None:
        with patch("libs.core.claude_manager.libtmux.Server"):
            self.controller = DashboardController("test_session")

    def test_detect_claude_edit_prompt(self) -> None:
        """Test detection of Claude edit confirmation prompts."""
        content = """
Do you want to make this edit to VideoProcessingService.kt?
❯ 1. Yes
  2. Yes, and don't ask again this session (shift+tab)
  3. No, and tell Claude what to do differently (esc)
"""

        prompt_info = self.controller.detect_prompt_type(content)
        assert prompt_info is not None
        assert prompt_info["type"] == "numbered"
        assert prompt_info["count"] == 3

    def test_detect_claude_suggestion_prompt(self) -> None:
        """Test detection of Claude suggestion prompts."""
        content = "Would you like me to continue with the implementation?"

        prompt_info = self.controller.detect_prompt_type(content)
        assert prompt_info is not None
        assert prompt_info["type"] == "yn"
        assert prompt_info.get("context") == "claude_suggestion"

    def test_detect_various_numbered_formats(self) -> None:
        """Test detection of different numbered selection formats."""
        test_cases = [
            # [1] format
            "[1] Yes\n[2] No",
            # ❯ 1. format
            "❯ 1. Yes\n  2. No\n  3. Cancel",
            # 1. format
            "1. Continue\n2. Stop\n3. Restart",
            # 1) format
            "1) Accept\n2) Reject\n3) Skip",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                prompt_info = self.controller.detect_prompt_type(content)
                assert prompt_info is not None, f"Failed to detect: {content}"
                assert prompt_info["type"] == "numbered"
                assert prompt_info["count"] >= 2

    def test_detect_claude_question_prompts(self) -> None:
        """Test detection of various Claude question formats."""
        test_cases = [
            "Do you want to make this edit?",
            "Should I continue with the changes?",
            "Would you like to proceed?",
            "Shall I apply these modifications?",
            "Apply this change?",
            "Make this edit?",
            "Continue with the implementation?",
            "Proceed with the update?",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                prompt_info = self.controller.detect_prompt_type(content)
                assert prompt_info is not None, f"Failed to detect: {content}"
                assert prompt_info["type"] == "yn"
                assert prompt_info.get("context") == "claude_suggestion"

    def test_auto_respond_numbered_selection(self) -> None:
        """Test auto response for numbered selections."""
        prompt_info = {
            "type": "numbered",
            "options": [("1", "Yes"), ("2", "No")],
            "count": 2,
        }

        response = self.controller.auto_respond(prompt_info)
        assert response == "1"

    def test_auto_respond_claude_suggestion(self) -> None:
        """Test auto response for Claude suggestions."""
        prompt_info = {
            "type": "yn",
            "context": "claude_suggestion",
        }

        response = self.controller.auto_respond(prompt_info)
        assert response == "yes"

    def test_no_detection_for_regular_text(self) -> None:
        """Test that regular text doesn't trigger detection."""
        content = "This is just regular text without any prompts or questions."

        prompt_info = self.controller.detect_prompt_type(content)
        assert prompt_info is None

    def test_single_numbered_item_not_detected(self) -> None:
        """Test that single numbered items are not detected as selections."""
        content = "1. This is just a list item"

        prompt_info = self.controller.detect_prompt_type(content)
        assert prompt_info is None

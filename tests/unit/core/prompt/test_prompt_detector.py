# Copyright notice.

import pytest

from libs.core.prompt_detector import ClaudePromptDetector, PromptType

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test prompt detection functionality."""


class TestClaudePromptDetector:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.detector = ClaudePromptDetector()

    def test_detect_numbered_selection_prompt_should_return_correct_type(self) -> None:
        """Test that numbered selection prompts are correctly detected and
        return PromptType.NUMBERED_SELECTION.
        """
        content = """
Do you want to make this edit to VideoProcessingService.kt?
❯ 1. Yes
  2. Yes, and don't ask again this session (shift+tab)
  3. No, and tell Claude what to do differently (esc)
"""

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.NUMBERED_SELECTION
        assert len(prompt_info.options) == 3
        assert "Yes" in prompt_info.options[0][1]

    def test_detect_binary_choice_yn_prompt_should_return_binary_choice_type(
        self,
    ) -> None:
        """Test that y/n binary choice prompts are correctly detected and
        return PromptType.BINARY_CHOICE.
        """
        content = "Do you want to continue? (y/n)"

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.BINARY_CHOICE
        assert len(prompt_info.options) == 2

    def test_detect_true_false_prompt_should_return_true_false_type(self) -> None:
        """Test that true/false prompts are correctly detected and return
        PromptType.TRUE_FALSE.
        """
        content = "Enable advanced features? (true/false)"

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.TRUE_FALSE
        assert prompt_info.options[0][0] == "true"
        assert prompt_info.options[1][0] == "false"

    def test_detect_text_input(self) -> None:
        """Test detection of text input prompts."""
        content = "Enter your name:"

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.TEXT_INPUT
        assert "name" in prompt_info.metadata.get("field_name", "").lower()

    def test_detect_terminal_settings(self) -> None:
        """Test detection of terminal settings prompts."""
        content = "Configure terminal settings for optimal display"

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.TERMINAL_SETTINGS

    def test_detect_login_redirect(self) -> None:
        """Test detection of login/authentication prompts."""
        content = "Login required to continue. Please sign in."

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.LOGIN_REDIRECT

    def test_detect_confirmation(self) -> None:
        """Test detection of confirmation prompts."""
        content = "Are you sure you want to proceed with this action?"

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.type == PromptType.CONFIRMATION

    def test_no_detection_regular_text(self) -> None:
        """Test that regular text doesn't trigger detection."""
        content = "This is just regular output from Claude Code without any prompts."

        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is None

    def test_is_waiting_for_input_true(self) -> None:
        """Test waiting for input detection - positive cases."""
        test_cases = [
            "Select an option: ❯",
            "Enter value: ",
            "Choose [1/2]: ",
            "Continue? (y/n): ",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                result = self.detector.is_waiting_for_input(content)
                assert result, f"Should detect waiting for input: {content}"

    def test_is_waiting_for_input_false(self) -> None:
        """Test waiting for input detection - negative cases."""
        test_cases = [
            "Processing complete.",
            "File saved successfully.",
            "Building project...",
            "",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                result = self.detector.is_waiting_for_input(content)
                assert not result, f"Should not detect waiting for input: {content}"

    def test_clean_content(self) -> None:
        """Test content cleaning functionality."""
        content_with_ansi = "\x1b[31mError:\x1b[0m Choose option (1/2)"
        cleaned = self.detector._clean_content(content_with_ansi)

        assert "\x1b" not in cleaned
        assert "Choose option" in cleaned

    def test_extract_question(self) -> None:
        """Test question extraction."""
        content = """
Some output here
Do you want to continue with this operation?
[1] Yes
[2] No
"""

        question = self.detector._extract_question(content)
        assert "Do you want to continue" in question
        assert question.endswith("?")

    def test_numbered_selection_variations(self) -> None:
        """Test different numbered selection formats."""
        test_cases = [
            # [1] format
            "[1] Option A\n[2] Option B\n[3] Option C",
            # 1. format
            "1. First choice\n2. Second choice",
            # 1) format
            "1) Accept\n2) Reject\n3) Skip",
            # ❯ format
            "❯ 1. Yes\n  2. No\n  3. Cancel",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                prompt_info = self.detector.detect_prompt(content)
                assert (
                    prompt_info is not None
                ), f"Should detect numbered selection: {content}"
                assert prompt_info.type == PromptType.NUMBERED_SELECTION
                assert len(prompt_info.options) >= 2

    def test_confidence_scores(self) -> None:
        """Test that confidence scores are reasonable."""
        # High confidence case
        content = "❯ 1. Yes\n  2. No\n  3. Cancel"
        prompt_info = self.detector.detect_prompt(content)
        assert prompt_info is not None
        assert prompt_info.confidence >= 0.8

        # Lower confidence case
        content = "Maybe continue?"
        prompt_info = self.detector.detect_prompt(content)
        if prompt_info:  # May or may not detect
            assert prompt_info.confidence <= 0.6

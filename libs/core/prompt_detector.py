# Copyright notice.

import logging
import re
from dataclasses import dataclass
from enum import Enum

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Advanced prompt detection system for Claude Code interactions."""


class PromptType(Enum):
    """Types of prompts that can be detected."""

    NUMBERED_SELECTION = "numbered_selection"  # 1, 2, 3 choices
    BINARY_CHOICE = "binary_choice"  # 1/2, yes/no
    TRUE_FALSE = "true_false"  # true/false
    TEXT_INPUT = "text_input"  # Free text input
    TERMINAL_SETTINGS = "terminal_settings"  # Terminal configuration
    LOGIN_REDIRECT = "login_redirect"  # Authentication redirect
    CONFIRMATION = "confirmation"  # Simple yes/no confirmation
    UNKNOWN = "unknown"  # Unrecognized prompt


@dataclass
class PromptInfo:
    """Information about a detected prompt."""

    type: PromptType
    question: str
    options: list[tuple[str, str]]  # (key, description) pairs
    context: str  # Original content where prompt was found
    confidence: float  # 0.0 to 1.0 confidence score
    metadata: dict[str, object]  # Additional information


class ClaudePromptDetector:
    """Advanced prompt detector for Claude Code interactions."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("yesman.dashboard.prompt_detector")

        # Compile regex patterns for better performance
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for prompt detection."""
        # Numbered selection patterns
        self.numbered_patterns = [
            # ❯ 1. Option format
            re.compile(r"❯?\s*(\d+)\.\s+(.+)", re.MULTILINE),
            # [1] Option format
            re.compile(r"\[(\d+)\]\s+(.+)", re.MULTILINE),
            # 1) Option format
            re.compile(r"(\d+)\)\s+(.+)", re.MULTILINE),
        ]

        # Binary choice patterns
        self.binary_patterns = [
            re.compile(r"\(y/n\)", re.IGNORECASE),
            re.compile(r"\(yes/no\)", re.IGNORECASE),
            re.compile(r"\[Y/n\]"),
            re.compile(r"\[y/N\]"),
            re.compile(r"\[1/2\]"),
        ]

        # True/False patterns
        self.true_false_patterns = [
            re.compile(r"\(true/false\)", re.IGNORECASE),
            re.compile(r"\[true/false\]", re.IGNORECASE),
            re.compile(r"true\s+or\s+false", re.IGNORECASE),
        ]

        # Text input patterns
        self.text_input_patterns = [
            re.compile(r"Enter\s+(.+?):", re.IGNORECASE),
            re.compile(r"Type\s+(.+?):", re.IGNORECASE),
            re.compile(r"Input\s+(.+?):", re.IGNORECASE),
            re.compile(r"Please\s+enter\s+(.+?):", re.IGNORECASE),
        ]

        # Terminal settings patterns
        self.terminal_patterns = [
            re.compile(r"terminal\s+settings?", re.IGNORECASE),
            re.compile(r"configure\s+terminal", re.IGNORECASE),
            re.compile(r"terminal\s+preferences", re.IGNORECASE),
        ]

        # Login redirect patterns
        self.login_patterns = [
            re.compile(r"login\s+required", re.IGNORECASE),
            re.compile(r"authenticate", re.IGNORECASE),
            re.compile(r"sign\s+in", re.IGNORECASE),
            re.compile(r"redirect.*login", re.IGNORECASE),
        ]

        # Question indicators
        self.question_patterns = [
            re.compile(r"Do you want to (.+?)\?", re.IGNORECASE),
            re.compile(r"Would you like to (.+?)\?", re.IGNORECASE),
            re.compile(r"Should (.+?)\?", re.IGNORECASE),
            re.compile(r"Shall (.+?)\?", re.IGNORECASE),
            re.compile(r"(.+?)\?$", re.MULTILINE),
        ]

    def detect_prompt(self, content: str) -> PromptInfo | None:
        """Detect prompt type and extract information.

        Args:
            content: The terminal content to analyze

        Returns:
                Promptinfo | None object.
        """
        if not content or len(content.strip()) < 3:
            return None

        # Clean content for better analysis
        cleaned_content = self._clean_content(content)

        # Try different detection methods in order of specificity
        detectors = [
            self._detect_numbered_selection,
            self._detect_binary_choice,
            self._detect_true_false,
            self._detect_terminal_settings,
            self._detect_login_redirect,
            self._detect_text_input,
            self._detect_confirmation,
        ]

        for detector in detectors:
            try:
                prompt_info = detector(cleaned_content)
                if prompt_info:
                    self.logger.debug(
                        f"Detected prompt: {prompt_info.type.value}"
                    )  # noqa: G004
                    return prompt_info
            except Exception:
                self.logger.exception(
                    "Error in detector {detector.__name__}"
                )  # noqa: G004

        return None

    @staticmethod
    def _clean_content(content: str) -> str:
        """Clean and normalize content for analysis.

        Returns:
        str: Description of return value.
        """
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        cleaned = ansi_escape.sub("", content)

        # Keep line structure but normalize spacing within lines
        lines = []
        for line in cleaned.split("\n"):
            # Normalize whitespace within each line but preserve line breaks
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lines.append(normalized_line)

        # Rejoin with preserved line structure
        cleaned = "\n".join(lines)

        # Remove excessive empty lines
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

        return cleaned.strip()

    def _detect_numbered_selection(self, content: str) -> PromptInfo | None:
        """Detect numbered selection prompts (1, 2, 3, etc.).

        Returns:
        object: Description of return value.
        """
        all_options = []

        for pattern in self.numbered_patterns:
            matches = pattern.findall(content)
            if matches:
                all_options.extend([(num, desc.strip()) for num, desc in matches])

        if len(all_options) >= 2:
            # Extract question text (usually appears before options)
            lines = content.split("\n")
            question = ""

            for line in lines:
                if any(
                    f"{opt[0]}." in line or f"[{opt[0]}]" in line for opt in all_options
                ):
                    break
                if "?" in line:
                    question = line.strip()
                    break

            if not question:
                question = "Select an option:"

            return PromptInfo(
                type=PromptType.NUMBERED_SELECTION,
                question=question,
                options=all_options,
                context=content,
                confidence=0.9,
                metadata={"option_count": len(all_options)},
            )

        return None

    def _detect_binary_choice(self, content: str) -> PromptInfo | None:
        """Detect binary choice prompts (1/2, y/n, etc.).

        Returns:
        object: Description of return value.
        """
        for pattern in self.binary_patterns:
            if pattern.search(content):
                # Find the question
                question = self._extract_question(content)

                # Determine options based on pattern
                if "y/n" in pattern.pattern.lower():
                    options = [("y", "Yes"), ("n", "No")]
                elif "[1/2]" in pattern.pattern:
                    options = [("1", "Option 1"), ("2", "Option 2")]
                else:
                    options = [("yes", "Yes"), ("no", "No")]

                return PromptInfo(
                    type=PromptType.BINARY_CHOICE,
                    question=question,
                    options=options,
                    context=content,
                    confidence=0.8,
                    metadata={"pattern": pattern.pattern},
                )

        return None

    def _detect_true_false(self, content: str) -> PromptInfo | None:
        """Detect true/false prompts.

        Returns:
        object: Description of return value.
        """
        for pattern in self.true_false_patterns:
            if pattern.search(content):
                question = self._extract_question(content)
                options = [("true", "True"), ("false", "False")]

                return PromptInfo(
                    type=PromptType.TRUE_FALSE,
                    question=question,
                    options=options,
                    context=content,
                    confidence=0.85,
                    metadata={"pattern": pattern.pattern},
                )

        return None

    def _detect_text_input(self, content: str) -> PromptInfo | None:
        """Detect text input prompts.

        Returns:
        object: Description of return value.
        """
        for pattern in self.text_input_patterns:
            match = pattern.search(content)
            if match:
                question = match.group(0)
                field_name = match.group(1) if len(match.groups()) > 0 else "input"

                return PromptInfo(
                    type=PromptType.TEXT_INPUT,
                    question=question,
                    options=[],
                    context=content,
                    confidence=0.7,
                    metadata={"field_name": field_name},
                )

        return None

    def _detect_terminal_settings(self, content: str) -> PromptInfo | None:
        """Detect terminal settings prompts.

        Returns:
        object: Description of return value.
        """
        for pattern in self.terminal_patterns:
            if pattern.search(content):
                question = self._extract_question(content)

                return PromptInfo(
                    type=PromptType.TERMINAL_SETTINGS,
                    question=question,
                    options=[],
                    context=content,
                    confidence=0.6,
                    metadata={"category": "terminal_config"},
                )

        return None

    def _detect_login_redirect(self, content: str) -> PromptInfo | None:
        """Detect login/authentication prompts.

        Returns:
        object: Description of return value.
        """
        for pattern in self.login_patterns:
            if pattern.search(content):
                question = self._extract_question(content)

                return PromptInfo(
                    type=PromptType.LOGIN_REDIRECT,
                    question=question,
                    options=[],
                    context=content,
                    confidence=0.7,
                    metadata={"category": "authentication"},
                )

        return None

    def _detect_confirmation(self, content: str) -> PromptInfo | None:
        """Detect general confirmation prompts.

        Returns:
        object: Description of return value.
        """
        question = self._extract_question(content)

        if question and ("?" in question):
            # Look for continuation indicators
            continuation_indicators = [
                "continue",
                "proceed",
                "confirm",
                "sure",
                "okay",
                "accept",
                "apply",
                "save",
                "commit",
            ]

            if any(
                indicator in question.lower() for indicator in continuation_indicators
            ):
                return PromptInfo(
                    type=PromptType.CONFIRMATION,
                    question=question,
                    options=[("yes", "Yes"), ("no", "No")],
                    context=content,
                    confidence=0.5,
                    metadata={"category": "confirmation"},
                )

        return None

    def _extract_question(self, content: str) -> str:
        """Extract the main question from content.

        Returns:
        str: Description of return value.
        """
        lines = content.split("\n")

        # Look for lines ending with '?'
        for raw_line in reversed(lines):
            line = raw_line.strip()
            if line.endswith("?"):
                return line

        # Look for question patterns
        for pattern in self.question_patterns:
            match = pattern.search(content)
            if match:
                return match.group(0).strip()

        # Fallback: return the last non-empty line
        for raw_line in reversed(lines):
            line = raw_line.strip()
            if line:
                return line

        return "Please make a selection:"

    def is_waiting_for_input(self, content: str) -> bool:
        """Check if Claude Code is waiting for input.

        Args:
            content: Terminal content to check

        Returns:
            True if waiting for input, False otherwise
        """
        if not content:
            return False

        # Look for cursor indicators
        cursor_indicators = ["❯", ">", ":", "?", "[", "("]
        last_line = content.strip().split("\n")[-1]

        # Check if last line ends with input indicators
        if any(
            last_line.strip().endswith(indicator) for indicator in cursor_indicators
        ):
            return True

        # Check for selection menus
        return bool(self.detect_prompt(content))

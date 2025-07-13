"""Claude session and pane management"""

import logging
from typing import Any, Optional

import libtmux  # type: ignore

from ..utils import ensure_log_directory, get_default_log_path


class ClaudeSessionManager:
    """Manages tmux session and Claude pane discovery"""

    def __init__(self, session_name: str, pane_id: Optional[str] = None):
        self.session_name = session_name
        self.pane_id = pane_id
        self.server = libtmux.Server()
        self.session = None
        self.claude_pane: Any = None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for session manager"""
        logger = logging.getLogger(f"yesman.claude_session.{self.session_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        log_path = ensure_log_directory(get_default_log_path())
        log_file = log_path / f"claude_session_{self.session_name}.log"

        if not logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def initialize_session(self) -> bool:
        """Initialize tmux session and find Claude pane"""
        try:
            self.session = self.server.find_where({"session_name": self.session_name})
            if not self.session:
                self.logger.error(f"Session '{self.session_name}' not found")
                return False

            # Find Claude pane
            self.claude_pane = self._find_claude_pane()
            if not self.claude_pane:
                self.logger.warning(f"No Claude pane found in session '{self.session_name}'")
                return False

            self.logger.info(f"Successfully initialized session '{self.session_name}'")
            return True

        except Exception as e:
            self.logger.error(f"Could not initialize session: {e}")
            return False

    def _find_claude_pane(self):
        """Find pane running Claude"""
        if not self.session:
            return None

        for window in self.session.list_windows():
            for pane in window.list_panes():
                try:
                    # Check both command and pane content
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]

                    # Capture pane content to check for Claude indicators
                    capture_result = pane.cmd("capture-pane", "-p")
                    content = "\n".join(capture_result.stdout) if capture_result.stdout else ""

                    # Enhanced Claude detection patterns
                    claude_indicators = [
                        "claude" in cmd.lower(),
                        "Welcome to Claude Code" in content,
                        "? for shortcuts" in content,
                        "Claude Code" in content,
                        "anthropic" in content.lower(),
                        "claude.ai" in content.lower(),
                    ]

                    if any(claude_indicators):
                        self.logger.info(f"Found Claude pane: {window.name}:{pane.index}")
                        return pane

                except Exception as e:
                    self.logger.debug(f"Error checking pane {window.name}:{pane.index}: {e}")
                    continue

        self.logger.warning("No Claude pane found in any window")
        return None

    def get_claude_pane(self):
        """Get the Claude pane"""
        return self.claude_pane

    def is_session_available(self) -> bool:
        """Check if session and Claude pane are available"""
        return self.session is not None and self.claude_pane is not None

    def capture_pane_content(self, lines: int = 50) -> str:
        """Capture content from Claude pane"""
        if not self.claude_pane:
            return ""

        try:
            # Get the last N lines from the pane
            result = self.claude_pane.cmd("capture-pane", "-p", "-S", f"-{lines}")
            content = "\n".join(result.stdout) if result.stdout else ""
            return content
        except Exception as e:
            self.logger.error(f"Error capturing pane content: {e}")
            return ""

    def send_keys(self, keys: str):
        """Send keys to Claude pane"""
        if self.claude_pane:
            self.claude_pane.send_keys(keys)

    def get_current_command(self) -> str:
        """Get current command running in Claude pane"""
        if not self.claude_pane:
            return ""

        try:
            cmd = self.claude_pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
            return cmd
        except Exception as e:
            self.logger.error(f"Error getting current command: {e}")
            return ""

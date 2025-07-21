# Copyright notice.

import unittest
from unittest.mock import Mock, patch
from libs.core.claude_manager import DashboardController

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test claude restart functionality."""


class TestClaudeRestart(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_server = Mock()
        self.mock_session = Mock()
        self.mock_pane = Mock()

        with patch("libs.core.claude_manager.libtmux.Server") as mock_server_class:
            mock_server_class.return_value = self.mock_server
            self.mock_server.find_where.return_value = self.mock_session

            self.controller = DashboardController("test_session")
            self.controller.claude_pane = self.mock_pane

    def test_terminate_claude_process_success(self) -> None:
        """Test successful claude process termination."""
        # Mock command output showing claude is running, then not running
        cmd_outputs = ["claude", "bash"]
        self.mock_pane.cmd.return_value.stdout = [cmd_outputs.pop(0)]

        # Should not raise exception
        self.controller._terminate_claude_process()

        # Verify send_keys was called multiple times
        assert self.mock_pane.send_keys.call_count > 3

        # Verify clear commands were sent
        clear_calls = [call for call in self.mock_pane.send_keys.call_args_list if call[0][0] == "clear"]
        assert len(clear_calls) >= 2

    def test_terminate_claude_process_with_exception(self) -> None:
        """Test claude process termination with command check exception."""
        # Mock cmd to raise exception (simulating terminated process)
        self.mock_pane.cmd.side_effect = Exception("Process not found")

        # Should not raise exception
        self.controller._terminate_claude_process()

        # Verify basic termination commands were sent
        assert self.mock_pane.send_keys.call_count > 0

    def test_restart_claude_pane_success(self) -> None:
        """Test successful claude pane restart."""
        self.controller.selected_model = "sonnet"

        # Mock successful termination
        with patch.object(self.controller, "_terminate_claude_process") as mock_terminate:
            result = self.controller.restart_claude_pane()

            assert result
            mock_terminate.assert_called_once()

            # Verify claude command was sent
            claude_calls = [call for call in self.mock_pane.send_keys.call_args_list if "claude" in str(call)]
            assert len(claude_calls) > 0

    def test_restart_claude_pane_no_pane(self) -> None:
        """Test restart with no claude pane."""
        self.controller.claude_pane = None

        result = self.controller.restart_claude_pane()
        assert not result

    def test_restart_claude_pane_with_exception(self) -> None:
        """Test restart with exception during termination."""
        with patch.object(
            self.controller,
            "_terminate_claude_process",
            side_effect=Exception("Termination failed"),
        ):
            result = self.controller.restart_claude_pane()
            assert not result

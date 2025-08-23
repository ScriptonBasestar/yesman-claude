# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for show command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.show import ShowCommand, show
from libs.core.base_command import BaseCommand


class TestShowCommand:
    """Test show command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_show_command_inheritance(self) -> None:
        """Test that ShowCommand properly inherits from BaseCommand."""
        assert issubclass(ShowCommand, BaseCommand)

    @patch("commands.show.ShowCommand")
    def test_show_cli(self, mock_command_class: MagicMock) -> None:
        """Test show CLI command."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(show)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with()

    def test_execute_calls_list_running_sessions(self) -> None:
        """Test execute calls tmux_manager.list_running_sessions()."""
        with patch.object(ShowCommand, '__init__', lambda x: None):
            command = ShowCommand()
            command.tmux_manager = MagicMock()

            result = command.execute()

            # Assertions
            assert result == {"success": True, "action": "list_sessions"}
            command.tmux_manager.list_running_sessions.assert_called_once()

    def test_execute_returns_correct_result(self) -> None:
        """Test execute returns expected result format."""
        with patch.object(ShowCommand, '__init__', lambda x: None):
            command = ShowCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.list_running_sessions.return_value = None

            result = command.execute()

            # Check result format
            assert isinstance(result, dict)
            assert result["success"] is True
            assert result["action"] == "list_sessions"

    def test_execute_with_kwargs(self) -> None:
        """Test execute handles extra kwargs gracefully."""
        with patch.object(ShowCommand, '__init__', lambda x: None):
            command = ShowCommand()
            command.tmux_manager = MagicMock()

            # Execute with extra kwargs that should be ignored
            result = command.execute(unused_param="test", another_param=123)

            # Should still work normally
            assert result == {"success": True, "action": "list_sessions"}
            command.tmux_manager.list_running_sessions.assert_called_once()
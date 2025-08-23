# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for teardown command."""

from unittest.mock import MagicMock, patch
import pytest

from click.testing import CliRunner

from commands.teardown import TeardownCommand, teardown
from libs.core.base_command import BaseCommand, CommandError


class TestTeardownCommand:
    """Test teardown command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_teardown_command_inheritance(self) -> None:
        """Test that TeardownCommand properly inherits from BaseCommand."""
        assert issubclass(TeardownCommand, BaseCommand)

    @patch("commands.teardown.TeardownCommand")
    def test_teardown_cli_without_session_name(self, mock_command_class: MagicMock) -> None:
        """Test teardown CLI command without session name (kills all sessions)."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(teardown)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None)

    @patch("commands.teardown.TeardownCommand")
    def test_teardown_cli_with_session_name(self, mock_command_class: MagicMock) -> None:
        """Test teardown CLI command with specific session name."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with session name
        result = self.runner.invoke(teardown, ["test-session"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name="test-session")

    @patch("commands.teardown.libtmux.Server")
    @patch("commands.teardown.subprocess.run")
    def test_execute_with_no_sessions_defined(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute when no sessions are defined in projects.yaml."""
        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {"sessions": {}}
            command.print_warning = MagicMock()

            result = command.execute()

            assert result == {"success": True, "sessions_found": 0}
            command.print_warning.assert_called_once_with("No sessions defined in projects.yaml")

    @patch("commands.teardown.libtmux.Server")
    @patch("commands.teardown.subprocess.run")
    def test_execute_kills_all_sessions_successfully(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute kills all sessions successfully."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        
        # Mock session exists
        mock_session = MagicMock()
        mock_server_instance.sessions.get.return_value = mock_session

        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {
                        "override": {"session_name": "actual-test-session"}
                    }
                }
            }
            command.print_success = MagicMock()
            command.print_warning = MagicMock()

            result = command.execute()

            # Assertions
            assert result["success"] is True
            assert result["killed_sessions"] == ["actual-test-session"]
            assert result["not_found_sessions"] == []
            assert result["total_sessions"] == 1
            mock_subprocess.assert_called_once_with(["tmux", "kill-session", "-t", "actual-test-session"], check=False)
            command.print_success.assert_called_with("Killed session: actual-test-session")

    @patch("commands.teardown.libtmux.Server")
    @patch("commands.teardown.subprocess.run")
    def test_execute_with_specific_session_not_defined(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute with specific session that's not defined in projects.yaml."""
        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "existing-session": {}
                }
            }
            command.print_error = MagicMock()

            result = command.execute(session_name="non-existent-session")

            assert result == {"success": False, "error": "session_not_defined"}
            command.print_error.assert_called_once_with("Session non-existent-session not defined in projects.yaml")

    @patch("commands.teardown.libtmux.Server")
    @patch("commands.teardown.subprocess.run")
    def test_execute_with_session_not_running(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute when target session is not currently running."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        
        # Mock session doesn't exist
        mock_server_instance.sessions.get.return_value = None

        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {
                        "override": {"session_name": "not-running-session"}
                    }
                }
            }
            command.print_success = MagicMock()
            command.print_warning = MagicMock()

            result = command.execute()

            # Assertions
            assert result["success"] is True
            assert result["killed_sessions"] == []
            assert result["not_found_sessions"] == ["not-running-session"]
            mock_subprocess.assert_not_called()
            command.print_warning.assert_called_with("Session not-running-session not found")

    def test_execute_handles_exceptions(self) -> None:
        """Test execute handles exceptions and raises CommandError."""
        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.side_effect = Exception("Test error")

            with pytest.raises(CommandError) as exc_info:
                command.execute()

            assert "Error tearing down sessions: Test error" in str(exc_info.value)

    @patch("commands.teardown.libtmux.Server")
    @patch("commands.teardown.subprocess.run")
    def test_execute_uses_session_key_as_default_name(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute uses session key as default name when override is not provided."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        
        # Mock session exists
        mock_session = MagicMock()
        mock_server_instance.sessions.get.return_value = mock_session

        with patch.object(TeardownCommand, '__init__', lambda x: None):
            command = TeardownCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "default-session-name": {
                        # No override provided - should use session key as name
                    }
                }
            }
            command.print_success = MagicMock()
            command.print_warning = MagicMock()

            result = command.execute()

            # Should use session key as the actual session name
            assert result["killed_sessions"] == ["default-session-name"]
            mock_subprocess.assert_called_once_with(["tmux", "kill-session", "-t", "default-session-name"], check=False)
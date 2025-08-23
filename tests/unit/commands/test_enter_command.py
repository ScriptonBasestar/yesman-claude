# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for enter command."""

from unittest.mock import MagicMock, patch
import sys
import pytest

from click.testing import CliRunner

from commands.enter import EnterCommand, enter
from libs.core.base_command import BaseCommand, CommandError


class TestEnterCommand:
    """Test enter command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_enter_command_inheritance(self) -> None:
        """Test that EnterCommand properly inherits from BaseCommand."""
        assert issubclass(EnterCommand, BaseCommand)

    @patch("commands.enter.EnterCommand")
    def test_enter_cli_without_session_name(self, mock_command_class: MagicMock) -> None:
        """Test enter CLI command without session name (should prompt)."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(enter)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None, list_sessions=False)

    @patch("commands.enter.EnterCommand")
    def test_enter_cli_with_session_name(self, mock_command_class: MagicMock) -> None:
        """Test enter CLI command with specific session name."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with session name
        result = self.runner.invoke(enter, ["test-session"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name="test-session", list_sessions=False)

    @patch("commands.enter.EnterCommand")
    def test_enter_cli_with_list_option(self, mock_command_class: MagicMock) -> None:
        """Test enter CLI command with --list option."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with list option
        result = self.runner.invoke(enter, ["--list"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None, list_sessions=True)

    @patch("sys.stdin.isatty")
    def test_validate_preconditions_non_interactive_terminal(self, mock_isatty: MagicMock) -> None:
        """Test validate_preconditions raises error for non-interactive terminal."""
        mock_isatty.return_value = False

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            
            with pytest.raises(CommandError) as exc_info:
                command.validate_preconditions()

            assert "interactive terminal" in str(exc_info.value)

    @patch("sys.stdin.isatty")
    def test_validate_preconditions_interactive_terminal(self, mock_isatty: MagicMock) -> None:
        """Test validate_preconditions passes for interactive terminal."""
        mock_isatty.return_value = True

        with patch.object(EnterCommand, '__init__', lambda x: None):
            with patch('libs.core.base_command.BaseCommand.validate_preconditions'):
                command = EnterCommand()
                
                # Should not raise exception
                try:
                    command.validate_preconditions()
                except Exception:
                    pytest.fail("validate_preconditions() raised an exception unexpectedly")

    def test_execute_list_sessions(self) -> None:
        """Test execute with list_sessions=True."""
        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.tmux_manager = MagicMock()

            result = command.execute(list_sessions=True)

            assert result == {"action": "list", "success": True}
            command.tmux_manager.list_running_sessions.assert_called_once()

    @patch("commands.enter.libtmux.Server")
    @patch("commands.enter.subprocess.run")
    def test_execute_with_existing_session(self, mock_subprocess: MagicMock, mock_server: MagicMock) -> None:
        """Test execute with existing session name."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_session = MagicMock()
        mock_server_instance.sessions.get.return_value = mock_session

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance
            command.tmux_manager = MagicMock()
            command.print_info = MagicMock()

            result = command.execute(session_name="test-session")

            assert result == {"action": "attached", "session": "test-session", "success": True}
            command.print_info.assert_called_with("Attaching to session: test-session")

    @patch("commands.enter.libtmux.Server")
    def test_execute_with_non_existent_session(self, mock_server: MagicMock) -> None:
        """Test execute with non-existent session name."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.sessions.get.return_value = None

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {"sessions": {}}
            command.print_error = MagicMock()
            command.print_info = MagicMock()

            result = command.execute(session_name="non-existent")

            assert result == {"action": "not_found", "success": False}
            command.print_error.assert_called_with("Session 'non-existent' not found.")
            command.tmux_manager.list_running_sessions.assert_called_once()

    @patch("commands.enter.libtmux.Server")
    def test_select_session_no_running_sessions(self, mock_server: MagicMock) -> None:
        """Test _select_session when no sessions are running."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.sessions.get.return_value = None

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {
                        "override": {"session_name": "test-session"}
                    }
                }
            }
            command.print_warning = MagicMock()
            command.print_info = MagicMock()

            result = command._select_session()

            assert result is None
            command.print_warning.assert_called_with("No running yesman sessions found.")

    @patch("commands.enter.show_session_selector")
    @patch("commands.enter.libtmux.Server")
    def test_select_session_with_tui_selector(self, mock_server: MagicMock, mock_selector: MagicMock) -> None:
        """Test _select_session using TUI selector."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_session = MagicMock()
        mock_server_instance.sessions.get.return_value = mock_session
        mock_selector.return_value = "selected-session"

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-project": {
                        "override": {"session_name": "test-session"}
                    }
                }
            }

            result = command._select_session()

            assert result == "selected-session"
            mock_selector.assert_called_once()

    @patch("commands.enter.os.environ", {"TMUX": "test"})
    @patch("commands.enter.subprocess.run")
    def test_attach_to_session_inside_tmux(self, mock_subprocess: MagicMock) -> None:
        """Test _attach_to_session when already inside tmux."""
        EnterCommand._attach_to_session("test-session")
        
        mock_subprocess.assert_called_once_with(
            ["tmux", "switch-client", "-t", "test-session"], 
            check=False
        )

    @patch("commands.enter.os.environ", {})
    @patch("commands.enter.subprocess.run")
    def test_attach_to_session_outside_tmux(self, mock_subprocess: MagicMock) -> None:
        """Test _attach_to_session when outside tmux."""
        EnterCommand._attach_to_session("test-session")
        
        mock_subprocess.assert_called_once_with(
            ["tmux", "attach-session", "-t", "test-session"], 
            check=False
        )

    @patch("commands.enter.libtmux.Server")
    def test_resolve_session_name_direct_match(self, mock_server: MagicMock) -> None:
        """Test _resolve_session_name with direct session name match."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_session = MagicMock()
        mock_server_instance.sessions.get.return_value = mock_session

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance

            result = command._resolve_session_name("existing-session")

            assert result == "existing-session"

    @patch("commands.enter.libtmux.Server")
    def test_resolve_session_name_by_project_name(self, mock_server: MagicMock) -> None:
        """Test _resolve_session_name using project name lookup."""
        # Setup mocks
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        
        def mock_sessions_get(session_name=None, default=None):
            if session_name == "actual-session-name":
                return MagicMock()  # Session exists
            return default  # Session doesn't exist

        mock_server_instance.sessions.get.side_effect = mock_sessions_get

        with patch.object(EnterCommand, '__init__', lambda x: None):
            command = EnterCommand()
            command.server = mock_server_instance
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "project-name": {
                        "override": {"session_name": "actual-session-name"}
                    }
                }
            }

            result = command._resolve_session_name("project-name")

            assert result == "actual-session-name"
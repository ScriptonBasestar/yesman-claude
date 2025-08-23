# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for validate command."""

from unittest.mock import MagicMock, patch
import pytest
import os
import tempfile

from click.testing import CliRunner

from commands.validate import ValidateCommand, validate
from libs.core.base_command import BaseCommand, CommandError


class TestValidateCommand:
    """Test validate command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    def test_validate_command_inheritance(self) -> None:
        """Test that ValidateCommand properly inherits from BaseCommand."""
        assert issubclass(ValidateCommand, BaseCommand)

    @patch("commands.validate.ValidateCommand")
    def test_validate_cli_without_session_name(self, mock_command_class: MagicMock) -> None:
        """Test validate CLI command without session name (validates all sessions)."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(validate)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None, format="table")

    @patch("commands.validate.ValidateCommand")
    def test_validate_cli_with_session_name(self, mock_command_class: MagicMock) -> None:
        """Test validate CLI command with specific session name."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with session name
        result = self.runner.invoke(validate, ["test-session"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name="test-session", format="table")

    @patch("commands.validate.ValidateCommand")
    def test_validate_cli_with_format_option(self, mock_command_class: MagicMock) -> None:
        """Test validate CLI command with format option."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with tree format
        result = self.runner.invoke(validate, ["--format", "tree"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None, format="tree")

    @patch("commands.validate.Console")
    def test_execute_no_sessions_defined(self, mock_console_class: MagicMock) -> None:
        """Test execute when no sessions are defined."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {"sessions": {}}

            result = command.execute()

            assert result == {"success": False, "error": "no_sessions_defined"}
            mock_console.print.assert_called_once()

    @patch("commands.validate.Console")
    def test_execute_specific_session_not_found(self, mock_console_class: MagicMock) -> None:
        """Test execute when specific session is not defined."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "existing-session": {}
                }
            }

            result = command.execute(session_name="non-existent-session")

            assert result == {"success": False, "error": "session_not_defined"}
            mock_console.print.assert_called_once()

    @patch("commands.validate.Console")
    @patch("commands.validate.pathlib.Path")
    @patch("commands.validate._display_success")
    def test_execute_all_directories_valid(
        self, 
        mock_display_success: MagicMock,
        mock_path: MagicMock, 
        mock_console_class: MagicMock
    ) -> None:
        """Test execute when all directories are valid."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Mock path exists
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {
                        "template_name": "basic"
                    }
                }
            }
            command.tmux_manager.get_session_config.return_value = {
                "start_directory": "/valid/path",
                "windows": []
            }

            result = command.execute()

            # Check result format
            assert result["success"] is True
            assert result["total_sessions"] == 1
            assert result["valid_sessions"] == 1
            assert result["invalid_sessions"] == 0
            assert result["missing_directories"] == []
            
            # Check that success display function was called
            mock_display_success.assert_called_once()

    @patch("commands.validate.Console")
    @patch("commands.validate.pathlib.Path")
    @patch("commands.validate._display_table_format")
    def test_execute_with_missing_directories(
        self, 
        mock_display_table: MagicMock,
        mock_path: MagicMock, 
        mock_console_class: MagicMock
    ) -> None:
        """Test execute when some directories are missing."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Mock path doesn't exist
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {
                        "template_name": "basic"
                    }
                }
            }
            command.tmux_manager.get_session_config.return_value = {
                "start_directory": "/invalid/path",
                "windows": []
            }

            result = command.execute(format="table")

            # Check result format
            assert result["success"] is True
            assert result["total_sessions"] == 1
            assert result["valid_sessions"] == 0
            assert result["invalid_sessions"] == 1
            assert len(result["missing_directories"]) == 1
            
            # Check that table display function was called
            mock_display_table.assert_called_once()

    @patch("commands.validate.Console")
    @patch("commands.validate.pathlib.Path")
    def test_execute_with_windows_and_panes(
        self, 
        mock_path: MagicMock, 
        mock_console_class: MagicMock
    ) -> None:
        """Test execute validates window and pane directories."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        
        # Mock different path existence scenarios
        def mock_exists_side_effect():
            call_count = 0
            def side_effect(*args):
                nonlocal call_count
                call_count += 1
                # Session root exists, window dir doesn't exist, pane dir doesn't exist
                return call_count == 1
            return side_effect

        mock_path_instance = MagicMock()
        mock_path_instance.exists.side_effect = mock_exists_side_effect()
        mock_path_instance.is_absolute.return_value = True
        mock_path.return_value = mock_path_instance

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {}
                }
            }
            command.tmux_manager.get_session_config.return_value = {
                "start_directory": "/valid/session/path",
                "windows": [
                    {
                        "window_name": "test-window",
                        "start_directory": "/invalid/window/path",
                        "panes": [
                            {
                                "start_directory": "/invalid/pane/path"
                            }
                        ]
                    }
                ]
            }

            result = command.execute()

            # Should have found missing directories for window and pane
            assert result["valid_sessions"] == 0
            assert result["invalid_sessions"] == 1
            assert len(result["missing_directories"]) == 1

    def test_execute_handles_exceptions(self) -> None:
        """Test execute handles exceptions and raises CommandError."""
        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.side_effect = Exception("Test error")

            with pytest.raises(CommandError) as exc_info:
                command.execute()

            assert "Error validating directories: Test error" in str(exc_info.value)

    @patch("commands.validate.Console")
    @patch("commands.validate.pathlib.Path")
    def test_execute_handles_session_processing_errors(
        self, 
        mock_path: MagicMock, 
        mock_console_class: MagicMock
    ) -> None:
        """Test execute handles errors when processing individual sessions."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        with patch.object(ValidateCommand, '__init__', lambda x: None):
            command = ValidateCommand()
            command.tmux_manager = MagicMock()
            command.tmux_manager.load_projects.return_value = {
                "sessions": {
                    "test-session": {},
                    "error-session": {}
                }
            }
            # First call succeeds, second call raises exception
            command.tmux_manager.get_session_config.side_effect = [
                {"start_directory": "/valid/path", "windows": []},
                Exception("Session config error")
            ]

            # Mock path exists for valid session
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            result = command.execute()

            # Should process first session successfully and skip the error session
            assert result["success"] is True
            assert result["total_sessions"] == 2
            assert result["valid_sessions"] == 1
            
            # Check that error was printed
            mock_console.print.assert_called()
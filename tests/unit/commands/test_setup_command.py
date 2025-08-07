# Copyright notice.

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.setup import setup

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for setup command - Migrated to use centralized mock factories."""


class TestSetupCommand:
    """Migrated to pytest-style with centralized mocks - Fixed for actual setup command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("commands.setup.SetupCommand")
    def test_setup_creates_sessions(self, mock_command_class: MagicMock) -> None:
        """Test setup command creates sessions."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(setup)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name=None)

    @patch("commands.setup.SetupCommand")
    def test_setup_with_specific_project(self, mock_command_class: MagicMock) -> None:
        """Test setup command with specific project name."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with session name
        result = self.runner.invoke(setup, ["myproject"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(session_name="myproject")

    @patch("commands.setup.SetupCommand")
    def test_setup_with_dry_run(self, mock_command_class: MagicMock) -> None:
        """Test setup command with dry run flag."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        # Run command with dry run
        result = self.runner.invoke(setup, ["--dry-run"])

        # Assertions - dry run returns early, so run() is not called
        assert result.exit_code == 0
        mock_command.print_info.assert_called_once_with("Dry-run mode: showing what would be done")
        mock_command.run.assert_not_called()

    @patch("commands.setup.SetupCommand")
    def test_setup_with_force(self, mock_command_class: MagicMock) -> None:
        """Test setup command with force flag."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with force
        result = self.runner.invoke(setup, ["--force"])

        # Assertions
        assert result.exit_code == 0
        mock_command.print_warning.assert_called_once_with("Force mode: existing sessions will be recreated without prompting")
        mock_command.run.assert_called_once_with(session_name=None)

    @patch("commands.setup.SetupCommand")
    def test_setup_handles_command_error(self, mock_command_class: MagicMock) -> None:
        """Test setup handles command errors."""
        # Setup mock to raise exception
        mock_command = MagicMock()
        mock_command.run.side_effect = Exception("Test error")
        mock_command_class.return_value = mock_command

        # Run command
        result = self.runner.invoke(setup)

        # Should handle error gracefully
        assert result.exit_code != 0

    def test_setup_help_output(self) -> None:
        """Test setup command help output."""
        result = self.runner.invoke(setup, ["--help"])

        assert result.exit_code == 0
        assert "Create all tmux sessions" in result.output
        assert "--dry-run" in result.output
        assert "--force" in result.output

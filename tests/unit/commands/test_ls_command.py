# Copyright notice.

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.ls import ls

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for ls command - Fixed for actual ls command."""


class TestLsCommand:
    """Test ls command functionality."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("commands.ls.LsCommand")
    def test_ls_shows_projects_and_templates(self, mock_command_class: MagicMock) -> None:
        """Test ls command shows projects and templates."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command
        result = self.runner.invoke(ls)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(output_format="table")

    @patch("commands.ls.LsCommand")
    def test_ls_with_json_format(self, mock_command_class: MagicMock) -> None:
        """Test ls command with JSON format."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with JSON format
        result = self.runner.invoke(ls, ["--format", "json"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(output_format="json")

    @patch("commands.ls.LsCommand")
    def test_ls_with_yaml_format(self, mock_command_class: MagicMock) -> None:
        """Test ls command with YAML format."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command
        mock_command.run.return_value = None

        # Run command with YAML format
        result = self.runner.invoke(ls, ["--format", "yaml"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(output_format="yaml")

    @patch("commands.ls.LsCommand")
    def test_ls_handles_command_error(self, mock_command_class: MagicMock) -> None:
        """Test ls handles command errors."""
        # Setup mock to raise exception
        mock_command = MagicMock()
        mock_command.run.side_effect = Exception("Test error")
        mock_command_class.return_value = mock_command

        # Run command
        result = self.runner.invoke(ls)

        # Should handle error gracefully
        assert result.exit_code != 0

    def test_ls_help_output(self) -> None:
        """Test ls command help output."""
        result = self.runner.invoke(ls, ["--help"])

        assert result.exit_code == 0
        assert "List all available projects" in result.output
        assert "--format" in result.output

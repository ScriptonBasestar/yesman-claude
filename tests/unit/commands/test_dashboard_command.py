# Copyright notice.

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.dashboard import dashboard

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for dashboard command."""


class TestDashboardCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    @patch("commands.dashboard.DashboardRunCommand")
    def test_dashboard_starts_tauri(self, mock_command_class: MagicMock) -> None:
        """Test dashboard command starts Tauri interface."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        # Run command
        result = self.runner.invoke(dashboard)

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(interface="tauri", port=1420, dev=False)

    @patch("commands.dashboard.DashboardRunCommand")
    def test_dashboard_with_custom_port(self, mock_command_class: MagicMock) -> None:
        """Test dashboard with custom port."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        # Run command with port
        result = self.runner.invoke(dashboard, ["--port", "9000"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(interface="tauri", port=9000, dev=False)

    @patch("commands.dashboard.DashboardRunCommand")
    def test_dashboard_with_dev_flag(self, mock_command_class: MagicMock) -> None:
        """Test dashboard with dev flag."""
        # Setup mocks
        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        # Run command with dev flag
        result = self.runner.invoke(dashboard, ["--dev"])

        # Assertions
        assert result.exit_code == 0
        mock_command.run.assert_called_once_with(interface="tauri", port=1420, dev=True)

    @patch("commands.dashboard.DashboardRunCommand")
    def test_dashboard_command_error_handling(self, mock_command_class: MagicMock) -> None:
        """Test dashboard handles command errors."""
        # Setup mock to raise exception
        mock_command = MagicMock()
        mock_command.run.side_effect = Exception("Test error")
        mock_command_class.return_value = mock_command

        # Run command
        result = self.runner.invoke(dashboard)

        # Should handle error gracefully
        assert result.exit_code != 0

    def test_dashboard_help_output(self) -> None:
        """Test dashboard command help output."""
        result = self.runner.invoke(dashboard, ["--help"])

        assert result.exit_code == 0
        assert "Legacy dashboard command" in result.output
        assert "--port" in result.output
        assert "--dev" in result.output

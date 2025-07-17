"""Test for dashboard command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.dashboard import dashboard


class TestDashboardCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("commands.dashboard.subprocess.run")
    @patch("commands.dashboard.find_free_port")
    def test_dashboard_starts_streamlit(self, mock_find_port, mock_subprocess):
        """Test dashboard command starts streamlit app."""
        # Setup mocks
        mock_find_port.return_value = 8501
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Run command
        result = self.runner.invoke(dashboard)

        # Assertions
        assert result.exit_code == 0
        mock_subprocess.assert_called_once()

        # Check streamlit was called with correct arguments
        call_args = mock_subprocess.call_args[0][0]
        assert "streamlit" in call_args
        assert "run" in call_args
        assert "--server.port" in call_args
        assert "8501" in call_args

    @patch("commands.dashboard.subprocess.run")
    @patch("commands.dashboard.find_free_port")
    def test_dashboard_with_custom_port(self, mock_find_port, mock_subprocess):
        """Test dashboard with custom port."""
        # Setup mocks
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Run command with port
        result = self.runner.invoke(dashboard, ["--port", "9000"])

        # Assertions
        assert result.exit_code == 0
        mock_find_port.assert_not_called()  # Should not find free port

        # Check port 9000 was used
        call_args = mock_subprocess.call_args[0][0]
        assert "9000" in call_args

    @patch("commands.dashboard.subprocess.run")
    def test_dashboard_handles_streamlit_not_found(self, mock_subprocess):
        """Test dashboard handles missing streamlit."""
        # Setup mock to simulate streamlit not found
        mock_subprocess.side_effect = FileNotFoundError("streamlit not found")

        # Run command
        result = self.runner.invoke(dashboard)

        # Should handle error
        assert result.exit_code != 0
        assert "streamlit not found" in result.output or "Error" in result.output

    @patch("commands.dashboard.subprocess.run")
    @patch("commands.dashboard.find_free_port")
    def test_dashboard_handles_port_in_use(self, mock_find_port, mock_subprocess):
        """Test dashboard handles port already in use."""
        # Setup mocks
        mock_find_port.return_value = 8501
        mock_subprocess.return_value = MagicMock(returncode=1)

        # Run command
        result = self.runner.invoke(dashboard)

        # Should show error about port
        assert result.exit_code != 0
        assert "port" in result.output.lower() or "failed" in result.output.lower()

    @patch("commands.dashboard.webbrowser.open")
    @patch("commands.dashboard.subprocess.run")
    @patch("commands.dashboard.find_free_port")
    def test_dashboard_opens_browser(self, mock_find_port, mock_subprocess, mock_webbrowser):
        """Test dashboard opens browser when --no-browser is not set."""
        # Setup mocks
        mock_find_port.return_value = 8501
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Run command
        result = self.runner.invoke(dashboard)

        # Browser should open
        assert result.exit_code == 0
        mock_webbrowser.assert_called_once_with("http://localhost:8501")

    @patch("commands.dashboard.webbrowser.open")
    @patch("commands.dashboard.subprocess.run")
    @patch("commands.dashboard.find_free_port")
    def test_dashboard_no_browser_flag(self, mock_find_port, mock_subprocess, mock_webbrowser):
        """Test dashboard --no-browser flag prevents browser opening."""
        # Setup mocks
        mock_find_port.return_value = 8501
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Run command with no-browser flag
        result = self.runner.invoke(dashboard, ["--no-browser"])

        # Browser should not open
        assert result.exit_code == 0
        mock_webbrowser.assert_not_called()

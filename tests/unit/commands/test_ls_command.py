"""Test for ls command."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from commands.ls import ls


class TestLsCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("commands.ls.TmuxManager")
    def test_ls_shows_templates(self, mock_tmux_manager):
        """Test that ls command shows available templates."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.list_templates.return_value = [
            "template1.yaml",
            "template2.yaml",
        ]
        mock_tmux_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(ls)

        # Assertions
        assert result.exit_code == 0
        assert "Available templates:" in result.output
        assert "template1.yaml" in result.output
        assert "template2.yaml" in result.output

    @patch("commands.ls.TmuxManager")
    def test_ls_shows_running_sessions(self, mock_tmux_manager):
        """Test that ls command shows running sessions."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.list_sessions.return_value = [
            {"name": "session1", "windows": 2},
            {"name": "session2", "windows": 3},
        ]
        mock_tmux_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(ls)

        # Assertions
        assert result.exit_code == 0
        assert "Running sessions:" in result.output
        assert "session1" in result.output
        assert "session2" in result.output

    @patch("commands.ls.TmuxManager")
    def test_ls_handles_no_templates(self, mock_tmux_manager):
        """Test ls command when no templates exist."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.list_templates.return_value = []
        mock_manager_instance.list_sessions.return_value = []
        mock_tmux_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(ls)

        # Assertions
        assert result.exit_code == 0
        assert "No templates found" in result.output or "Available templates:" in result.output

    @patch("commands.ls.TmuxManager")
    def test_ls_handles_tmux_error(self, mock_tmux_manager):
        """Test ls command handles tmux errors gracefully."""
        # Setup mock to raise exception
        mock_tmux_manager.side_effect = Exception("Tmux not found")

        # Run command
        result = self.runner.invoke(ls)

        # Should handle error gracefully
        assert result.exit_code != 0
        assert "Error" in result.output or "Tmux not found" in result.output

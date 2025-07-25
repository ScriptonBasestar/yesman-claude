# Copyright notice.

import unittest
from unittest.mock import MagicMock, call, patch

from click.testing import CliRunner

from commands.setup import up

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for setup alias (up command)."""


class TestSetupAliasCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    @patch("commands.up.SessionManager")
    def test_setup_alias_creates_all_sessions(
        self, mock_session_manager: object
    ) -> None:
        """Test setup alias (up) command creates all sessions from
        projects.yaml.
        """
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_projects.return_value = [
            {"name": "project1", "template": "template1.yaml"},
            {"name": "project2", "template": "template2.yaml"},
        ]
        mock_manager_instance.create_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(up)

        # Assertions
        assert result.exit_code == 0
        assert mock_manager_instance.create_session.call_count == 2
        mock_manager_instance.create_session.assert_has_calls(
            [
                call("project1"),
                call("project2"),
            ],
            any_order=True,
        )

    @patch("commands.up.SessionManager")
    def test_setup_alias_with_specific_project(
        self, mock_session_manager: object
    ) -> None:
        """Test setup alias (up) command with specific project name."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance

        # Run command with project name
        result = self.runner.invoke(up, ["--project", "myproject"])

        # Assertions
        assert result.exit_code == 0
        mock_manager_instance.create_session.assert_called_once_with("myproject")

    @patch("commands.up.SessionManager")
    def test_setup_alias_handles_session_exists(
        self, mock_session_manager: object
    ) -> None:
        """Test setup alias (up) handles existing session gracefully."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.side_effect = Exception(
            "Session already exists"
        )
        mock_session_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(up, ["--project", "existing"])

        # Should handle error
        assert result.exit_code != 0
        assert "already exists" in result.output or "Error" in result.output

    @patch("commands.up.SessionManager")
    def test_setup_alias_with_force_flag(self, mock_session_manager: object) -> None:
        """Test setup alias (up) with --force flag recreates session."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.return_value = True
        mock_manager_instance.kill_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance

        # Run command with force flag
        result = self.runner.invoke(up, ["--project", "myproject", "--force"])

        # Assertions
        assert result.exit_code == 0
        mock_manager_instance.kill_session.assert_called_once_with("myproject")
        mock_manager_instance.create_session.assert_called_once_with("myproject")

    @patch("commands.up.SessionManager")
    def test_setup_alias_no_projects_found(self, mock_session_manager: object) -> None:
        """Test setup alias (up) when no projects are configured."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_projects.return_value = []
        mock_session_manager.return_value = mock_manager_instance

        # Run command
        result = self.runner.invoke(up)

        # Should show appropriate message
        assert result.exit_code == 0
        assert "No projects" in result.output or "Nothing to setup" in result.output

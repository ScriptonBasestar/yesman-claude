# Copyright notice.

from unittest.mock import patch
from click.testing import CliRunner
from commands.setup import setup
from tests.fixtures.mock_factories import PatchContextFactory

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test for setup command - Migrated to use centralized mock factories."""


class TestSetupCommand:
    """Migrated to pytest-style with centralized mocks - Fixed for actual setup command."""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("commands.setup.YesmanConfig")
    def test_setup_creates_all_sessions(self, mock_config: object) -> None:  # noqa: ARG002
        """Test setup command creates all sessions from projects.yaml."""
        projects = {
            "sessions": {
                "project1": {"template_name": "template1"},
                "project2": {"template_name": "template2"},
            },
        }

        with PatchContextFactory.patch_setup_tmux_manager(
            load_projects_result=projects,
            create_session_result=True,
        ) as mock_manager:
            # Run command
            result = self.runner.invoke(setup)

            # Assertions
            assert result.exit_code == 0
            assert mock_manager.create_session.call_count == 2
            mock_manager.list_running_sessions.assert_called_once()

    @patch("commands.setup.YesmanConfig")
    def test_setup_with_specific_project(self, mock_config: object) -> None:  # noqa: ARG002
        """Test setup command with specific project name."""
        projects = {
            "sessions": {
                "myproject": {"template_name": "my_template"},
            },
        }

        with PatchContextFactory.patch_setup_tmux_manager(
            load_projects_result=projects,
            create_session_result=True,
        ) as mock_manager:
            # Run command with project name
            result = self.runner.invoke(setup, ["myproject"])

            # Assertions
            assert result.exit_code == 0
            mock_manager.create_session.assert_called_once()

    @patch("commands.setup.YesmanConfig")
    def test_setup_handles_session_creation_failure(self, mock_config: object) -> None:  # noqa: ARG002
        """Test setup handles session creation failure gracefully."""
        projects = {
            "sessions": {
                "existing": {"template_name": "my_template"},
            },
        }

        with PatchContextFactory.patch_setup_tmux_manager(
            load_projects_result=projects,
            create_session_result=False,  # Simulate failure
        ):
            # Run command
            result = self.runner.invoke(setup, ["existing"])

            # Should handle error gracefully
            assert result.exit_code == 0  # Command completes but reports failure
            assert "already exists" in result.output or "failed to create" in result.output

    @patch("commands.setup.YesmanConfig")
    def test_setup_with_nonexistent_project(self, mock_config: object) -> None:  # noqa: ARG002
        """Test setup with nonexistent project name."""
        projects = {
            "sessions": {
                "valid_project": {"template_name": "template1"},
            },
        }

        with PatchContextFactory.patch_setup_tmux_manager(
            load_projects_result=projects,
        ) as mock_manager:
            # Run command with nonexistent project
            result = self.runner.invoke(setup, ["nonexistent"])

            # Should show error and not call create_session
            assert result.exit_code == 0  # Click command completes
            assert "not defined" in result.output
            mock_manager.create_session.assert_not_called()

    @patch("commands.setup.YesmanConfig")
    def test_setup_no_projects_found(self, mock_config: object) -> None:  # noqa: ARG002
        """Test setup when no projects are configured."""
        projects = {"sessions": {}}  # Empty sessions

        with PatchContextFactory.patch_setup_tmux_manager(
            load_projects_result=projects,
        ) as mock_manager:
            # Run command
            result = self.runner.invoke(setup)

            # Should show appropriate message
            assert result.exit_code == 0
            assert "No sessions defined" in result.output
            mock_manager.create_session.assert_not_called()

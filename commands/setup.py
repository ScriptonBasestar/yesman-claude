#!/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Improved setup command using refactored session setup logic."""

from typing import Any

import click

from libs.core.base_command import (
    BaseCommand,
    CommandError,
    ConfigCommandMixin,
    SessionCommandMixin,
)
from libs.core.progress_indicators import with_startup_progress
from libs.core.session_setup import SessionSetupService


class SetupCommand(BaseCommand, SessionCommandMixin, ConfigCommandMixin):
    """Create all tmux sessions defined in projects.yaml."""

    def execute(self, **kwargs: Any) -> dict:  # noqa: ANN401
        """Execute the setup command.

        Args:
            **kwargs: Keyword arguments including:
                session_name: Optional session name to set up only that session

        Returns:
            Dictionary with setup results
        """
        session_name = kwargs.get("session_name")
        with with_startup_progress("🔧 Initializing session setup...") as update:  # type: ignore
            setup_service = SessionSetupService(self.tmux_manager)
            update("🚀 Setting up tmux sessions...")

            # Set up sessions
            successful_count, failed_count = setup_service.setup_sessions(session_name)
            update("✅ Session setup completed")

        # Prepare result
        result = {
            "successful_sessions": successful_count,
            "failed_sessions": failed_count,
            "total_sessions": successful_count + failed_count,
            "success_rate": (
                (successful_count / (successful_count + failed_count) * 100)
                if (successful_count + failed_count) > 0
                else 0
            ),
        }

        # Log results
        if failed_count == 0:
            self.print_success(f"All {successful_count} sessions set up successfully")
        elif successful_count == 0:
            self.print_error(f"Failed to set up all {failed_count} sessions")
        else:
            self.print_warning(
                f"Partial success: {successful_count} successful, {failed_count} failed",
            )

        # List running sessions after setup
        self.tmux_manager.list_running_sessions()

        return result

    def validate_preconditions(self) -> None:
        """Validate command preconditions."""
        super().validate_preconditions()

        # Check if projects.yaml exists
        projects_config = self.load_projects_config()
        if not projects_config.get("sessions"):
            msg = "No sessions defined in projects.yaml"
            raise CommandError(msg)


@click.command()
@click.argument("session_name", required=False)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually creating sessions",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force recreation of existing sessions without prompting",
)
def setup(session_name: str | None, dry_run: bool, force: bool) -> None:  # noqa: FBT001
    """Create all tmux sessions defined in projects.yaml; or only a specified session if provided.

    Args:
        session_name: Optional session name to set up only that session
        dry_run: Show what would be done without actually creating sessions
        force: Force recreation of existing sessions without prompting
    """
    command = SetupCommand()

    if dry_run:
        command.print_info("Dry-run mode: showing what would be done")
        # TODO: Implement dry-run logic
        return

    if force:
        command.print_warning(
            "Force mode: existing sessions will be recreated without prompting"
        )
        # TODO: Pass force flag to setup service

    command.run(session_name=session_name)


# Create alias
up = setup

if __name__ == "__main__":
    setup()

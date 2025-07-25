# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
from typing import Any

import click

from libs.core.base_command import BaseCommand, SessionCommandMixin


class ShowCommand(BaseCommand, SessionCommandMixin):
    """List all running tmux sessions."""

    def execute(self, **kwargs: Any) -> dict:
        """Execute the show command.

        Returns:
        dict: Description of return value.
        """
        self.tmux_manager.list_running_sessions()
        return {"success": True, "action": "list_sessions"}


@click.command()
def show() -> None:
    """List all running tmux sessions."""
    command = ShowCommand()
    command.run()

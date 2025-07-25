#!/usr/bin/env python3

# Copyright notice.

import click

from commands.ai import ai
from commands.automate import automate
from commands.browse import browse
from commands.dashboard import dashboard, dashboard_group
from commands.enter import enter

# from commands.fix_lint import fix_lint  # File doesn't exist
from commands.logs import logs
from commands.ls import ls
from commands.multi_agent import multi_agent as multi_agent_cli
from commands.setup import setup
from commands.show import show
from commands.status import status
from commands.task_runner import task_runner
from commands.teardown import teardown
from commands.validate import validate

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Main entry point for the Yesman Claude application."""


@click.group()
def cli() -> None:
    """Yesman - Claude automation tool."""
    pass


cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)  # Main setup command
cli.add_command(teardown)  # Main teardown command
cli.add_command(dashboard)
cli.add_command(dashboard_group)  # New dashboard interface management
cli.add_command(enter)
cli.add_command(browse)
cli.add_command(ai)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(automate)
cli.add_command(task_runner)
cli.add_command(multi_agent_cli)
cli.add_command(validate)
# cli.add_command(fix_lint)  # Command doesn't exist

if __name__ == "__main__":
    cli()

#!/usr/bin/env python3
"""Main entry point for the Yesman Claude application."""

import click

from commands.ai import ai
from commands.automate import automate
from commands.browse import browse
from commands.cleanup import cleanup
from commands.dashboard import dashboard, dashboard_group
from commands.enter import enter

# from commands.fix_lint import fix_lint  # File doesn't exist
from commands.logs import logs
from commands.ls import ls
from commands.multi_agent import multi_agent as multi_agent_cli
from commands.setup import setup, up  # setup is main, up is alias
from commands.show import show
from commands.status import status
from commands.task_runner import task_runner
from commands.teardown import down, teardown  # teardown is main, down is alias
from commands.validate import validate


@click.group()
def cli():
    """Yesman - Claude automation tool."""
    pass


cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)  # Main setup command
cli.add_command(up)  # Alias for setup
cli.add_command(teardown)  # Main teardown command
cli.add_command(down)  # Alias for teardown
cli.add_command(dashboard)
cli.add_command(dashboard_group)  # New dashboard interface management
# Add dash as an alias for dashboard
dashboard_alias = click.Group(name="dash", help="Alias for 'dashboard' command")
for command_name, command in dashboard_group.commands.items():
    dashboard_alias.add_command(command, name=command_name)
cli.add_command(dashboard_alias)
cli.add_command(enter)
cli.add_command(browse)
cli.add_command(ai)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(automate)
cli.add_command(cleanup)
cli.add_command(task_runner)
cli.add_command(multi_agent_cli)
cli.add_command(validate)
# cli.add_command(fix_lint)  # Command doesn't exist

if __name__ == "__main__":
    cli()

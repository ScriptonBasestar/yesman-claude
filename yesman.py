#!/usr/bin/env python3
"""Main entry point for the Yesman Claude application."""
import click

from commands.ai import ai
from commands.automate import automate
from commands.browse import browse
from commands.cleanup import cleanup
from commands.dashboard import dashboard, dashboard_group
from commands.teardown import teardown, destroy, down  # teardown is main group, down is deprecated alias
from commands.enter import enter
from commands.logs import logs
from commands.ls import ls
from commands.multi_agent import multi_agent_cli
from commands.show import show
from commands.status import status
from commands.task_runner import task_runner
from commands.setup import setup, create, up  # setup is main group, up is deprecated alias


@click.group()
def cli():
    """Yesman - Claude automation tool."""
    pass


cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)  # Main setup group
cli.add_command(teardown)  # Main teardown group
cli.add_command(up)  # Deprecated alias
cli.add_command(down)  # Deprecated alias
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

if __name__ == "__main__":
    cli()

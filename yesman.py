#!/usr/bin/env python3
import click


@click.group()
def cli():
    """Yesman - Claude automation tool"""
    pass

from commands.ls import ls
from commands.show import show
from commands.setup import setup
from commands.teardown import teardown
from commands.dashboard import dashboard
from commands.enter import enter
from commands.browse import browse
from commands.ai import ai
from commands.status import status
from commands.logs import logs
from commands.automate import automate

cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(dashboard)
cli.add_command(enter)
cli.add_command(browse)
cli.add_command(ai)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(automate)

if __name__ == "__main__":
    cli()
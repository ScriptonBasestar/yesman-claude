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

cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(dashboard)
cli.add_command(enter)

if __name__ == "__main__":
    cli()
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
from commands.controller import controller
from commands.dashboard import dashboard

cli.add_command(ls)
cli.add_command(show)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(controller)
cli.add_command(dashboard)

if __name__ == "__main__":
    cli()
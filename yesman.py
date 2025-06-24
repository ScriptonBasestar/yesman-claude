#!/usr/bin/env python3
import click


@click.group()
def cli():
    """Yesman - Claude automation tool"""
    pass

from commands.ls import ls
from commands.show import show
from commands.session import session
from commands.setup import setup
from commands.teardown import teardown

cli.add_command(ls)
cli.add_command(show)
cli.add_command(session)
cli.add_command(setup)
cli.add_command(teardown)

if __name__ == "__main__":
    cli()
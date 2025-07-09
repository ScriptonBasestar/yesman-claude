#!/usr/bin/env python3
import click


@click.group()
def cli():
    """Yesman - Claude automation tool"""
    pass

from commands.ls import ls
from commands.show import show
from commands.up import up
from commands.down import down
from commands.setup import setup  # Keep for backward compatibility
from commands.teardown import teardown  # Keep for backward compatibility
from commands.dashboard import dashboard
from commands.enter import enter
from commands.browse import browse
from commands.ai import ai
from commands.status import status
from commands.logs import logs
from commands.automate import automate

cli.add_command(ls)
cli.add_command(show)
cli.add_command(up)
cli.add_command(down)
cli.add_command(setup)  # Keep for backward compatibility
cli.add_command(teardown)  # Keep for backward compatibility
cli.add_command(dashboard)
cli.add_command(enter)
cli.add_command(browse)
cli.add_command(ai)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(automate)

if __name__ == "__main__":
    cli()
import click

from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig


@click.command()
def show():
    """List all running tmux sessions"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    tmux_manager.list_running_sessions()

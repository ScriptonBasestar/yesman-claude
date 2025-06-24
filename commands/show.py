import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
def show():
    """List all running tmux sessions"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    tmux_manager.list_running_sessions()

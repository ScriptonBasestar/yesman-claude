import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
def ls():
    """List all available project"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    tmux_manager.list_project() 
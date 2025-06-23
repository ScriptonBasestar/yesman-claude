import click
from yesman import YesmanConfig, TmuxManager

@click.command()
def show():
    """List all available project sessions"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    tmux_manager.list_sessions() 
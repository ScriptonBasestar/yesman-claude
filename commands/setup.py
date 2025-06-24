import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
def setup():
    """Create all tmux sessions defined in projects.yaml"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("projects", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    for name in sessions.keys():
        if tmux_manager.create_session(name):
            click.echo(f"Created session: {name}")
        else:
            click.echo(f"Session {name} already exists.")
    click.echo("All sessions setup completed.") 
import click
from yesman import YesmanConfig, TmuxManager

@click.command()
def setup():
    """Create all tmux sessions defined in projects.yaml"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    for name, projs in sessions.items():
        if tmux_manager.create_session(name, projs):
            click.echo(f"Created session: {name}")
        else:
            click.echo(f"Session {name} already exists.")
    click.echo("All sessions setup completed.") 
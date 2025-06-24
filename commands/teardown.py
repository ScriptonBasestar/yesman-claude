import click
import subprocess
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.command()
def teardown():
    """Kill all tmux sessions defined in projects.yaml"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    for name in sessions.keys():
        subprocess.run(["tmux", "kill-session", "-t", name])
        click.echo(f"Killed session: {name}")
    click.echo("All sessions torn down.") 
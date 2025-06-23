import click
import subprocess
import os
from yesman import YesmanConfig, TmuxManager

@click.command()
@click.argument('session_name')
def session(session_name: str):
    """Create or attach tmux session for given project session"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if session_name not in sessions:
        click.echo(f"Session '{session_name}' not found")
        tmux_manager.list_sessions()
        return
    projects = sessions[session_name]
    if tmux_manager.create_session(session_name, projects):
        click.echo(f"Created session: {session_name}")
    else:
        click.echo(f"Session {session_name} already exists.")
    # Attach to session
    click.echo(f"Connecting to session: {session_name}")
    if os.environ.get("TMUX"):
        # Already inside tmux, switch to the session
        try:
            subprocess.run(["tmux", "switch-client", "-t", session_name], check=True)
        except subprocess.CalledProcessError:
            click.echo("Failed to switch client. The session might be attached elsewhere.")
    else:
        # Outside tmux, attach to the session
        subprocess.run(["tmux", "attach-session", "-t", session_name]) 
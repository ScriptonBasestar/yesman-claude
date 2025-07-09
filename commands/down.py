import click
import subprocess
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
import libtmux

@click.command()
def down():
    """Kill all tmux sessions defined in projects.yaml"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    
    server = libtmux.Server()
    for session_name, sess_conf in sessions.items():
        # Get the actual session name from override or use the key
        override_conf = sess_conf.get("override", {})
        actual_session_name = override_conf.get("session_name", session_name)
        
        # Check if session exists before trying to kill it
        if server.find_where({"session_name": actual_session_name}):
            subprocess.run(["tmux", "kill-session", "-t", actual_session_name])
            click.echo(f"Killed session: {actual_session_name}")
        else:
            click.echo(f"Session {actual_session_name} not found")
    click.echo("All sessions torn down.") 
import click
import subprocess
import os
from pathlib import Path
import yaml
from tmuxp.workspace.loader import expand, trickle  # type: ignore
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager

@click.group()
def session():
    """Manage tmux sessions"""
    pass

@session.command('create')
@click.argument('session_name')
def create_session(session_name: str):
    """Create and attach tmux session from a config file."""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    
    session_file = Path.home() / ".yesman" / "sessions" / f"{session_name}.yaml"
    
    # We need the real session name from the config for attaching
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
        workspace_config = expand(config_dict, cwd=session_file.parent)
        workspace_config = trickle(workspace_config)
        session_name_from_config = workspace_config.get("session_name", session_name)
    except Exception:
        click.echo(f"Could not read session config: {session_file}")
        tmux_manager.list_sessions()
        return

    if tmux_manager.create_session(session_name):
        click.echo(f"Created session: {session_name_from_config}")
    
    # Attach to session
    click.echo(f"Connecting to session: {session_name_from_config}")
    if os.environ.get("TMUX"):
        # Already inside tmux, switch to the session
        try:
            subprocess.run(["tmux", "switch-client", "-t", session_name_from_config], check=True)
        except subprocess.CalledProcessError:
             subprocess.run(["tmux", "attach-session", "-t", session_name_from_config])
    else:
        # Outside tmux, attach to the session
        subprocess.run(["tmux", "attach-session", "-t", session_name_from_config])

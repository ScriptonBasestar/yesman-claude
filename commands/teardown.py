import subprocess

import click
import libtmux

from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig


@click.command()
@click.argument("session_name", required=False)
def teardown(session_name):
    """Kill all tmux sessions (기본) 또는 지정한 세션만 삭제합니다."""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return

    server = libtmux.Server()
    # If a specific session is provided, only kill that session
    if session_name:
        if session_name not in sessions:
            click.echo(f"Session {session_name} not defined in projects.yaml")
            return
        sessions = {session_name: sessions[session_name]}
    for session_name, sess_conf in sessions.items():
        override_conf = sess_conf.get("override", {})
        actual_session_name = override_conf.get("session_name", session_name)
        if server.find_where({"session_name": actual_session_name}):
            subprocess.run(["tmux", "kill-session", "-t", actual_session_name], check=False)
            click.echo(f"Killed session: {actual_session_name}")
        else:
            click.echo(f"Session {actual_session_name} not found")
    click.echo("All sessions torn down.")

# Alias
@click.command()
@click.argument("session_name", required=False)
def down(session_name):
    """Alias for 'teardown' command"""
    ctx = click.get_current_context()
    ctx.invoke(teardown, session_name=session_name)

__all__ = ["teardown", "down"]

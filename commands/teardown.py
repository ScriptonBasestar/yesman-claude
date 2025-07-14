import subprocess

import click
import libtmux

from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig


@click.group(name="teardown")
def teardown():
    """Session teardown commands"""
    pass


@teardown.command()
def destroy():
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
            subprocess.run(["tmux", "kill-session", "-t", actual_session_name], check=False)
            click.echo(f"Killed session: {actual_session_name}")
        else:
            click.echo(f"Session {actual_session_name} not found")
    click.echo("All sessions torn down.")


# Deprecated alias
@click.command()
def down():
    """[DEPRECATED] Use 'teardown destroy' instead."""
    click.secho("[DEPRECATED] 'down' 명령어 대신 'teardown destroy'를 사용하세요.", fg="yellow")
    ctx = click.get_current_context()
    ctx.invoke(destroy)

__all__ = ["teardown", "destroy", "down"]

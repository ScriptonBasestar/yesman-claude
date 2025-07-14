import os
import click
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig

@click.command()
@click.argument("session_name", required=False)
def validate(session_name):
    """Check if all directories in projects.yaml exist (or only for a specific session)."""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    if session_name:
        if session_name not in sessions:
            click.echo(f"Session {session_name} not defined in projects.yaml")
            return
        sessions = {session_name: sessions[session_name]}

    missing = []
    for s_name, sess_conf in sessions.items():
        override_conf = sess_conf.get("override", {})
        start_dir = override_conf.get("start_directory", os.getcwd())
        expanded_dir = os.path.expanduser(start_dir)
        if not os.path.exists(expanded_dir):
            missing.append((s_name, "session", expanded_dir))
        # 윈도우별 start_directory 검사
        windows = sess_conf.get("windows", [])
        for i, window in enumerate(windows):
            window_start_dir = window.get("start_directory")
            if window_start_dir:
                if not os.path.isabs(window_start_dir):
                    base_dir = expanded_dir
                    window_start_dir = os.path.join(base_dir, window_start_dir)
                expanded_window_dir = os.path.expanduser(window_start_dir)
                if not os.path.exists(expanded_window_dir):
                    window_name = window.get("window_name", f"window_{i}")
                    missing.append((s_name, window_name, expanded_window_dir))
    if not missing:
        click.secho("✅ 모든 세션/윈도우의 디렉토리가 존재합니다!", fg="green")
    else:
        click.secho("❌ 존재하지 않는 디렉토리:", fg="red")
        for s_name, target, path in missing:
            click.echo(f"  [세션: {s_name}] 대상: {target} → {path}")

__all__ = ["validate"] 
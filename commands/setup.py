import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from pathlib import Path
import yaml

@click.command()
def setup():
    """Create all tmux sessions defined in projects.yaml"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    for session_name, sess_conf in sessions.items():
        template_name = sess_conf.get("template_name")
        if not template_name:
            click.echo(f"No template_name specified for session {session_name}")
            continue
        templates_path = Path.home() / ".yesman" / "templates"
        template_file = templates_path / f"{template_name}.yaml"
        if not template_file.is_file():
            click.echo(f"Template {template_name} not found at {template_file}")
            continue
        try:
            with open(template_file, "r", encoding="utf-8") as tf:
                template_conf = yaml.safe_load(tf) or {}
        except Exception as e:
            click.echo(f"Failed to read template {template_file}: {e}")
            continue
        # Apply overrides (all keys except template_name)
        override_conf = {k: v for k, v in sess_conf.items() if k != "template_name"}
        merged_conf = {**template_conf, **override_conf}
        # Write merged config to sessions path
        session_file = tmux_manager.templates_path / f"{template_name}.yaml"
        try:
            with open(session_file, "w", encoding="utf-8") as sf:
                yaml.safe_dump(merged_conf, sf, sort_keys=False)
        except Exception as e:
            click.echo(f"Failed to write session config {session_file}: {e}")
            continue
        # Create tmux session
        if tmux_manager.create_session(session_name, template_name):
            click.echo(f"Created session: {session_name}")
        else:
            click.echo(f"Session {session_name} already exists or failed to create.")
    click.echo("All sessions setup completed.") 
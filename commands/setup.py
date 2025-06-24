import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
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

        template_conf = {}

        if not template_name:
            click.echo(f"No template_name specified for session {session_name}. USE override")
        else:
            template_file = tmux_manager.templates_path / f"{template_name}.yaml"
            if not template_file.is_file():
                click.echo(f"template_name exists({template_name}). but file not found at {template_file}")
                continue

            try:
                with open(template_file, "r", encoding="utf-8") as tf:
                    template_conf = yaml.safe_load(tf) or {}
            except Exception as e:
                click.echo(f"Failed to read template {template_file}: {e}")
                continue

        
        # Prepare variables for template rendering
        override_conf = sess_conf.get("override", {})
        config_dict = {
            "session_name": override_conf.get("session_name", session_name),
            "start_directory": override_conf.get("start_directory", "~"),
            **override_conf
        }

        # template_conf에 config_dict를 덮어씌우기
        for key, value in config_dict.items():
            if key in template_conf:
                if isinstance(template_conf[key], list) and isinstance(value, list):
                    template_conf[key] = value
                else:
                    template_conf[key] = value
        
        # Apply overrides after rendering
        for key, value in override_conf.items():
            if key in config_dict:
                if isinstance(config_dict[key], list) and isinstance(value, list):
                    # For lists like windows, merge intelligently
                    config_dict[key] = value
                else:
                    config_dict[key] = value
        
        # window를 하나 추가해서 controller 실행
        config_dict["windows"].append({
            "window_name": "controller",
            "layout": "even-horizontal",
            "panes": [
                {"claude": {}},
            ]
        })

        # Create tmux session
        if tmux_manager.create_session(session_name, config_dict):
            click.echo(f"Created session: {session_name}")
        else:
            click.echo(f"Session {session_name} already exists or failed to create.")
    click.echo("All sessions setup completed.") 
import click
from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
import yaml

@click.command()
@click.argument('session_name', required=False)
def setup(session_name):
    """Create all tmux sessions defined in projects.yaml; or only a specified session if provided."""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    sessions = tmux_manager.load_projects().get("sessions", {})
    if not sessions:
        click.echo("No sessions defined in projects.yaml")
        return
    # If a specific session is provided, only set up that session
    if session_name:
        if session_name not in sessions:
            click.echo(f"Session {session_name} not defined in projects.yaml")
            return
        sessions = {session_name: sessions[session_name]}
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
        
        # Start with template configuration as base
        config_dict = template_conf.copy()
        
        # Apply default values
        config_dict["session_name"] = override_conf.get("session_name", session_name)
        # config_dict["start_directory"] = override_conf.get("start_directory", "~")
        config_dict["start_directory"] = override_conf.get("start_directory", pwd)
        
        # Apply all overrides
        for key, value in override_conf.items():
            config_dict[key] = value
        
        # window를 하나 추가해서 controller 실행
        # config_dict가 windows 키를 가지고 있는지 확인
        if "windows" not in config_dict:
            config_dict["windows"] = []
        
        # controller window 추가
        # actual_session_name = config_dict.get("session_name", session_name)
        # config_dict["windows"].append({
        #     "window_name": "controller",
        #     "panes": [
        #         f"yesman controller {actual_session_name}"
        #     ]
        # })

        # Create tmux session
        if tmux_manager.create_session(session_name, config_dict):
            click.echo(f"Created session: {session_name}")
        else:
            click.echo(f"Session {session_name} already exists or failed to create.")

    tmux_manager.list_running_sessions()

    click.echo("All sessions setup completed.") 
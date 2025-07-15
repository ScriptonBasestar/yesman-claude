import os

import click
import yaml

from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig


@click.command()
@click.argument("session_name", required=False)
def setup(session_name):
    """Create all tmux sessions (기본) 또는 지정한 세션만 생성합니다."""
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
    for s_name, sess_conf in sessions.items():
        template_name = sess_conf.get("template_name")

        template_conf = {}

        if not template_name:
            click.echo(f"No template_name specified for session {s_name}. USE override")
        else:
            template_file = tmux_manager.templates_path / f"{template_name}.yaml"
            if not template_file.is_file():
                click.echo(f"template_name exists({template_name}). but file not found at {template_file}")
                continue

            try:
                with open(template_file, encoding="utf-8") as tf:
                    template_conf = yaml.safe_load(tf) or {}
            except Exception as e:
                click.echo(f"Failed to read template {template_file}: {e}")
                continue

        # Prepare variables for template rendering
        override_conf = sess_conf.get("override", {})

        # Start with template configuration as base
        config_dict = template_conf.copy()

        # Apply default values
        config_dict["session_name"] = override_conf.get("session_name", s_name)
        config_dict["start_directory"] = override_conf.get("start_directory", os.getcwd())

        # Apply all overrides
        for key, value in override_conf.items():
            config_dict[key] = value

        # Validate start_directory exists
        start_dir = config_dict.get("start_directory")
        if start_dir:
            expanded_dir = os.path.expanduser(start_dir)
            if not os.path.exists(expanded_dir):
                click.echo(f"❌ Error: start_directory '{start_dir}' does not exist for session '{s_name}'")
                click.echo(f"   Resolved path: {expanded_dir}")
                if click.confirm(f"Would you like to create the missing directory '{expanded_dir}'?"):
                    try:
                        os.makedirs(expanded_dir, exist_ok=True)
                        click.echo(f"✅ Created directory: {expanded_dir}")
                    except Exception as e:
                        click.echo(f"❌ Failed to create directory: {e}")
                        continue
                else:
                    click.echo(f"⏭️  Skipping session '{s_name}'")
                    continue
            elif not os.path.isdir(expanded_dir):
                click.echo(f"❌ Error: start_directory '{start_dir}' is not a directory for session '{s_name}'")
                continue
            config_dict["start_directory"] = expanded_dir

        # Validate window start_directories if specified
        windows = config_dict.get("windows", [])
        validation_failed = False
        for i, window in enumerate(windows):
            window_start_dir = window.get("start_directory")
            if window_start_dir:
                if not os.path.isabs(window_start_dir):
                    base_dir = config_dict.get("start_directory", os.getcwd())
                    window_start_dir = os.path.join(base_dir, window_start_dir)

                expanded_window_dir = os.path.expanduser(window_start_dir)
                if not os.path.exists(expanded_window_dir):
                    window_name = window.get("window_name", f"window_{i}")
                    click.echo(f"❌ Error: Window '{window_name}' start_directory '{window.get('start_directory')}' does not exist")
                    click.echo(f"   Resolved path: {expanded_window_dir}")
                    if click.confirm(f"Would you like to create the missing directory '{expanded_window_dir}'?"):
                        try:
                            os.makedirs(expanded_window_dir, exist_ok=True)
                            click.echo(f"✅ Created directory: {expanded_window_dir}")
                        except Exception as e:
                            click.echo(f"❌ Failed to create directory: {e}")
                            validation_failed = True
                            break
                    else:
                        click.echo(f"⏭️  Skipping session '{s_name}' due to missing window directory")
                        validation_failed = True
                        break
                elif not os.path.isdir(expanded_window_dir):
                    click.echo(f"❌ Error: Window '{window.get('window_name', i)}' start_directory '{window.get('start_directory')}' is not a directory")
                    validation_failed = True
                    break
                window["start_directory"] = expanded_window_dir

        if validation_failed:
            continue

        # Create tmux session
        if tmux_manager.create_session(s_name, config_dict):
            click.echo(f"Created session: {s_name}")
        else:
            click.echo(f"Session {s_name} already exists or failed to create.")

    tmux_manager.list_running_sessions()

    click.echo("All sessions setup completed.")


# Alias
@click.command()
@click.argument("session_name", required=False)
def up(session_name):
    """Alias for 'setup' command"""
    ctx = click.get_current_context()
    ctx.invoke(setup, session_name=session_name)


__all__ = ["setup", "up"]

#!/usr/bin/env python3
import click
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from libs.yesman_config import YesmanConfig
from tmuxp.workspace.builder import WorkspaceBuilder  # type: ignore
from tmuxp.workspace.loader import expand, trickle  # type: ignore
import libtmux  # type: ignore

class TmuxManager:
    def __init__(self, config: YesmanConfig):
        self.config = config
        self.logger = logging.getLogger("yesman.tmux")
        self.templates_path = Path.home() / ".yesman" / "templates"
        self.templates_path.mkdir(parents=True, exist_ok=True)

    def create_session(self, template_name: str) -> bool:
        """Create tmux session from a YAML config file"""
        template_file = self.templates_path / f"{template_name}.yaml"
        if not template_file.is_file():
            self.logger.error(f"Session config file not found: {template_file}")
            self.list_templates()
            return False

        try:
            with open(template_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f) or {}
            workspace_config = expand(config_dict, cwd=template_file.parent)
            workspace_config = trickle(workspace_config)
            
            server = libtmux.Server()
            
            session_name_from_config = workspace_config.get("session_name", template_name)

            if server.find_where({"session_name": session_name_from_config}):
                self.logger.warning(f"Session {session_name_from_config} already exists.")
                return False

            builder = WorkspaceBuilder(workspace_config, server=server)
            builder.build()
            self.logger.info(f"Session {session_name_from_config} created successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create session from {template_file}: {e}")
            return False

    def list_templates(self):
        """List all available session templates"""
        templates = [f.stem for f in self.templates_path.glob("*.yaml")]
        
        if not templates:
            click.echo("No session templates found in ~/.yesman/templates/")
            return
        
        click.echo("Available session templates:")
        for template_name in templates:
            click.echo(f"  - {template_name}")

    def load_projects(self) -> Dict[str, Any]:
        """Load project sessions defined in projects.yaml"""
        global_path = Path.home() / ".yesman" / "projects.yaml"
        local_path = Path.cwd() / ".yesman" / "projects.yaml"
        projects: Dict[str, Any] = {}
        # Load global projects
        if global_path.exists():
            with open(global_path, "r", encoding="utf-8") as f:
                projects = yaml.safe_load(f) or {}
        # Override with local projects if present
        if local_path.exists():
            with open(local_path, "r", encoding="utf-8") as f:
                local_projects = yaml.safe_load(f) or {}
            projects = {**projects, **local_projects}
        return projects

    def list_running_sessions(self) -> None:
        """List currently running tmux sessions"""
        server = libtmux.Server()
        sessions = server.list_sessions()
        if not sessions:
            click.echo("No running tmux sessions found")
            return
        click.echo("Running tmux sessions:")
        for sess in sessions:
            name = sess.get("session_name")
            click.echo(f"  - {name}")
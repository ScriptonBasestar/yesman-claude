#!/usr/bin/env python3
import click
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from libs.yesman_config import YesmanConfig
from tmuxp.workspace.builder import WorkspaceBuilder  # type: ignore
from tmuxp.workspace.loader import expand  # type: ignore
import libtmux  # type: ignore

class TmuxManager:
    def __init__(self, config: YesmanConfig):
        self.config = config
        self.logger = logging.getLogger("yesman.tmux")
        # Directory for session templates
        self.templates_path = Path.home() / ".yesman" / "templates"
        self.templates_path.mkdir(parents=True, exist_ok=True)

    def create_session(self, session_name: str, config_dict: Dict) -> bool:
        """Create tmux session from a YAML config file in templates directory"""
        try:
            server = libtmux.Server()
            session_name_from_config = config_dict.get("session_name", session_name)

            if server.find_where({"session_name": session_name_from_config}):
                self.logger.warning(f"Session {session_name_from_config} already exists.")
                return False
            
            # print("--------------------------------")
            # # print(config_dict)
            # print(yaml.dump(config_dict))
            # print("--------------------------------")
            config_dict = expand(config_dict, cwd=self.templates_path)
            # print(yaml.dump(config_dict))
            # print("--------------------------------")

            builder = WorkspaceBuilder(config_dict, server=server)
            builder.build()
            self.logger.info(f"Session {session_name_from_config} created successfully.")
            return True
        except Exception as e:
            # print e
            raise e
            self.logger.error(f"Failed to create session from {session_name}: {e}")
            return False

    def get_templates(self) -> List[str]:
        """Get all available session templates"""
        return [f.stem for f in self.templates_path.glob("*.yaml")]

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
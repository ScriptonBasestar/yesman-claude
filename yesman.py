#!/usr/bin/env python3
import click
import os
import yaml
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from tmuxp.workspace.builder import WorkspaceBuilder  # type: ignore
from tmuxp.workspace.loader import expand, trickle  # type: ignore
import libtmux  # type: ignore

class YesmanConfig:
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        global_path = Path.home() / ".yesman" / "yesman.yaml"
        local_path = Path.cwd() / ".yesman" / "yesman.yaml"
        
        global_cfg: Dict[str, Any] = {}
        local_cfg: Dict[str, Any] = {}
        
        if global_path.exists():
            with open(global_path, "r", encoding="utf-8") as f:
                global_cfg = yaml.safe_load(f) or {}
        
        if local_path.exists():
            with open(local_path, "r", encoding="utf-8") as f:
                local_cfg = yaml.safe_load(f) or {}
        
        mode = local_cfg.get("mode", "merge")
        
        if mode == "local":
            if not local_cfg:
                raise RuntimeError(f"mode: local but {local_path} doesn't exist or is empty")
            return local_cfg
        elif mode == "merge":
            merged = {**global_cfg, **local_cfg}
            return merged
        else:
            raise ValueError(f"Unsupported mode: {mode}")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO").upper()
        log_path = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = Path(os.path.expanduser(log_path))
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "yesman.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("yesman")
        self.logger.info(f"Yesman started with log level: {log_level}")
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

class TmuxManager:
    def __init__(self, config: YesmanConfig):
        self.config = config
        self.logger = logging.getLogger("yesman.tmux")
        self.sessions_path = Path.home() / ".yesman" / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)

    def create_session(self, session_name: str) -> bool:
        """Create tmux session from a YAML config file"""
        session_file = self.sessions_path / f"{session_name}.yaml"
        if not session_file.is_file():
            self.logger.error(f"Session config file not found: {session_file}")
            self.list_sessions()
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f) or {}
            workspace_config = expand(config_dict, cwd=session_file.parent)
            workspace_config = trickle(workspace_config)
            
            server = libtmux.Server()
            
            session_name_from_config = workspace_config.get("session_name", session_name)

            if server.find_where({"session_name": session_name_from_config}):
                self.logger.warning(f"Session {session_name_from_config} already exists.")
                return False

            builder = WorkspaceBuilder(workspace_config, server=server)
            builder.build()
            self.logger.info(f"Session {session_name_from_config} created successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create session from {session_file}: {e}")
            return False

    def list_sessions(self):
        """List all available session configs"""
        sessions = [f.stem for f in self.sessions_path.glob("*.yaml")]
        
        if not sessions:
            click.echo("No session configs found in ~/.yesman/sessions/")
            return
        
        click.echo("Available session configs:")
        for session_name in sessions:
            click.echo(f"  - {session_name}")

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

@click.group()
def cli():
    """Yesman - Claude automation tool"""
    pass

from commands.show import show
from commands.session import session
from commands.setup import setup
from commands.teardown import teardown

cli.add_command(show)
cli.add_command(session)
cli.add_command(setup)
cli.add_command(teardown)

if __name__ == "__main__":
    cli()
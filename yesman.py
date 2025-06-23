#!/usr/bin/env python3
import click
import os
import yaml
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class YesmanConfig:
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        global_path = Path.home() / ".yesman" / "yesman.yaml"
        local_path = Path.cwd() / ".yesman" / "yesman.yaml"
        
        global_cfg = {}
        local_cfg = {}
        
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
        self.projects_path = Path.home() / ".yesman" / "projects.yaml"
    
    def load_projects(self) -> Dict[str, Any]:
        if not self.projects_path.exists():
            self.logger.warning(f"Projects file not found: {self.projects_path}")
            return {}
        
        with open(self.projects_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def create_session(self, session_name: str, projects: list):
        """Create tmux session with specified projects"""
        self.logger.info(f"Creating tmux session: {session_name}")
        
        # Check if session already exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True
        )
        
        if result.returncode == 0:
            self.logger.warning(f"Session {session_name} already exists")
            return False
        
        # Create new session
        subprocess.run([
            "tmux", "new-session", "-d", "-s", session_name
        ])
        
        for idx, project in enumerate(projects):
            if idx > 0:
                # Create new window for each project after the first
                subprocess.run([
                    "tmux", "new-window", "-t", f"{session_name}:{idx}",
                    "-n", project["name"]
                ])
            else:
                # Rename first window
                subprocess.run([
                    "tmux", "rename-window", "-t", f"{session_name}:0",
                    project["name"]
                ])
            
            # Split pane horizontally
            subprocess.run([
                "tmux", "split-window", "-h", "-t", f"{session_name}:{idx}"
            ])
            
            # Left pane: run claude
            subprocess.run([
                "tmux", "send-keys", "-t", f"{session_name}:{idx}.0",
                f"cd {project['path']} && python {Path(__file__).parent}/auto_claude.py",
                "Enter"
            ])
            
            # Right pane: regular terminal
            subprocess.run([
                "tmux", "send-keys", "-t", f"{session_name}:{idx}.1",
                f"cd {project['path']}", "Enter"
            ])
        
        return True
    
    def list_sessions(self):
        """List all project sessions"""
        projects = self.load_projects()
        sessions = projects.get("sessions", {})
        
        if not sessions:
            click.echo("No sessions defined in projects.yaml")
            return
        
        click.echo("Available sessions:")
        for session_name, projects in sessions.items():
            click.echo(f"  - {session_name} ({len(projects)} projects)")
            for project in projects:
                click.echo(f"    • {project['name']} ({project['path']})")

@click.group()
def cli():
    """Yesman - Claude automation tool"""
    pass

@cli.command()
@click.argument('session_name', required=False)
def claude(session_name: Optional[str] = None):
    """Launch Claude with project configuration"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    
    if session_name is None:
        # List available sessions
        tmux_manager.list_sessions()
        return
    
    # Load projects
    projects_data = tmux_manager.load_projects()
    sessions = projects_data.get("sessions", {})
    
    if session_name not in sessions:
        click.echo(f"Session '{session_name}' not found in projects.yaml")
        tmux_manager.list_sessions()
        return
    
    # Create tmux session
    projects = sessions[session_name]
    if tmux_manager.create_session(session_name, projects):
        click.echo(f"Created session: {session_name}")
        # Attach to the session
        subprocess.run(["tmux", "attach-session", "-t", session_name])
    else:
        click.echo(f"Session {session_name} already exists. Attaching...")
        subprocess.run(["tmux", "attach-session", "-t", session_name])

@cli.command()
def list():
    """List all available project sessions"""
    config = YesmanConfig()
    tmux_manager = TmuxManager(config)
    tmux_manager.list_sessions()

if __name__ == "__main__":
    cli()
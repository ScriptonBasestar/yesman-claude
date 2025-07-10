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
    
    def get_session_info(self, session_name: str) -> Dict[str, Any]:
        """Get session information directly from tmux"""
        def fetch_session_info():
            """Fetch session information from tmux"""
            try:
                server = libtmux.Server()
                session = server.find_where({"session_name": session_name})
                if not session:
                    return {"exists": False, "session_name": session_name}
                
                # Get session details
                windows = []
                for window in session.list_windows():
                    panes = []
                    for pane in window.list_panes():
                        panes.append({
                            "pane_id": pane.get("pane_id"),
                            "pane_current_command": pane.get("pane_current_command", ""),
                            "pane_active": pane.get("pane_active") == "1",
                            "pane_width": pane.get("pane_width"),
                            "pane_height": pane.get("pane_height")
                        })
                    
                    windows.append({
                        "window_id": window.get("window_id"),
                        "window_name": window.get("window_name"),
                        "window_active": window.get("window_active") == "1",
                        "panes": panes
                    })
                
                return {
                    "exists": True,
                    "session_name": session_name,
                    "session_id": session.get("session_id"),
                    "session_created": session.get("session_created"),
                    "windows": windows
                }
            except Exception as e:
                self.logger.error(f"Failed to get session info for {session_name}: {e}")
                return {"exists": False, "session_name": session_name, "error": str(e)}
        
        return fetch_session_info()
    
    def get_cached_sessions_list(self) -> List[Dict[str, Any]]:
        """Get list of all sessions directly from tmux"""
        try:
            server = libtmux.Server()
            sessions = server.list_sessions()
            return [
                {
                    "session_name": sess.get("session_name"),
                    "session_id": sess.get("session_id"),
                    "session_created": sess.get("session_created"),
                    "session_windows": sess.get("session_windows", 0)
                }
                for sess in sessions
            ]
        except Exception as e:
            self.logger.error(f"Failed to get sessions list: {e}")
            return []

    def teardown_session(self, session_name: str) -> bool:
        """Teardown a specific tmux session"""
        try:
            server = libtmux.Server()
            session = server.find_where({"session_name": session_name})
            if session:
                session.kill_session()
                self.logger.info(f"Session {session_name} terminated.")
                return True
            else:
                self.logger.warning(f"Session {session_name} not found.")
                return False
        except Exception as e:
            self.logger.error(f"Failed to teardown session {session_name}: {e}")
            return False

    def teardown_all_sessions(self) -> None:
        """Teardown all tmux sessions"""
        try:
            server = libtmux.Server()
            server.kill_server()
            self.logger.info("All tmux sessions terminated.")
        except Exception as e:
            self.logger.error(f"Failed to teardown all sessions: {e}")

    def attach_to_session(self, session_name: str) -> None:
        """Attach to a specific tmux session"""
        import os
        os.system(f"tmux attach -t {session_name}")

    def get_session_activity(self, session_name: str) -> Dict[str, Any]:
        """
        Get session activity data by parsing session logs.
        """
        try:
            log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
            safe_session_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_')).rstrip()
            log_file = Path(log_path_str).expanduser() / f"{safe_session_name}.log"

            if not log_file.exists():
                # Fallback to the main log if a session-specific log is not found
                log_file = Path(log_path_str).expanduser() / "yesman.log"
                if not log_file.exists():
                    return {"session_name": session_name, "activity_data": []}

            from datetime import datetime, timedelta
            import re
            from collections import defaultdict

            # Activity per hour for the last 7 days
            activity_counts = defaultdict(int)
            
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    # Extract timestamp from log line
                    # Example log format: [2025-07-10 14:22:01,161] [INFO] [session:my-session] Log message
                    match = re.match(r'\[(.*?)\]', line)
                    if match:
                        timestamp_str = match.group(1).split(',')[0] # Get 'YYYY-MM-DD HH:MM:SS'
                        try:
                            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            if log_time > seven_days_ago:
                                # Round down to the hour
                                hour_timestamp = log_time.strftime('%Y-%m-%dT%H:00:00')
                                activity_counts[hour_timestamp] += 1
                        except ValueError:
                            continue
            
            # Format data for heatmap
            activity_data = [
                {"timestamp": ts, "activity": count}
                for ts, count in activity_counts.items()
            ]
            
            return {
                "session_name": session_name,
                "activity_data": activity_data
            }
        except Exception as e:
            self.logger.error(f"Failed to get session activity for {session_name}: {e}")
            return {"session_name": session_name, "activity_data": []}
    

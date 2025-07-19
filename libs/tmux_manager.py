#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Any

import click
import libtmux
import yaml
from tmuxp.workspace.builder import WorkspaceBuilder
from tmuxp.workspace.loader import expand

from libs.yesman_config import YesmanConfig


class TmuxManager:
    def __init__(self, config: YesmanConfig):
        self.config = config
        self.logger = logging.getLogger("yesman.tmux")
        # Directory for session templates
        self.templates_path = config.get_templates_dir()
        self.sessions_path = config.get_sessions_dir()

    def create_session(self, session_name: str, config_dict: dict) -> bool:
        """Create tmux session from a YAML config file in templates directory."""
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

    def get_templates(self) -> list[str]:
        """Get all available session templates."""
        return [f.stem for f in self.templates_path.glob("*.yaml")]

    def load_projects(self) -> dict[str, Any]:
        """Load project sessions from individual session files in sessions/ directory."""
        projects: dict[str, Any] = {"sessions": {}}

        # 새로운 sessions/ 디렉토리에서 개별 세션 파일들 로드
        if self.sessions_path.exists():
            for session_file in self.sessions_path.glob("*.yaml"):
                try:
                    with open(session_file, encoding="utf-8") as f:
                        session_config = yaml.safe_load(f) or {}
                    session_name = session_file.stem
                    projects["sessions"][session_name] = session_config
                    self.logger.debug(f"Loaded session config: {session_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load session file {session_file}: {e}")

            # .yml 확장자도 지원
            for session_file in self.sessions_path.glob("*.yml"):
                try:
                    with open(session_file, encoding="utf-8") as f:
                        session_config = yaml.safe_load(f) or {}
                    session_name = session_file.stem
                    # .yaml 파일이 이미 있으면 건너뛰기 (중복 방지)
                    if session_name not in projects["sessions"]:
                        projects["sessions"][session_name] = session_config
                        self.logger.debug(f"Loaded session config: {session_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load session file {session_file}: {e}")

        return projects

    def save_session_config(self, session_name: str, session_config: dict[str, Any]) -> bool:
        """Save a session configuration to an individual file."""
        try:
            session_file = self.sessions_path / f"{session_name}.yaml"
            with open(session_file, "w", encoding="utf-8") as f:
                yaml.dump(session_config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"Saved session config: {session_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session config {session_name}: {e}")
            return False

    def delete_session_config(self, session_name: str) -> bool:
        """Delete a session configuration file."""
        try:
            session_file = self.sessions_path / f"{session_name}.yaml"
            if session_file.exists():
                session_file.unlink()
                self.logger.info(f"Deleted session config: {session_name}")
                return True

            # .yml 확장자도 확인
            session_file_yml = self.sessions_path / f"{session_name}.yml"
            if session_file_yml.exists():
                session_file_yml.unlink()
                self.logger.info(f"Deleted session config: {session_name}")
                return True

            self.logger.warning(f"Session config file not found: {session_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete session config {session_name}: {e}")
            return False

    def get_session_config_file(self, session_name: str) -> Path | None:
        """Get the path to a session configuration file."""
        yaml_file = self.sessions_path / f"{session_name}.yaml"
        yml_file = self.sessions_path / f"{session_name}.yml"

        if yaml_file.exists():
            return yaml_file
        elif yml_file.exists():
            return yml_file
        else:
            return None

    def list_session_configs(self) -> list[str]:
        """List all available session configurations."""
        session_names = set()

        # .yaml 파일들
        for session_file in self.sessions_path.glob("*.yaml"):
            session_names.add(session_file.stem)

        # .yml 파일들
        for session_file in self.sessions_path.glob("*.yml"):
            session_names.add(session_file.stem)

        return sorted(list(session_names))

    def load_template(self, template_name: str) -> dict[str, Any]:
        """Load a specific template file."""
        template_path = self.templates_path / f"{template_name}.yaml"
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found at {template_path}")

        with open(template_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_session_config(self, session_name: str, session_config: dict[str, Any]) -> dict[str, Any]:
        """Get final session configuration after applying template and overrides."""
        # Start with base configuration
        final_config = {}

        # Load template if specified
        template_name = session_config.get("template_name")
        if template_name:
            try:
                template_config = self.load_template(template_name)
                final_config = template_config.copy()
            except FileNotFoundError:
                self.logger.warning(f"Template {template_name} not found for session {session_name}")

        # Apply override configuration
        override_config = session_config.get("override", {})
        if override_config:
            # Deep merge override config
            final_config = self._deep_merge_dicts(final_config, override_config)

        # Ensure session_name is set
        if "session_name" not in final_config:
            final_config["session_name"] = session_name

        return final_config

    def _deep_merge_dicts(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def list_running_sessions(self) -> None:
        """List currently running tmux sessions."""
        server = libtmux.Server()
        sessions = server.list_sessions()
        if not sessions:
            click.echo("No running tmux sessions found")
            return
        click.echo("Running tmux sessions:")
        for sess in sessions:
            name = sess.get("session_name")
            click.echo(f"  - {name}")

    def get_session_info(self, session_name: str) -> dict[str, Any]:
        """Get session information directly from tmux."""

        def fetch_session_info() -> dict[str, Any]:
            """Fetch session information from tmux."""
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
                        panes.append(
                            {
                                "pane_id": pane.get("pane_id"),
                                "pane_current_command": pane.get("pane_current_command", ""),
                                "pane_active": pane.get("pane_active") == "1",
                                "pane_width": pane.get("pane_width"),
                                "pane_height": pane.get("pane_height"),
                            }
                        )

                    windows.append(
                        {
                            "window_id": window.get("window_id"),
                            "window_name": window.get("window_name"),
                            "window_active": window.get("window_active") == "1",
                            "panes": panes,
                        }
                    )

                return {
                    "exists": True,
                    "session_name": session_name,
                    "session_id": session.get("session_id"),
                    "session_created": session.get("session_created"),
                    "windows": windows,
                }
            except Exception as e:
                self.logger.error(f"Failed to get session info for {session_name}: {e}")
                return {"exists": False, "session_name": session_name, "error": str(e)}

        return fetch_session_info()

    def get_cached_sessions_list(self) -> list[dict[str, Any]]:
        """Get list of all sessions directly from tmux."""
        try:
            server = libtmux.Server()
            sessions = server.list_sessions()
            return [
                {
                    "session_name": sess.get("session_name"),
                    "session_id": sess.get("session_id"),
                    "session_created": sess.get("session_created"),
                    "session_windows": sess.get("session_windows", 0),
                }
                for sess in sessions
            ]
        except Exception as e:
            self.logger.error(f"Failed to get sessions list: {e}")
            return []

    def teardown_session(self, session_name: str) -> bool:
        """Teardown a specific tmux session."""
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
        """Teardown all tmux sessions."""
        try:
            server = libtmux.Server()
            server.kill_server()
            self.logger.info("All tmux sessions terminated.")
        except Exception as e:
            self.logger.error(f"Failed to teardown all sessions: {e}")

    def attach_to_session(self, session_name: str) -> None:
        """Attach to a specific tmux session."""
        import subprocess

        # Use subprocess.run for security (no shell injection)
        try:
            subprocess.run(["tmux", "attach", "-t", session_name], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to attach to session {session_name}: {e}")
        except FileNotFoundError:
            self.logger.error("tmux command not found")

    def get_session_activity(self, session_name: str) -> dict[str, Any]:
        """Get session activity data by parsing session logs."""
        try:
            log_path_str = self.config.get("log_path", "~/.scripton/yesman/logs/")
            safe_session_name = "".join(c for c in session_name if c.isalnum() or c in ("-", "_")).rstrip()
            log_file = Path(log_path_str).expanduser() / f"{safe_session_name}.log"

            if not log_file.exists():
                # Fallback to the main log if a session-specific log is not found
                log_file = Path(log_path_str).expanduser() / "yesman.log"
                if not log_file.exists():
                    return {"session_name": session_name, "activity_data": []}

            import re
            from collections import defaultdict
            from datetime import datetime, timedelta

            # Activity per hour for the last 7 days
            activity_counts: dict[str, int] = defaultdict(int)

            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)

            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    # Extract timestamp from log line
                    # Example log format: [2025-07-10 14:22:01,161] [INFO] [session:my-session] Log message
                    match = re.match(r"\[(.*?)\]", line)
                    if match:
                        timestamp_str = match.group(1).split(",")[0]  # Get 'YYYY-MM-DD HH:MM:SS'
                        try:
                            log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if log_time > seven_days_ago:
                                # Round down to the hour
                                hour_timestamp = log_time.strftime("%Y-%m-%dT%H:00:00")
                                activity_counts[hour_timestamp] += 1
                        except ValueError:
                            continue

            # Format data for heatmap
            activity_data = [{"timestamp": ts, "activity": count} for ts, count in activity_counts.items()]

            return {
                "session_name": session_name,
                "activity_data": activity_data,
            }
        except Exception as e:
            self.logger.error(f"Failed to get session activity for {session_name}: {e}")
            return {"session_name": session_name, "activity_data": []}

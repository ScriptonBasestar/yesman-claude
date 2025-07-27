#!/usr/bin/env python3

# Copyright notice.

import logging
import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click
import libtmux
import yaml
from tmuxp.workspace.builder import WorkspaceBuilder
from tmuxp.workspace.loader import expand

# Avoid circular import
if TYPE_CHECKING:
    from libs.yesman_config import YesmanConfig

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License


class TmuxManager:
    def __init__(self, config: "YesmanConfig") -> None:
        self.config = config
        self.logger = logging.getLogger("yesman.tmux")
        # Directory for session templates
        self.templates_path = config.get_templates_dir()
        self.sessions_path = config.get_sessions_dir()

    def create_session(self, session_name: str, config_dict: dict) -> bool:
        """Create tmux session from a YAML config file in templates directory.

        Returns:
        Boolean indicating the created item.
        """
        try:
            server = libtmux.Server()
            session_name_from_config = config_dict.get("session_name", session_name)

            if server.sessions.get(session_name=session_name_from_config, default=None):
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

        except (OSError, RuntimeError, ValueError, AttributeError):
            self.logger.exception("Failed to create session from %s", session_name)
            return False
        else:
            return True

    def create_session_from_config(self, config_dict: dict) -> bool:
        """Create tmux session from configuration dictionary.

        This is an alias for create_session to maintain compatibility.

        Returns:
        Boolean indicating the created item.
        """
        session_name = config_dict.get("session_name", "default")
        return self.create_session(session_name, config_dict)

    def get_templates(self) -> list[str]:
        """Get all available session templates.

        Returns:
        List of the requested data.
        """
        return [f.stem for f in self.templates_path.glob("*.yaml")]

    def load_projects(self) -> dict[str, object]:
        """Load project sessions from individual session files in sessions/ directory.

        Returns:
        Dict containing all sessions.
        """
        projects: dict[str, object] = {"sessions": {}}
        sessions_dict = projects["sessions"]
        if not isinstance(sessions_dict, dict):
            sessions_dict = {}

        # sessions/ 디렉토리에서 개별 세션 파일들 로드
        if self.sessions_path.exists():
            # 재귀적으로 모든 yaml 파일 찾기 (subdirectory 지원)
            for session_file in self.sessions_path.rglob("*.yaml"):
                # 언더스코어로 시작하는 파일은 템플릿이므로 제외
                if session_file.name.startswith("_"):
                    continue
                try:
                    with session_file.open(encoding="utf-8") as f:
                        session_config = yaml.safe_load(f) or {}

                    # subdirectory가 있는 경우 디렉토리명을 prefix로 사용
                    relative_path = session_file.relative_to(self.sessions_path)
                    if len(relative_path.parts) > 1:
                        # e.g., development/frontend.yaml -> development-frontend
                        session_name = "-".join(relative_path.parts[:-1]) + "-" + session_file.stem
                    else:
                        session_name = session_file.stem

                    sessions_dict[session_name] = session_config
                    self.logger.debug(f"Loaded session config: {session_name} from {relative_path}")
                except Exception:
                    self.logger.exception(f"Failed to load session file {session_file}:")

            # .yml 확장자도 지원
            for session_file in self.sessions_path.rglob("*.yml"):
                # 언더스코어로 시작하는 파일은 템플릿이므로 제외
                if session_file.name.startswith("_"):
                    continue
                try:
                    with session_file.open(encoding="utf-8") as f:
                        session_config = yaml.safe_load(f) or {}

                    # subdirectory가 있는 경우 디렉토리명을 prefix로 사용
                    relative_path = session_file.relative_to(self.sessions_path)
                    if len(relative_path.parts) > 1:
                        session_name = "-".join(relative_path.parts[:-1]) + "-" + session_file.stem
                    else:
                        session_name = session_file.stem

                    # .yaml 파일이 이미 있으면 건너뛰기 (중복 방지)
                    if session_name not in sessions_dict:
                        sessions_dict[session_name] = session_config
                        self.logger.debug(f"Loaded session config: {session_name} from {relative_path}")
                except Exception:
                    self.logger.exception(f"Failed to load session file {session_file}:")

        return projects

    def save_session_config(self, session_name: str, session_config: dict[str, object]) -> bool:
        """Save a session configuration to an individual file.

        Returns:
        Configuration object or settings.
        """
        try:
            session_file = self.sessions_path / f"{session_name}.yaml"
            with session_file.open("w", encoding="utf-8") as f:
                yaml.dump(session_config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info("Saved session config: {session_name}")

        except (OSError, PermissionError, yaml.YAMLError):
            self.logger.exception("Failed to save session config %s")
            return False
        else:
            return True

    def delete_session_config(self, session_name: str) -> bool:
        """Delete a session configuration file.

        Returns:
        Configuration object or settings.
        """
        try:
            session_file = self.sessions_path / f"{session_name}.yaml"
            if session_file.exists():
                session_file.unlink()
                self.logger.info("Deleted session config: {session_name}")
                return True

            # .yml 확장자도 확인
            session_file_yml = self.sessions_path / f"{session_name}.yml"
            if session_file_yml.exists():
                session_file_yml.unlink()
                self.logger.info("Deleted session config: {session_name}")
                return True

            self.logger.warning("Session config file not found: {session_name}")

        except (OSError, PermissionError):
            self.logger.exception("Failed to delete session config %s")
            return False
        else:
            return False

    def get_session_config_file(self, session_name: str) -> Path | None:
        """Get the path to a session configuration file.

        Returns:
        Configuration object or settings.
        """
        # 먼저 루트에서 찾기
        yaml_file = self.sessions_path / f"{session_name}.yaml"
        yml_file = self.sessions_path / f"{session_name}.yml"

        if yaml_file.exists():
            return yaml_file
        if yml_file.exists():
            return yml_file

        # subdirectory에서 찾기
        # e.g., development-frontend -> development/frontend.yaml
        if "-" in session_name:
            parts = session_name.split("-")
            for i in range(1, len(parts)):
                subdir = "-".join(parts[:i])
                filename = "-".join(parts[i:])

                yaml_file = self.sessions_path / subdir / f"{filename}.yaml"
                yml_file = self.sessions_path / subdir / f"{filename}.yml"

                if yaml_file.exists():
                    return yaml_file
                if yml_file.exists():
                    return yml_file

        return None

    def list_session_configs(self) -> list[str]:
        """List all available session configurations.

        Returns:
        Configuration object or settings.
        """
        session_names = set()

        if self.sessions_path.exists():
            # .yaml 파일들 (재귀적으로 찾기)
            for session_file in self.sessions_path.rglob("*.yaml"):
                # 언더스코어로 시작하는 파일은 템플릿이므로 제외
                if session_file.name.startswith("_"):
                    continue

                relative_path = session_file.relative_to(self.sessions_path)
                if len(relative_path.parts) > 1:
                    # e.g., development/frontend.yaml -> development-frontend
                    session_name = "-".join(relative_path.parts[:-1]) + "-" + session_file.stem
                else:
                    session_name = session_file.stem
                session_names.add(session_name)

            # .yml 파일들 (재귀적으로 찾기)
            for session_file in self.sessions_path.rglob("*.yml"):
                # 언더스코어로 시작하는 파일은 템플릿이므로 제외
                if session_file.name.startswith("_"):
                    continue

                relative_path = session_file.relative_to(self.sessions_path)
                if len(relative_path.parts) > 1:
                    session_name = "-".join(relative_path.parts[:-1]) + "-" + session_file.stem
                else:
                    session_name = session_file.stem
                session_names.add(session_name)

        return sorted(session_names)

    def load_template(self, template_name: str) -> dict[str, object]:
        """Load a specific template file.

        Returns:
        Dict containing.
        """
        template_path = self.templates_path / f"{template_name}.yaml"
        if not template_path.exists():
            msg = f"Template {template_name} not found at {template_path}"
            raise FileNotFoundError(msg)

        with template_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_session_config(self, session_name: str, session_config: dict[str, object]) -> dict[str, object]:
        """Get final session configuration after applying template and
        overrides.

        Returns:
        Configuration object or settings.
        """
        # Start with base configuration
        final_config = {}

        # Load template if specified
        template_name = session_config.get("template_name")
        if template_name:
            try:
                template_config = self.load_template(cast("str", template_name))
                final_config = template_config.copy()
            except FileNotFoundError:
                self.logger.warning("Template {template_name} not found for session {session_name}")

        # Apply override configuration
        override_config = session_config.get("override", {})
        if override_config:
            # Deep merge override config
            final_config = self._deep_merge_dicts(final_config, cast("dict[str, object]", override_config))

        # Ensure session_name is set
        if "session_name" not in final_config:
            final_config["session_name"] = session_name

        return final_config

    def _deep_merge_dicts(self, base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
        """Deep merge two dictionaries, with override taking precedence.

        Returns:
        Dict containing.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dicts(
                    cast("dict[str, object]", result[key]),
                    cast("dict[str, object]", value),
                )
            else:
                result[key] = value

        return result

    @staticmethod
    def list_running_sessions() -> None:
        """List currently running tmux sessions."""
        server = libtmux.Server()
        sessions = list(server.sessions)
        if not sessions:
            click.echo("No running tmux sessions found")
            return
        click.echo("Running tmux sessions:")
        for sess in sessions:
            name = sess.get("session_name")
            click.echo(f"  - {name}")

    def get_session_info(self, session_name: str) -> dict[str, object]:
        """Get session information directly from tmux.

        Returns:
        Dict containing service information.
        """

        def fetch_session_info() -> dict[str, object]:
            """Fetch session information from tmux.

            Returns:
            Dict containing service information.
            """
            try:
                server = libtmux.Server()
                session = server.sessions.get(session_name=session_name, default=None)
                if not session:
                    return {"exists": False, "session_name": session_name}

                # Get session details
                windows = []
                if hasattr(session, "list_windows"):
                    for window in session.windows:
                        panes: list[dict[str, Any]] = []
                        if hasattr(window, "list_panes"):
                            panes.extend(
                                {
                                    "pane_id": (getattr(pane, "pane_id", None) or pane.get("pane_id", "unknown")),
                                    "pane_current_command": (getattr(pane, "pane_current_command", "") or pane.get("pane_current_command", "")),
                                    "pane_active": ((getattr(pane, "pane_active", "0") or pane.get("pane_active", "0")) == "1"),
                                    "pane_width": (getattr(pane, "pane_width", 0) or pane.get("pane_width", 0)),
                                    "pane_height": (getattr(pane, "pane_height", 0) or pane.get("pane_height", 0)),
                                }
                                for pane in window.panes
                            )

                        windows.append(
                            {
                                "window_id": (getattr(window, "window_id", None) or window.get("window_id", "unknown")),
                                "window_name": (getattr(window, "window_name", None) or window.get("window_name", "unknown")),
                                "window_active": ((getattr(window, "window_active", "0") or window.get("window_active", "0")) == "1"),
                                "panes": panes,
                            }
                        )

                return {
                    "exists": True,
                    "session_name": session_name,
                    "session_id": (getattr(session, "session_id", None) or session.get("session_id", "unknown")),
                    "session_created": (getattr(session, "session_created", None) or session.get("session_created", None)),
                    "windows": windows,
                }
            except Exception as e:
                self.logger.exception("Failed to get session info for {session_name}:")
                return {"exists": False, "session_name": session_name, "error": str(e)}

        return fetch_session_info()

    def get_cached_sessions_list(self) -> list[dict[str, object]]:
        """Get list of all sessions directly from tmux.

        Returns:
        List of items.
        """
        try:
            server = libtmux.Server()
            sessions = list(server.sessions)
            return [
                {
                    "session_name": (getattr(sess, "session_name", None) or sess.get("session_name", "unknown")),
                    "session_id": (getattr(sess, "session_id", None) or sess.get("session_id", "unknown")),
                    "session_created": (getattr(sess, "session_created", None) or sess.get("session_created", None)),
                    "session_windows": (getattr(sess, "session_windows", 0) or sess.get("session_windows", 0)),
                }
                for sess in sessions
            ]
        except Exception:
            self.logger.exception("Failed to get sessions list:")
            return []

    def get_cache_stats(self) -> dict[str, object]:
        """Get cache statistics for performance monitoring.

        Returns:
        Dict containing cache statistics.
        """
        # Simple implementation - in a real system this would track actual cache metrics
        return {
            "hit_rate": 0.85,  # 85% hit rate
            "total_requests": 100,
            "cache_hits": 85,
            "cache_misses": 15,
            "cache_size": 50,
        }

    def teardown_session(self, session_name: str) -> bool:
        """Teardown a specific tmux session.

        Returns:
        Boolean indicating.
        """
        try:
            server = libtmux.Server()
            session = server.find_where({"session_name": session_name})
            if session and hasattr(session, "kill_session"):
                session.kill_session()
                self.logger.info("Session {session_name} terminated.")
                return True
            self.logger.warning("Session {session_name} not found.")

        except (OSError, RuntimeError, AttributeError):
            self.logger.exception("Failed to teardown session %s")
            return False
        else:
            return False

    def teardown_all_sessions(self) -> None:
        """Teardown all tmux sessions."""
        try:
            server = libtmux.Server()
            if hasattr(server, "kill_server"):
                server.kill_server()
                self.logger.info("All tmux sessions terminated.")
        except Exception:
            self.logger.exception("Failed to teardown all sessions:")

    def attach_to_session(self, session_name: str) -> None:
        """Attach to a specific tmux session."""
        # Use subprocess.run for security (no shell injection)
        try:
            subprocess.run(["tmux", "attach", "-t", session_name], check=True)
        except subprocess.CalledProcessError:
            self.logger.exception("Failed to attach to session {session_name}:")
        except FileNotFoundError:
            self.logger.exception("tmux command not found")

    def get_session_activity(self, session_name: str) -> dict[str, object]:
        """Get session activity data by parsing session logs.

        Returns:
        Dict containing the requested data.
        """
        try:
            log_path_str = self.config.get("log_path", "~/.scripton/yesman/logs/")
            safe_session_name = "".join(c for c in session_name if c.isalnum() or c in {"-", "_"}).rstrip()
            log_file = Path(str(log_path_str)).expanduser() / f"{safe_session_name}.log"

            if not log_file.exists():
                # Fallback to the main log if a session-specific log is not found
                log_file = Path(str(log_path_str)).expanduser() / "yesman.log"
                if not log_file.exists():
                    return {"session_name": session_name, "activity_data": []}

            # Activity per hour for the last 7 days
            activity_counts: dict[str, int] = defaultdict(int)

            now = datetime.now(UTC)
            seven_days_ago = now - timedelta(days=7)

            with log_file.open(encoding="utf-8") as f:
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

        except (OSError, PermissionError, ValueError):
            self.logger.exception("Failed to get session activity for %s")
            return {"session_name": session_name, "activity_data": []}
        else:
            return {
                "session_name": session_name,
                "activity_data": activity_data,
            }

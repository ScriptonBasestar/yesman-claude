import subprocess

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
from typing import Any

import click
import libtmux

from libs.core.base_command import BaseCommand, CommandError, SessionCommandMixin


class TeardownCommand(BaseCommand, SessionCommandMixin):
    """Kill all tmux sessions (기본) 또는 지정한 세션만 삭제합니다."""

    def execute(self, session_name: str | None = None, **kwargs: Any) -> dict:
        """Execute the teardown command.

        Returns:
        dict: Description of return value.
        """
        try:
            sessions_obj = self.tmux_manager.load_projects().get("sessions", {})
            sessions = sessions_obj if isinstance(sessions_obj, dict) else {}
            if not sessions:
                self.print_warning("No sessions defined in projects.yaml")
                return {"success": True, "sessions_found": 0}

            server = libtmux.Server()
            killed_sessions = []
            not_found_sessions = []

            # If a specific session is provided, only kill that session
            if session_name:
                if session_name not in sessions:
                    self.print_error(f"Session {session_name} not defined in projects.yaml")
                    return {"success": False, "error": "session_not_defined"}
                sessions = {session_name: sessions[session_name]}

            for session_key, sess_conf in sessions.items():
                override_conf = sess_conf.get("override", {})
                actual_session_name = override_conf.get("session_name", session_key)

                if server.find_where({"session_name": actual_session_name}):
                    subprocess.run(["tmux", "kill-session", "-t", actual_session_name], check=False)
                    self.print_success(f"Killed session: {actual_session_name}")
                    killed_sessions.append(actual_session_name)
                else:
                    self.print_warning(f"Session {actual_session_name} not found")
                    not_found_sessions.append(actual_session_name)

            self.print_success("All sessions torn down.")
            return {
                "success": True,
                "killed_sessions": killed_sessions,
                "not_found_sessions": not_found_sessions,
                "total_sessions": len(sessions),
            }

        except Exception as e:
            msg = f"Error tearing down sessions: {e}"
            raise CommandError(msg) from e


@click.command()
@click.argument("session_name", required=False)
def teardown(session_name: str | None) -> None:
    """Kill all tmux sessions (기본) 또는 지정한 세션만 삭제합니다."""
    command = TeardownCommand()
    command.run(session_name=session_name)


__all__ = ["teardown"]

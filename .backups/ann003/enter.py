# Copyright notice.

import os
import subprocess  # noqa: S404
import sys

import click
import libtmux

from libs.core.base_command import BaseCommand, CommandError, SessionCommandMixin
from libs.ui.session_selector import show_session_selector

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Enter (attach to) a tmux session command."""


class EnterCommand(BaseCommand, SessionCommandMixin):
    """Enter (attach to) a tmux session."""

    def __init__(self) -> None:
        super().__init__()
        self.server = libtmux.Server()

    @staticmethod
    def validate_preconditions() -> None:
        """Validate command preconditions."""
        super().validate_preconditions()

        # Check if running in interactive terminal
        if not sys.stdin.isatty():
            msg = "Error: 'enter' command requires an interactive terminal\n💡 Tip: Run this command directly in your terminal, not through pipes or scripts"
            raise CommandError(msg)

    def execute(self, session_name: str | None = None, list_sessions: bool = False, **kwargs) -> dict:  # noqa: FBT001, ARG002
        """Execute the enter command.

        Returns:
        Dict containing.
        """
        if list_sessions:
            # Show available sessions
            self.tmux_manager.list_running_sessions()
            return {"action": "list", "success": True}

        # If no session name provided, show available sessions and prompt
        if not session_name:
            session_name = self._select_session()
            if not session_name:
                return {"action": "cancelled", "success": False}

        # Check if the session exists
        actual_session_name = self._resolve_session_name(session_name)
        if not actual_session_name:
            self.print_error(f"Session '{session_name}' not found.")
            self.print_info("Available sessions:")
            self.tmux_manager.list_running_sessions()
            return {"action": "not_found", "success": False}

        # Attach to the session
        self.print_info(f"Attaching to session: {actual_session_name}")
        self._attach_to_session(actual_session_name)

        return {"action": "attached", "session": actual_session_name, "success": True}

    def _select_session(self) -> str | None:
        """Select a session from running sessions.

        Returns:
        Str | None object.
        """
        # Get all running sessions
        running_sessions = []
        projects = self.tmux_manager.load_projects().get("sessions", {})

        for project_name, project_conf in projects.items():
            override = project_conf.get("override", {})
            actual_session_name = override.get("session_name", project_name)

            # Check if session exists
            if self.server.find_where({"session_name": actual_session_name}):
                running_sessions.append(
                    {
                        "project": project_name,
                        "session": actual_session_name,
                    }
                )

        if not running_sessions:
            self.print_warning("No running yesman sessions found.")
            self.print_info("Run 'yesman up' to create sessions.")
            return None

        # Try to use TUI selector first
        try:
            selected = show_session_selector(running_sessions)
            if selected:
                return selected
            self.print_info("Selection cancelled")
            return None
        except Exception:
            # Fallback to text-based selection
            self.print_warning("TUI unavailable, falling back to text selection...")
            self.print_info("Available sessions:")
            for i, sess in enumerate(running_sessions, 1):
                self.print_info(f"  [{i}] {sess['project']} (session: {sess['session']})")

            # Prompt for selection
            try:
                choice = click.prompt("Select session number", type=int)
                if 1 <= choice <= len(running_sessions):
                    session_data: dict[str] = running_sessions[choice - 1]
                    return str(session_data["session"])
                self.print_error("Invalid selection")
                return None
            except click.Abort:
                self.print_info("Selection cancelled")
                return None

    def _resolve_session_name(self, session_name: str) -> str | None:
        """Resolve session name from project name if needed.

        Returns:
        Str | None object.
        """
        # Check if the session exists directly
        if self.server.find_where({"session_name": session_name}):
            return session_name

        # Try to find by project name
        projects = self.tmux_manager.load_projects().get("sessions", {})

        for project_name, project_conf in projects.items():
            if project_name == session_name:
                override = project_conf.get("override", {})
                actual_session_name: str = override.get("session_name", project_name)
                if self.server.find_where({"session_name": actual_session_name}):
                    return actual_session_name
                break

        return None

    @staticmethod
    def _attach_to_session(session_name: str) -> None:
        """Attach to the specified tmux session."""
        # Check if we're already in a tmux session
        if "TMUX" in os.environ:
            # Switch to the session
            subprocess.run(["tmux", "switch-client", "-t", session_name], check=False)
        else:
            # Attach to the session
            subprocess.run(["tmux", "attach-session", "-t", session_name], check=False)


@click.command()
@click.argument("session_name", required=False)
@click.option("--list", "-l", "list_sessions", is_flag=True, help="List available sessions")
def enter(session_name: str | None, list_sessions: bool) -> None:  # noqa: FBT001
    """Enter (attach to) a tmux session."""
    command = EnterCommand()
    command.run(session_name=session_name, list_sessions=list_sessions)

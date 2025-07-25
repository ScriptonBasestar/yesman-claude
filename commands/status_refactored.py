#!/usr/bin/env python3

# Copyright notice.


from typing import Any, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from libs.core.base_command import BaseCommand
from libs.core.mixins import LayoutManagerMixin, StatusManagerMixin

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Status command - Refactored version using base command and mixins."""


class StatusCommand(BaseCommand, StatusManagerMixin, LayoutManagerMixin):
    """Show status of all or specific tmux sessions."""

    def __init__(self) -> None:
        """Initialize status command."""
        super().__init__()
        self.console = Console()
        self._current_status = "idle"
        self._layout_config = {
            "format": "table",  # table, grid, or list
            "columns": ["project", "session", "status", "windows", "panes"],
            "show_details": True,
        }

    def execute(self, **kwargs: Any) -> dict[str, object]:
        """Execute the status command.

        Args:
            session_name: Optional specific session to check

        Returns:
            Dictionary with session status information
        """
        session_name = kwargs.get("session_name")
        self.update_status("checking")

        try:
            if session_name:
                # Check specific session
                result = self._check_single_session(session_name)
            else:
                # Check all sessions
                result = self._check_all_sessions()

            self.update_status("idle")
            return result

        except Exception:
            self.update_status("error")
            self.logger.exception("Error checking status")
            raise

    def update_status(self, status: str) -> None:
        """Update the current status - implements StatusManagerMixin interface."""
        self._current_status = status
        self.logger.debug(f"Status updated to: {status}")

    def update_activity(self, activity: str) -> None:
        """Update the current activity - implements StatusManagerMixin interface."""
        self.logger.debug(f"Activity: {activity}")

    def create_layout(self) -> dict[str, object]:
        """Create and return layout configuration - implements LayoutManagerMixin interface.

        Returns:
        object: Description of return value.
        """
        return self._layout_config.copy()

    def update_layout(self, layout_config: object) -> None:
        """Update layout configuration - implements LayoutManagerMixin interface."""
        self._layout_config.update(cast("dict", layout_config))
        self.logger.debug(f"Layout updated: {layout_config}")

    def _check_single_session(self, session_name: str) -> dict[str, object]:
        """Check status of a single session.

        Returns:
        object: Description of return value.
        """
        self.update_status("checking_session")

        # Load projects configuration
        projects = self.tmux_manager.load_projects()
        sessions_config = cast("dict", projects.get("sessions", {}))

        if session_name not in sessions_config:
            self.print_error(f"Session '{session_name}' not found in configuration")
            return {"error": "session_not_found"}

        # Get session info
        session_info = self._get_session_info(session_name, cast("dict", sessions_config[session_name]))

        # Display based on layout
        self._display_session_status([session_info])

        return {"sessions": [session_info]}

    def _check_all_sessions(self) -> dict[str, object]:
        """Check status of all sessions.

        Returns:
        object: Description of return value.
        """
        self.update_status("checking_all")

        # Load projects configuration
        projects = self.tmux_manager.load_projects()
        sessions_config = cast("dict", projects.get("sessions", {}))

        if not sessions_config:
            self.print_warning("No sessions configured in projects.yaml")
            return {"sessions": []}

        # Get info for all sessions
        session_infos = []
        for name, config in sessions_config.items():
            session_infos.append(self._get_session_info(name, cast("dict", config)))

        # Display based on layout
        self._display_session_status(session_infos)

        return {"sessions": session_infos}

    def _get_session_info(self, session_name: str, session_config: dict[str, object]) -> dict[str, object]:
        """Get detailed information about a session.

        Returns:
        object: Description of return value.
        """
        info = {
            "name": session_name,
            "project": session_config.get("project_name", session_name),
            "template": session_config.get("template_name", "none"),
            "exists": False,
            "status": "stopped",
            "windows": 0,
            "panes": 0,
            "attached": False,
            "created_time": None,
        }

        # Check if session exists
        try:
            tmux_sessions = self.tmux_manager.get_cached_sessions_list()
            for tmux_session in tmux_sessions:
                if tmux_session.get("session_name") == session_name:
                    info["exists"] = True
                    info["status"] = "running"
                    info["attached"] = tmux_session.get("attached", "0") != "0"
                    info["created_time"] = tmux_session.get("created")

                    # Get window and pane count
                    session_info = self.tmux_manager.get_session_info(session_name)
                    windows = cast("list", session_info.get("windows", []))
                    info["windows"] = len(windows)
                    info["panes"] = sum(len(cast("list", w.get("panes", []))) for w in windows)
                    break

        except Exception:
            self.logger.exception("Error getting tmux info for {session_name}")
            info["status"] = "error"

        return info

    def _display_session_status(self, sessions: list[dict[str, object]]) -> None:
        """Display session status based on current layout configuration."""
        layout_format = self._layout_config.get("format", "table")

        if layout_format == "table":
            self._display_as_table(sessions)
        elif layout_format == "grid":
            self._display_as_grid(sessions)
        else:  # list
            self._display_as_list(sessions)

    def _display_as_table(self, sessions: list[dict[str, object]]) -> None:
        """Display sessions in table format."""
        table = Table(
            title="Tmux Session Status",
            show_header=True,
            header_style="bold magenta",
        )

        # Add columns based on layout config
        columns = self._layout_config.get("columns", ["project", "session", "status"])
        if not isinstance(columns, list):
            columns = ["project", "session", "status"]
        column_map = {
            "project": ("Project", "cyan"),
            "session": ("Session", "green"),
            "status": ("Status", "yellow"),
            "windows": ("Windows", "blue"),
            "panes": ("Panes", "blue"),
            "template": ("Template", "magenta"),
            "attached": ("Attached", "green"),
        }

        for col in columns:
            if col in column_map:
                table.add_column(column_map[col][0], style=column_map[col][1])

        # Add rows
        for session in sessions:
            row = []
            for col in columns:
                if col == "project":
                    row.append(session["project"])
                elif col == "session":
                    row.append(session["name"])
                elif col == "status":
                    status = session["status"]
                    if status == "running":
                        row.append("[green]● running[/green]")
                    elif status == "stopped":
                        row.append("[red]○ stopped[/red]")
                    else:
                        row.append("[yellow]? error[/yellow]")
                elif col == "windows":
                    row.append(str(session["windows"]))
                elif col == "panes":
                    row.append(str(session["panes"]))
                elif col == "template":
                    row.append(session["template"])
                elif col == "attached":
                    row.append("✓" if session["attached"] else "")

            table.add_row(*[str(item) for item in row])

        self.console.print(table)

        # Summary
        running = sum(1 for s in sessions if s["status"] == "running")
        total = len(sessions)
        self.console.print(f"\n[dim]Total: {total} sessions, {running} running[/dim]")

    def _display_as_grid(self, sessions: list[dict[str, object]]) -> None:
        """Display sessions in grid format."""
        for i, session in enumerate(sessions):
            # Create panel for each session
            content = []
            content.extend((f"[bold]Project:[/bold] {session['project']}", f"[bold]Template:[/bold] {session['template']}"))

            if session["status"] == "running":
                content.extend(("[bold]Status:[/bold] [green]● running[/green]", f"[bold]Windows:[/bold] {session['windows']}", f"[bold]Panes:[/bold] {session['panes']}"))
                if session["attached"]:
                    content.append("[bold]Attached:[/bold] ✓")
            else:
                content.append("[bold]Status:[/bold] [red]○ stopped[/red]")

            panel = Panel(
                "\n".join(content),
                title=f"[cyan]{session['name']}[/cyan]",
                border_style="blue" if session["status"] == "running" else "red",
            )

            self.console.print(panel)
            if i < len(sessions) - 1:
                self.console.print()

    def _display_as_list(self, sessions: list[dict[str, object]]) -> None:
        """Display sessions in simple list format."""
        for session in sessions:
            status_icon = "●" if session["status"] == "running" else "○"
            status_color = "green" if session["status"] == "running" else "red"

            line = f"[{status_color}]{status_icon}[/{status_color}] {session['name']}"

            if self._layout_config.get("show_details", True):
                details = []
                if session["status"] == "running":
                    details.append(f"{session['windows']}w/{session['panes']}p")
                    if session["attached"]:
                        details.append("attached")
                details.append(f"template: {session['template']}")

                if details:
                    line += f" [dim]({', '.join(details)})[/dim]"

            self.console.print(line)


@click.command()
@click.argument("session_name", required=False)
@click.option(
    "--format",
    type=click.Choice(["table", "grid", "list"]),
    default="table",
    help="Display format",
)
@click.option(
    "--details/--no-details",
    default=True,
    help="Show detailed information",
)
def status(session_name: str | None, format: str, details: bool) -> None:
    """Show status of all or specific tmux sessions."""
    command = StatusCommand()

    # Update layout configuration
    command.update_layout(
        {
            "format": format,
            "show_details": details,
        }
    )

    # Execute command
    command.run(session_name=session_name)


if __name__ == "__main__":
    status()

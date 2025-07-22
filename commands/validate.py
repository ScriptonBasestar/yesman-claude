import os

# Try to keep the important parts (end of path)
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from libs.core.base_command import BaseCommand, CommandError, SessionCommandMixin


class ValidateCommand(BaseCommand, SessionCommandMixin):
    """Check if all directories in projects.yaml exist (or only for a specific session)."""

    def execute(self, session_name: str | None = None, format: str = "table", **kwargs: Any) -> dict:  # noqa: ARG002
        """Execute the validate command.

        Returns:
        dict: Description of return value.
        """
        try:
            console = Console()
            sessions = self.tmux_manager.load_projects().get("sessions", {})

            if not sessions:
                console.print("[red]❌ No sessions defined in projects.yaml[/red]")
                return {"success": False, "error": "no_sessions_defined"}

            if session_name:
                if session_name not in sessions:
                    console.print(f"[red]❌ Session '{session_name}' not defined in projects.yaml[/red]")
                    return {"success": False, "error": "session_not_defined"}
                sessions = {session_name: sessions[session_name]}

            # Show progress for multiple sessions
            if len(sessions) > 1:
                console.print(f"[blue]🔍 Validating {len(sessions)} sessions...[/blue]\n")

            missing = []
            valid_count = 0

            # Process sessions with progress tracking for multiple sessions
            sessions_to_process = list(sessions.items())
            iterator = track(sessions_to_process, description="Validating sessions...") if len(sessions) > 3 else sessions_to_process

            for s_name, sess_conf in iterator:
                try:
                    # 템플릿이 적용된 최종 설정을 가져오기
                    final_config = self.tmux_manager.get_session_config(s_name, sess_conf)
                    session_missing = []

                    # 세션 시작 디렉토리 검사
                    start_dir = final_config.get("start_directory", os.getcwd())
                    expanded_dir = os.path.expanduser(start_dir)
                    if not os.path.exists(expanded_dir):
                        session_missing.append(("session", "Session Root", expanded_dir))

                    # 윈도우별 start_directory 검사
                    windows = final_config.get("windows", [])
                    for i, window in enumerate(windows):
                        window_start_dir = window.get("start_directory")
                        if window_start_dir:
                            if not os.path.isabs(window_start_dir):
                                # 상대 경로인 경우 세션의 시작 디렉토리를 기준으로 함
                                base_dir = expanded_dir
                                window_start_dir = os.path.join(base_dir, window_start_dir)
                            expanded_window_dir = os.path.expanduser(window_start_dir)
                            if not os.path.exists(expanded_window_dir):
                                window_name = window.get("window_name", f"window_{i}")
                                session_missing.append(("window", window_name, expanded_window_dir))

                        # 팬별 start_directory 검사 (팬이 있는 경우)
                        panes = window.get("panes", [])
                        for j, pane in enumerate(panes):
                            if isinstance(pane, dict) and "start_directory" in pane:
                                pane_start_dir = pane["start_directory"]
                                if not os.path.isabs(pane_start_dir):
                                    base_dir = expanded_dir
                                    pane_start_dir = os.path.join(base_dir, pane_start_dir)
                                expanded_pane_dir = os.path.expanduser(pane_start_dir)
                                if not os.path.exists(expanded_pane_dir):
                                    window_name = window.get("window_name", f"window_{i}")
                                    session_missing.append(
                                        (
                                            "pane",
                                            f"{window_name}/pane_{j}",
                                            expanded_pane_dir,
                                        )
                                    )

                    # Store results for this session
                    if session_missing:
                        missing.append((s_name, session_missing))
                    else:
                        valid_count += 1

                except Exception as e:
                    console.print(f"[yellow]⚠️  Error processing session '{s_name}': {e}[/yellow]")
                    continue

            # Display results based on format
            if not missing:
                _display_success(console, valid_count, len(sessions))
            elif format == "table":
                _display_table_format(console, missing, valid_count, len(sessions))
            elif format == "tree":
                _display_tree_format(console, missing, valid_count, len(sessions))
            else:
                _display_simple_format(console, missing, valid_count, len(sessions))

            return {
                "success": True,
                "total_sessions": len(sessions),
                "valid_sessions": valid_count,
                "invalid_sessions": len(missing),
                "missing_directories": missing,
            }

        except Exception as e:
            msg = f"Error validating directories: {e}"
            raise CommandError(msg) from e


@click.command()
@click.argument("session_name", required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "tree", "simple"]),
    default="table",
    help="Output format",
)
def validate(session_name: str | None, format: str) -> None:
    """Check if all directories in projects.yaml exist (or only for a specific session)."""
    command = ValidateCommand()
    command.run(session_name=session_name, format=format)


def _display_success(console: Console, valid_count: int, total_count: int) -> None:
    """Display success message when all directories exist."""
    success_panel = Panel(
        Text("✅ All directories exist!", style="bold green"),
        title="[green]Validation Complete[/green]",
        subtitle=f"[dim]{valid_count}/{total_count} sessions validated[/dim]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(success_panel)


def _display_table_format(console: Console, missing: list, valid_count: int, total_count: int) -> None:  # noqa: ARG001
    """Display results in table format."""
    table = Table(
        title="[red]Directory Validation Results[/red]",
        caption=f"[dim]{len(missing)} sessions with issues, {valid_count} sessions valid[/dim]",
        show_header=True,
        header_style="bold blue",
        border_style="red",
    )

    table.add_column("Session", style="cyan", width=15)
    table.add_column("Type", style="yellow", width=10)
    table.add_column("Target", style="magenta", width=20)
    table.add_column("Missing Path", style="red", no_wrap=False)

    for session_name, session_missing in missing:
        for i, (target_type, target_name, path) in enumerate(session_missing):
            # Show session name only on first row for each session
            session_display = session_name if i == 0 else ""

            # Add icons based on type
            if target_type == "session":
                type_display = "🏠 Session"
            elif target_type == "window":
                type_display = "🪟 Window"
            else:
                type_display = "📄 Pane"

            # Shorten path for display
            display_path = _shorten_path(path)

            table.add_row(session_display, type_display, target_name, display_path)

        # Add separator between sessions if there are multiple missing items
        if len(session_missing) > 1 and session_name != missing[-1][0]:
            table.add_row("", "", "", "", end_section=True)

    console.print(table)


def _display_tree_format(console: Console, missing: list, valid_count: int, total_count: int) -> None:  # noqa: ARG001
    """Display results in tree format."""
    console.print("\n[red bold]❌ Directory Validation Issues[/red bold]")
    console.print(f"[dim]{len(missing)} sessions with issues, {valid_count} sessions valid[/dim]\n")

    tree = Tree("[red]📁 Missing Directories[/red]", style="red")

    for session_name, session_missing in missing:
        session_branch = tree.add(f"[cyan bold]🎯 {session_name}[/cyan bold]")

        # Group by type
        by_type: dict[str, list[tuple[str, str]]] = {"session": [], "window": [], "pane": []}
        for target_type, target_name, path in session_missing:
            by_type[target_type].append((target_name, path))

        for target_type, items in by_type.items():
            if items:
                if target_type == "session":
                    icon = "🏠"
                    label = "Session"
                elif target_type == "window":
                    icon = "🪟"
                    label = "Windows"
                else:
                    icon = "📄"
                    label = "Panes"

                type_branch = session_branch.add(f"[yellow]{icon} {label}[/yellow]")

                for target_name, path in items:
                    display_path = _shorten_path(path)
                    type_branch.add(f"[magenta]{target_name}[/magenta] → [red]{display_path}[/red]")

    console.print(tree)


def _display_simple_format(console: Console, missing: list, valid_count: int, total_count: int) -> None:  # noqa: ARG001
    """Display results in simple format."""
    console.print("[red bold]❌ Missing Directories Found[/red bold]\n")

    for session_name, session_missing in missing:
        console.print(f"[cyan bold]📋 Session: {session_name}[/cyan bold]")

        for target_type, target_name, path in session_missing:
            if target_type == "session":
                icon = "🏠"
            elif target_type == "window":
                icon = "🪟"
            else:
                icon = "📄"

            display_path = _shorten_path(path)
            console.print(f"  {icon} [magenta]{target_name}[/magenta] → [red]{display_path}[/red]")

        console.print()  # Empty line between sessions

    console.print(f"[dim]Summary: {len(missing)} sessions with issues, {valid_count} sessions valid[/dim]")


def _shorten_path(path: str, max_length: int = 60) -> str:
    """Shorten path for better display.

    Returns:
        str: Description of return value.
    """
    if len(path) <= max_length:
        return path

    parts = path.split("/")
    if len(parts) > 3:
        return f".../{'/'.join(parts[-3:])}"
    if len(path) > max_length:
        return f"...{path[-(max_length - 3) :]}"

    return path


__all__ = ["validate"]

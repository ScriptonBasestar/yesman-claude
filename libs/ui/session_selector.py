# Copyright notice.

from typing import Any
import libtmux
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""TUI Session Selector using Rich."""




class SessionSelector:
    """Interactive TUI session selector."""

    def __init__(self, sessions: list[dict[str, str]]) -> None:
        self.sessions = sessions
        self.console = Console()

    @staticmethod
    def _get_session_details(session_name: str) -> dict[str, object]:
        """Get session details from tmux.

        Returns:
        object: Description of return value.
        """
        try:
            server = libtmux.Server()
            session = server.find_where({"session_name": session_name})
            if session:
                windows = session.windows if hasattr(session, "windows") else []
                window_names = [w.name for w in windows] if windows else []
                # Get session info using format strings
                attached_clients = getattr(session, "attached", 0)
                return {
                    "windows": len(windows),
                    "window_names": ", ".join(window_names[:3]) + ("..." if len(window_names) > 3 else ""),
                    "attached": attached_clients > 0,
                    "clients": attached_clients,
                }
        except:
            pass
        return {
            "windows": 0,
            "window_names": "",
            "attached": False,
            "clients": 0,
        }

    def _create_display(self, search_term: str = "") -> tuple[Table, list[dict[str, str]]]:
        """Create the display table.

        Returns:
        object: Description of return value.
        """
        table = Table(
            title="🖥️  Select a tmux session",
            show_header=True,
            header_style="bold magenta",
            title_style="bold cyan",
            expand=True,
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Project", style="cyan", no_wrap=True)
        table.add_column("Session", style="green")
        table.add_column("Windows", justify="center", style="yellow")
        table.add_column("Status", justify="center")

        # Filter sessions if search term provided
        filtered_sessions = self.sessions
        if search_term:
            filtered_sessions = [s for s in self.sessions if search_term.lower() in s["project"].lower() or search_term.lower() in s["session"].lower()]

        for i, session in enumerate(filtered_sessions, 1):
            details = self._get_session_details(session["session"])

            # Status indicator
            if details["attached"]:
                status = f"🟢 ({details['clients']})"
                status_style = "green"
            else:
                status = "⚪"
                status_style = "dim"

            # Window info
            window_info = f"{details['windows']} windows"
            if details["window_names"]:
                window_info = f"{details['windows']} ({details['window_names']})"

            table.add_row(
                str(i),
                session["project"],
                session["session"],
                window_info,
                Text(status, style=status_style),
            )

        return table, filtered_sessions

    def select_session(self) -> str | None:
        """Show interactive session selector and return selected session.
        
            Returns:
                Str | None object.
        
                
        """
        if not self.sessions:
            return None

        self.console.clear()

        while True:
            # Display sessions
            table, filtered_sessions = self._create_display()
            self.console.print(table)

            # Help text
            help_panel = Panel(
                "[bold cyan]Enter[/] number to select • [bold cyan]s[/] to search • [bold cyan]q[/] to quit",
                style="dim",
                expand=False,
            )
            self.console.print(help_panel)

            # Get user input
            choice = Prompt.ask("\n[bold]Select", default="")

            if choice.lower() == "q":
                return None
            if choice.lower() == "s":
                search_term = Prompt.ask("Search")
                self.console.clear()
                table, filtered_sessions = self._create_display(search_term)
                self.console.print(table)
                self.console.print(help_panel)

                if filtered_sessions:
                    choice = Prompt.ask("\n[bold]Select", default="")
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(filtered_sessions):
                            return filtered_sessions[idx]["session"]
                else:
                    self.console.print("[yellow]No sessions found matching search term[/]")
                    Prompt.ask("Press Enter to continue")
                self.console.clear()
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(filtered_sessions):
                    return filtered_sessions[idx]["session"]
                self.console.print("[red]Invalid selection[/]")
            else:
                self.console.print("[red]Invalid input. Enter a number, 's' to search, or 'q' to quit[/]")


def show_session_selector(sessions: list[dict[str, str]]) -> str | None:
    """Show interactive session selector.

    Args:
        sessions: List of session dictionaries with 'project' and 'session' keys

    Returns:
        Selected session name or None if cancelled
    """
    selector = SessionSelector(sessions)
    return selector.select_session()

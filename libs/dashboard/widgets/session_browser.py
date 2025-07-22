# Copyright notice.

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Interactive session browser with tree view and keyboard navigation."""


class ViewMode(Enum):
    """Session browser view modes."""

    TREE = "tree"
    LIST = "list"
    GRID = "grid"


@dataclass
class SessionNode:
    """Represents a session in the tree structure."""

    session_name: str
    status: str
    windows: list[dict[str, object]]
    last_activity: float
    is_active: bool = False
    claude_status: str | None = None


class SessionBrowser:
    """Interactive tmux session browser with file-browser-like navigation."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.logger = logging.getLogger("yesman.dashboard.session_browser")

        # Browser state
        self.view_mode = ViewMode.TREE
        self.selected_index = 0
        self.sessions: list[SessionNode] = []
        self.current_session: str | None = None
        self.show_details = True

        # Activity tracking
        self.activity_levels: dict[str, float] = {}
        self.last_update = time.time()

    def update_sessions(self, sessions_data: list[dict[str, object]]) -> None:
        """Update session data and refresh display."""
        self.sessions = []
        current_time = time.time()

        for session_data in sessions_data:
            # Calculate activity level based on processes and recent changes
            activity_level = self._calculate_activity_level(session_data)
            session_name = cast(str, session_data["session_name"])
            self.activity_levels[session_name] = activity_level

            node = SessionNode(
                session_name=session_name,
                status=self._get_session_status(session_data),
                windows=cast(list[dict[str, object]], session_data.get("windows", [])),
                last_activity=current_time,
                claude_status=self._detect_claude_status(session_data),
            )
            self.sessions.append(node)

        self.last_update = current_time

    @staticmethod
    def _calculate_activity_level(session_data: dict[str, object]) -> float:
        """Calculate activity level (0.0 - 1.0) based on session state.

        Returns:
        Float representing.
        """
        activity = 0.0

        # Check for active processes
        windows = cast(list[dict[str, Any]], session_data.get("windows", []))
        for window in windows:
            panes = cast(list[dict[str, Any]], window.get("panes", []))
            for pane in panes:
                command = pane.get("pane_current_command", "")
                if command and command not in {"zsh", "bash", "sh"}:
                    activity += 0.3

                # Claude sessions get higher activity
                if "claude" in command.lower():
                    activity += 0.5

        return min(activity, 1.0)

    @staticmethod
    def _get_session_status(session_data: dict[str, object]) -> str:
        """Determine session status with emoji indicators.

        Returns:
        Dict containing status information.
        """
        if not session_data.get("exists", True):
            return "❌ Not Found"

        window_count = len(session_data.get("windows", []))
        if window_count == 0:
            return "⚠️  No Windows"

        # Check for active processes
        active_processes = 0
        for window in session_data.get("windows", []):
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")
                if command and command not in {"zsh", "bash", "sh"}:
                    active_processes += 1

        if active_processes > 0:
            return f"🟢 Running ({active_processes} processes)"
        return "🟡 Idle"

    @staticmethod
    def _detect_claude_status(session_data: dict[str, object]) -> str | None:
        """Detect Claude status in session.

        Returns:
        Dict containing status information.
        """
        for window in session_data.get("windows", []):
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")
                if "claude" in command.lower():
                    # Simple heuristic for Claude status
                    if "working" in command.lower():
                        return "📝 Writing"
                    if "waiting" in command.lower():
                        return "⏳ Waiting"
                    return "🤖 Active"
        return None

    def render_tree_view(self) -> Panel:
        """Render sessions as a tree structure.

        Returns:
        Panel object.
        """
        tree = Tree("📁 Yesman Sessions", guide_style="bright_blue")

        for i, session in enumerate(self.sessions):
            # Highlight selected session
            style = "bold yellow" if i == self.selected_index else "white"

            # Session node with status
            session_text = Text()
            session_text.append(f"📁 {session.session_name} ", style=style)
            session_text.append(f"({session.status})", style="dim")

            if session.claude_status:
                session_text.append(f" {session.claude_status}", style="cyan")

            session_node = tree.add(session_text)

            # Add windows as child nodes
            for window in session.windows:
                window_text = Text()
                window_text.append(f"🪟 {window.get('window_name', 'unnamed')}", style="blue")

                if window.get("window_active"):
                    window_text.append(" (active)", style="green")

                window_node = session_node.add(window_text)

                # Add panes as child nodes
                for pane in window.get("panes", []):
                    pane_text = Text()
                    command = pane.get("pane_current_command", "")

                    if "claude" in command.lower():
                        pane_text.append("🤖 Claude", style="cyan")
                    elif command and command not in {"zsh", "bash", "sh"}:
                        pane_text.append(f"💻 {command}", style="green")
                    else:
                        pane_text.append("📺 Terminal", style="dim")

                    if pane.get("pane_active"):
                        pane_text.append(" (active)", style="yellow")

                    window_node.add(pane_text)

        return Panel(tree, title="Session Browser", border_style="blue")

    def render_list_view(self) -> Panel:
        """Render sessions as a detailed list.

        Returns:
        List of items.
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session", style="cyan", width=20)
        table.add_column("Status", width=25)
        table.add_column("Windows", justify="center", width=8)
        table.add_column("Activity", justify="center", width=10)
        table.add_column("Claude", width=15)

        for i, session in enumerate(self.sessions):
            # Highlight selected row
            row_style = "on bright_black" if i == self.selected_index else None

            # Activity bar
            activity = self.activity_levels.get(session.session_name, 0.0)
            activity_bar = "█" * int(activity * 8) + "░" * (8 - int(activity * 8))

            table.add_row(
                session.session_name,
                session.status,
                str(len(session.windows)),
                activity_bar,
                session.claude_status or "❌",
                style=row_style,
            )

        return Panel(table, title="Session List", border_style="blue")

    def render_grid_view(self) -> Panel:
        """Render sessions as a grid of cards.

        Returns:
        Panel object.
        """
        cards = []
        for i, session in enumerate(self.sessions):
            # Create session card
            card_style = "bold yellow on bright_black" if i == self.selected_index else "white"

            card_content = Text()
            card_content.append(f"📁 {session.session_name}\n", style=card_style)
            card_content.append(f"{session.status}\n", style="dim")

            if session.claude_status:
                card_content.append(f"{session.claude_status}\n", style="cyan")

            # Activity indicator
            activity = self.activity_levels.get(session.session_name, 0.0)
            card_content.append(f"Activity: {'█' * int(activity * 5)}", style="green")

            card = Panel(
                Padding(card_content, (0, 1)),
                width=25,
                height=6,
                border_style="yellow" if i == self.selected_index else "blue",
            )
            cards.append(card)

        return Panel(
            Columns(cards, equal=True, expand=True),
            title="Session Grid",
            border_style="blue",
        )

    def render_status_bar(self) -> Text:
        """Render status bar with navigation help.

        Returns:
        Dict containing status information.
        """
        status = Text()
        status.append("📋 Navigation: ", style="bold")
        status.append("↑↓ Select  ", style="cyan")
        status.append("Enter Connect  ", style="green")
        status.append("Tab Views  ", style="yellow")
        status.append("R Refresh  ", style="magenta")
        status.append(f"Mode: {self.view_mode.value.title()}", style="blue")

        return status

    def render(self) -> tuple[Panel, Text]:
        """Render current view based on view mode.

        Returns:
        Tuple[Panel, Text] object.
        """
        if self.view_mode == ViewMode.TREE:
            content = self.render_tree_view()
        elif self.view_mode == ViewMode.LIST:
            content = self.render_list_view()
        else:  # GRID
            content = self.render_grid_view()

        status_bar = self.render_status_bar()
        return content, status_bar

    def handle_key(self, key: str) -> str | None:
        """Handle keyboard input and return action if any.

        Returns:
        Str | None object.
        """
        if not self.sessions:
            return None

        if key in {"up", "k"}:
            self.selected_index = max(0, self.selected_index - 1)
        elif key in {"down", "j"}:
            self.selected_index = min(len(self.sessions) - 1, self.selected_index + 1)
        elif key == "enter":
            if self.sessions:
                return f"connect:{self.sessions[self.selected_index].session_name}"
        elif key == "tab":
            # Cycle through view modes
            modes = list(ViewMode)
            current_idx = modes.index(self.view_mode)
            self.view_mode = modes[(current_idx + 1) % len(modes)]
        elif key == "r":
            return "refresh"
        elif key == "q":
            return "quit"

        return None

    def get_selected_session(self) -> str | None:
        """Get currently selected session name.

        Returns:
        Str | None object the requested data.
        """
        if self.sessions and 0 <= self.selected_index < len(self.sessions):
            return self.sessions[self.selected_index].session_name
        return None

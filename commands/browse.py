"""Interactive session browser command."""

import threading
import time
from typing import Any

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from libs.core.base_command import BaseCommand, CommandError, SessionCommandMixin
from libs.core.progress_indicators import with_startup_progress
from libs.core.session_manager import SessionManager
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmapGenerator
from libs.dashboard.widgets.session_browser import SessionBrowser
from libs.dashboard.widgets.session_progress import SessionProgressWidget


class InteractiveBrowser:
    """Interactive session browser with live updates."""

    def __init__(self, tmux_manager: Any, config: Any, update_interval: float = 2.0) -> None:
        self.console = Console()
        self.config = config
        self.tmux_manager = tmux_manager

        # Initialize widgets
        self.session_browser = SessionBrowser(self.console)
        self.activity_heatmap = ActivityHeatmapGenerator(self.config)
        self.progress_widget = SessionProgressWidget(self.console)

        # Initialize session manager for progress tracking
        self.session_manager = SessionManager()

        self.update_interval = update_interval
        self.running = False
        self.update_thread: threading.Thread | None = None
        self.progress_data: dict[str, Any] | None = None
        self.session_data: list[dict[str, Any]] = []

    def update_data(self) -> None:
        """Update session data and activity metrics."""
        try:
            # Get session information using cached method
            sessions_list = self.tmux_manager.get_cached_sessions_list()
            detailed_sessions = []

            for session_info in sessions_list:
                session_name = session_info["session_name"]
                detailed_info = self.tmux_manager.get_session_info(session_name)
                detailed_sessions.append(detailed_info)

                # Calculate and record activity
                self._calculate_session_activity(detailed_info)
                # Note: Recording activity for potential future use
                # Activity is collected on-demand in generate_heatmap_data

            # Update browser with new data
            self.session_browser.update_sessions(detailed_sessions)
            self.session_data = detailed_sessions

            # Update progress data
            self.progress_data = self.session_manager.get_progress_overview()

        except Exception as e:
            self.console.print(f"[red]Error updating session data: {e}[/]")

    def _calculate_session_activity(self, session_info: dict) -> float:
        """Calculate activity level for a session."""
        if not session_info.get("exists", True):
            return 0.0

        activity = 0.0
        windows = session_info.get("windows", [])

        for window in windows:
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")

                # Active processes contribute to activity
                if command and command not in ["zsh", "bash", "sh"]:
                    activity += 0.2

                # Claude sessions get higher weight
                if "claude" in command.lower():
                    activity += 0.4

                # Active panes get bonus
                if pane.get("pane_active"):
                    activity += 0.1

        return min(activity, 1.0)

    def create_layout(self) -> Layout:
        """Create the main dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1),
        )

        # Split left panel for sessions and progress
        layout["left"].split_column(
            Layout(name="sessions", ratio=3),
            Layout(name="progress", size=10),
        )

        # Right panel is for activity heatmap
        layout["right"].update(Layout(name="activity"))

        return layout

    def update_layout(self, layout: Layout) -> None:
        """Update layout content."""
        # Header
        header_text = f"🚀 Yesman Session Browser - {time.strftime('%H:%M:%S')}"
        cache_stats = self.tmux_manager.get_cache_stats()
        header_text += f" | Cache: {cache_stats.get('hit_rate', 0):.1%} hit rate"
        layout["header"].update(self.console.render_str(header_text, style="bold blue"))

        # Main session browser
        browser_content, status_bar = self.session_browser.render()
        layout["sessions"].update(browser_content)

        # Progress overview
        if self.progress_data:
            progress_panel = self.progress_widget.render_progress_overview(self.progress_data)
            layout["progress"].update(progress_panel)
        else:
            layout["progress"].update("[dim]Loading progress data...[/dim]")

        # Activity heatmap
        session_names = [s["name"] for s in self.session_data if "name" in s]
        heatmap_data = self.activity_heatmap.generate_heatmap_data(session_names)
        heatmap_content = self._render_heatmap_display(heatmap_data)
        layout["activity"].update(heatmap_content)

        # Footer
        layout["footer"].update(status_bar)

    def background_updater(self) -> None:
        """Background thread for updating data."""
        while self.running:
            self.update_data()
            time.sleep(self.update_interval)

    def start(self) -> None:
        """Start the interactive browser."""
        self.running = True

        # Initial data load
        self.update_data()

        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_updater, daemon=True)
        self.update_thread.start()

        # Create layout
        layout = self.create_layout()

        try:
            with Live(layout, console=self.console, refresh_per_second=10):
                while self.running:
                    self.update_layout(layout)

                    # Handle keyboard input (basic implementation)
                    # In a real implementation, you'd use a library like keyboard or blessed
                    time.sleep(0.1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the browser."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)

    def _render_heatmap_display(self, heatmap_data: dict[str, Any]) -> str:
        """Render heatmap data as a simple text display."""
        if not heatmap_data or "heatmap" not in heatmap_data:
            return "[dim]No activity data available[/dim]"

        lines = ["📊 Activity Heatmap (Last 7 days)"]
        heatmap = heatmap_data["heatmap"]

        # Simple text representation
        for day, hours in heatmap.items():
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day]
            activity_count = sum(hours.values())
            lines.append(f"{day_name}: {activity_count} events")

        return "\n".join(lines)


class BrowseCommand(BaseCommand, SessionCommandMixin):
    """Interactive session browser with activity monitoring."""

    def validate_preconditions(self) -> None:
        """Validate command preconditions."""
        super().validate_preconditions()
        # Check if tmux is available and running
        if not self._is_tmux_available():
            msg = "tmux is not available or not properly installed"
            raise CommandError(msg)

    def execute(self, update_interval: float = 2.0, **kwargs) -> dict:
        """Execute the browse command."""
        try:
            with with_startup_progress("🔧 Initializing session browser...") as update:
                update("📊 Loading session data...")
                browser = InteractiveBrowser(self.tmux_manager, self.config, update_interval)
                update("🚀 Starting interactive browser...")

            self.print_info("Press Ctrl+C to exit")
            browser.start()

            return {"success": True}

        except KeyboardInterrupt:
            self.print_info("\nSession browser stopped.")
            return {"success": True, "stopped_by_user": True}
        except Exception as e:
            msg = f"Error during browsing: {e}"
            raise CommandError(msg) from e


@click.command()
@click.option(
    "--update-interval",
    "-i",
    default=2.0,
    type=float,
    help="Update interval in seconds (default: 2.0)",
)
def browse(update_interval: float) -> None:
    """Interactive session browser with activity monitoring."""
    command = BrowseCommand()
    command.run(update_interval=update_interval)

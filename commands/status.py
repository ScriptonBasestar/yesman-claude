# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Comprehensive project status dashboard command."""

import time
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel

from libs.core.base_command import BaseCommand, CommandError, SessionCommandMixin
from libs.core.session_manager import SessionManager
from libs.dashboard.widgets import (
    ActivityHeatmapGenerator,
    GitActivityWidget,
    ProgressTracker,
    ProjectHealth,
    SessionBrowser,
)
from libs.dashboard.widgets.session_progress import SessionProgressWidget
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig


class StatusDashboard:
    """Comprehensive status dashboard."""

    def __init__(
        self,
        project_path: str = ".",
        update_interval: float = 5.0,
        config: YesmanConfig | None = None,
        tmux_manager: TmuxManager | None = None,
    ) -> None:
        self.console = Console()
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.update_interval = update_interval

        # Use provided dependencies or create defaults
        self.config = config if config is not None else YesmanConfig()
        self.tmux_manager = tmux_manager if tmux_manager is not None else TmuxManager(self.config)

        # Initialize widgets
        self.session_browser = SessionBrowser(self.console)
        self.activity_heatmap = ActivityHeatmapGenerator(self.config)
        self.project_health = ProjectHealth(str(self.project_path))
        self.git_activity = GitActivityWidget(self.console, str(self.project_path))
        self.progress_tracker = ProgressTracker(self.console)
        self.session_progress = SessionProgressWidget(self.console)

        # Initialize session manager
        self.session_manager = SessionManager()

        # Load initial data
        self._load_todo_data()
        self.progress_data: dict[str, Any] | None = None

    def _load_todo_data(self) -> None:
        """Load TODO data from various sources."""
        # Try to load from common TODO file locations
        todo_files = [
            self.project_path / "TODO.md",
            self.project_path / "BACKLOG.md",
            self.project_path / "results" / "todos" / "high-priority-improvements.md",
            self.project_path / "results" / "todos" / "medium-priority-tasks.md",
        ]

        for todo_file in todo_files:
            if todo_file.exists() and self.progress_tracker.load_todos_from_file(str(todo_file)):
                break

    def update_data(self) -> None:
        """Update all dashboard data."""
        try:
            # Update session data
            sessions_list = self.tmux_manager.get_cached_sessions_list()
            detailed_sessions = []

            for session_info in sessions_list:
                session_name_obj = session_info.get("session_name", "unknown")
                session_name = str(session_name_obj)
                detailed_info = self.tmux_manager.get_session_info(session_name)
                detailed_sessions.append(detailed_info)

                # Calculate activity for heatmap
                self._calculate_session_activity(detailed_info)
                # Note: add_activity_point method not available, skip heatmap update

            # Update session browser
            self.session_browser.update_sessions(detailed_sessions)

            # Update project health - calculate health directly since update method not available
            self.project_health.calculate_health()

            # Update session progress
            self.progress_data = self.session_manager.get_progress_overview()

            # Git and progress data updates happen automatically in their respective widgets

        except Exception as e:
            self.console.print(f"[red]Error updating data: {e}[/]")

    @staticmethod
    def _calculate_session_activity(session_info: dict) -> float:
        """Calculate activity level for a session."""
        if not session_info.get("exists", True):
            return 0.0

        activity = 0.0
        windows = session_info.get("windows", [])

        for window in windows:
            for pane in window.get("panes", []):
                command = pane.get("pane_current_command", "")

                if command and command not in {"zsh", "bash", "sh"}:
                    activity += 0.2

                if "claude" in command.lower():
                    activity += 0.4

                if pane.get("pane_active"):
                    activity += 0.1

        return min(activity, 1.0)

    @staticmethod
    def create_layout() -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        # Main layout structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # Split main area
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=2),
        )

        # Split left column
        layout["left"].split_column(
            Layout(name="sessions", ratio=3),
            Layout(name="health", ratio=2),
        )

        # Split right column
        layout["right"].split_column(
            Layout(name="activity", ratio=2),
            Layout(name="progress", ratio=2),
            Layout(name="session_progress", ratio=2),
        )

        return layout

    def update_layout(self, layout: Layout) -> None:
        """Update layout with current data."""
        # Header
        cache_hit_rate = self.tmux_manager.get_cache_stats().get("hit_rate", 0)
        header_text = f"🚀 Yesman Project Dashboard - {self.project_name} | {time.strftime('%H:%M:%S')} | Cache Hit Rate: {cache_hit_rate:.1%}"
        layout["header"].update(Panel(header_text, style="bold blue"))

        # Sessions
        session_content, _ = self.session_browser.render()
        layout["sessions"].update(session_content)

        # Project health - use available method or create fallback
        try:
            health_data = self.project_health.calculate_health()
            health_content = Panel(f"Project Health: {health_data.get('overall_score', 'Unknown')}", title="Health")
        except Exception:
            health_content = Panel("Health data unavailable", title="Health")
        layout["health"].update(health_content)

        # Activity heatmap - create fallback since render method not available
        activity_content = Panel("Activity heatmap not available", title="Activity")
        layout["activity"].update(activity_content)

        # Progress tracking
        progress_content = self.progress_tracker.render_progress_overview()
        layout["progress"].update(progress_content)

        # Session progress
        if self.progress_data:
            session_progress_content = self.session_progress.render_progress_overview(self.progress_data)
            layout["session_progress"].update(session_progress_content)
        else:
            layout["session_progress"].update(
                Panel(
                    "[dim]Loading session progress...[/dim]",
                    title="📊 Session Progress",
                )
            )

        # Footer with compact status
        footer_parts = []
        # Use fallback for project health since render method not available
        try:
            health_data = self.project_health.calculate_health()
            footer_parts.append(f"Health: {health_data.get('overall_score', 'N/A')}")
        except Exception:
            footer_parts.append("Health: N/A")
        footer_parts.append(str(self.git_activity.render_compact_status()))
        footer_parts.append(str(self.progress_tracker.render_compact_progress()))
        footer_parts.append("Activity: N/A")  # render_compact_overview not available

        footer_text = " | ".join(str(part) for part in footer_parts)
        layout["footer"].update(Panel(footer_text, style="dim"))

    def run_interactive(self) -> None:
        """Run interactive dashboard."""
        layout = self.create_layout()

        try:
            with Live(layout, console=self.console, refresh_per_second=2):
                while True:
                    self.update_data()
                    self.update_layout(layout)
                    time.sleep(self.update_interval)

        except KeyboardInterrupt:
            self.console.print("\\n[yellow]Dashboard stopped[/]")

    def render_detailed_view(self) -> None:
        """Render detailed view with all components."""
        self.update_data()

        # Create detailed panels
        panels = []

        # Session browser
        session_content, _ = self.session_browser.render()
        panels.append(session_content)

        # Project health detailed - use fallback since render method not available
        try:
            health_data = self.project_health.calculate_health()
            health_detailed = Panel(f"Project Health Details: {health_data}", title="Health Details")
        except Exception:
            health_detailed = Panel("Health details unavailable", title="Health Details")
        panels.append(health_detailed)

        # Git activity
        git_overview = self.git_activity.render_activity_overview()
        git_commits = self.git_activity.render_recent_commits()
        panels.extend([git_overview, git_commits])

        # Progress tracking
        progress_overview = self.progress_tracker.render_progress_overview()
        todo_list = self.progress_tracker.render_todo_list(limit=8)
        panels.extend([progress_overview, todo_list])

        # Activity heatmap - create fallback since render method not available
        activity_heatmap = Panel("Activity heatmap not available", title="Activity Heatmap")
        panels.append(activity_heatmap)

        # Display all panels
        for panel in panels:
            self.console.print(panel)
            self.console.print()


class StatusCommand(BaseCommand, SessionCommandMixin):
    """Comprehensive project status dashboard."""

    def execute(
        self,
        project_path: str = ".",
        interactive: bool = False,  # noqa: FBT001
        update_interval: float = 5.0,
        detailed: bool = False,  # noqa: FBT001
        **kwargs: Any,  # noqa: ARG002
    ) -> dict:
        """Execute the status command."""
        try:
            dashboard = StatusDashboard(project_path, update_interval, self.config, self.tmux_manager)

            if interactive:
                self.print_info("Starting interactive project status dashboard...")
                self.print_info("Press Ctrl+C to exit")
                dashboard.run_interactive()
                return {
                    "success": True,
                    "mode": "interactive",
                    "project_path": project_path,
                }
            if detailed:
                dashboard.render_detailed_view()
                return {
                    "success": True,
                    "mode": "detailed",
                    "project_path": project_path,
                }
            # Quick status overview
            dashboard.update_data()

            console = Console()

            # Quick summary
            console.print(f"🎯 Project: {dashboard.project_name}", style="bold cyan")
            console.print()

            # Compact status from each widget
            try:
                health_data = dashboard.project_health.calculate_health()
                health_status = f"Health: {health_data.get('overall_score', 'N/A')}"
            except Exception:
                health_status = "Health: N/A"
            git_status = str(dashboard.git_activity.render_compact_status())
            progress_status = str(dashboard.progress_tracker.render_compact_progress())

            console.print("📊 Quick Status:")
            console.print(f"  Health: {health_status}")
            console.print(f"  Git: {git_status}")
            console.print(f"  Progress: {progress_status}")

            console.print("\n💡 Use --interactive for live dashboard or --detailed for full view")
            return {"success": True, "mode": "quick", "project_path": project_path}

        except KeyboardInterrupt:
            self.print_warning("\nStatus dashboard stopped.")
            return {"success": True, "stopped_by_user": True}
        except Exception as e:
            msg = f"Error running status dashboard: {e}"
            raise CommandError(msg) from e


@click.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
@click.option("--interactive", "-i", is_flag=True, help="Run interactive dashboard")
@click.option(
    "--update-interval",
    "-u",
    default=5.0,
    type=float,
    help="Update interval in seconds",
)
@click.option("--detailed", "-d", is_flag=True, help="Show detailed view")
def status(project_path: str, interactive: bool, update_interval: float, detailed: bool) -> None:  # noqa: FBT001
    """Comprehensive project status dashboard."""
    command = StatusCommand()
    command.run(
        project_path=project_path,
        interactive=interactive,
        update_interval=update_interval,
        detailed=detailed,
    )

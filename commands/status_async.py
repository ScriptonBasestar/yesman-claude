from typing import Any
import asyncio
import time
from pathlib import Path
import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from libs.core.async_base_command import AsyncMonitoringCommand, CommandError
from libs.core.base_command import SessionCommandMixin
from libs.core.session_manager import SessionManager
from libs.dashboard.widgets import (
from libs.dashboard.widgets.session_progress import SessionProgressWidget
from rich.table import Table
from rich.text import Text
from rich.table import Table
from commands.status import StatusCommand as SyncStatusCommand


# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Async comprehensive project status dashboard command with performance optimizations."""



    ActivityHeatmapGenerator,
    GitActivityWidget,
    ProgressTracker,
    ProjectHealth,
    SessionBrowser,
)


class AsyncStatusDashboard:
    """Async comprehensive status dashboard with performance optimizations."""

    def __init__(
        self,
        project_path: str = ".",
        update_interval: float = 5.0,
        config: object = None,
        tmux_manager: object = None,
    ) -> None:
        self.console = Console()
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.update_interval = update_interval

        # Use provided dependencies or create defaults
        self.config = config
        self.tmux_manager = tmux_manager

        # Initialize widgets
        self.session_browser = SessionBrowser(self.console)
        self.activity_heatmap = ActivityHeatmapGenerator(self.config)
        self.project_health = ProjectHealth(str(self.project_path))
        self.git_activity = GitActivityWidget(self.console, str(self.project_path))
        self.progress_tracker = ProgressTracker(self.console)
        self.session_progress = SessionProgressWidget(self.console)

        # Initialize session manager
        self.session_manager = SessionManager()

        # Data cache for performance
        self._data_cache = {
            "sessions": [],
            "progress_data": None,
            "health_data": None,
            "last_update": 0,
        }
        self._cache_ttl = 2.0  # Cache TTL in seconds

        # Load initial data
        self._load_todo_data()

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

    async def update_data(self) -> None:
        """Async update of all dashboard data with caching."""
        current_time = time.time()

        # Check if cache is still valid
        last_update = self._data_cache.get("last_update", 0)
        if isinstance(last_update, int | float) and current_time - last_update < self._cache_ttl:
            return

        try:
            # Run multiple data updates concurrently
            tasks = [
                self._update_session_data(),
                self._update_project_health(),
                self._update_progress_data(),
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # Update cache timestamp
            self._data_cache["last_update"] = current_time

        except Exception as e:
            self.console.print(f"[red]Error updating data: {e}[/]")

    async def _update_session_data(self) -> None:
        """Async update of session data."""
        # Get session information using cached method
        loop = asyncio.get_event_loop()
        sessions_list = await loop.run_in_executor(None, self.tmux_manager.get_cached_sessions_list)

        detailed_sessions = []

        # Process sessions concurrently
        session_tasks = []
        for session_info in sessions_list:
            session_name = session_info["session_name"]
            task = self._get_session_detail_async(session_name)
            session_tasks.append(task)

        if session_tasks:
            session_details = await asyncio.gather(*session_tasks, return_exceptions=True)

            for session_detail in session_details:
                if isinstance(session_detail, Exception):
                    self.console.print(f"[yellow]Warning: Session detail error: {session_detail}[/]")
                    continue
                if isinstance(session_detail, dict):
                    detailed_sessions.append(session_detail)

                    # Calculate activity for heatmap
                    self._calculate_session_activity(session_detail)
                    # Use activity collection method instead of add_activity_point
                    session_name = session_detail.get("session_name", "unknown")
                    # Store activity data for later rendering

        # Update session browser
        self.session_browser.update_sessions(detailed_sessions)
        self._data_cache["sessions"] = detailed_sessions

    async def _get_session_detail_async(self, session_name: str):
        """Async wrapper for getting session details."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.tmux_manager.get_session_info, session_name)

    async def _update_project_health(self) -> None:
        """Async update of project health."""
        loop = asyncio.get_event_loop()
        # ProjectHealth doesn't have update_project_health method, it calculates on demand
        # So we'll just trigger a calculation to refresh the data
        await loop.run_in_executor(None, self.project_health.calculate_health)

    async def _update_progress_data(self) -> None:
        """Async update of progress data."""
        loop = asyncio.get_event_loop()
        progress_data = await loop.run_in_executor(None, self.session_manager.get_progress_overview)
        self._data_cache["progress_data"] = progress_data

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

    async def update_layout(self, layout: Layout) -> None:
        """Async update layout with current data."""
        # Header with performance indicators
        loop = asyncio.get_event_loop()
        cache_stats = await loop.run_in_executor(None, self.tmux_manager.get_cache_stats)

        last_update = self._data_cache.get("last_update", time.time())
        cache_age = time.time() - last_update if isinstance(last_update, int | float) else 0.0
        header_text = f"🚀 Yesman Dashboard (Async) - {self.project_name} | {time.strftime('%H:%M:%S')} | Cache: {cache_stats.get('hit_rate', 0):.1%} | Data Age: {cache_age:.1f}s"
        layout["header"].update(Panel(header_text, style="bold green"))

        # Sessions panel
        sessions_content, _ = self.session_browser.render()
        layout["sessions"].update(Panel(sessions_content, title="📋 Active Sessions", border_style="blue"))

        # Project health panel
        health_data = self.project_health.calculate_health()
        health_content = self._render_health_summary(health_data)
        layout["health"].update(Panel(health_content, title="🏥 Project Health", border_style="green"))

        # Activity heatmap panel
        # Generate heatmap data from collected sessions
        sessions_data = self._data_cache.get("sessions", [])
        session_names = [s.get("session_name", "unknown") for s in sessions_data if isinstance(s, dict)] if isinstance(sessions_data, list) else []
        heatmap_data = self.activity_heatmap.generate_heatmap_data(session_names)
        activity_content = self._render_heatmap(heatmap_data)
        layout["activity"].update(Panel(activity_content, title="🔥 Activity Heatmap", border_style="red"))

        # Progress tracker panel
        progress_stats = self._calculate_progress_stats()
        progress_content = self._render_progress_summary(progress_stats)
        layout["progress"].update(Panel(progress_content, title="📈 TODO Progress", border_style="yellow"))

        # Session progress panel
        progress_data = self._data_cache.get("progress_data")
        if progress_data and isinstance(progress_data, dict):
            session_progress_content = self.session_progress.render_progress_overview(progress_data)
            layout["session_progress"].update(
                Panel(
                    session_progress_content,
                    title="🎯 Session Progress",
                    border_style="magenta",
                )
            )
        else:
            layout["session_progress"].update(
                Panel(
                    "[dim]Loading session progress...[/dim]",
                    title="🎯 Session Progress",
                )
            )

        # Footer with performance stats
        sessions_data = self._data_cache.get("sessions", [])
        session_count = len(sessions_data) if isinstance(sessions_data, list) else 0
        footer_text = f"💡 Async Mode | Update Interval: {self.update_interval}s | Cache TTL: {self._cache_ttl}s | Sessions: {session_count}"
        layout["footer"].update(Panel(footer_text, style="dim"))

    async def run_interactive(self) -> None:
        """Run the interactive dashboard."""
        # Initial data load
        await self.update_data()

        # Create layout
        layout = self.create_layout()

        try:
            with Live(layout, console=self.console, refresh_per_second=4):
                while True:
                    await self.update_data()
                    await self.update_layout(layout)
                    await asyncio.sleep(self.update_interval)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]📊 Async dashboard stopped[/]")

    def render_detailed_view(self) -> None:
        """Render detailed static view (sync operation)."""
        # Synchronous version for detailed output
        layout = self.create_layout()

        # Run a single update synchronously
        asyncio.run(self.update_data())
        asyncio.run(self.update_layout(layout))

        self.console.print(layout)

    def _render_health_summary(self, health_data: dict) -> str:
        """Render health summary from health data."""

        table = Table(show_header=False, expand=True)
        table.add_column("Metric")
        table.add_column("Score", justify="right")

        overall_score = health_data.get("overall_score", 0)
        table.add_row("Overall Health", f"{overall_score}%")

        # Add individual scores
        metrics = [
            ("Build", "build_score"),
            ("Tests", "test_score"),
            ("Dependencies", "deps_score"),
            ("Security", "security_score"),
            ("Performance", "perf_score"),
            ("Code Quality", "quality_score"),
            ("Git", "git_score"),
            ("Documentation", "docs_score"),
        ]

        for label, key in metrics:
            score = health_data.get(key, 0)
            table.add_row(label, f"{score}%")

        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    @staticmethod
    def _render_heatmap(heatmap_data: dict) -> str:
        """Render activity heatmap visualization."""

        # Simple text representation of heatmap
        output = Text()
        output.append("Session Activity (Last 7 days)\n\n")

        heatmap = heatmap_data.get("heatmap", {})
        if not heatmap:
            output.append("No activity data available", style="dim")
        else:
            # Days of week
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for day_idx, day_name in enumerate(days):
                output.append(f"{day_name}: ")
                for hour in range(24):
                    count = heatmap.get(day_idx, {}).get(hour, 0)
                    if count == 0:
                        output.append("·", style="dim")
                    elif count < 5:
                        output.append("▪", style="yellow")
                    else:
                        output.append("█", style="red")
                output.append("\n")

        return str(output)

    def _calculate_progress_stats(self) -> dict:
        """Calculate progress statistics from tracked TODOs."""
        total = len(self.progress_tracker.todos)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "completion_rate": 0.0,
            }

        completed = sum(1 for todo in self.progress_tracker.todos if todo.status.value == "completed")
        in_progress = sum(1 for todo in self.progress_tracker.todos if todo.status.value == "in_progress")
        pending = sum(1 for todo in self.progress_tracker.todos if todo.status.value == "pending")

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": (completed / total) * 100 if total > 0 else 0.0,
        }

    def _render_progress_summary(self, stats: dict) -> str:
        """Render progress summary visualization."""

        table = Table(show_header=False, expand=True)
        table.add_column("Metric")
        table.add_column("Value", justify="right")

        table.add_row("Total TODOs", str(stats.get("total", 0)))
        table.add_row("Completed", str(stats.get("completed", 0)))
        table.add_row("In Progress", str(stats.get("in_progress", 0)))
        table.add_row("Pending", str(stats.get("pending", 0)))
        table.add_row("Completion Rate", f"{stats.get('completion_rate', 0):.1f}%")

        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()


class AsyncStatusCommand(AsyncMonitoringCommand, SessionCommandMixin):
    """Async comprehensive project status dashboard."""

    @staticmethod
    def validate_preconditions() -> None:
        """Validate command preconditions."""
        super().validate_preconditions()

    async def execute_async(
        self,
        project_path: str = ".",
        update_interval: float = 5.0,
        interactive: bool = False,  # noqa: FBT001
        **kwargs: Any,  # noqa: ARG002
    ) -> dict:
        """Execute the async status command."""
        try:
            dashboard = AsyncStatusDashboard(
                project_path=project_path,
                update_interval=update_interval,
                config=self.config,
                tmux_manager=self.tmux_manager,
            )

            if interactive:
                self.print_info("🚀 Starting async interactive status dashboard...")
                self.print_info("⚡ Performance optimized with async operations")
                self.print_info("Press Ctrl+C to exit")

                await dashboard.run_interactive()
            else:
                self.print_info("📊 Generating async status report...")
                dashboard.render_detailed_view()

            return {"success": True, "mode": "async", "interactive": interactive}

        except KeyboardInterrupt:
            self.print_info("\n📊 Status dashboard stopped")
            return {"success": True, "stopped_by_user": True}
        except Exception as e:
            msg = f"Error in async status dashboard: {e}"
            raise CommandError(msg) from e

    @staticmethod
    async def update_monitoring_data() -> None:
        """Implement monitoring data updates."""
        # Dashboard handles its own monitoring


# Create alias for backward compatibility
StatusCommand = AsyncStatusCommand


@click.command()
@click.option(
    "--project-path",
    "-p",
    default=".",
    help="Project directory path (default: current directory)",
)
@click.option(
    "--update-interval",
    "-i",
    default=5.0,
    type=float,
    help="Update interval for interactive mode in seconds (default: 5.0)",
)
@click.option(
    "--interactive/--static",
    default=False,
    help="Run in interactive mode with live updates",
)
@click.option(
    "--async-mode/--sync-mode",
    default=True,
    help="Use async mode for better performance (default: enabled)",
)
def status(project_path: str, update_interval: float, interactive: bool, async_mode: bool) -> None:  # noqa: FBT001
    """Comprehensive project status dashboard with async optimizations."""
    if async_mode:
        command = AsyncStatusCommand()
        if interactive:
            command.print_info("⚡ Running async interactive dashboard")
    else:
        # Fallback to original implementation if needed

        command: AsyncStatusCommand = SyncStatusCommand()  # type: ignore
        command.print_warning("⚠️  Running in sync mode (consider using --async-mode)")

    command.run(
        project_path=project_path,
        update_interval=update_interval,
        interactive=interactive,
    )


@click.command()
@click.option(
    "--project-path",
    "-p",
    default=".",
    help="Project directory path (default: current directory)",
)
@click.option(
    "--update-interval",
    "-i",
    default=5.0,
    type=float,
    help="Update interval in seconds (default: 5.0)",
)
@click.option(
    "--interactive/--static",
    default=True,
    help="Run in interactive mode with live updates (default: interactive)",
)
def status_async(project_path: str, update_interval: float, interactive: bool) -> None:  # noqa: FBT001
    """Async comprehensive project status dashboard (explicit async version)."""
    command = AsyncStatusCommand()
    command.run(
        project_path=project_path,
        update_interval=update_interval,
        interactive=interactive,
    )

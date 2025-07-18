"""Async Interactive session browser command with enhanced performance."""

import asyncio
import time

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from libs.core.async_base_command import AsyncMonitoringCommand, CommandError
from libs.core.base_command import SessionCommandMixin
from libs.core.session_manager import SessionManager
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmapGenerator
from libs.dashboard.widgets.session_browser import SessionBrowser
from libs.dashboard.widgets.session_progress import SessionProgressWidget


class AsyncInteractiveBrowser:
    """Async interactive session browser with live updates."""

    def __init__(self, tmux_manager, config, update_interval: float = 2.0):
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
        self.progress_data = None
        self._update_task: asyncio.Task | None = None

    async def update_data(self) -> None:
        """Async update of session data and activity metrics."""
        try:
            # Get session information using cached method
            sessions_list = await self._get_sessions_async()
            detailed_sessions = []

            for session_info in sessions_list:
                session_name = session_info["session_name"]
                detailed_info = await self._get_session_info_async(session_name)
                detailed_sessions.append(detailed_info)

                # Calculate and record activity
                activity_level = self._calculate_session_activity(detailed_info)
                # Store activity for later heatmap generation

            # Update browser with new data
            self.session_browser.update_sessions(detailed_sessions)

            # Update progress data
            self.progress_data = await self._get_progress_overview_async()

        except Exception as e:
            self.console.print(f"[red]Error updating session data: {e}[/]")

    async def _get_sessions_async(self):
        """Async wrapper for getting sessions list."""
        # Run blocking operation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.tmux_manager.get_cached_sessions_list)

    async def _get_session_info_async(self, session_name: str):
        """Async wrapper for getting session info."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.tmux_manager.get_session_info, session_name)

    async def _get_progress_overview_async(self):
        """Async wrapper for getting progress overview."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.session_manager.get_progress_overview)

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

    async def update_layout(self, layout: Layout):
        """Async update layout content."""
        # Header with async cache stats
        header_text = f"🚀 Yesman Session Browser (Async) - {time.strftime('%H:%M:%S')}"

        # Get cache stats asynchronously
        loop = asyncio.get_event_loop()
        cache_stats = await loop.run_in_executor(None, self.tmux_manager.get_cache_stats)
        header_text += f" | Cache: {cache_stats.get('hit_rate', 0):.1%} hit rate"
        layout["header"].update(self.console.render_str(header_text, style="bold green"))

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
        # Generate heatmap from collected session data
        session_names = [s.session_name for s in self.session_browser.sessions]
        heatmap_data = self.activity_heatmap.generate_heatmap_data(session_names)
        heatmap_content = self._render_heatmap(heatmap_data)
        layout["activity"].update(heatmap_content)

        # Footer
        layout["footer"].update(status_bar)

    async def start_background_updates(self):
        """Start background data updates using async pattern."""
        while self.running:
            await self.update_data()
            await asyncio.sleep(self.update_interval)

    async def start(self):
        """Start the async interactive browser."""
        self.running = True

        # Initial data load
        await self.update_data()

        # Start background update task
        self._update_task = asyncio.create_task(self.start_background_updates())

        # Create layout
        layout = self.create_layout()

        try:
            with Live(layout, console=self.console, refresh_per_second=10):
                while self.running:
                    await self.update_layout(layout)

                    # Small async sleep instead of blocking
                    await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            await self.stop()

    async def stop(self):
        """Stop the browser gracefully."""
        self.running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    def _render_heatmap(self, heatmap_data: dict) -> str:
        """Render activity heatmap visualization."""
        from rich.text import Text

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


class AsyncBrowseCommand(AsyncMonitoringCommand, SessionCommandMixin):
    """Async interactive session browser with enhanced performance."""

    def validate_preconditions(self) -> None:
        """Validate command preconditions."""
        super().validate_preconditions()
        # Check if tmux is available and running
        if not self._is_tmux_available():
            raise CommandError("tmux is not available or not properly installed")

    async def execute_async(self, update_interval: float = 2.0, **kwargs) -> dict:
        """Execute the async browse command."""
        try:
            browser = AsyncInteractiveBrowser(self.tmux_manager, self.config, update_interval)

            self.print_info("🚀 Starting async interactive session browser...")
            self.print_info("⚡ Enhanced with async performance optimizations")
            self.print_info("Press Ctrl+C to exit")

            await browser.start()

            return {"success": True, "mode": "async"}

        except KeyboardInterrupt:
            self.print_info("\n📊 Async session browser stopped.")
            return {"success": True, "stopped_by_user": True, "mode": "async"}
        except Exception as e:
            raise CommandError(f"Error during async browsing: {e}") from e

    async def update_monitoring_data(self) -> None:
        """Implement monitoring data updates."""
        # This could be used for additional monitoring metrics
        # For now, the browser handles its own updates
        pass


# Create alias for backward compatibility
BrowseCommand = AsyncBrowseCommand


@click.command()
@click.option(
    "--update-interval",
    "-i",
    default=2.0,
    type=float,
    help="Update interval in seconds (default: 2.0)",
)
@click.option(
    "--async-mode/--sync-mode",
    default=True,
    help="Use async mode for better performance (default: enabled)",
)
def browse(update_interval, async_mode):
    """Interactive session browser with async performance optimizations."""
    if async_mode:
        command = AsyncBrowseCommand()
        command.print_info("🔥 Running in async mode for optimal performance")
    else:
        # Fallback to original implementation if needed
        from commands.browse import BrowseCommand as SyncBrowseCommand

        command: AsyncBrowseCommand = SyncBrowseCommand()  # type: ignore
        command.print_warning("⚠️  Running in sync mode (consider using --async-mode)")

    command.run(update_interval=update_interval)


@click.command()
@click.option(
    "--update-interval",
    "-i",
    default=2.0,
    type=float,
    help="Update interval in seconds (default: 2.0)",
)
def browse_async(update_interval):
    """Async interactive session browser (explicit async version)."""
    command = AsyncBrowseCommand()
    command.run(update_interval=update_interval)

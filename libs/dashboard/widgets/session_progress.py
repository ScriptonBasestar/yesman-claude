"""Session progress overview widget"""

from datetime import datetime
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class SessionProgressWidget:
    """Widget for displaying session progress overview"""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def render_progress_overview(self, progress_data: dict[str, Any]) -> Panel:
        """Render the main progress overview panel"""
        if not progress_data:
            return Panel(
                Text("No progress data available", style="dim"),
                title="📊 Progress Overview",
            )

        # Create layout
        layout = Layout()
        layout.split(
            Layout(name="summary", size=7),
            Layout(name="sessions", ratio=1),
        )

        # Render summary section
        layout["summary"].update(self._render_summary(progress_data))

        # Render sessions section
        layout["sessions"].update(self._render_sessions_table(progress_data.get("sessions", [])))

        return Panel(layout, title="📊 Progress Overview", border_style="cyan")

    def _render_summary(self, data: dict[str, Any]) -> Panel:
        """Render summary statistics"""
        content = Text()

        # Overall progress bar
        avg_progress = data.get("average_progress", 0)
        bar_length = 40
        filled = int(avg_progress / 100 * bar_length)
        progress_bar = "█" * filled + "░" * (bar_length - filled)

        content.append("🎯 Overall Progress\n", style="bold cyan")
        content.append(f"  {progress_bar} {avg_progress:.1f}%\n", style="green")
        content.append(f"  {data.get('sessions_with_progress', 0)}/{data.get('total_sessions', 0)} sessions active\n\n")

        # Task statistics
        content.append("📋 Task Statistics\n", style="bold yellow")
        content.append(f"  🔄 Active: {data.get('active_tasks', 0)}\n", style="yellow")
        content.append(f"  ✅ Completed: {data.get('completed_tasks', 0)}\n", style="green")

        # Activity metrics
        content.append("\n⚡ Activity Metrics\n", style="bold magenta")
        content.append(f"  📁 Files Changed: {data.get('total_files_changed', 0)}\n")
        content.append(f"  💻 Commands Executed: {data.get('total_commands_executed', 0)}\n")

        return Panel(content, title="Summary", border_style="dim")

    def _render_sessions_table(self, sessions: list[dict[str, Any]]) -> Panel:
        """Render individual sessions progress table"""
        if not sessions:
            return Panel(Text("No active sessions", style="dim"), title="Sessions")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session", style="cyan", width=20)
        table.add_column("Progress", style="white", width=25)
        table.add_column("Phase", style="yellow", width=15)
        table.add_column("Files", style="green", width=8, justify="center")
        table.add_column("Commands", style="blue", width=10, justify="center")

        for session in sessions:
            # Progress bar for session
            progress = session.get("overall_progress", 0)
            bar_length = 20
            filled = int(progress / 100 * bar_length)
            progress_bar = "█" * filled + "░" * (bar_length - filled)

            # Phase emoji
            phase_emoji = self._get_phase_emoji(session.get("current_phase", "idle"))

            table.add_row(
                session.get("session_name", "Unknown"),
                f"{progress_bar} {progress:.0f}%",
                f"{phase_emoji} {session.get('current_phase', 'idle')}",
                str(session.get("files_changed", 0)),
                str(session.get("commands_executed", 0)),
            )

        return Panel(table, title="Active Sessions", border_style="dim")

    def _get_phase_emoji(self, phase: str) -> str:
        """Get emoji for task phase"""
        phase_emojis = {
            "starting": "🚀",
            "analyzing": "🔍",
            "implementing": "⚡",
            "testing": "🧪",
            "completing": "🏁",
            "completed": "✅",
            "idle": "💤",
        }
        return phase_emojis.get(phase, "❓")

    def render_compact_progress(self, progress_data: dict[str, Any]) -> Text:
        """Render compact progress for status bars"""
        if not progress_data:
            return Text("Progress: No data", style="dim")

        avg_progress = progress_data.get("average_progress", 0)
        active_sessions = progress_data.get("sessions_with_progress", 0)
        total_sessions = progress_data.get("total_sessions", 0)

        text = Text()
        text.append("Progress: ", style="bold")
        text.append(f"{avg_progress:.0f}%", style="green")
        text.append(f" ({active_sessions}/{total_sessions} active)", style="white")

        return text

    def render_session_detail(self, session_name: str, session_info: Any, progress: Any) -> Panel:
        """Render detailed progress for a specific session"""
        if not progress:
            return Panel(
                Text("No progress data for this session", style="dim"),
                title=f"📊 {session_name} Progress",
            )

        content = Text()

        # Current task progress
        current_task = progress.get_current_task()
        if current_task:
            content.append("📍 Current Task\n", style="bold cyan")
            content.append(f"  Phase: {current_task.phase.value}\n", style="yellow")

            # Phase progress bar
            phase_progress = current_task.phase_progress
            bar_length = 30
            filled = int(phase_progress / 100 * bar_length)
            phase_bar = "█" * filled + "░" * (bar_length - filled)
            content.append(f"  Progress: {phase_bar} {phase_progress:.0f}%\n\n")

            # Task metrics
            content.append("📊 Task Metrics\n", style="bold yellow")
            content.append(f"  Files: +{current_task.files_created} / ~{current_task.files_modified}\n")
            content.append(f"  Commands: {current_task.commands_succeeded}✓ / {current_task.commands_failed}✗\n")
            content.append(f"  TODOs: {current_task.todos_completed} / {current_task.todos_identified}\n\n")

        # Overall session progress
        overall_progress = progress.calculate_overall_progress()
        bar_length = 40
        filled = int(overall_progress / 100 * bar_length)
        overall_bar = "█" * filled + "░" * (bar_length - filled)

        content.append("🎯 Overall Progress\n", style="bold green")
        content.append(f"  {overall_bar} {overall_progress:.1f}%\n")
        content.append(f"  Tasks: {len(progress.tasks)} total\n")

        # Session duration
        if progress.session_start_time:
            duration = datetime.now() - progress.session_start_time
            hours = duration.total_seconds() / 3600
            content.append(f"  Duration: {hours:.1f} hours\n")

        return Panel(content, title=f"📊 {session_name} Progress", border_style="cyan")

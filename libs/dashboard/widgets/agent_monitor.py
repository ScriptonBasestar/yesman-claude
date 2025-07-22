# Copyright notice.

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.text import Text

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.types import Agent, AgentState, Task, TaskStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Real-time multi-agent monitoring dashboard widget."""


if TYPE_CHECKING:
    pass

try:
    pass
except ImportError:
    # For development/testing when multi_agent is not available
    class AgentState(Enum):  # type: ignore[no-redef]
        IDLE = "idle"
        WORKING = "working"
        SUSPENDED = "suspended"
        TERMINATED = "terminated"
        ERROR = "error"

    class TaskStatus(Enum):  # type: ignore[no-redef]
        PENDING = "pending"
        ASSIGNED = "assigned"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"

    @dataclass
    class Agent:  # type: ignore[no-redef]
        agent_id: str
        state: str

    @dataclass
    class Task:  # type: ignore[no-redef]
        task_id: str
        title: str
        status: str

    class AgentPool:  # type: ignore[no-redef]
        """Fallback AgentPool class for when multi_agent is not available."""


class MonitorDisplayMode(Enum):
    """Agent monitor display modes."""

    OVERVIEW = "overview"
    DETAILED = "detailed"
    PERFORMANCE = "performance"
    TASKS = "tasks"


@dataclass
class AgentMetrics:
    """Real-time agent performance metrics."""

    agent_id: str
    current_task: str | None = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 1.0
    current_load: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)

    @property
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        if self.tasks_completed == 0:
            return 0.5
        return self.success_rate * 0.6 + (1.0 - self.current_load) * 0.3 + min(1.0, self.tasks_completed / 10.0) * 0.1


@dataclass
class TaskMetrics:
    """Task execution metrics."""

    task_id: str
    title: str
    status: TaskStatus
    assigned_agent: str | None = None
    start_time: datetime | None = None
    estimated_duration: float | None = None
    progress: float = 0.0


class AgentMonitor:
    """Real-time multi-agent monitoring dashboard."""

    def __init__(
        self,
        agent_pool: AgentPool | None = None,
        console: Console | None = None,
    ) -> None:
        self.console = console or Console()
        self.logger = logging.getLogger("yesman.dashboard.agent_monitor")
        self.agent_pool = agent_pool

        # Display state
        self.display_mode = MonitorDisplayMode.OVERVIEW
        self.selected_agent: str | None = None
        self.auto_refresh = True
        self.refresh_interval = 1.0  # seconds

        # Metrics storage
        self.agent_metrics: dict[str, AgentMetrics] = {}
        self.task_metrics: dict[str, TaskMetrics] = {}
        self.system_metrics = {
            "total_agents": 0,
            "active_agents": 0,
            "idle_agents": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "queue_size": 0,
            "average_efficiency": 0.0,
        }

        # Performance tracking
        self.performance_history: dict[str, list[tuple[datetime, float]]] = {}
        self.task_completion_rate: list[tuple[datetime, int]] = []

        # Visual components
        self.progress_bars: dict[str, TaskID] = {}
        self.progress_display: Progress | None = None

    def update_metrics(self) -> None:
        """Update all metrics from agent pool."""
        if not self.agent_pool:
            return

        try:
            # Update agent metrics
            agents = self.agent_pool.list_agents()
            for agent_data in agents:
                agent_id = agent_data["agent_id"]

                if agent_id not in self.agent_metrics:
                    self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

                metrics = self.agent_metrics[agent_id]
                metrics.current_task = agent_data.get("current_task")
                metrics.tasks_completed = agent_data.get("completed_tasks", 0)
                metrics.tasks_failed = agent_data.get("failed_tasks", 0)
                metrics.total_execution_time = agent_data.get(
                    "total_execution_time",
                    0.0,
                )

                if metrics.tasks_completed > 0:
                    metrics.average_execution_time = metrics.total_execution_time / metrics.tasks_completed
                    metrics.success_rate = metrics.tasks_completed / (metrics.tasks_completed + metrics.tasks_failed)

                # Update performance history
                now = datetime.now(UTC)
                if agent_id not in self.performance_history:
                    self.performance_history[agent_id] = []

                self.performance_history[agent_id].append(
                    (now, metrics.efficiency_score),
                )
                # Keep only last 100 data points
                if len(self.performance_history[agent_id]) > 100:
                    self.performance_history[agent_id] = self.performance_history[agent_id][-100:]

            # Update task metrics
            tasks = self.agent_pool.list_tasks()
            for task_data in tasks:
                task_id = task_data["task_id"]

                self.task_metrics[task_id] = TaskMetrics(
                    task_id=task_id,
                    title=task_data["title"],
                    status=TaskStatus(task_data["status"]),
                    assigned_agent=task_data.get("assigned_agent"),
                    start_time=(datetime.fromisoformat(task_data["start_time"]) if task_data.get("start_time") else None),
                    progress=self._calculate_task_progress(task_data),
                )

            # Update system metrics
            stats = self.agent_pool.get_pool_statistics()
            self.system_metrics.update(
                {
                    "total_agents": len(agents),
                    "active_agents": stats.get("active_agents", 0),
                    "idle_agents": stats.get("idle_agents", 0),
                    "total_tasks": stats.get("total_tasks", 0),
                    "completed_tasks": stats.get("completed_tasks", 0),
                    "failed_tasks": stats.get("failed_tasks", 0),
                    "queue_size": stats.get("queue_size", 0),
                    "average_efficiency": sum(m.efficiency_score for m in self.agent_metrics.values()) / max(len(self.agent_metrics), 1),
                },
            )

        except Exception as e:
            self.logger.exception("Error updating metrics")  # noqa: G004

    @staticmethod
    def _calculate_task_progress(task_data: dict[str, object]) -> float:
        """Calculate task progress percentage."""
        status = task_data["status"]
        start_time = task_data.get("start_time")

        if status == "completed":
            return 1.0
        if status in {"failed", "cancelled"}:
            return 0.0
        if status == "running" and start_time:
            # Estimate progress based on elapsed time and timeout
            start = datetime.fromisoformat(start_time)
            elapsed = (datetime.now(UTC) - start).total_seconds()
            timeout: float = task_data.get("timeout", 300)
            return min(0.9, elapsed / timeout)  # Cap at 90% for running tasks
        if status == "assigned":
            return 0.1
        # pending
        return 0.0

    def render_overview(self) -> Panel:
        """Render overview dashboard."""
        layout = Layout()

        # System stats table
        stats_table = Table(
            title="System Overview",
            show_header=True,
            header_style="bold magenta",
        )
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total Agents", str(self.system_metrics["total_agents"]))
        stats_table.add_row("Active Agents", str(self.system_metrics["active_agents"]))
        stats_table.add_row("Idle Agents", str(self.system_metrics["idle_agents"]))
        stats_table.add_row("Queue Size", str(self.system_metrics["queue_size"]))
        stats_table.add_row(
            "Completed Tasks",
            str(self.system_metrics["completed_tasks"]),
        )
        stats_table.add_row("Failed Tasks", str(self.system_metrics["failed_tasks"]))
        stats_table.add_row(
            "Average Efficiency",
            f"{self.system_metrics['average_efficiency']:.2%}",
        )

        # Agent status table
        agent_table = Table(
            title="Agent Status",
            show_header=True,
            header_style="bold blue",
        )
        agent_table.add_column("Agent ID", style="cyan")
        agent_table.add_column("State", style="magenta")
        agent_table.add_column("Current Task", style="yellow")
        agent_table.add_column("Completed", style="green")
        agent_table.add_column("Failed", style="red")
        agent_table.add_column("Efficiency", style="blue")

        for agent_id, metrics in self.agent_metrics.items():
            state_color = {
                "idle": "green",
                "working": "yellow",
                "error": "red",
                "terminated": "dim",
            }.get((metrics.current_task and "working") or "idle", "white")

            agent_table.add_row(
                agent_id,
                Text((metrics.current_task and "WORKING") or "IDLE", style=state_color),
                metrics.current_task or "-",
                str(metrics.tasks_completed),
                str(metrics.tasks_failed),
                f"{metrics.efficiency_score:.2%}",
            )

        layout.split_column(
            Layout(Align.center(stats_table), size=10),
            Layout(Align.center(agent_table)),
        )

        return Panel(
            layout,
            title="Multi-Agent Monitor - Overview",
            border_style="bright_blue",
        )

    def render_detailed(self) -> Panel:
        """Render detailed agent view."""
        if not self.selected_agent or self.selected_agent not in self.agent_metrics:
            return Panel("No agent selected", title="Detailed View")

        metrics = self.agent_metrics[self.selected_agent]

        # Agent details
        details_table = Table(show_header=False)
        details_table.add_column("Property", style="cyan")
        details_table.add_column("Value", style="white")

        details_table.add_row("Agent ID", metrics.agent_id)
        details_table.add_row("Current Task", metrics.current_task or "None")
        details_table.add_row("Tasks Completed", str(metrics.tasks_completed))
        details_table.add_row("Tasks Failed", str(metrics.tasks_failed))
        details_table.add_row("Success Rate", f"{metrics.success_rate:.2%}")
        details_table.add_row(
            "Average Execution Time",
            f"{metrics.average_execution_time:.1f}s",
        )
        details_table.add_row("Current Load", f"{metrics.current_load:.1%}")
        details_table.add_row("Efficiency Score", f"{metrics.efficiency_score:.2%}")
        details_table.add_row(
            "Last Heartbeat",
            metrics.last_heartbeat.strftime("%H:%M:%S"),
        )

        # Performance history (simple text representation)
        history = self.performance_history.get(self.selected_agent, [])
        if history:
            recent_performance = [score for _, score in history[-20:]]  # Last 20 data points
            perf_text = "█" * int(
                sum(recent_performance) / len(recent_performance) * 20,
            )
            details_table.add_row("Performance Trend", perf_text)

        return Panel(
            details_table,
            title=f"Agent Details - {self.selected_agent}",
            border_style="bright_yellow",
        )

    def render_tasks(self) -> Panel:
        """Render task status view."""
        tasks_table = Table(
            title="Task Status",
            show_header=True,
            header_style="bold green",
        )
        tasks_table.add_column("Task ID", style="cyan")
        tasks_table.add_column("Title", style="white")
        tasks_table.add_column("Status", style="magenta")
        tasks_table.add_column("Agent", style="blue")
        tasks_table.add_column("Progress", style="green")
        tasks_table.add_column("Duration", style="yellow")

        for task_id, metrics in self.task_metrics.items():
            status_color = {
                TaskStatus.PENDING: "dim",
                TaskStatus.ASSIGNED: "blue",
                TaskStatus.RUNNING: "yellow",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.CANCELLED: "dim",
            }.get(metrics.status, "white")

            duration = ""
            if metrics.start_time:
                elapsed = datetime.now(UTC) - metrics.start_time
                duration = f"{elapsed.total_seconds():.0f}s"

            progress_bar = "█" * int(metrics.progress * 10) + "░" * (10 - int(metrics.progress * 10))

            tasks_table.add_row(
                task_id[:8] + "...",  # Truncate long IDs
                (metrics.title[:30] + "..." if len(metrics.title) > 30 else metrics.title),
                Text(metrics.status.value.upper(), style=status_color),
                metrics.assigned_agent or "-",
                f"{progress_bar} {metrics.progress:.0%}",
                duration,
            )

        return Panel(tasks_table, title="Task Monitor", border_style="bright_green")

    def render_performance(self) -> Panel:
        """Render performance analytics view."""
        perf_table = Table(
            title="Performance Analytics",
            show_header=True,
            header_style="bold red",
        )
        perf_table.add_column("Agent", style="cyan")
        perf_table.add_column("Efficiency Trend", style="green")
        perf_table.add_column("Throughput", style="yellow")
        perf_table.add_column("Avg Task Time", style="blue")
        perf_table.add_column("Load Factor", style="magenta")

        for agent_id, metrics in self.agent_metrics.items():
            # Calculate trend
            history = self.performance_history.get(agent_id, [])
            if len(history) >= 2:
                recent_avg = sum(score for _, score in history[-5:]) / min(
                    5,
                    len(history),
                )
                older_slice = history[-10:-5] if len(history) >= 10 else history[:-5]
                older_avg = sum(score for _, score in older_slice) / len(older_slice) if older_slice else recent_avg
                trend = "↗" if recent_avg > older_avg else "↘" if recent_avg < older_avg else "→"
            else:
                trend = "→"

            # Throughput (tasks per hour)
            throughput = metrics.tasks_completed / (metrics.total_execution_time / 3600.0) if metrics.total_execution_time > 0 else 0.0

            perf_table.add_row(
                agent_id,
                f"{trend} {metrics.efficiency_score:.1%}",
                f"{throughput:.1f}/h",
                f"{metrics.average_execution_time:.1f}s",
                f"{metrics.current_load:.1%}",
            )

        return Panel(
            perf_table,
            title="Performance Analytics",
            border_style="bright_red",
        )

    def render(self) -> Panel:
        """Render the current view based on display mode."""
        if self.display_mode == MonitorDisplayMode.OVERVIEW:
            return self.render_overview()
        if self.display_mode == MonitorDisplayMode.DETAILED:
            return self.render_detailed()
        if self.display_mode == MonitorDisplayMode.TASKS:
            return self.render_tasks()
        if self.display_mode == MonitorDisplayMode.PERFORMANCE:
            return self.render_performance()
        return Panel("Unknown display mode", title="Error")

    def set_display_mode(self, mode: MonitorDisplayMode) -> None:
        """Change display mode."""
        self.display_mode = mode
        self.logger.info(f"Display mode changed to: {mode.value}")  # noqa: G004

    def select_agent(self, agent_id: str) -> None:
        """Select an agent for detailed view."""
        if agent_id in self.agent_metrics:
            self.selected_agent = agent_id
            self.set_display_mode(MonitorDisplayMode.DETAILED)

    @staticmethod
    def get_keyboard_help() -> str:
        """Get keyboard shortcuts help text."""
        return """
Keyboard Shortcuts:
  1,2,3,4 - Switch view modes (Overview/Detailed/Tasks/Performance)
  ↑↓      - Navigate agents (in detailed mode)
  Enter   - Select agent for detailed view
  r       - Refresh data
  q       - Quit monitor
  h       - Show this help
        """.strip()

    async def start_monitoring(self, duration: float | None = None) -> None:
        """Start real-time monitoring."""
        start_time = time.time()

        try:
            with Live(self.render(), refresh_per_second=1) as live:
                while self.auto_refresh:
                    if duration and (time.time() - start_time) > duration:
                        break

                    self.update_metrics()
                    live.update(self.render())
                    await asyncio.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.exception("Error in monitoring loop")  # noqa: G004
            raise


# Helper function for standalone usage
def create_agent_monitor(agent_pool: AgentPool | None = None) -> AgentMonitor:
    """Create and configure an agent monitor."""
    return AgentMonitor(agent_pool=agent_pool)


# CLI integration function
async def run_agent_monitor(
    agent_pool: AgentPool | None = None,
    duration: float | None = None,
) -> None:
    """Run the agent monitor as a standalone application."""
    monitor = create_agent_monitor(agent_pool)
    await monitor.start_monitoring(duration)

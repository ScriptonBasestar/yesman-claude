"""Agent pool management commands."""

import asyncio
import logging
from pathlib import Path
from typing import Never

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from libs.core.base_command import BaseCommand, CommandError
from libs.dashboard.widgets.agent_monitor import AgentMonitor, run_agent_monitor
from libs.multi_agent.agent_pool import AgentPool

logger = logging.getLogger(__name__)


class StartAgentsCommand(BaseCommand):
    """Start the multi-agent pool."""

    def execute(
        self,
        max_agents: int = 3,
        work_dir: str | None = None,
        monitor: bool = False,
        **kwargs,
    ) -> dict:
        """Execute the start agents command."""
        try:
            # Create progress indicator for agent startup
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                startup_task = progress.add_task(
                    f"🤖 Starting multi-agent pool with {max_agents} agents...",
                    total=None,
                )

                # Create agent pool
                pool = AgentPool(max_agents=max_agents, work_dir=work_dir)

                async def run_pool() -> None:
                    await pool.start()
                    progress.update(startup_task, description="✅ Agent pool started successfully")

                    if monitor:
                        progress.update(
                            startup_task,
                            description="📊 Starting monitoring dashboard...",
                        )
                        await run_agent_monitor(pool)
                    else:
                        self.print_success("✅ Agent pool started successfully")
                        self.print_info("Use 'yesman multi-agent monitor' to view status")

                        # Keep running until interrupted
                        try:
                            while pool._running:
                                await asyncio.sleep(1)
                        except KeyboardInterrupt:
                            self.print_warning("\n🛑 Stopping agent pool...")
                            await pool.stop()

                asyncio.run(run_pool())
            return {"success": True, "max_agents": max_agents, "work_dir": work_dir}

        except Exception as e:
            msg = f"Error starting agents: {e}"
            raise CommandError(msg) from e


class MonitorAgentsCommand(BaseCommand):
    """Start real-time agent monitoring dashboard."""

    def execute(
        self,
        work_dir: str | None = None,
        duration: float | None = None,
        refresh: float = 1.0,
        **kwargs,
    ) -> dict:
        """Execute the monitor agents command."""
        try:
            self.print_info("📊 Starting agent monitoring dashboard...")

            # Try to connect to existing agent pool
            pool = None
            if work_dir:
                pool_dir = Path(work_dir) / ".yesman-agents"
                if pool_dir.exists():
                    pool = AgentPool(work_dir=work_dir)
                    # Load existing state without starting
                    pool._load_state()

            async def run_monitor() -> None:
                monitor = AgentMonitor(agent_pool=pool)
                monitor.refresh_interval = refresh

                if not pool:
                    self.print_warning("⚠️  No active agent pool found. Showing demo mode.")
                    # Add some demo data for visualization
                    from libs.dashboard.widgets.agent_monitor import AgentMetrics

                    monitor.agent_metrics = {
                        "agent-1": AgentMetrics(
                            agent_id="agent-1",
                            current_task="task-123",
                            tasks_completed=5,
                            tasks_failed=1,
                            total_execution_time=300.0,
                        ),
                    }

                if duration:
                    self.print_info(f"⏱️  Monitoring for {duration} seconds...")
                    import signal

                    def timeout_handler(signum: int, frame: Any) -> Never:
                        raise KeyboardInterrupt

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(duration))

                try:
                    await monitor.start_monitoring(duration)
                except KeyboardInterrupt:
                    self.print_info("\n📊 Monitoring stopped.")

            asyncio.run(run_monitor())
            return {"success": True, "work_dir": work_dir, "duration": duration}

        except Exception as e:
            msg = f"Error monitoring agents: {e}"
            raise CommandError(msg) from e


class StatusCommand(BaseCommand):
    """Show current agent pool status."""

    def execute(self, work_dir: str | None = None, **kwargs) -> dict:
        """Execute the status command."""
        try:
            # Initialize agent pool
            pool = AgentPool(work_dir=work_dir)
            pool._load_state()

            # Get pool statistics
            stats = pool.get_pool_statistics()
            agents = pool.list_agents()
            tasks = pool.list_tasks()

            # Display status information
            self.print_info("🤖 Multi-Agent Pool Status")
            self.print_info("=" * 40)
            self.print_info(f"Total Agents: {len(agents)}")
            self.print_info(f"Active Agents: {stats.get('active_agents', 0)}")
            self.print_info(f"Idle Agents: {stats.get('idle_agents', 0)}")
            self.print_info(f"Total Tasks: {len(tasks)}")
            self.print_info(f"Completed Tasks: {stats.get('completed_tasks', 0)}")
            self.print_info(f"Failed Tasks: {stats.get('failed_tasks', 0)}")
            self.print_info(f"Queue Size: {stats.get('queue_size', 0)}")
            self.print_info(f"Average Execution Time: {stats.get('average_execution_time', 0):.1f}s")

            # Display agent details
            if agents:
                self.print_info("\n📋 Agents:")
                for agent in agents:
                    status_icon = {
                        "idle": "🟢",
                        "working": "🟡",
                        "error": "🔴",
                        "terminated": "⚫",
                    }.get(agent.get("state", "unknown"), "❓")

                    self.print_info(f"  {status_icon} {agent['agent_id']} - Completed: {agent.get('completed_tasks', 0)}, Failed: {agent.get('failed_tasks', 0)}")

            return {
                "success": True,
                "work_dir": work_dir,
                "statistics": stats,
                "agents": agents,
                "tasks": tasks,
            }

        except Exception as e:
            msg = f"Error getting agent pool status: {e}"
            raise CommandError(msg) from e


class StopAgentsCommand(BaseCommand):
    """Stop the multi-agent pool."""

    def execute(self, work_dir: str | None = None, **kwargs) -> dict:
        """Execute the stop agents command."""
        try:
            self.print_info("🛑 Stopping multi-agent pool...")

            pool = AgentPool(work_dir=work_dir)

            async def stop_pool() -> None:
                await pool.stop()
                self.print_success("✅ Agent pool stopped successfully")

            asyncio.run(stop_pool())

            return {
                "success": True,
                "work_dir": work_dir,
                "message": "Agent pool stopped successfully",
            }

        except Exception as e:
            msg = f"Error stopping agents: {e}"
            raise CommandError(msg) from e


class AddTaskCommand(BaseCommand):
    """Add a task to the agent pool queue."""

    def execute(
        self,
        title: str | None = None,
        command: list[str] | None = None,
        work_dir: str | None = None,
        directory: str = ".",
        priority: int = 5,
        complexity: int = 5,
        timeout: int = 300,
        description: str | None = None,
        **kwargs,
    ) -> dict:
        """Execute the add task command."""
        try:
            # Validate required parameters
            if not title:
                msg = "Task title is required"
                raise CommandError(msg)
            if not command:
                msg = "Task command is required"
                raise CommandError(msg)

            pool = AgentPool(work_dir=work_dir)

            task = pool.create_task(
                title=title,
                command=command,
                working_directory=directory,
                description=description or f"Execute: {' '.join(command)}",
                priority=priority,
                complexity=complexity,
                timeout=timeout,
            )

            self.print_success(f"✅ Task added: {task.task_id}")
            self.print_info(f"   Title: {task.title}")
            self.print_info(f"   Command: {' '.join(task.command)}")
            self.print_info(f"   Priority: {task.priority}")

            return {
                "success": True,
                "work_dir": work_dir,
                "task_id": task.task_id,
                "title": task.title,
                "command": task.command,
                "priority": task.priority,
            }

        except Exception as e:
            msg = f"Error adding task: {e}"
            raise CommandError(msg) from e


class ListTasksCommand(BaseCommand):
    """List tasks in the agent pool."""

    def execute(self, work_dir: str | None = None, status: str | None = None, **kwargs) -> dict:
        """Execute the list tasks command."""
        try:
            pool = AgentPool(work_dir=work_dir)

            from libs.multi_agent.types import TaskStatus

            filter_status = None
            if status:
                try:
                    filter_status = TaskStatus(status.lower())
                except ValueError as e:
                    msg = f"Invalid status: {status}"
                    raise CommandError(
                        msg,
                        recovery_hint="Valid statuses are: pending, assigned, running, completed, failed, cancelled",
                    ) from e

            tasks = pool.list_tasks(filter_status)

            if not tasks:
                self.print_info("📝 No tasks found")
                return {"success": True, "work_dir": work_dir, "tasks": [], "count": 0}

            self.print_info(f"📋 Tasks ({len(tasks)} found):")
            self.print_info("=" * 80)

            for task in tasks:
                status_icon = {
                    "pending": "⏳",
                    "assigned": "📤",
                    "running": "⚡",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(task.get("status", "unknown"), "❓")

                self.print_info(f"{status_icon} {task['task_id'][:8]}... - {task['title']}")
                self.print_info(f"   Status: {task['status'].upper()}")
                if task.get("assigned_agent"):
                    self.print_info(f"   Agent: {task['assigned_agent']}")
                self.print_info(f"   Command: {' '.join(task['command'])}")
                self.print_info("")

            return {
                "success": True,
                "work_dir": work_dir,
                "tasks": tasks,
                "count": len(tasks),
                "filter_status": status,
            }

        except Exception as e:
            msg = f"Error listing tasks: {e}"
            raise CommandError(msg) from e

# Copyright notice.

import click

from .agent_pool import (
    AddTaskCommand,
    ListTasksCommand,
    MonitorAgentsCommand,
    StartAgentsCommand,
    StatusCommand,
    StopAgentsCommand,
)
from .conflict_resolution import (
    ConflictSummaryCommand,
    DetectConflictsCommand,
    ResolveConflictCommand,
)


@click.group(name="multi-agent")
@click.pass_context
def multi_agent(ctx: click.Context) -> None:
    """Multi-agent system for parallel development automation."""


# Agent Pool Management Commands
@multi_agent.command("start")
@click.option("--max-agents", "-n", default=3, help="Maximum number of agents")
@click.option("--work-dir", "-w", help="Working directory for agents")
@click.option("--monitor", "-m", is_flag=True, help="Start with monitoring dashboard")
def start(max_agents: int, work_dir: str | None, monitor: bool) -> None:  # noqa: FBT001
    """Start the multi-agent pool."""
    command = StartAgentsCommand()
    command.run(max_agents=max_agents, work_dir=work_dir, monitor=monitor)


@multi_agent.command("monitor")
@click.option("--work-dir", "-w", help="Working directory for agents")
@click.option("--duration", "-d", type=float, help="Monitoring duration in seconds")
@click.option("--refresh", "-r", default=1.0, help="Refresh interval in seconds")
def monitor(work_dir: str | None, duration: float | None, refresh: float) -> None:
    """Start real-time agent monitoring dashboard."""
    command = MonitorAgentsCommand()
    command.run(work_dir=work_dir, duration=duration, refresh=refresh)


@multi_agent.command("status")
@click.option("--work-dir", "-w", help="Working directory for agents")
def status(work_dir: str | None) -> None:
    """Show current agent pool status."""
    command = StatusCommand()
    command.run(work_dir=work_dir)


@multi_agent.command("stop")
@click.option("--work-dir", "-w", help="Working directory for agents")
def stop(work_dir: str | None) -> None:
    """Stop the multi-agent pool."""
    command = StopAgentsCommand()
    command.run(work_dir=work_dir)


@multi_agent.command("add-task")
@click.argument("title")
@click.argument("command", nargs=-1, required=True)
@click.option("--work-dir", "-w", help="Working directory for agents")
@click.option("--directory", "-d", default=".", help="Task working directory")
@click.option("--priority", "-p", default=5, help="Task priority (1-10)")
@click.option("--complexity", "-c", default=5, help="Task complexity (1-10)")
@click.option("--timeout", "-t", default=300, help="Task timeout in seconds")
@click.option("--description", help="Task description")
def add_task(title: str, command: tuple[str, ...], work_dir: str | None, directory: str, priority: int, complexity: int, timeout: int, description: str | None) -> None:
    """Add a task to the agent pool queue."""
    command_obj = AddTaskCommand()
    command_obj.run(
        title=title,
        command=list(command),
        work_dir=work_dir,
        directory=directory,
        priority=priority,
        complexity=complexity,
        timeout=timeout,
        description=description,
    )


@multi_agent.command("list-tasks")
@click.option("--work-dir", "-w", help="Working directory for agents")
@click.option("--status", "-s", help="Filter by status")
def list_tasks(work_dir: str | None, status: str | None) -> None:
    """List tasks in the agent pool."""
    command = ListTasksCommand()
    command.run(work_dir=work_dir, status=status)


# Conflict Resolution Commands
@multi_agent.command("detect-conflicts")
@click.argument("branches", nargs=-1, required=True)
@click.option("--repo-path", "-r", help="Repository path")
@click.option("--auto-resolve", is_flag=True, help="Attempt automatic resolution")
def detect_conflicts(branches: str, repo_path: str | None, auto_resolve: bool) -> None:  # noqa: FBT001
    """Detect conflicts between branches."""
    command = DetectConflictsCommand()
    command.run(branches=list(branches), repo_path=repo_path, auto_resolve=auto_resolve)


@multi_agent.command("resolve-conflict")
@click.argument("conflict_id")
@click.option("--strategy", "-s", help="Resolution strategy")
@click.option("--repo-path", "-r", help="Repository path")
def resolve_conflict(conflict_id: str, strategy: str | None, repo_path: str | None) -> None:
    """Resolve a specific conflict."""
    command = ResolveConflictCommand()
    command.run(conflict_id=conflict_id, strategy=strategy, repo_path=repo_path)


@multi_agent.command("conflict-summary")
@click.option("--repo-path", "-r", help="Repository path")
def conflict_summary(repo_path: str | None) -> None:
    """Show conflict resolution summary and statistics."""
    command = ConflictSummaryCommand()
    command.run(repo_path=repo_path)


# Export the main group for registration
__all__ = ["multi_agent"]

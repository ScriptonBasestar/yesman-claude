# Copyright notice.

import asyncio
import contextlib
import json
import logging
import os
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

# Import scheduler types after main types to avoid circular imports
from typing import TYPE_CHECKING, Any

from .branch_test_manager import BranchTestManager
from .recovery_engine import OperationType, RecoveryEngine
from .task_scheduler import AgentCapability, TaskScheduler
from .types import Agent, AgentState, Task, TaskStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Agent pool management for multi-agent development system."""


if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AgentPool:  # noqa: PLR0904
    """Manages a pool of agents for parallel task execution."""

    def __init__(self, max_agents: int = 3, work_dir: str | None = None) -> None:
        """Initialize agent pool.

        Args:
            max_agents: Maximum number of concurrent agents
            work_dir: Directory for agent work and metadata
        """
        self.max_agents = max_agents
        self.work_dir = Path(work_dir) if work_dir else Path.cwd() / ".yesman-agents"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Agent and task management
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self.task_queue: asyncio.Queue[Task] = asyncio.Queue()
        self.completed_tasks: list[str] = []

        # Intelligent task scheduling
        self.scheduler = TaskScheduler()
        self.intelligent_scheduling = True

        # Event callbacks
        self.task_started_callbacks: list[Callable[[Task], Awaitable[None]]] = []
        self.task_completed_callbacks: list[Callable[[Task], Awaitable[None]]] = []
        self.task_failed_callbacks: list[Callable[[Task], Awaitable[None]]] = []
        self.agent_error_callbacks: list[Callable[[Agent, Exception], Awaitable[None]]] = []

        # Control
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Auto-rebalancing
        self._auto_rebalancing_enabled = False
        self._auto_rebalancing_interval = 300

        # Branch testing integration
        self.branch_test_manager = None
        self._test_integration_enabled = False

        # Recovery and rollback system
        self.recovery_engine = None
        self._recovery_enabled = False

        # Load persistent state
        self._load_state()

    def _get_state_file(self) -> Path:
        """Get path to state file."""
        return self.work_dir / "pool_state.json"

    def _load_state(self) -> None:
        """Load agent pool state from disk."""
        state_file = self._get_state_file()

        if state_file.exists():
            try:
                with state_file.open() as f:
                    data = json.load(f)

                # Load agents (without active processes)
                for agent_data in data.get("agents", []):
                    agent = Agent.from_dict(agent_data)
                    # Reset state for loaded agents
                    agent.state = AgentState.IDLE
                    agent.current_task = None
                    agent.process = None
                    self.agents[agent.agent_id] = agent

                # Load tasks
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.task_id] = task

                self.completed_tasks = data.get("completed_tasks", [])

                logger.info(
                    "Loaded %d agents and %d tasks",
                    len(self.agents),
                    len(self.tasks),
                )

            except Exception:
                logger.exception("Failed to load agent pool state:")

    def _save_state(self) -> None:
        """Save agent pool state to disk."""
        state_file = self._get_state_file()

        try:
            data = {
                "agents": [agent.to_dict() for agent in self.agents.values()],
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "completed_tasks": self.completed_tasks,
                "saved_at": datetime.now(UTC).isoformat(),
            }

            with state_file.open("w") as f:
                json.dump(data, f, indent=2)

        except Exception:
            logger.exception("Failed to save agent pool state:")

    async def start(self) -> None:
        """Start the agent pool."""
        if self._running:
            logger.warning("Agent pool is already running")
            return

        self._running = True
        self._shutdown_event.clear()

        logger.info("Starting agent pool with max %d agents", self.max_agents)

        # Start task dispatcher
        asyncio.create_task(self._task_dispatcher())

        # Start agent monitor
        asyncio.create_task(self._agent_monitor())

        # Enable auto-rebalancing by default for pools with multiple agents
        if self.max_agents > 1:
            self.enable_auto_rebalancing()

        logger.info("Agent pool started")

    async def stop(self) -> None:
        """Stop the agent pool."""
        if not self._running:
            return

        logger.info("Stopping agent pool...")
        self._running = False

        # Disable auto-rebalancing
        self._auto_rebalancing_enabled = False

        # Terminate all agents
        for agent in self.agents.values():
            await self._terminate_agent(agent.agent_id)

        # Signal shutdown
        self._shutdown_event.set()

        # Save state
        self._save_state()

        logger.info("Agent pool stopped")

    def add_task(self, task: Task) -> None:
        """Add a task to the queue."""
        self.tasks[task.task_id] = task

        if self.intelligent_scheduling:
            # Add to intelligent scheduler
            self.scheduler.add_task(task)
        else:
            # Add to simple queue (non-blocking)
            try:
                self.task_queue.put_nowait(task)
                logger.info("Added task %s to queue", task.task_id)
            except asyncio.QueueFull:
                logger.exception("Task queue is full, cannot add task %s", task.task_id)

    def create_task(
        self,
        title: str,
        command: list[str],
        working_directory: str,
        description: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> Task:
        """Create and add a task."""
        task = Task(
            task_id=str(uuid.uuid4()),
            title=title,
            description=description,
            command=command,
            working_directory=working_directory,
            **kwargs,
        )

        self.add_task(task)
        return task

    async def _task_dispatcher(self) -> None:
        """Dispatch tasks to available agents."""
        while self._running:
            try:
                if self.intelligent_scheduling:
                    await self._intelligent_dispatch()
                else:
                    await self._simple_dispatch()

                await asyncio.sleep(1)  # Brief pause between dispatch cycles

            except Exception:
                logger.exception("Error in task dispatcher:")
                await asyncio.sleep(1)

    async def _intelligent_dispatch(self) -> None:
        """Intelligent task dispatching using the scheduler."""
        # Get all available agents
        available_agents = [agent for agent in self.agents.values() if agent.state == AgentState.IDLE]

        # Create new agents if needed and under limit
        while len(available_agents) < self.max_agents and len(self.agents) < self.max_agents:
            new_agent = await self._create_agent()
            available_agents.append(new_agent)

        if not available_agents:
            return

        # Get optimal task assignments
        assignments = self.scheduler.get_optimal_task_assignment(available_agents)

        # Execute assignments
        for agent, task in assignments:
            await self._assign_task_to_agent(agent, task)

    async def _simple_dispatch(self) -> None:
        """Simple task dispatching (original logic)."""
        try:
            # Wait for task or shutdown
            task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

            # Find available agent or create new one
            agent = await self._get_available_agent()

            if agent:
                await self._assign_task_to_agent(agent, task)
            else:
                # Put task back in queue
                await self.task_queue.put(task)

        except TimeoutError:
            # No task in queue, continue
            pass

    async def _get_available_agent(self) -> Agent | None:
        """Get an available agent or create a new one."""
        # Look for idle agents
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                return agent

        # Create new agent if under limit
        if len(self.agents) < self.max_agents:
            return await self._create_agent()

        return None

    async def _create_agent(self) -> Agent:
        """Create a new agent."""
        agent_id = f"agent-{len(self.agents) + 1}-{int(time.time())}"

        agent = Agent(agent_id=agent_id)
        self.agents[agent_id] = agent

        # Register with intelligent scheduler
        if self.intelligent_scheduling:
            self.scheduler.register_agent(agent)

        logger.info("Created agent %s", agent_id)
        return agent

    async def _assign_task_to_agent(self, agent: Agent, task: Task) -> None:
        """Assign a task to an agent."""
        # Update task
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent = agent.agent_id

        # Update agent
        agent.state = AgentState.WORKING
        agent.current_task = task.task_id
        agent.last_heartbeat = datetime.now(UTC)

        logger.info("Assigned task %s to agent %s", task.task_id, agent.agent_id)

        # Start task execution
        asyncio.create_task(self._execute_task(agent, task))

    async def _execute_task(self, agent: Agent, task: Task) -> None:
        """Execute a task on an agent."""
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now(UTC)

            # Notify callbacks
            for callback in self.task_started_callbacks:
                try:
                    await callback(task)
                except Exception:
                    logger.exception("Error in task started callback:")

            logger.info("Agent %s starting task %s", agent.agent_id, task.task_id)

            # Prepare environment
            env = os.environ.copy()
            env.update(task.environment)
            env["YESMAN_AGENT_ID"] = agent.agent_id
            env["YESMAN_TASK_ID"] = task.task_id

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *task.command,
                cwd=task.working_directory,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            agent.process = process  # type: ignore[assignment]

            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout,
                )

                # Update task results
                task.output = stdout.decode("utf-8")
                task.error = stderr.decode("utf-8")
                task.exit_code = process.returncode
                task.end_time = datetime.now(UTC)

                if process.returncode == 0:
                    task.status = TaskStatus.COMPLETED
                    agent.completed_tasks += 1
                    self.completed_tasks.append(task.task_id)

                    # Notify completion
                    for callback in self.task_completed_callbacks:
                        try:
                            await callback(task)
                        except Exception:
                            logger.exception("Error in task completed callback:")

                    logger.info("Task %s completed successfully", task.task_id)

                else:
                    task.status = TaskStatus.FAILED
                    agent.failed_tasks += 1

                    # Notify failure
                    for callback in self.task_failed_callbacks:
                        try:
                            await callback(task)
                        except Exception:
                            logger.exception("Error in task failed callback:")

                    logger.error(
                        "Task %s failed with exit code %d",
                        task.task_id,
                        process.returncode,
                    )

            except TimeoutError:
                # Task timed out
                logger.exception(
                    "Task %s timed out after %d seconds",
                    task.task_id,
                    task.timeout,
                )

                # Terminate process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except:
                    # Force kill if terminate doesn't work
                    with contextlib.suppress(Exception):
                        process.kill()

                task.status = TaskStatus.FAILED
                task.error = f"Task timed out after {task.timeout} seconds"
                task.end_time = datetime.now(UTC)
                agent.failed_tasks += 1

            # Update execution time
            if task.start_time and task.end_time:
                execution_time = (task.end_time - task.start_time).total_seconds()
                agent.total_execution_time += execution_time

                # Update scheduler with performance data
                if self.intelligent_scheduling:
                    success = task.status == TaskStatus.COMPLETED
                    self.scheduler.update_agent_performance(
                        agent.agent_id,
                        task,
                        success,
                        execution_time,
                    )

        except Exception as e:
            logger.exception("Error executing task %s:", task.task_id)

            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now(UTC)
            agent.failed_tasks += 1
            agent.state = AgentState.ERROR

            # Notify task failure callbacks
            for callback in self.task_failed_callbacks:
                try:
                    await callback(task)
                except Exception:
                    logger.exception("Error in agent error callback:")

        finally:
            # Reset agent state
            agent.current_task = None
            agent.process = None
            if agent.state != AgentState.ERROR:
                agent.state = AgentState.IDLE

            # Save state
            self._save_state()

    async def _agent_monitor(self) -> None:
        """Monitor agent health and status."""
        while self._running:
            try:
                current_time = datetime.now(UTC)

                for agent in list(self.agents.values()):
                    # Check for stale agents (no heartbeat in 5 minutes)
                    if (current_time - agent.last_heartbeat).total_seconds() > 300:
                        logger.warning(
                            "Agent %s appears stale, terminating",
                            agent.agent_id,
                        )
                        await self._terminate_agent(agent.agent_id)

                    # Update heartbeat for working agents
                    if agent.state == AgentState.WORKING:
                        agent.last_heartbeat = current_time

                # Save state periodically
                self._save_state()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception:
                logger.exception("Error in agent monitor:")
                await asyncio.sleep(30)

    async def _terminate_agent(self, agent_id: str) -> None:
        """Terminate an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return

        # Terminate running process
        if agent.process:
            try:
                agent.process.terminate()
                await asyncio.wait_for(agent.process.wait(), timeout=5.0)  # type: ignore[arg-type]
            except:
                with contextlib.suppress(Exception):
                    agent.process.kill()

        # Update state
        agent.state = AgentState.TERMINATED
        agent.current_task = None
        agent.process = None

        logger.info("Terminated agent %s", agent_id)

    def get_agent_status(self, agent_id: str) -> dict[str, object] | None:
        """Get status of a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return agent.to_dict()

    def get_task_status(self, task_id: str) -> dict[str, object] | None:
        """Get status of a specific task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return task.to_dict()

    def list_agents(self) -> list[dict[str, object]]:
        """List all agents and their status."""
        return [agent.to_dict() for agent in self.agents.values()]

    def list_tasks(self, status: TaskStatus | None = None) -> list[dict[str, object]]:
        """List tasks, optionally filtered by status."""
        tasks = self.tasks.values()

        if status:
            filtered_tasks = [t for t in tasks if t.status == status]
            return [task.to_dict() for task in filtered_tasks]

        return [task.to_dict() for task in tasks]

    def get_pool_statistics(self) -> dict[str, object]:
        """Get pool statistics."""
        active_agents = len(
            [a for a in self.agents.values() if a.state != AgentState.TERMINATED],
        )
        working_agents = len(
            [a for a in self.agents.values() if a.state == AgentState.WORKING],
        )

        total_completed = sum(a.completed_tasks for a in self.agents.values())
        total_failed = sum(a.failed_tasks for a in self.agents.values())
        total_execution_time = sum(a.total_execution_time for a in self.agents.values())

        task_counts = {}
        for status in TaskStatus:
            task_counts[status.value] = len(
                [t for t in self.tasks.values() if t.status == status],
            )

        return {
            "max_agents": self.max_agents,
            "active_agents": active_agents,
            "working_agents": working_agents,
            "idle_agents": active_agents - working_agents,
            "total_tasks": len(self.tasks),
            "completed_tasks": total_completed,
            "failed_tasks": total_failed,
            "total_execution_time": total_execution_time,
            "average_execution_time": total_execution_time / max(total_completed, 1),
            "task_status_counts": task_counts,
            "queue_size": self.task_queue.qsize(),
            "running": self._running,
        }

    # Event callback registration
    def on_task_started(self, callback: Callable[[Task], Awaitable[None]]) -> None:
        """Register callback for task started events."""
        self.task_started_callbacks.append(callback)

    def on_task_completed(self, callback: Callable[[Task], Awaitable[None]]) -> None:
        """Register callback for task completed events."""
        self.task_completed_callbacks.append(callback)

    def on_task_failed(self, callback: Callable[[Task], Awaitable[None]]) -> None:
        """Register callback for task failed events."""
        self.task_failed_callbacks.append(callback)

    def on_agent_error(
        self,
        callback: Callable[[Agent, Exception], Awaitable[None]],
    ) -> None:
        """Register callback for agent error events."""
        self.agent_error_callbacks.append(callback)

    def get_scheduling_metrics(self) -> dict[str, object]:
        """Get intelligent scheduling metrics."""
        if self.intelligent_scheduling:
            return self.scheduler.get_scheduling_metrics()
        return {
            "intelligent_scheduling": False,
            "queue_size": self.task_queue.qsize(),
        }

    def set_intelligent_scheduling(self, enabled: bool) -> None:  # noqa: FBT001
        """Enable or disable intelligent scheduling."""
        self.intelligent_scheduling = enabled

        if enabled:
            # Register existing agents with scheduler
            for agent in self.agents.values():
                self.scheduler.register_agent(agent)

        logger.info("Intelligent scheduling %s", "enabled" if enabled else "disabled")

    def update_agent_capability(
        self,
        agent_id: str,
        capability: "AgentCapability",
    ) -> None:
        """Update an agent's capability profile."""
        if self.intelligent_scheduling and agent_id in self.agents:
            self.scheduler.agent_capabilities[agent_id] = capability
            logger.info("Updated capability for agent %s", agent_id)

    def rebalance_workload(self) -> list[tuple[str, str]]:
        """Trigger workload rebalancing."""
        if self.intelligent_scheduling:
            rebalancing_actions = self.scheduler.rebalance_tasks()

            # Execute rebalancing actions
            for overloaded_agent_id, underloaded_agent_id in rebalancing_actions:
                self._execute_rebalancing(overloaded_agent_id, underloaded_agent_id)

            return rebalancing_actions
        return []

    def _execute_rebalancing(self, from_agent_id: str, to_agent_id: str) -> None:
        """Execute task rebalancing between two agents."""
        try:
            # Update agent loads immediately to prevent over-rebalancing
            from_agent = self.agents.get(from_agent_id)
            to_agent = self.agents.get(to_agent_id)

            if not from_agent or not to_agent:
                logger.warning("Cannot rebalance: agent not found")
                return

            # Update scheduler agent loads
            if self.intelligent_scheduling:
                from_cap = self.scheduler.agent_capabilities.get(from_agent_id)
                to_cap = self.scheduler.agent_capabilities.get(to_agent_id)

                if from_cap and to_cap:
                    # Redistribute load (move 10% from overloaded to underloaded)
                    load_transfer = min(0.1, from_cap.current_load * 0.2)
                    from_cap.current_load = max(0.0, from_cap.current_load - load_transfer)
                    to_cap.current_load = min(1.0, to_cap.current_load + load_transfer)

                    logger.info(
                        "Rebalanced load: %s (%.2f) -> %s (%.2f)",
                        from_agent_id,
                        from_cap.current_load,
                        to_agent_id,
                        to_cap.current_load,
                    )

        except Exception:
            logger.exception("Error executing rebalancing:")

    def enable_auto_rebalancing(self, interval_seconds: int = 300) -> None:
        """Enable automatic workload rebalancing."""
        if not self.intelligent_scheduling:
            logger.warning("Cannot enable auto-rebalancing without intelligent scheduling")
            return

        self._auto_rebalancing_enabled = True
        self._auto_rebalancing_interval = interval_seconds

        # Start auto-rebalancing task
        asyncio.create_task(self._auto_rebalancing_loop())
        logger.info("Auto-rebalancing enabled with %ds interval", interval_seconds)

    async def _auto_rebalancing_loop(self) -> None:
        """Automatic rebalancing loop."""
        while self._running and getattr(self, "_auto_rebalancing_enabled", False):
            try:
                # Check if rebalancing is needed
                metrics = self.scheduler.get_scheduling_metrics()
                load_balancing_score = metrics.get("load_balancing_score", 1.0)

                # Trigger rebalancing if score is below threshold (0.7)
                if load_balancing_score < 0.7:
                    logger.info(
                        "Load balancing score low (%.3f), triggering rebalancing",
                        load_balancing_score,
                    )
                    rebalancing_actions = self.rebalance_workload()

                    if rebalancing_actions:
                        logger.info("Executed %d rebalancing actions", len(rebalancing_actions))

                await asyncio.sleep(getattr(self, "_auto_rebalancing_interval", 300))

            except Exception:
                logger.exception("Error in auto-rebalancing loop:")
                await asyncio.sleep(60)  # Wait before retrying

    def enable_branch_testing(self, repo_path: str | None = None, results_dir: str | None = None) -> None:
        """Enable automatic branch testing integration."""
        try:
            repo_path = repo_path or "."
            results_dir = results_dir or ".scripton/yesman/test_results"

            self.branch_test_manager = BranchTestManager(  # type: ignore[assignment]
                repo_path=repo_path,
                results_dir=results_dir,
                agent_pool=self,
            )

            self._test_integration_enabled = True
            logger.info("Branch testing integration enabled")

        except Exception:
            logger.exception("Failed to enable branch testing:")
            self._test_integration_enabled = False

    def create_test_task(
        self,
        branch_name: str,
        test_suite_name: str | None = None,
        priority: int = 7,
        timeout: int = 600,
    ) -> Task:
        """Create a test task for a specific branch.

        Args:
            branch_name: Name of the branch to test
            test_suite_name: Specific test suite to run (None for all tests)
            priority: Task priority (1-10)
            timeout: Test timeout in seconds

        Returns:
            Task object for test execution
        """
        if not self._test_integration_enabled or not self.branch_test_manager:
            msg = "Branch testing is not enabled"
            raise RuntimeError(msg)

        task_id = f"test-{branch_name}-{test_suite_name or 'all'}-{int(time.time())}"

        # Prepare test command
        if test_suite_name:
            # Run specific test suite
            test_command = [
                "python",
                "-c",
                f"import asyncio; "
                f"from libs.multi_agent.branch_test_manager import BranchTestManager; "
                f"btm = BranchTestManager(); "
                f"result = asyncio.run(btm.run_test_suite('{branch_name}', '{test_suite_name}')); "
                f"print(f'Test {{result.status.value}}: {{result.test_id}}')",
            ]
        else:
            # Run all tests
            test_command = [
                "python",
                "-c",
                f"import asyncio; "
                f"from libs.multi_agent.branch_test_manager import BranchTestManager; "
                f"btm = BranchTestManager(); "
                f"results = asyncio.run(btm.run_all_tests('{branch_name}')); "
                f"print(f'Completed {{len(results)}} tests on {branch_name}')",
            ]

        return Task(
            task_id=task_id,
            title=f"Test {test_suite_name or 'All'} on {branch_name}",
            description=f"Execute {'specific' if test_suite_name else 'all'} tests on branch {branch_name}",
            command=test_command,
            working_directory=".",
            timeout=timeout,
            priority=priority,
            complexity=6,  # Medium complexity
            metadata={
                "type": "test",
                "branch": branch_name,
                "test_suite": test_suite_name,
                "auto_generated": True,
            },
        )

    async def auto_test_branch(self, branch_name: str) -> list[str]:
        """Automatically create and schedule test tasks for a branch.

        Args:
            branch_name: Name of the branch to test

        Returns:
            List of created task IDs
        """
        if not self._test_integration_enabled or not self.branch_test_manager:
            logger.warning("Branch testing is not enabled")
            return []

        task_ids = []

        try:
            # Get critical test suites first
            critical_suites = [name for name, suite in self.branch_test_manager.test_suites.items() if suite.critical]

            # Create tasks for critical tests (higher priority)
            for suite_name in critical_suites:
                task = self.create_test_task(
                    branch_name=branch_name,
                    test_suite_name=suite_name,
                    priority=8,  # High priority for critical tests
                )
                self.add_task(task)
                task_ids.append(task.task_id)

            # Create task for non-critical tests (combined)
            non_critical_suites = [name for name, suite in self.branch_test_manager.test_suites.items() if not suite.critical]

            if non_critical_suites:
                # Create a single task for all non-critical tests
                task = self.create_test_task(
                    branch_name=branch_name,
                    test_suite_name=None,  # All remaining tests
                    priority=6,  # Medium priority
                )
                self.add_task(task)
                task_ids.append(task.task_id)

            logger.info("Created %d test tasks for branch %s", len(task_ids), branch_name)

        except Exception:
            logger.exception("Error creating test tasks for %s:", branch_name)

        return task_ids

    def get_branch_test_status(self, branch_name: str) -> dict[str, object]:
        """Get test status summary for a branch."""
        if not self._test_integration_enabled or not self.branch_test_manager:
            return {"error": "Branch testing not enabled"}

        try:
            return self.branch_test_manager.get_branch_test_summary(branch_name)
        except Exception as e:
            logger.exception("Error getting test status for %s:", branch_name)
            return {"error": str(e)}

    def get_all_branch_test_status(self) -> dict[str, dict[str, object]]:
        """Get test status for all active branches."""
        if not self._test_integration_enabled or not self.branch_test_manager:
            return {"error": "Branch testing not enabled"}  # type: ignore[dict-item]

        try:
            return self.branch_test_manager.get_all_branch_summaries()
        except Exception as e:
            logger.exception("Error getting all branch test status:")
            return {"error": str(e)}

    def enable_recovery_system(self, work_dir: str | None = None, max_snapshots: int = 50) -> None:
        """Enable automatic rollback and error recovery system."""
        try:
            work_dir = work_dir or ".scripton/yesman"

            self.recovery_engine = RecoveryEngine(  # type: ignore[assignment]
                work_dir=work_dir,
                max_snapshots=max_snapshots,
            )

            self._recovery_enabled = True

            # Register recovery callbacks
            self._setup_recovery_callbacks()

            logger.info("Recovery and rollback system enabled")

        except Exception:
            logger.exception("Failed to enable recovery system:")
            self._recovery_enabled = False

    def _setup_recovery_callbacks(self) -> None:
        """Setup callbacks for automatic recovery."""
        if not self.recovery_engine:
            return

        # Register task failure callback
        async def handle_task_failure(task: Task) -> None:
            if self._recovery_enabled and self.recovery_engine:
                operation_id = f"task-{task.task_id}"
                context = {
                    "operation_type": "task_execution",
                    "task_id": task.task_id,
                    "agent_id": task.assigned_agent,
                }

                # Create exception from task error
                exception = Exception(task.error or f"Task failed with exit code {task.exit_code}")

                await self.recovery_engine.handle_operation_failure(
                    operation_id=operation_id,
                    exception=exception,
                    context=context,
                    agent_pool=self,
                )

        # Register agent error callback
        async def handle_agent_error(agent: Agent, exception: Exception) -> None:
            if self._recovery_enabled and self.recovery_engine:
                operation_id = f"agent-{agent.agent_id}-{int(time.time())}"
                context = {
                    "operation_type": "agent_operation",
                    "agent_id": agent.agent_id,
                    "task_id": agent.current_task,
                }

                await self.recovery_engine.handle_operation_failure(
                    operation_id=operation_id,
                    exception=exception,
                    context=context,
                    agent_pool=self,
                )

        # Add callbacks
        self.on_task_failed(handle_task_failure)
        self.on_agent_error(handle_agent_error)

    async def create_operation_snapshot(
        self,
        operation_type: str,
        description: str,
        files_to_backup: list[str] | None = None,
        context: dict[str, object] | None = None,
    ) -> str | None:
        """Create a snapshot before a critical operation.

        Args:
            operation_type: Type of operation (for recovery strategy selection)
            description: Human-readable description of the operation
            files_to_backup: List of files to backup before the operation
            context: Additional context for the operation

        Returns:
            Snapshot ID if successful, None otherwise
        """
        if not self._recovery_enabled or not self.recovery_engine:
            logger.warning("Recovery system not enabled, cannot create snapshot")
            return None

        try:
            # Map string to enum
            op_type_map = {
                "task_execution": OperationType.TASK_EXECUTION,
                "branch_operation": OperationType.BRANCH_OPERATION,
                "agent_assignment": OperationType.AGENT_ASSIGNMENT,
                "file_modification": OperationType.FILE_MODIFICATION,
                "system_config": OperationType.SYSTEM_CONFIG,
                "test_execution": OperationType.TEST_EXECUTION,
            }

            op_type = op_type_map.get(operation_type, OperationType.TASK_EXECUTION)

            return await self.recovery_engine.create_snapshot(
                operation_type=op_type,
                description=description,
                agent_pool=self,
                branch_manager=getattr(self, "branch_manager", None),
                files_to_backup=files_to_backup,
                operation_context=context,
            )

        except Exception:
            logger.exception("Failed to create operation snapshot:")
            return None

    async def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """Manually rollback to a specific snapshot.

        Args:
            snapshot_id: ID of the snapshot to rollback to

        Returns:
            True if rollback successful, False otherwise
        """
        if not self._recovery_enabled or not self.recovery_engine:
            logger.error("Recovery system not enabled")
            return False

        try:
            success = await self.recovery_engine.manual_rollback(
                snapshot_id=snapshot_id,
                agent_pool=self,
                branch_manager=getattr(self, "branch_manager", None),
            )

            if success:
                logger.info("Successfully rolled back to snapshot %s", snapshot_id)
            else:
                logger.error("Failed to rollback to snapshot %s", snapshot_id)

            return success

        except Exception:
            logger.exception("Error during rollback to snapshot %s:", snapshot_id)
            return False

    def get_recovery_status(self) -> dict[str, object]:
        """Get status and metrics of the recovery system."""
        if not self._recovery_enabled or not self.recovery_engine:
            return {"recovery_enabled": False}

        try:
            metrics = self.recovery_engine.get_recovery_metrics()
            recent_operations = self.recovery_engine.get_recent_operations(10)

            return {
                "recovery_enabled": True,
                "metrics": metrics,
                "recent_operations": recent_operations,
                "active_operations": len(self.recovery_engine.active_operations),
            }

        except Exception as e:
            logger.exception("Error getting recovery status:")
            return {"recovery_enabled": True, "error": str(e)}

    def list_recovery_snapshots(self) -> list[dict[str, object]]:
        """List available recovery snapshots."""
        if not self._recovery_enabled or not self.recovery_engine:
            return []

        try:
            snapshots = []
            for snapshot_id, snapshot in self.recovery_engine.snapshots.items():
                snapshots.append(
                    {
                        "snapshot_id": snapshot_id,
                        "operation_type": snapshot.operation_type.value,
                        "description": snapshot.description,
                        "timestamp": snapshot.timestamp.isoformat(),
                        "agent_count": len(snapshot.agent_states),
                        "task_count": len(snapshot.task_states),
                        "file_count": len(snapshot.file_states),
                    }
                )

            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda x: x["timestamp"], reverse=True)
            return snapshots

        except Exception:
            logger.exception("Error listing recovery snapshots:")
            return []

    async def execute_with_recovery(
        self,
        operation_func: Callable[[], Awaitable[object]],
        operation_type: str,
        description: str,
        files_to_backup: list[str] | None = None,
        max_retries: int = 3,
        context: dict[str, object] | None = None,
    ) -> tuple[bool, object]:
        """Execute an operation with automatic snapshot and recovery.

        Args:
            operation_func: Async function to execute
            operation_type: Type of operation for recovery strategy
            description: Description of the operation
            files_to_backup: Files to backup before operation
            max_retries: Maximum number of retry attempts
            context: Additional context for recovery

        Returns:
            Tuple of (success, result)
        """
        if not self._recovery_enabled or not self.recovery_engine:
            logger.warning("Recovery system not enabled, executing without protection")
            try:
                result = await operation_func()
                return True, result
            except Exception as e:
                logger.exception("Operation failed without recovery:")
                return False, str(e)

        # Create snapshot before operation
        snapshot_id = await self.create_operation_snapshot(
            operation_type=operation_type,
            description=description,
            files_to_backup=files_to_backup,
            context=context,
        )

        if not snapshot_id:
            logger.warning("Failed to create snapshot, proceeding without recovery protection")

        operation_id = f"op-{int(time.time())}-{str(uuid.uuid4())[:8]}"

        if snapshot_id:
            self.recovery_engine.start_operation(operation_id, snapshot_id)

        retry_count = 0
        while retry_count <= max_retries:
            try:
                # Execute the operation
                result = await operation_func()

                # Mark operation as successful
                if self.recovery_engine:
                    self.recovery_engine.complete_operation(operation_id)

                logger.info("Operation completed successfully: %s", description)
                return True, result

            except Exception as e:
                logger.exception("Operation failed (attempt %d):", retry_count + 1)

                if retry_count < max_retries:
                    # Attempt recovery
                    if self.recovery_engine:
                        recovery_success = await self.recovery_engine.handle_operation_failure(
                            operation_id=operation_id,
                            exception=e,
                            context={
                                **(context or {}),
                                "operation_type": operation_type,
                                "retry_count": retry_count,
                            },
                            agent_pool=self,
                            branch_manager=getattr(self, "branch_manager", None),
                        )

                        if recovery_success:
                            logger.info("Recovery successful, retrying operation")
                            retry_count += 1
                            continue

                    # Simple retry without recovery
                    logger.info(
                        "Retrying operation without recovery (attempt %d)",
                        retry_count + 2,
                    )
                    retry_count += 1
                    await asyncio.sleep(2**retry_count)  # Exponential backoff
                else:
                    # Max retries exceeded
                    logger.exception("Operation failed after %d attempts")
                    return False, str(e)

        return False, "Max retries exceeded"

    def all_tasks_completed(self) -> bool:
        """Check if all tasks have been completed."""
        if not self.tasks:
            return True

        incomplete_tasks = [task for task in self.tasks.values() if task.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED}]
        return len(incomplete_tasks) == 0

    def reset(self) -> None:
        """Reset the agent pool state."""
        # Clear all tasks and completed task list
        self.tasks.clear()
        self.completed_tasks.clear()

        # Clear task queue
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Reset scheduler if using intelligent scheduling
        if hasattr(self.scheduler, "reset"):
            self.scheduler.reset()
        else:
            # Recreate scheduler if reset method doesn't exist

            self.scheduler = TaskScheduler()

        logger.info("Agent pool reset completed")

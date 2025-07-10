"""Agent pool management for multi-agent development system"""

import asyncio
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Awaitable, Set, Tuple
from datetime import datetime
import json
from pathlib import Path
import subprocess
import os
import signal

from .types import Agent, Task, AgentState, TaskStatus

# Import scheduler types after main types to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .task_scheduler import TaskScheduler, AgentCapability

logger = logging.getLogger(__name__)


class AgentPool:
    """Manages a pool of agents for parallel task execution"""

    def __init__(self, max_agents: int = 3, work_dir: Optional[str] = None):
        """
        Initialize agent pool

        Args:
            max_agents: Maximum number of concurrent agents
            work_dir: Directory for agent work and metadata
        """
        self.max_agents = max_agents
        self.work_dir = Path(work_dir) if work_dir else Path.cwd() / ".yesman-agents"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Agent and task management
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.completed_tasks: List[str] = []

        # Intelligent task scheduling - import here to avoid circular import
        from .task_scheduler import TaskScheduler

        self.scheduler = TaskScheduler()
        self.intelligent_scheduling = True

        # Event callbacks
        self.task_started_callbacks: List[Callable[[Task], Awaitable[None]]] = []
        self.task_completed_callbacks: List[Callable[[Task], Awaitable[None]]] = []
        self.task_failed_callbacks: List[Callable[[Task], Awaitable[None]]] = []
        self.agent_error_callbacks: List[
            Callable[[Agent, Exception], Awaitable[None]]
        ] = []

        # Control
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Load persistent state
        self._load_state()

    def _get_state_file(self) -> Path:
        """Get path to state file"""
        return self.work_dir / "pool_state.json"

    def _load_state(self) -> None:
        """Load agent pool state from disk"""
        state_file = self._get_state_file()

        if state_file.exists():
            try:
                with open(state_file, "r") as f:
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
                    f"Loaded {len(self.agents)} agents and {len(self.tasks)} tasks"
                )

            except Exception as e:
                logger.error(f"Failed to load agent pool state: {e}")

    def _save_state(self) -> None:
        """Save agent pool state to disk"""
        state_file = self._get_state_file()

        try:
            data = {
                "agents": [agent.to_dict() for agent in self.agents.values()],
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "completed_tasks": self.completed_tasks,
                "saved_at": datetime.now().isoformat(),
            }

            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save agent pool state: {e}")

    async def start(self) -> None:
        """Start the agent pool"""
        if self._running:
            logger.warning("Agent pool is already running")
            return

        self._running = True
        self._shutdown_event.clear()

        logger.info(f"Starting agent pool with max {self.max_agents} agents")

        # Start task dispatcher
        asyncio.create_task(self._task_dispatcher())

        # Start agent monitor
        asyncio.create_task(self._agent_monitor())

        logger.info("Agent pool started")

    async def stop(self) -> None:
        """Stop the agent pool"""
        if not self._running:
            return

        logger.info("Stopping agent pool...")
        self._running = False

        # Terminate all agents
        for agent in self.agents.values():
            await self._terminate_agent(agent.agent_id)

        # Signal shutdown
        self._shutdown_event.set()

        # Save state
        self._save_state()

        logger.info("Agent pool stopped")

    def add_task(self, task: Task) -> None:
        """Add a task to the queue"""
        self.tasks[task.task_id] = task

        if self.intelligent_scheduling:
            # Add to intelligent scheduler
            self.scheduler.add_task(task)
        else:
            # Add to simple queue (non-blocking)
            try:
                self.task_queue.put_nowait(task)
                logger.info(f"Added task {task.task_id} to queue")
            except asyncio.QueueFull:
                logger.error(f"Task queue is full, cannot add task {task.task_id}")

    def create_task(
        self,
        title: str,
        command: List[str],
        working_directory: str,
        description: str = "",
        **kwargs,
    ) -> Task:
        """Create and add a task"""
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
        """Dispatch tasks to available agents"""
        while self._running:
            try:
                if self.intelligent_scheduling:
                    await self._intelligent_dispatch()
                else:
                    await self._simple_dispatch()

                await asyncio.sleep(1)  # Brief pause between dispatch cycles

            except Exception as e:
                logger.error(f"Error in task dispatcher: {e}")
                await asyncio.sleep(1)

    async def _intelligent_dispatch(self) -> None:
        """Intelligent task dispatching using the scheduler"""
        # Get all available agents
        available_agents = [
            agent for agent in self.agents.values() if agent.state == AgentState.IDLE
        ]

        # Create new agents if needed and under limit
        while (
            len(available_agents) < self.max_agents
            and len(self.agents) < self.max_agents
        ):
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
        """Simple task dispatching (original logic)"""
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

        except asyncio.TimeoutError:
            # No task in queue, continue
            pass

    async def _get_available_agent(self) -> Optional[Agent]:
        """Get an available agent or create a new one"""
        # Look for idle agents
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                return agent

        # Create new agent if under limit
        if len(self.agents) < self.max_agents:
            return await self._create_agent()

        return None

    async def _create_agent(self) -> Agent:
        """Create a new agent"""
        agent_id = f"agent-{len(self.agents) + 1}-{int(time.time())}"

        agent = Agent(agent_id=agent_id)
        self.agents[agent_id] = agent

        # Register with intelligent scheduler
        if self.intelligent_scheduling:
            self.scheduler.register_agent(agent)

        logger.info(f"Created agent {agent_id}")
        return agent

    async def _assign_task_to_agent(self, agent: Agent, task: Task) -> None:
        """Assign a task to an agent"""
        # Update task
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent = agent.agent_id

        # Update agent
        agent.state = AgentState.WORKING
        agent.current_task = task.task_id
        agent.last_heartbeat = datetime.now()

        logger.info(f"Assigned task {task.task_id} to agent {agent.agent_id}")

        # Start task execution
        asyncio.create_task(self._execute_task(agent, task))

    async def _execute_task(self, agent: Agent, task: Task) -> None:
        """Execute a task on an agent"""
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()

            # Notify callbacks
            for callback in self.task_started_callbacks:
                try:
                    await callback(task)
                except Exception as e:
                    logger.error(f"Error in task started callback: {e}")

            logger.info(f"Agent {agent.agent_id} starting task {task.task_id}")

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

            agent.process = process

            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=task.timeout
                )

                # Update task results
                task.output = stdout.decode("utf-8")
                task.error = stderr.decode("utf-8")
                task.exit_code = process.returncode
                task.end_time = datetime.now()

                if process.returncode == 0:
                    task.status = TaskStatus.COMPLETED
                    agent.completed_tasks += 1
                    self.completed_tasks.append(task.task_id)

                    # Notify completion
                    for callback in self.task_completed_callbacks:
                        try:
                            await callback(task)
                        except Exception as e:
                            logger.error(f"Error in task completed callback: {e}")

                    logger.info(f"Task {task.task_id} completed successfully")

                else:
                    task.status = TaskStatus.FAILED
                    agent.failed_tasks += 1

                    # Notify failure
                    for callback in self.task_failed_callbacks:
                        try:
                            await callback(task)
                        except Exception as e:
                            logger.error(f"Error in task failed callback: {e}")

                    logger.error(
                        f"Task {task.task_id} failed with exit code {process.returncode}"
                    )

            except asyncio.TimeoutError:
                # Task timed out
                logger.error(
                    f"Task {task.task_id} timed out after {task.timeout} seconds"
                )

                # Terminate process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except:
                    # Force kill if terminate doesn't work
                    try:
                        process.kill()
                    except:
                        pass

                task.status = TaskStatus.FAILED
                task.error = f"Task timed out after {task.timeout} seconds"
                task.end_time = datetime.now()
                agent.failed_tasks += 1

            # Update execution time
            if task.start_time and task.end_time:
                execution_time = (task.end_time - task.start_time).total_seconds()
                agent.total_execution_time += execution_time

                # Update scheduler with performance data
                if self.intelligent_scheduling:
                    success = task.status == TaskStatus.COMPLETED
                    self.scheduler.update_agent_performance(
                        agent.agent_id, task, success, execution_time
                    )

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")

            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            agent.failed_tasks += 1
            agent.state = AgentState.ERROR

            # Notify error callbacks
            for callback in self.agent_error_callbacks:
                try:
                    await callback(agent, e)
                except Exception as cb_error:
                    logger.error(f"Error in agent error callback: {cb_error}")

        finally:
            # Reset agent state
            agent.current_task = None
            agent.process = None
            if agent.state != AgentState.ERROR:
                agent.state = AgentState.IDLE

            # Save state
            self._save_state()

    async def _agent_monitor(self) -> None:
        """Monitor agent health and status"""
        while self._running:
            try:
                current_time = datetime.now()

                for agent in list(self.agents.values()):
                    # Check for stale agents (no heartbeat in 5 minutes)
                    if (current_time - agent.last_heartbeat).total_seconds() > 300:
                        logger.warning(
                            f"Agent {agent.agent_id} appears stale, terminating"
                        )
                        await self._terminate_agent(agent.agent_id)

                    # Update heartbeat for working agents
                    if agent.state == AgentState.WORKING:
                        agent.last_heartbeat = current_time

                # Save state periodically
                self._save_state()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in agent monitor: {e}")
                await asyncio.sleep(30)

    async def _terminate_agent(self, agent_id: str) -> None:
        """Terminate an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return

        # Terminate running process
        if agent.process:
            try:
                agent.process.terminate()
                await asyncio.wait_for(agent.process.wait(), timeout=5)
            except:
                try:
                    agent.process.kill()
                except:
                    pass

        # Update state
        agent.state = AgentState.TERMINATED
        agent.current_task = None
        agent.process = None

        logger.info(f"Terminated agent {agent_id}")

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return agent.to_dict()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return task.to_dict()

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents and their status"""
        return [agent.to_dict() for agent in self.agents.values()]

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """List tasks, optionally filtered by status"""
        tasks = self.tasks.values()

        if status:
            tasks = [t for t in tasks if t.status == status]

        return [task.to_dict() for task in tasks]

    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get pool statistics"""
        active_agents = len(
            [a for a in self.agents.values() if a.state != AgentState.TERMINATED]
        )
        working_agents = len(
            [a for a in self.agents.values() if a.state == AgentState.WORKING]
        )

        total_completed = sum(a.completed_tasks for a in self.agents.values())
        total_failed = sum(a.failed_tasks for a in self.agents.values())
        total_execution_time = sum(a.total_execution_time for a in self.agents.values())

        task_counts = {}
        for status in TaskStatus:
            task_counts[status.value] = len(
                [t for t in self.tasks.values() if t.status == status]
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
        """Register callback for task started events"""
        self.task_started_callbacks.append(callback)

    def on_task_completed(self, callback: Callable[[Task], Awaitable[None]]) -> None:
        """Register callback for task completed events"""
        self.task_completed_callbacks.append(callback)

    def on_task_failed(self, callback: Callable[[Task], Awaitable[None]]) -> None:
        """Register callback for task failed events"""
        self.task_failed_callbacks.append(callback)

    def on_agent_error(
        self, callback: Callable[[Agent, Exception], Awaitable[None]]
    ) -> None:
        """Register callback for agent error events"""
        self.agent_error_callbacks.append(callback)

    def get_scheduling_metrics(self) -> Dict[str, Any]:
        """Get intelligent scheduling metrics"""
        if self.intelligent_scheduling:
            return self.scheduler.get_scheduling_metrics()
        else:
            return {
                "intelligent_scheduling": False,
                "queue_size": self.task_queue.qsize(),
            }

    def set_intelligent_scheduling(self, enabled: bool) -> None:
        """Enable or disable intelligent scheduling"""
        self.intelligent_scheduling = enabled

        if enabled:
            # Register existing agents with scheduler
            for agent in self.agents.values():
                self.scheduler.register_agent(agent)

        logger.info(f"Intelligent scheduling {'enabled' if enabled else 'disabled'}")

    def update_agent_capability(
        self, agent_id: str, capability: "AgentCapability"
    ) -> None:
        """Update an agent's capability profile"""
        if self.intelligent_scheduling and agent_id in self.agents:
            self.scheduler.agent_capabilities[agent_id] = capability
            logger.info(f"Updated capability for agent {agent_id}")

    def rebalance_workload(self) -> List[Tuple[str, str]]:
        """Trigger workload rebalancing"""
        if self.intelligent_scheduling:
            return self.scheduler.rebalance_tasks()
        return []

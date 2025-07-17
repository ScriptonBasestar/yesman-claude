"""Tests for AgentPool class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.types import Agent, AgentState, Task, TaskStatus


class TestAgentPool:
    """Test cases for AgentPool."""

    @pytest.fixture
    def work_dir(self, tmp_path):
        """Create temporary work directory."""
        work_path = tmp_path / "agent_work"
        work_path.mkdir()
        return work_path

    @pytest.fixture
    def agent_pool(self, work_dir):
        """Create AgentPool instance."""
        return AgentPool(max_agents=2, work_dir=str(work_dir))

    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        return Task(
            task_id="test-task-1",
            title="Test Task",
            description="A test task",
            command=["echo", "Hello World"],
            working_directory="/tmp",
            timeout=30,
        )

    def test_init(self, agent_pool, work_dir):
        """Test AgentPool initialization."""
        assert agent_pool.max_agents == 2
        assert agent_pool.work_dir == work_dir
        assert agent_pool.agents == {}
        assert agent_pool.tasks == {}
        assert not agent_pool._running
        assert work_dir.exists()

    def test_add_task(self, agent_pool, sample_task):
        """Test adding a task to the pool."""
        agent_pool.add_task(sample_task)

        assert sample_task.task_id in agent_pool.tasks
        assert agent_pool.tasks[sample_task.task_id] == sample_task
        assert agent_pool.task_queue.qsize() == 1

    def test_create_task(self, agent_pool):
        """Test creating and adding a task."""
        task = agent_pool.create_task(
            title="New Task",
            command=["ls", "-la"],
            working_directory="/tmp",
            description="List files",
        )

        assert task.title == "New Task"
        assert task.command == ["ls", "-la"]
        assert task.working_directory == "/tmp"
        assert task.description == "List files"
        assert task.task_id in agent_pool.tasks

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_pool):
        """Test creating a new agent."""
        agent = await agent_pool._create_agent()

        assert agent.agent_id.startswith("agent-")
        assert agent.state == AgentState.IDLE
        assert agent.current_task is None
        assert agent.agent_id in agent_pool.agents

    @pytest.mark.asyncio
    async def test_get_available_agent(self, agent_pool):
        """Test getting available agent."""
        # No agents initially
        agent = await agent_pool._get_available_agent()
        assert agent is not None  # Should create new agent
        assert len(agent_pool.agents) == 1

        # Agent should be available
        same_agent = await agent_pool._get_available_agent()
        assert same_agent == agent

        # Make agent busy
        agent.state = AgentState.WORKING

        # Should create new agent
        new_agent = await agent_pool._get_available_agent()
        assert new_agent != agent
        assert len(agent_pool.agents) == 2

        # Both agents busy, at max capacity
        new_agent.state = AgentState.WORKING
        no_agent = await agent_pool._get_available_agent()
        assert no_agent is None

    @pytest.mark.asyncio
    async def test_assign_task_to_agent(self, agent_pool, sample_task):
        """Test assigning a task to an agent."""
        agent = await agent_pool._create_agent()

        await agent_pool._assign_task_to_agent(agent, sample_task)

        # Check task state
        assert sample_task.status == TaskStatus.ASSIGNED
        assert sample_task.assigned_agent == agent.agent_id

        # Check agent state
        assert agent.state == AgentState.WORKING
        assert agent.current_task == sample_task.task_id

    @pytest.mark.asyncio
    async def test_execute_task_success(self, agent_pool):
        """Test successful task execution."""
        agent = await agent_pool._create_agent()
        task = Task(
            task_id="success-task",
            title="Success Task",
            description="Should succeed",
            command=["echo", "success"],
            working_directory="/tmp",
        )

        # Mock callbacks
        started_callback = AsyncMock()
        completed_callback = AsyncMock()
        agent_pool.on_task_started(started_callback)
        agent_pool.on_task_completed(completed_callback)

        await agent_pool._execute_task(agent, task)

        # Check task completion
        assert task.status == TaskStatus.COMPLETED
        assert task.exit_code == 0
        assert "success" in task.output
        assert task.start_time is not None
        assert task.end_time is not None

        # Check agent state
        assert agent.state == AgentState.IDLE
        assert agent.current_task is None
        assert agent.completed_tasks == 1
        assert agent.failed_tasks == 0

        # Check callbacks
        started_callback.assert_called_once_with(task)
        completed_callback.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_execute_task_failure(self, agent_pool):
        """Test failed task execution."""
        agent = await agent_pool._create_agent()
        task = Task(
            task_id="fail-task",
            title="Fail Task",
            description="Should fail",
            command=["false"],  # Command that always fails
            working_directory="/tmp",
        )

        # Mock callbacks
        failed_callback = AsyncMock()
        agent_pool.on_task_failed(failed_callback)

        await agent_pool._execute_task(agent, task)

        # Check task failure
        assert task.status == TaskStatus.FAILED
        assert task.exit_code != 0

        # Check agent state
        assert agent.state == AgentState.IDLE
        assert agent.current_task is None
        assert agent.completed_tasks == 0
        assert agent.failed_tasks == 1

        # Check callback
        failed_callback.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self, agent_pool):
        """Test task timeout handling."""
        agent = await agent_pool._create_agent()
        task = Task(
            task_id="timeout-task",
            title="Timeout Task",
            description="Should timeout",
            command=["sleep", "10"],  # Long running command
            working_directory="/tmp",
            timeout=1,  # 1 second timeout
        )

        await agent_pool._execute_task(agent, task)

        # Check task timeout
        assert task.status == TaskStatus.FAILED
        assert "timed out" in task.error

        # Check agent state
        assert agent.state == AgentState.IDLE
        assert agent.failed_tasks == 1

    @pytest.mark.asyncio
    async def test_terminate_agent(self, agent_pool):
        """Test agent termination."""
        agent = await agent_pool._create_agent()

        # Mock process
        mock_process = MagicMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()
        agent.process = mock_process

        await agent_pool._terminate_agent(agent.agent_id)

        assert agent.state == AgentState.TERMINATED
        assert agent.current_task is None
        assert agent.process is None
        mock_process.terminate.assert_called_once()

    def test_get_agent_status(self, agent_pool):
        """Test getting agent status."""
        # Non-existent agent
        status = agent_pool.get_agent_status("non-existent")
        assert status is None

        # Create agent
        agent = Agent(agent_id="test-agent")
        agent_pool.agents["test-agent"] = agent

        status = agent_pool.get_agent_status("test-agent")
        assert status is not None
        assert status["agent_id"] == "test-agent"
        assert status["state"] == AgentState.IDLE.value

    def test_get_task_status(self, agent_pool, sample_task):
        """Test getting task status."""
        # Non-existent task
        status = agent_pool.get_task_status("non-existent")
        assert status is None

        # Add task
        agent_pool.tasks[sample_task.task_id] = sample_task

        status = agent_pool.get_task_status(sample_task.task_id)
        assert status is not None
        assert status["task_id"] == sample_task.task_id
        assert status["status"] == TaskStatus.PENDING.value

    def test_list_agents(self, agent_pool):
        """Test listing agents."""
        # Empty list initially
        agents = agent_pool.list_agents()
        assert agents == []

        # Add agents
        agent1 = Agent(agent_id="agent-1")
        agent2 = Agent(agent_id="agent-2")
        agent_pool.agents["agent-1"] = agent1
        agent_pool.agents["agent-2"] = agent2

        agents = agent_pool.list_agents()
        assert len(agents) == 2
        assert any(a["agent_id"] == "agent-1" for a in agents)
        assert any(a["agent_id"] == "agent-2" for a in agents)

    def test_list_tasks(self, agent_pool):
        """Test listing tasks."""
        # Empty list initially
        tasks = agent_pool.list_tasks()
        assert tasks == []

        # Add tasks
        task1 = Task(
            task_id="task-1",
            title="Task 1",
            command=["echo"],
            working_directory="/tmp",
        )
        task2 = Task(
            task_id="task-2",
            title="Task 2",
            command=["echo"],
            working_directory="/tmp",
            status=TaskStatus.COMPLETED,
        )
        agent_pool.tasks["task-1"] = task1
        agent_pool.tasks["task-2"] = task2

        # List all tasks
        all_tasks = agent_pool.list_tasks()
        assert len(all_tasks) == 2

        # Filter by status
        pending_tasks = agent_pool.list_tasks(TaskStatus.PENDING)
        assert len(pending_tasks) == 1
        assert pending_tasks[0]["task_id"] == "task-1"

        completed_tasks = agent_pool.list_tasks(TaskStatus.COMPLETED)
        assert len(completed_tasks) == 1
        assert completed_tasks[0]["task_id"] == "task-2"

    def test_get_pool_statistics(self, agent_pool):
        """Test getting pool statistics."""
        stats = agent_pool.get_pool_statistics()

        assert stats["max_agents"] == 2
        assert stats["active_agents"] == 0
        assert stats["working_agents"] == 0
        assert stats["total_tasks"] == 0
        assert stats["running"] is False

        # Add some data
        agent = Agent(agent_id="test-agent", completed_tasks=5, failed_tasks=2)
        agent_pool.agents["test-agent"] = agent

        task = Task(
            task_id="test-task",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
        )
        agent_pool.tasks["test-task"] = task

        stats = agent_pool.get_pool_statistics()
        assert stats["active_agents"] == 1
        assert stats["total_tasks"] == 1
        assert stats["completed_tasks"] == 5
        assert stats["failed_tasks"] == 2

    def test_state_persistence(self, agent_pool, work_dir):
        """Test saving and loading state."""
        # Add some data
        agent = Agent(agent_id="test-agent", completed_tasks=3)
        agent_pool.agents["test-agent"] = agent

        task = Task(
            task_id="test-task",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
        )
        agent_pool.tasks["test-task"] = task
        agent_pool.completed_tasks = ["completed-1", "completed-2"]

        # Save state
        agent_pool._save_state()

        # Create new pool and load
        new_pool = AgentPool(max_agents=2, work_dir=str(work_dir))

        assert len(new_pool.agents) == 1
        assert "test-agent" in new_pool.agents
        assert new_pool.agents["test-agent"].completed_tasks == 3

        assert len(new_pool.tasks) == 1
        assert "test-task" in new_pool.tasks

        assert len(new_pool.completed_tasks) == 2
        assert "completed-1" in new_pool.completed_tasks

    def test_task_serialization(self):
        """Test task to/from dict conversion."""
        task = Task(
            task_id="test",
            title="Test Task",
            command=["echo", "test"],
            working_directory="/tmp",
            status=TaskStatus.RUNNING,
            start_time=datetime.now(),
            metadata={"key": "value"},
        )

        # To dict
        data = task.to_dict()
        assert data["task_id"] == "test"
        assert data["status"] == "running"
        assert "start_time" in data

        # From dict
        task2 = Task.from_dict(data)
        assert task2.task_id == task.task_id
        assert task2.status == task.status
        assert task2.metadata == task.metadata

    def test_agent_serialization(self):
        """Test agent to/from dict conversion."""
        agent = Agent(
            agent_id="test-agent",
            state=AgentState.WORKING,
            completed_tasks=5,
            metadata={"key": "value"},
        )

        # To dict
        data = agent.to_dict()
        assert data["agent_id"] == "test-agent"
        assert data["state"] == "working"
        assert data["completed_tasks"] == 5
        assert "process" not in data  # Should be excluded

        # From dict
        agent2 = Agent.from_dict(data)
        assert agent2.agent_id == agent.agent_id
        assert agent2.state == agent.state
        assert agent2.completed_tasks == agent.completed_tasks

    def test_event_callbacks(self, agent_pool):
        """Test event callback registration."""
        task_started_cb = AsyncMock()
        task_completed_cb = AsyncMock()
        task_failed_cb = AsyncMock()
        agent_error_cb = AsyncMock()

        agent_pool.on_task_started(task_started_cb)
        agent_pool.on_task_completed(task_completed_cb)
        agent_pool.on_task_failed(task_failed_cb)
        agent_pool.on_agent_error(agent_error_cb)

        assert task_started_cb in agent_pool.task_started_callbacks
        assert task_completed_cb in agent_pool.task_completed_callbacks
        assert task_failed_cb in agent_pool.task_failed_callbacks
        assert agent_error_cb in agent_pool.agent_error_callbacks

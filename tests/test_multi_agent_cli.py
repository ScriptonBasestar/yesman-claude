"""Tests for multi-agent CLI commands."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from commands.multi_agent import multi_agent_cli


class TestMultiAgentCLI:
    """Test cases for multi-agent CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_agent_pool(self):
        """Create mock agent pool."""
        pool = Mock()
        pool._running = True
        pool.start = AsyncMock()
        pool.stop = AsyncMock()
        pool._load_state = Mock()
        pool.get_pool_statistics.return_value = {
            "active_agents": 2,
            "idle_agents": 1,
            "completed_tasks": 10,
            "failed_tasks": 2,
            "queue_size": 3,
            "average_execution_time": 45.5,
        }
        pool.list_agents.return_value = [
            {
                "agent_id": "agent-1",
                "state": "working",
                "completed_tasks": 5,
                "failed_tasks": 1,
            },
            {
                "agent_id": "agent-2",
                "state": "idle",
                "completed_tasks": 3,
                "failed_tasks": 0,
            },
        ]
        pool.list_tasks.return_value = [
            {
                "task_id": "task-123",
                "title": "Test Task",
                "status": "running",
                "command": ["echo", "test"],
                "assigned_agent": "agent-1",
            },
        ]

        # Mock task creation
        mock_task = Mock()
        mock_task.task_id = "new-task-456"
        mock_task.title = "New Task"
        mock_task.command = ["ls", "-la"]
        mock_task.priority = 5
        pool.create_task.return_value = mock_task

        return pool

    def test_multi_agent_cli_help(self, runner):
        """Test multi-agent CLI help."""
        result = runner.invoke(multi_agent_cli, ["--help"])

        assert result.exit_code == 0
        assert "Multi-agent system" in result.output
        assert "start" in result.output
        assert "monitor" in result.output
        assert "status" in result.output

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.asyncio.run")
    def test_start_agents_basic(
        self,
        mock_asyncio_run,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test basic agent start command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["start"])

        assert result.exit_code == 0
        assert "Starting multi-agent pool" in result.output
        mock_agent_pool_class.assert_called_once_with(max_agents=3, work_dir=None)
        mock_asyncio_run.assert_called_once()

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.asyncio.run")
    def test_start_agents_with_options(
        self,
        mock_asyncio_run,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test agent start with options."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(
            multi_agent_cli,
            ["start", "--max-agents", "5", "--work-dir", "/tmp/test"],
        )

        assert result.exit_code == 0
        mock_agent_pool_class.assert_called_once_with(
            max_agents=5,
            work_dir="/tmp/test",
        )

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.run_agent_monitor")
    @patch("commands.multi_agent.asyncio.run")
    def test_start_agents_with_monitor(
        self,
        mock_asyncio_run,
        mock_run_monitor,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test agent start with monitoring."""
        mock_agent_pool_class.return_value = mock_agent_pool
        mock_run_monitor.return_value = AsyncMock()

        result = runner.invoke(multi_agent_cli, ["start", "--monitor"])

        assert result.exit_code == 0
        assert "Starting monitoring dashboard" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_status_command(self, mock_agent_pool_class, runner, mock_agent_pool):
        """Test status command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["status"])

        assert result.exit_code == 0
        assert "Multi-Agent Pool Status" in result.output
        assert "Total Agents: 2" in result.output
        assert "Active Agents: 2" in result.output
        assert "Completed Tasks: 10" in result.output
        assert "agent-1" in result.output
        assert "agent-2" in result.output

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.asyncio.run")
    def test_stop_command(
        self,
        mock_asyncio_run,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test stop command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["stop"])

        assert result.exit_code == 0
        assert "Stopping multi-agent pool" in result.output
        mock_asyncio_run.assert_called_once()

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.asyncio.run")
    def test_monitor_command(
        self,
        mock_asyncio_run,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test monitor command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["monitor"])

        assert result.exit_code == 0
        assert "Starting agent monitoring dashboard" in result.output
        mock_asyncio_run.assert_called_once()

    @patch("commands.multi_agent.AgentPool")
    @patch("commands.multi_agent.asyncio.run")
    def test_monitor_with_options(
        self,
        mock_asyncio_run,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test monitor command with options."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(
            multi_agent_cli,
            ["monitor", "--duration", "10", "--refresh", "2.0"],
        )

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("commands.multi_agent.AgentPool")
    def test_add_task_command(self, mock_agent_pool_class, runner, mock_agent_pool):
        """Test add-task command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(
            multi_agent_cli,
            [
                "add-task",
                "Test Task",
                "echo",
                "hello",
                "world",
                "--priority",
                "8",
                "--complexity",
                "3",
                "--timeout",
                "120",
            ],
        )

        assert result.exit_code == 0
        assert "Task added: new-task-456" in result.output
        assert "Title: New Task" in result.output
        assert "Priority: 5" in result.output  # From mock task

        # Verify create_task was called with correct parameters
        mock_agent_pool.create_task.assert_called_once()
        call_kwargs = mock_agent_pool.create_task.call_args[1]
        assert call_kwargs["title"] == "Test Task"
        assert call_kwargs["command"] == ["echo", "hello", "world"]
        assert call_kwargs["priority"] == 8
        assert call_kwargs["complexity"] == 3
        assert call_kwargs["timeout"] == 120

    @patch("commands.multi_agent.AgentPool")
    def test_list_tasks_command(self, mock_agent_pool_class, runner, mock_agent_pool):
        """Test list-tasks command."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["list-tasks"])

        assert result.exit_code == 0
        assert "Tasks (1 found)" in result.output
        assert "task-123" in result.output
        assert "Test Task" in result.output
        assert "RUNNING" in result.output
        assert "Agent: agent-1" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_list_tasks_with_status_filter(
        self,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test list-tasks with status filter."""
        mock_agent_pool_class.return_value = mock_agent_pool

        # Mock filtered response
        from libs.multi_agent.types import TaskStatus

        mock_agent_pool.list_tasks.return_value = []  # No running tasks

        result = runner.invoke(multi_agent_cli, ["list-tasks", "--status", "running"])

        assert result.exit_code == 0
        assert "No tasks found" in result.output
        mock_agent_pool.list_tasks.assert_called_once_with(TaskStatus.RUNNING)

    @patch("commands.multi_agent.AgentPool")
    def test_list_tasks_invalid_status(
        self,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test list-tasks with invalid status."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(multi_agent_cli, ["list-tasks", "--status", "invalid"])

        assert result.exit_code == 0
        assert "Invalid status: invalid" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_status_command_exception(self, mock_agent_pool_class, runner):
        """Test status command with exception."""
        mock_agent_pool_class.side_effect = Exception("Test error")

        result = runner.invoke(multi_agent_cli, ["status"])

        assert result.exit_code == 0
        assert "Error getting status: Test error" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_add_task_exception(self, mock_agent_pool_class, runner):
        """Test add-task command with exception."""
        mock_agent_pool_class.side_effect = Exception("Test error")

        result = runner.invoke(multi_agent_cli, ["add-task", "Test", "echo", "test"])

        assert result.exit_code == 0
        assert "Error adding task: Test error" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_list_tasks_exception(self, mock_agent_pool_class, runner):
        """Test list-tasks command with exception."""
        mock_agent_pool_class.side_effect = Exception("Test error")

        result = runner.invoke(multi_agent_cli, ["list-tasks"])

        assert result.exit_code == 0
        assert "Error listing tasks: Test error" in result.output

    def test_add_task_required_arguments(self, runner):
        """Test add-task command missing required arguments."""
        result = runner.invoke(multi_agent_cli, ["add-task", "Test Task"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output

    @patch("commands.multi_agent.AgentPool")
    def test_add_task_with_description(
        self,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test add-task with custom description."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(
            multi_agent_cli,
            [
                "add-task",
                "Test Task",
                "echo",
                "hello",
                "--description",
                "Custom description",
            ],
        )

        assert result.exit_code == 0

        call_kwargs = mock_agent_pool.create_task.call_args[1]
        assert call_kwargs["description"] == "Custom description"

    @patch("commands.multi_agent.AgentPool")
    def test_add_task_default_description(
        self,
        mock_agent_pool_class,
        runner,
        mock_agent_pool,
    ):
        """Test add-task with default description."""
        mock_agent_pool_class.return_value = mock_agent_pool

        result = runner.invoke(
            multi_agent_cli,
            ["add-task", "Test Task", "echo", "hello"],
        )

        assert result.exit_code == 0

        call_kwargs = mock_agent_pool.create_task.call_args[1]
        assert call_kwargs["description"] == "Execute: echo hello"

    @patch("commands.multi_agent.AgentPool")
    def test_monitor_no_active_pool(self, mock_agent_pool_class, runner):
        """Test monitor command when no active pool exists."""
        # Simulate no existing pool directory
        with patch("pathlib.Path.exists", return_value=False):
            result = runner.invoke(
                multi_agent_cli,
                ["monitor", "--work-dir", "/tmp/test"],
            )

            assert result.exit_code == 0
            assert "No active agent pool found" in result.output

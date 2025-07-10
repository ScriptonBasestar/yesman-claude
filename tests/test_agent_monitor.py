"""Tests for AgentMonitor dashboard widget"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from libs.dashboard.widgets.agent_monitor import (
    AgentMonitor,
    AgentMetrics,
    TaskMetrics,
    MonitorDisplayMode,
)
from libs.multi_agent.types import Agent, Task, AgentState, TaskStatus


class TestAgentMetrics:
    """Test cases for AgentMetrics"""

    def test_init(self):
        """Test AgentMetrics initialization"""
        metrics = AgentMetrics(agent_id="test-agent")

        assert metrics.agent_id == "test-agent"
        assert metrics.current_task is None
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.total_execution_time == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.current_load == 0.0

    def test_efficiency_score_no_tasks(self):
        """Test efficiency score with no completed tasks"""
        metrics = AgentMetrics(agent_id="test-agent")

        score = metrics.efficiency_score
        assert score == 0.5  # Default score for new agents

    def test_efficiency_score_with_tasks(self):
        """Test efficiency score calculation with completed tasks"""
        metrics = AgentMetrics(
            agent_id="test-agent", tasks_completed=10, tasks_failed=2, current_load=0.3
        )
        metrics.success_rate = 10 / 12  # 83%

        score = metrics.efficiency_score
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be above default


class TestTaskMetrics:
    """Test cases for TaskMetrics"""

    def test_init(self):
        """Test TaskMetrics initialization"""
        metrics = TaskMetrics(
            task_id="task-1", title="Test Task", status=TaskStatus.PENDING
        )

        assert metrics.task_id == "task-1"
        assert metrics.title == "Test Task"
        assert metrics.status == TaskStatus.PENDING
        assert metrics.assigned_agent is None
        assert metrics.progress == 0.0


class TestAgentMonitor:
    """Test cases for AgentMonitor"""

    @pytest.fixture
    def mock_agent_pool(self):
        """Create mock agent pool"""
        pool = Mock()
        pool.list_agents.return_value = [
            {
                "agent_id": "agent-1",
                "state": "working",
                "current_task": "task-123",
                "completed_tasks": 5,
                "failed_tasks": 1,
                "total_execution_time": 300.0,
            },
            {
                "agent_id": "agent-2",
                "state": "idle",
                "current_task": None,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "total_execution_time": 180.0,
            },
        ]

        pool.list_tasks.return_value = [
            {
                "task_id": "task-123",
                "title": "Test Task 1",
                "status": "running",
                "assigned_agent": "agent-1",
                "start_time": datetime.now().isoformat(),
                "timeout": 300,
            },
            {
                "task_id": "task-456",
                "title": "Test Task 2",
                "status": "pending",
                "assigned_agent": None,
                "start_time": None,
                "timeout": 300,
            },
        ]

        pool.get_pool_statistics.return_value = {
            "active_agents": 1,
            "idle_agents": 1,
            "total_tasks": 2,
            "completed_tasks": 8,
            "failed_tasks": 1,
            "queue_size": 1,
        }

        return pool

    @pytest.fixture
    def monitor(self, mock_agent_pool):
        """Create AgentMonitor instance"""
        return AgentMonitor(agent_pool=mock_agent_pool)

    def test_init(self, monitor):
        """Test AgentMonitor initialization"""
        assert monitor.display_mode == MonitorDisplayMode.OVERVIEW
        assert monitor.selected_agent is None
        assert monitor.auto_refresh is True
        assert monitor.refresh_interval == 1.0
        assert monitor.agent_metrics == {}
        assert monitor.task_metrics == {}

    def test_update_metrics(self, monitor, mock_agent_pool):
        """Test metrics update from agent pool"""
        monitor.update_metrics()

        # Check agent metrics were created
        assert len(monitor.agent_metrics) == 2
        assert "agent-1" in monitor.agent_metrics
        assert "agent-2" in monitor.agent_metrics

        # Check agent-1 metrics
        agent1_metrics = monitor.agent_metrics["agent-1"]
        assert agent1_metrics.current_task == "task-123"
        assert agent1_metrics.tasks_completed == 5
        assert agent1_metrics.tasks_failed == 1
        assert agent1_metrics.total_execution_time == 300.0
        assert agent1_metrics.average_execution_time == 60.0  # 300/5
        assert agent1_metrics.success_rate == 5 / 6  # 5/(5+1)

        # Check task metrics were created
        assert len(monitor.task_metrics) == 2
        assert "task-123" in monitor.task_metrics
        assert "task-456" in monitor.task_metrics

        # Check task-123 metrics
        task123_metrics = monitor.task_metrics["task-123"]
        assert task123_metrics.task_id == "task-123"
        assert task123_metrics.title == "Test Task 1"
        assert task123_metrics.status == TaskStatus.RUNNING
        assert task123_metrics.assigned_agent == "agent-1"
        assert task123_metrics.progress > 0.0  # Should have some progress

        # Check system metrics
        assert monitor.system_metrics["total_agents"] == 2
        assert monitor.system_metrics["active_agents"] == 1
        assert monitor.system_metrics["idle_agents"] == 1
        assert monitor.system_metrics["completed_tasks"] == 8

    def test_calculate_task_progress(self, monitor):
        """Test task progress calculation"""
        # Completed task
        completed_task = {"status": "completed"}
        assert monitor._calculate_task_progress(completed_task) == 1.0

        # Failed task
        failed_task = {"status": "failed"}
        assert monitor._calculate_task_progress(failed_task) == 0.0

        # Pending task
        pending_task = {"status": "pending"}
        assert monitor._calculate_task_progress(pending_task) == 0.0

        # Assigned task
        assigned_task = {"status": "assigned"}
        assert monitor._calculate_task_progress(assigned_task) == 0.1

        # Running task with start time
        start_time = (datetime.now() - timedelta(seconds=30)).isoformat()
        running_task = {"status": "running", "start_time": start_time, "timeout": 300}
        progress = monitor._calculate_task_progress(running_task)
        assert 0.0 < progress < 1.0

    def test_render_overview(self, monitor, mock_agent_pool):
        """Test overview rendering"""
        monitor.update_metrics()
        panel = monitor.render_overview()

        assert panel is not None
        assert "Multi-Agent Monitor - Overview" in str(panel)

    def test_render_detailed_no_selection(self, monitor):
        """Test detailed rendering with no agent selected"""
        panel = monitor.render_detailed()

        assert panel is not None
        assert "No agent selected" in str(panel)

    def test_render_detailed_with_selection(self, monitor, mock_agent_pool):
        """Test detailed rendering with agent selected"""
        monitor.update_metrics()
        monitor.select_agent("agent-1")

        panel = monitor.render_detailed()

        assert panel is not None
        assert "Agent Details - agent-1" in str(panel)

    def test_render_tasks(self, monitor, mock_agent_pool):
        """Test task rendering"""
        monitor.update_metrics()
        panel = monitor.render_tasks()

        assert panel is not None
        assert "Task Monitor" in str(panel)

    def test_render_performance(self, monitor, mock_agent_pool):
        """Test performance rendering"""
        monitor.update_metrics()
        panel = monitor.render_performance()

        assert panel is not None
        assert "Performance Analytics" in str(panel)

    def test_set_display_mode(self, monitor):
        """Test display mode changes"""
        monitor.set_display_mode(MonitorDisplayMode.DETAILED)
        assert monitor.display_mode == MonitorDisplayMode.DETAILED

        monitor.set_display_mode(MonitorDisplayMode.TASKS)
        assert monitor.display_mode == MonitorDisplayMode.TASKS

    def test_select_agent(self, monitor, mock_agent_pool):
        """Test agent selection"""
        monitor.update_metrics()
        monitor.select_agent("agent-1")

        assert monitor.selected_agent == "agent-1"
        assert monitor.display_mode == MonitorDisplayMode.DETAILED

    def test_select_invalid_agent(self, monitor):
        """Test selecting non-existent agent"""
        monitor.select_agent("invalid-agent")

        # Should not change selected agent
        assert monitor.selected_agent is None

    def test_keyboard_help(self, monitor):
        """Test keyboard help text"""
        help_text = monitor.get_keyboard_help()

        assert "Keyboard Shortcuts" in help_text
        assert "1,2,3,4" in help_text
        assert "↑↓" in help_text
        assert "Enter" in help_text

    @pytest.mark.asyncio
    async def test_start_monitoring_duration(self, monitor):
        """Test monitoring with duration limit"""
        monitor.auto_refresh = True

        # Mock the update and render methods
        monitor.update_metrics = Mock()
        monitor.render = Mock(return_value="Test render")

        # Run monitoring for short duration
        await monitor.start_monitoring(duration=0.1)

        # Should have called update at least once
        assert monitor.update_metrics.called

    @pytest.mark.asyncio
    async def test_start_monitoring_keyboard_interrupt(self, monitor):
        """Test monitoring stops on keyboard interrupt"""
        monitor.auto_refresh = True

        # Mock methods to raise KeyboardInterrupt
        def mock_update():
            raise KeyboardInterrupt()

        monitor.update_metrics = mock_update
        monitor.render = Mock(return_value="Test render")

        # Should handle KeyboardInterrupt gracefully
        await monitor.start_monitoring()

    def test_update_metrics_no_pool(self, monitor):
        """Test update_metrics with no agent pool"""
        monitor.agent_pool = None

        # Should not raise exception
        monitor.update_metrics()

        # Metrics should remain empty
        assert monitor.agent_metrics == {}
        assert monitor.task_metrics == {}

    def test_update_metrics_exception_handling(self, monitor, mock_agent_pool):
        """Test update_metrics handles exceptions"""
        # Make agent pool raise exception
        mock_agent_pool.list_agents.side_effect = Exception("Test error")

        # Should not raise exception
        monitor.update_metrics()

        # Metrics should remain empty
        assert monitor.agent_metrics == {}

    def test_performance_history_tracking(self, monitor, mock_agent_pool):
        """Test performance history tracking"""
        # Update metrics multiple times
        for _ in range(5):
            monitor.update_metrics()

        # Should have performance history for agents
        assert "agent-1" in monitor.performance_history
        assert "agent-2" in monitor.performance_history

        # Each agent should have 5 data points
        assert len(monitor.performance_history["agent-1"]) == 5
        assert len(monitor.performance_history["agent-2"]) == 5

    def test_performance_history_limit(self, monitor, mock_agent_pool):
        """Test performance history size limiting"""
        # Add more than 100 data points
        agent_id = "agent-1"
        monitor.performance_history[agent_id] = [
            (datetime.now(), 0.5) for _ in range(105)
        ]

        monitor.update_metrics()

        # Should be limited to 100 points
        assert len(monitor.performance_history[agent_id]) == 100


class TestStandaloneFunctions:
    """Test standalone helper functions"""

    def test_create_agent_monitor(self):
        """Test create_agent_monitor function"""
        from libs.dashboard.widgets.agent_monitor import create_agent_monitor

        monitor = create_agent_monitor()
        assert isinstance(monitor, AgentMonitor)
        assert monitor.agent_pool is None

    def test_create_agent_monitor_with_pool(self):
        """Test create_agent_monitor with agent pool"""
        from libs.dashboard.widgets.agent_monitor import create_agent_monitor

        mock_pool = Mock()
        monitor = create_agent_monitor(mock_pool)
        assert isinstance(monitor, AgentMonitor)
        assert monitor.agent_pool == mock_pool

    @pytest.mark.asyncio
    async def test_run_agent_monitor(self):
        """Test run_agent_monitor function"""
        from libs.dashboard.widgets.agent_monitor import run_agent_monitor

        # Mock the monitor to avoid actual UI
        with patch("libs.dashboard.widgets.agent_monitor.AgentMonitor") as MockMonitor:
            mock_monitor = MockMonitor.return_value
            mock_monitor.start_monitoring = AsyncMock()

            await run_agent_monitor(duration=0.1)

            MockMonitor.assert_called_once()
            mock_monitor.start_monitoring.assert_called_once_with(0.1)

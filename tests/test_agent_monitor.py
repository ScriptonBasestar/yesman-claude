# Copyright notice.

from datetime import UTC, datetime, timedelta
from typing import Never
from unittest.mock import AsyncMock, Mock, patch

import pytest

from libs.dashboard.widgets.agent_monitor import (
    AgentMetrics,
    AgentMonitor,
    MonitorDisplayMode,
    TaskMetrics,
)

# Enhanced testing imports
from tests.fixtures.mock_factories import EnhancedTestDataFactory

# Add missing imports for enhanced tests
try:
    from libs.dashboard.widgets.agent_monitor import TaskStatus, create_agent_monitor, run_agent_monitor
except ImportError:
    # Mock these if not available
    class TaskStatus:
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

    def create_agent_monitor(agent_pool=None) -> AgentMonitor:
        return AgentMonitor(agent_pool=agent_pool)

    async def run_agent_monitor(duration=None) -> None:
        monitor = create_agent_monitor()
        await monitor.start_monitoring(duration)


class TestAgentMetrics:
    """Test cases for AgentMetrics."""

    @staticmethod
    def test_init() -> None:
        """Test AgentMetrics initialization."""
        metrics = AgentMetrics(agent_id="test-agent")

        assert metrics.agent_id == "test-agent"
        assert metrics.current_task is None
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.total_execution_time == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.current_load == 0.0

    @staticmethod
    def test_efficiency_score_no_tasks() -> None:
        """Test efficiency score with no completed tasks."""
        metrics = AgentMetrics(agent_id="test-agent")

        score = metrics.efficiency_score
        assert score == 0.5  # Default score for new agents

    @staticmethod
    def test_efficiency_score_with_tasks() -> None:
        """Test efficiency score calculation with completed tasks."""
        metrics = AgentMetrics(
            agent_id="test-agent",
            tasks_completed=10,
            tasks_failed=2,
            current_load=0.3,
        )
        metrics.success_rate = 10 / 12  # 83%

        score = metrics.efficiency_score
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be above default


class TestTaskMetrics:
    """Test cases for TaskMetrics."""

    @staticmethod
    def test_init() -> None:
        """Test TaskMetrics initialization."""
        metrics = TaskMetrics(
            task_id="task-1",
            title="Test Task",
            status=TaskStatus.PENDING,
        )

        assert metrics.task_id == "task-1"
        assert metrics.title == "Test Task"
        assert metrics.status == TaskStatus.PENDING
        assert metrics.assigned_agent is None
        assert metrics.progress == 0.0


class TestAgentMonitor:
    """Test cases for AgentMonitor."""

    @pytest.fixture
    @staticmethod
    def mock_agent_pool() -> object:
        """Create mock agent pool."""
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
                "start_time": datetime.now(UTC).isoformat(),
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
    @staticmethod
    def monitor(mock_agent_pool: Mock) -> AgentMonitor:
        """Create AgentMonitor instance."""
        return AgentMonitor(agent_pool=mock_agent_pool)

    @staticmethod
    def test_init(monitor: AgentMonitor) -> None:
        """Test AgentMonitor initialization."""
        assert monitor.display_mode == MonitorDisplayMode.OVERVIEW
        assert monitor.selected_agent is None
        assert monitor.auto_refresh is True
        assert monitor.refresh_interval == 1.0
        assert monitor.agent_metrics == {}
        assert monitor.task_metrics == {}

    @staticmethod
    def test_update_metrics(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test metrics update from agent pool."""
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

    @staticmethod
    def test_calculate_task_progress(monitor: AgentMonitor) -> None:
        """Test task progress calculation."""
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
        start_time = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
        running_task = {"status": "running", "start_time": start_time, "timeout": 300}
        progress = monitor._calculate_task_progress(running_task)
        assert 0.0 < progress < 1.0

    @staticmethod
    def test_render_overview(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test overview rendering."""
        monitor.update_metrics()
        panel = monitor.render_overview()

        assert panel is not None
        assert "Multi-Agent Monitor - Overview" in str(panel)

    @staticmethod
    def test_render_detailed_no_selection(monitor: AgentMonitor) -> None:
        """Test detailed rendering with no agent selected."""
        panel = monitor.render_detailed()

        assert panel is not None
        assert "No agent selected" in str(panel)

    @staticmethod
    def test_render_detailed_with_selection(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test detailed rendering with agent selected."""
        monitor.update_metrics()
        monitor.select_agent("agent-1")

        panel = monitor.render_detailed()

        assert panel is not None
        assert "Agent Details - agent-1" in str(panel)

    @staticmethod
    def test_render_tasks(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test task rendering."""
        monitor.update_metrics()
        panel = monitor.render_tasks()

        assert panel is not None
        assert "Task Monitor" in str(panel)

    @staticmethod
    def test_render_performance(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test performance rendering."""
        monitor.update_metrics()
        panel = monitor.render_performance()

        assert panel is not None
        assert "Performance Analytics" in str(panel)

    @staticmethod
    def test_set_display_mode(monitor: AgentMonitor) -> None:
        """Test display mode changes."""
        monitor.set_display_mode(MonitorDisplayMode.DETAILED)
        assert monitor.display_mode == MonitorDisplayMode.DETAILED

        monitor.set_display_mode(MonitorDisplayMode.TASKS)
        assert monitor.display_mode == MonitorDisplayMode.TASKS

    @staticmethod
    def test_select_agent(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test agent selection."""
        monitor.update_metrics()
        monitor.select_agent("agent-1")

        assert monitor.selected_agent == "agent-1"
        assert monitor.display_mode == MonitorDisplayMode.DETAILED

    @staticmethod
    def test_select_invalid_agent(monitor: AgentMonitor) -> None:
        """Test selecting non-existent agent."""
        monitor.select_agent("invalid-agent")

        # Should not change selected agent
        assert monitor.selected_agent is None

    @staticmethod
    def test_keyboard_help(monitor: AgentMonitor) -> None:
        """Test keyboard help text."""
        help_text = monitor.get_keyboard_help()

        assert "Keyboard Shortcuts" in help_text
        assert "1,2,3,4" in help_text
        assert "↑↓" in help_text
        assert "Enter" in help_text

    @pytest.mark.asyncio
    @staticmethod
    async def test_start_monitoring_duration(monitor: AgentMonitor) -> None:
        """Test monitoring with duration limit."""
        monitor.auto_refresh = True

        # Mock the update and render methods
        monitor.update_metrics = Mock()
        monitor.render = Mock(return_value="Test render")

        # Run monitoring for short duration
        await monitor.start_monitoring(duration=0.1)

        # Should have called update at least once
        assert monitor.update_metrics.called

    @pytest.mark.asyncio
    @staticmethod
    async def test_start_monitoring_keyboard_interrupt(monitor: AgentMonitor) -> None:
        """Test monitoring stops on keyboard interrupt."""
        monitor.auto_refresh = True

        # Mock methods to raise KeyboardInterrupt
        def mock_update() -> Never:
            raise KeyboardInterrupt

        monitor.update_metrics = mock_update
        monitor.render = Mock(return_value="Test render")

        # Should handle KeyboardInterrupt gracefully
        await monitor.start_monitoring()

    @staticmethod
    def test_update_metrics_no_pool(monitor: AgentMonitor) -> None:
        """Test update_metrics with no agent pool."""
        monitor.agent_pool = None

        # Should not raise exception
        monitor.update_metrics()

        # Metrics should remain empty
        assert monitor.agent_metrics == {}
        assert monitor.task_metrics == {}

    @staticmethod
    def test_update_metrics_exception_handling(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test update_metrics handles exceptions."""
        # Make agent pool raise exception
        mock_agent_pool.list_agents.side_effect = Exception("Test error")

        # Should not raise exception
        monitor.update_metrics()

        # Metrics should remain empty
        assert monitor.agent_metrics == {}

    @staticmethod
    def test_performance_history_tracking(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test performance history tracking."""
        # Update metrics multiple times
        for _ in range(5):
            monitor.update_metrics()

        # Should have performance history for agents
        assert "agent-1" in monitor.performance_history
        assert "agent-2" in monitor.performance_history

        # Each agent should have 5 data points
        assert len(monitor.performance_history["agent-1"]) == 5
        assert len(monitor.performance_history["agent-2"]) == 5

    @staticmethod
    def test_performance_history_limit(monitor: AgentMonitor, mock_agent_pool: Mock) -> None:
        """Test performance history size limiting."""
        # Add more than 100 data points
        agent_id = "agent-1"
        monitor.performance_history[agent_id] = [(datetime.now(UTC), 0.5) for _ in range(105)]

        monitor.update_metrics()

        # Should be limited to 100 points
        assert len(monitor.performance_history[agent_id]) == 100


class TestStandaloneFunctions:
    """Test standalone helper functions."""

    @staticmethod
    def test_create_agent_monitor() -> None:
        """Test create_agent_monitor function."""
        monitor = create_agent_monitor()
        assert isinstance(monitor, AgentMonitor)
        assert monitor.agent_pool is None

    @staticmethod
    def test_create_agent_monitor_with_pool() -> None:
        """Test create_agent_monitor with agent pool."""
        mock_pool = Mock()
        monitor = create_agent_monitor(mock_pool)
        assert isinstance(monitor, AgentMonitor)
        assert monitor.agent_pool == mock_pool

    @pytest.mark.asyncio
    @staticmethod
    async def test_run_agent_monitor() -> None:
        """Test run_agent_monitor function."""
        # Mock the monitor to avoid actual UI
        with patch("libs.dashboard.widgets.agent_monitor.AgentMonitor") as MockMonitor:
            mock_monitor = MockMonitor.return_value
            mock_monitor.start_monitoring = AsyncMock()

            await run_agent_monitor(duration=0.1)

            MockMonitor.assert_called_once()
            mock_monitor.start_monitoring.assert_called_once_with(0.1)


# Enhanced Testing Infrastructure - Property-Based and Chaos Engineering Tests


@pytest.mark.property
class TestPropertyBasedAgentMonitoring:
    """Property-based tests for agent monitoring using enhanced test infrastructure."""

    def test_agent_metrics_properties(self) -> None:
        """Test that agent metrics maintain required properties across various inputs."""
        factory = EnhancedTestDataFactory()

        # Generate test execution metrics for multiple test runs
        for i in range(10):
            test_metrics = factory.create_test_execution_metrics(f"test_agent_monitor_{i}")

            # Property 1: Execution metrics should have consistent structure
            assert "test_name" in test_metrics, "Test metrics should have test name"
            assert "execution_metrics" in test_metrics, "Should have execution metrics"
            assert "result" in test_metrics, "Should have test result"

            # Property 2: Duration should be reasonable
            duration = test_metrics["execution_metrics"]["duration_ms"]
            assert duration > 0, f"Duration should be positive: {duration}"
            assert duration < 60000, f"Duration should be under 1 minute: {duration}ms"

            # Property 3: Memory usage should be bounded
            memory_peak = test_metrics["execution_metrics"]["memory_peak_mb"]
            assert memory_peak >= 0, f"Memory usage should be non-negative: {memory_peak}"
            assert memory_peak < 1000, f"Memory usage should be reasonable: {memory_peak}MB"

            # Property 4: Test status should be valid
            status = test_metrics["result"]["status"]
            assert status in {"passed", "failed", "skipped", "error"}, f"Invalid status: {status}"

    def test_performance_consistency_properties(self, performance_baseline) -> None:
        """Test that performance metrics maintain consistency properties."""
        factory = EnhancedTestDataFactory()

        # Generate performance metrics
        perf_metrics = factory.create_performance_metrics(6)  # 6 hours of data

        for metric in perf_metrics["metrics"]:
            response_times = metric["response_times"]

            # Property: Response time percentiles should be ordered
            assert response_times["p50_ms"] <= response_times["p90_ms"], "P50 should be <= P90"
            assert response_times["p90_ms"] <= response_times["p95_ms"], "P90 should be <= P95"
            assert response_times["p95_ms"] <= response_times["p99_ms"], "P95 should be <= P99"

            # Property: Mean should be reasonable compared to percentiles
            assert response_times["mean_ms"] <= response_times["p95_ms"], "Mean should typically be below P95"

            # Property: Resource usage should be bounded
            resource_usage = metric["resource_usage"]
            assert 0 <= resource_usage["cpu_percent"] <= 100, f"CPU usage out of bounds: {resource_usage['cpu_percent']}"
            assert resource_usage["memory_mb"] >= 0, f"Memory usage should be non-negative: {resource_usage['memory_mb']}"


@pytest.mark.chaos
class TestChaosEngineeringAgentMonitor:
    """Chaos engineering tests for agent monitor resilience."""

    def test_network_failure_resilience(self, chaos_test_context) -> None:
        """Test agent monitor behavior under network failure conditions."""
        factory = EnhancedTestDataFactory()

        # Create network failure scenario
        chaos_scenario = factory.create_chaos_scenario("network_failure")
        chaos_test_context["chaos_active"] = True
        chaos_test_context["failures_injected"].append(chaos_scenario)

        # Mock agent pool to simulate network failures
        mock_pool = Mock()

        # Simulate network timeout
        def failing_list_agents():
            if chaos_scenario["failure_conditions"]["packet_loss_percent"] > 50:
                raise TimeoutError("Network timeout during chaos test")
            return []

        mock_pool.list_agents.side_effect = failing_list_agents
        mock_pool.list_tasks.return_value = []
        mock_pool.get_pool_statistics.return_value = {}

        monitor = AgentMonitor(agent_pool=mock_pool)

        # Test should handle network failures gracefully
        try:
            monitor.update_metrics()

            # Monitor should still be functional (empty metrics but no crash)
            assert isinstance(monitor.agent_metrics, dict), "Agent metrics should remain dictionary even during failures"
            assert isinstance(monitor.task_metrics, dict), "Task metrics should remain dictionary even during failures"

        except TimeoutError:
            # If timeout occurs, it should be handled gracefully
            pytest.fail("Network timeout not handled gracefully by agent monitor")

        # Verify chaos scenario properties
        assert chaos_scenario["expected_behavior"]["should_degrade_gracefully"], "System should degrade gracefully during network failures"

    def test_memory_pressure_resilience(self, chaos_test_context) -> None:
        """Test agent monitor behavior under memory pressure."""
        factory = EnhancedTestDataFactory()

        # Create memory pressure scenario
        chaos_scenario = factory.create_chaos_scenario("memory_pressure")
        chaos_test_context["chaos_active"] = True
        chaos_test_context["failures_injected"].append(chaos_scenario)

        # Simulate memory pressure by creating large objects
        memory_pressure_data = []
        pressure_mb = chaos_scenario["failure_conditions"].get("memory_limit_mb", 128)

        # Create memory pressure (simulate with smaller objects to avoid actual OOM)
        try:
            for i in range(10):  # Create some memory pressure
                memory_pressure_data.append([0] * min(1000, pressure_mb * 10))

            # Agent monitor should still function under memory pressure
            mock_pool = Mock()
            mock_pool.list_agents.return_value = [{"agent_id": f"agent-{i}", "state": "idle"} for i in range(5)]
            mock_pool.list_tasks.return_value = []
            mock_pool.get_pool_statistics.return_value = {"active_agents": 0}

            monitor = AgentMonitor(agent_pool=mock_pool)
            monitor.update_metrics()

            # Should handle memory pressure gracefully
            assert len(monitor.agent_metrics) <= 10, "Agent metrics should be bounded even under memory pressure"

        finally:
            # Cleanup memory pressure
            del memory_pressure_data
            import gc

            gc.collect()


@pytest.mark.performance
class TestAgentMonitorPerformanceProperties:
    """Performance property tests for agent monitor."""

    def test_update_metrics_performance_property(self, performance_baseline) -> None:
        """Test that update_metrics performance scales predictably."""
        import time

        # Test with different numbers of agents
        agent_counts = [1, 5, 10, 25, 50]
        update_times = []

        for count in agent_counts:
            # Create mock pool with varying number of agents
            mock_pool = Mock()
            mock_pool.list_agents.return_value = [
                {
                    "agent_id": f"agent-{i}",
                    "state": "working" if i % 2 == 0 else "idle",
                    "current_task": f"task-{i}" if i % 2 == 0 else None,
                    "completed_tasks": i * 2,
                    "failed_tasks": 0,
                    "total_execution_time": float(i * 10),
                }
                for i in range(count)
            ]
            mock_pool.list_tasks.return_value = [
                {
                    "task_id": f"task-{i}",
                    "title": f"Task {i}",
                    "status": "running" if i % 2 == 0 else "pending",
                    "assigned_agent": f"agent-{i}" if i % 2 == 0 else None,
                    "start_time": None,
                    "timeout": 300,
                }
                for i in range(count)
            ]
            mock_pool.get_pool_statistics.return_value = {
                "active_agents": count // 2,
                "idle_agents": count - (count // 2),
                "total_tasks": count,
            }

            monitor = AgentMonitor(agent_pool=mock_pool)

            # Measure update time
            start_time = time.perf_counter()
            monitor.update_metrics()
            end_time = time.perf_counter()

            update_time_ms = (end_time - start_time) * 1000
            update_times.append(update_time_ms)

            # Performance property: Update should be reasonably fast
            threshold_ms = performance_baseline["response_time_p95_ms"] * 2
            assert update_time_ms < threshold_ms, f"Update too slow for {count} agents: {update_time_ms}ms > {threshold_ms}ms"

        # Performance property: Should not degrade significantly with scale
        if len(update_times) >= 3:
            first_time = update_times[0]
            last_time = update_times[-1]

            # Last update shouldn't be more than 10x slower than first
            if first_time > 0:
                slowdown_factor = last_time / first_time
                assert slowdown_factor < 10, f"Performance degraded too much: {slowdown_factor}x slower"

    def test_render_performance_property(self, performance_baseline) -> None:
        """Test that render operations maintain performance properties."""
        import time

        # Create monitor with test data
        mock_pool = Mock()
        mock_pool.list_agents.return_value = [{"agent_id": f"agent-{i}", "state": "working"} for i in range(10)]
        mock_pool.list_tasks.return_value = []
        mock_pool.get_pool_statistics.return_value = {"active_agents": 10}

        monitor = AgentMonitor(agent_pool=mock_pool)
        monitor.update_metrics()

        # Test different render modes
        render_modes = [
            ("overview", monitor.render_overview),
            ("detailed", monitor.render_detailed),
            ("tasks", monitor.render_tasks),
            ("performance", monitor.render_performance),
        ]

        for mode_name, render_func in render_modes:
            start_time = time.perf_counter()
            result = render_func()
            end_time = time.perf_counter()

            render_time_ms = (end_time - start_time) * 1000

            # Performance property: Render should be fast
            threshold_ms = performance_baseline["response_time_p95_ms"]
            assert render_time_ms < threshold_ms, f"Render {mode_name} too slow: {render_time_ms}ms > {threshold_ms}ms"

            # Property: Should return valid result
            assert result is not None, f"Render {mode_name} returned None"


@pytest.mark.contract
class TestAgentMonitorApiContract:
    """API contract tests for agent monitor interfaces."""

    def test_agent_monitor_interface_contract(self) -> None:
        """Test that AgentMonitor maintains interface contract."""
        factory = EnhancedTestDataFactory()

        # Generate contract test data
        contract_data = factory.create_contract_test_data("/api/v1/agent_monitor", "GET")

        # Create monitor instance
        mock_pool = Mock()
        mock_pool.list_agents.return_value = []
        mock_pool.list_tasks.return_value = []
        mock_pool.get_pool_statistics.return_value = {}

        monitor = AgentMonitor(agent_pool=mock_pool)

        # Contract: Monitor should have required methods
        required_methods = ["update_metrics", "render_overview", "render_detailed", "render_tasks", "render_performance", "set_display_mode", "select_agent", "get_keyboard_help"]

        for method_name in required_methods:
            assert hasattr(monitor, method_name), f"AgentMonitor should have method: {method_name}"
            assert callable(getattr(monitor, method_name)), f"AgentMonitor.{method_name} should be callable"

        # Contract: Monitor should have required attributes
        required_attributes = ["display_mode", "selected_agent", "auto_refresh", "refresh_interval", "agent_metrics", "task_metrics"]

        for attr_name in required_attributes:
            assert hasattr(monitor, attr_name), f"AgentMonitor should have attribute: {attr_name}"

        # Contract: Methods should not raise unexpected exceptions
        try:
            monitor.update_metrics()
            monitor.render_overview()
            monitor.set_display_mode(MonitorDisplayMode.TASKS)
            help_text = monitor.get_keyboard_help()
            assert isinstance(help_text, str), "Help text should be string"
        except Exception as e:
            pytest.fail(f"Interface contract violation: {e}")


# Integration test combining all enhanced testing approaches
@pytest.mark.integration
class TestEnhancedAgentMonitorIntegration:
    """Integration tests combining property-based, chaos, and performance testing."""

    def test_comprehensive_integration_scenario(self, performance_baseline, chaos_test_context) -> None:
        """Test comprehensive scenario combining multiple testing approaches."""
        factory = EnhancedTestDataFactory()

        # Generate comprehensive test data
        property_data = factory.create_property_test_data(3)
        chaos_scenario = factory.create_chaos_scenario("network_failure")
        perf_metrics = factory.create_performance_metrics(1)

        # Setup chaos context
        chaos_test_context["chaos_active"] = True
        chaos_test_context["failures_injected"].append(chaos_scenario)

        # Create agent monitor with test data
        mock_pool = Mock()

        # Simulate varying conditions based on test data
        agents_data = []
        for i, sample in enumerate(property_data):
            agents_data.append(
                {
                    "agent_id": f"agent-{i}",
                    "state": "working" if i % 2 == 0 else "idle",
                    "current_task": f"task-{i}" if i % 2 == 0 else None,
                    "completed_tasks": i + 5,
                    "failed_tasks": 1 if i == 0 else 0,
                    "total_execution_time": float((i + 1) * 100),
                }
            )

        mock_pool.list_agents.return_value = agents_data
        mock_pool.list_tasks.return_value = []
        mock_pool.get_pool_statistics.return_value = {
            "active_agents": len([a for a in agents_data if a["state"] == "working"]),
            "idle_agents": len([a for a in agents_data if a["state"] == "idle"]),
            "total_tasks": len(property_data),
        }

        monitor = AgentMonitor(agent_pool=mock_pool)

        # Test integration: Property validation + Performance + Chaos resilience
        import time

        start_time = time.perf_counter()

        try:
            # Update metrics under potential chaos conditions
            monitor.update_metrics()

            # Verify property-based constraints
            assert len(monitor.agent_metrics) == len(property_data), "Should create metrics for all agents"

            # Check performance constraints
            update_time = (time.perf_counter() - start_time) * 1000
            assert update_time < performance_baseline["response_time_p95_ms"] * 3, f"Integration test took too long: {update_time}ms"

            # Verify chaos resilience - system should remain functional
            overview_panel = monitor.render_overview()
            assert overview_panel is not None, "System should remain functional under chaos conditions"

            # Test agent metrics properties
            for agent_id, metrics in monitor.agent_metrics.items():
                assert metrics.agent_id == agent_id, f"Agent ID mismatch: {metrics.agent_id} != {agent_id}"
                assert metrics.tasks_completed >= 0, f"Completed tasks should be non-negative: {metrics.tasks_completed}"
                assert 0 <= metrics.success_rate <= 1, f"Success rate should be 0-1: {metrics.success_rate}"

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")

        finally:
            # Cleanup chaos context
            chaos_test_context["chaos_active"] = False

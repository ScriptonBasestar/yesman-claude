# Copyright notice.

import asyncio
from unittest.mock import patch
import pytest
from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.task_scheduler import AgentCapability, TaskScheduler
from libs.multi_agent.types import Agent, Task

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test dynamic work redistribution algorithm."""


class TestDynamicRedistribution:
    """Test dynamic work redistribution functionality."""

    @pytest.fixture
    @staticmethod
    def agent_pool():
        """Create agent pool for testing."""
        return AgentPool(max_agents=3, work_dir="/tmp/test-agents")

    @pytest.fixture
    @staticmethod
    def scheduler():
        """Create scheduler for testing."""
        return TaskScheduler()

    @staticmethod
    def test_rebalance_detection(scheduler: TaskScheduler) -> None:
        """Test detection of overloaded and underloaded agents."""
        # Create agents with different loads
        overloaded_agent = Agent(agent_id="agent-1")
        normal_agent = Agent(agent_id="agent-2")
        underloaded_agent = Agent(agent_id="agent-3")

        # Register agents with different capabilities and loads
        overloaded_cap = AgentCapability(
            agent_id="agent-1",
            current_load=0.9,
            processing_power=1.0,
        )
        normal_cap = AgentCapability(
            agent_id="agent-2",
            current_load=0.5,
            processing_power=1.0,
        )
        underloaded_cap = AgentCapability(
            agent_id="agent-3",
            current_load=0.1,
            processing_power=1.0,
        )

        scheduler.register_agent(overloaded_agent, overloaded_cap)
        scheduler.register_agent(normal_agent, normal_cap)
        scheduler.register_agent(underloaded_agent, underloaded_cap)

        # Trigger rebalancing
        rebalancing_actions = scheduler.rebalance_tasks()

        # Should detect need for rebalancing
        assert len(rebalancing_actions) > 0
        assert any(action[0] == "agent-1" and action[1] == "agent-3" for action in rebalancing_actions)

    @staticmethod
    def test_assignment_preference_adjustment(scheduler: TaskScheduler) -> None:
        """Test adjustment of task assignment preferences."""
        # Setup agents
        overloaded_agent = Agent(agent_id="agent-1")
        underloaded_agent = Agent(agent_id="agent-2")

        overloaded_cap = AgentCapability(
            agent_id="agent-1",
            current_load=0.9,
            processing_power=1.0,
        )
        underloaded_cap = AgentCapability(
            agent_id="agent-2",
            current_load=0.1,
            processing_power=1.0,
        )

        scheduler.register_agent(overloaded_agent, overloaded_cap)
        scheduler.register_agent(underloaded_agent, underloaded_cap)

        # Store initial processing powers
        initial_overloaded_power = overloaded_cap.processing_power
        initial_underloaded_power = underloaded_cap.processing_power

        # Trigger rebalancing
        rebalancing_actions = scheduler.rebalance_tasks()

        # Should detect need for rebalancing and adjust preferences
        assert len(rebalancing_actions) > 0

        # Processing power should be adjusted
        assert overloaded_cap.processing_power < initial_overloaded_power  # Penalty applied
        assert underloaded_cap.processing_power > initial_underloaded_power  # Boost applied

    @staticmethod
    def test_load_estimation(scheduler: TaskScheduler) -> None:
        """Test task load estimation."""
        agent_cap = AgentCapability(
            agent_id="test-agent",
            processing_power=1.0,
            success_rate=0.9,
        )

        task = Task(
            task_id="test-task",
            title="Test Task",
            description="Test task description",
            command=["test", "command"],
            working_directory="/tmp",
            complexity=5,
        )

        load = scheduler._estimate_task_load(task, agent_cap)  # noqa: SLF001

        # Load should be a reasonable fraction
        assert 0.0 <= load <= 1.0
        assert isinstance(load, float)

    @pytest.mark.asyncio
    @staticmethod
    async def test_auto_rebalancing_loop(agent_pool: AgentPool) -> None:
        """Test automatic rebalancing loop."""
        # Set the agent pool as running
        agent_pool._running = True  # noqa: SLF001

        # Mock the scheduler to return low load balancing score
        with patch.object(agent_pool, "scheduler") as mock_scheduler:
            mock_scheduler.get_scheduling_metrics.return_value = {
                "load_balancing_score": 0.6,  # Below threshold
            }
            mock_scheduler.rebalance_tasks.return_value = [("agent-1", "agent-2")]

            # Enable auto-rebalancing with short interval
            agent_pool._auto_rebalancing_enabled = True  # noqa: SLF001
            agent_pool._auto_rebalancing_interval = 0.1  # 100ms for testing  # noqa: SLF001

            # Start the auto-rebalancing loop
            task = asyncio.create_task(agent_pool._auto_rebalancing_loop())  # noqa: SLF001

            # Let it run for enough time to execute at least once
            await asyncio.sleep(0.3)

            # Stop the loop
            agent_pool._auto_rebalancing_enabled = False  # noqa: SLF001
            agent_pool._running = False  # noqa: SLF001

            try:
                await asyncio.wait_for(task, timeout=0.1)
            except (TimeoutError, asyncio.CancelledError):
                task.cancel()

            # Verify rebalancing was called
            mock_scheduler.rebalance_tasks.assert_called()

    @staticmethod
    def test_rebalancing_execution(agent_pool: AgentPool) -> None:
        """Test execution of rebalancing actions."""
        # Create mock agents
        agent_1 = Agent(agent_id="agent-1")
        agent_2 = Agent(agent_id="agent-2")

        agent_pool.agents["agent-1"] = agent_1
        agent_pool.agents["agent-2"] = agent_2

        # Setup scheduler capabilities
        agent_pool.scheduler.agent_capabilities["agent-1"] = AgentCapability(
            agent_id="agent-1",
            current_load=0.8,
        )
        agent_pool.scheduler.agent_capabilities["agent-2"] = AgentCapability(
            agent_id="agent-2",
            current_load=0.2,
        )

        # Execute rebalancing
        agent_pool._execute_rebalancing("agent-1", "agent-2")  # noqa: SLF001

        # Verify load was redistributed
        cap_1 = agent_pool.scheduler.agent_capabilities["agent-1"]
        cap_2 = agent_pool.scheduler.agent_capabilities["agent-2"]

        assert cap_1.current_load < 0.8  # Should be reduced
        assert cap_2.current_load > 0.2  # Should be increased

    @staticmethod
    def test_scheduling_metrics_calculation(scheduler: TaskScheduler) -> None:
        """Test calculation of scheduling metrics."""
        # Add agents with different loads
        agents = [
            ("agent-1", 0.9),
            ("agent-2", 0.1),
            ("agent-3", 0.5),
        ]

        for agent_id, load in agents:
            cap = AgentCapability(
                agent_id=agent_id,
                current_load=load,
                processing_power=1.0,
                success_rate=0.9,
            )
            scheduler.agent_capabilities[agent_id] = cap

        metrics = scheduler.get_scheduling_metrics()

        assert "load_balancing_score" in metrics
        assert "efficiency_score" in metrics
        assert 0.0 <= metrics["load_balancing_score"] <= 1.0
        assert 0.0 <= metrics["efficiency_score"] <= 1.0

    @staticmethod
    def test_no_rebalancing_when_balanced(scheduler: TaskScheduler) -> None:
        """Test that no rebalancing occurs when loads are balanced."""
        # Create agents with similar loads
        for i in range(3):
            agent = Agent(agent_id=f"agent-{i}")
            cap = AgentCapability(
                agent_id=f"agent-{i}",
                current_load=0.5,
                processing_power=1.0,
            )
            scheduler.register_agent(agent, cap)

        # Should not trigger rebalancing
        rebalancing_actions = scheduler.rebalance_tasks()
        assert len(rebalancing_actions) == 0

    @staticmethod
    def test_preference_reset_functionality(scheduler: TaskScheduler) -> None:
        """Test that assignment preferences can be reset."""
        # Setup agent
        agent = Agent(agent_id="agent-1")
        cap = AgentCapability(
            agent_id="agent-1",
            current_load=0.5,
            processing_power=1.5,  # Modified from baseline
        )

        scheduler.register_agent(agent, cap)

        # Reset preferences
        scheduler.reset_assignment_preferences("agent-1")

        # Should be reset to baseline
        assert cap.processing_power == 1.0
        assert hasattr(cap, "_baseline_processing_power")

    @staticmethod
    def test_load_balancing_with_specializations(scheduler: TaskScheduler) -> None:
        """Test load balancing considers agent specializations."""
        # Setup agents with different specializations
        overloaded_agent = Agent(agent_id="agent-1")
        underloaded_agent = Agent(agent_id="agent-2")

        overloaded_cap = AgentCapability(
            agent_id="agent-1",
            current_load=0.9,
            specializations=["python", "testing"],
            processing_power=1.0,
        )
        underloaded_cap = AgentCapability(
            agent_id="agent-2",
            current_load=0.1,
            specializations=["javascript", "build"],
            processing_power=1.0,
        )

        scheduler.register_agent(overloaded_agent, overloaded_cap)
        scheduler.register_agent(underloaded_agent, underloaded_cap)

        # Trigger rebalancing
        rebalancing_actions = scheduler.rebalance_tasks()

        # Should still rebalance despite different specializations
        assert len(rebalancing_actions) > 0

        # Verify load was redistributed
        assert overloaded_cap.current_load < 0.9
        assert underloaded_cap.current_load > 0.1


if __name__ == "__main__":
    pytest.main([__file__])

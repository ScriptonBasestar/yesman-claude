"""Tests for TaskScheduler class"""

import pytest

from libs.multi_agent.task_scheduler import AgentCapability, PriorityTask, TaskScheduler
from libs.multi_agent.types import Agent, Task


class TestAgentCapability:
    """Test cases for AgentCapability"""

    def test_init(self):
        """Test AgentCapability initialization"""
        capability = AgentCapability(agent_id="test-agent")

        assert capability.agent_id == "test-agent"
        assert capability.processing_power == 1.0
        assert capability.success_rate == 1.0
        assert capability.average_execution_time == 0.0
        assert capability.complexity_preference == 0.5
        assert capability.specializations == []
        assert capability.current_load == 0.0

    def test_get_efficiency_score_basic(self):
        """Test basic efficiency score calculation"""
        capability = AgentCapability(
            agent_id="test-agent",
            processing_power=1.5,
            success_rate=0.9,
        )

        task = Task(
            task_id="test-task",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
            complexity=5,
        )

        score = capability.get_efficiency_score(task)
        assert score > 0.0
        assert score <= 2.0  # Max theoretical score

    def test_get_efficiency_score_with_specialization(self):
        """Test efficiency score with specialization bonus"""
        capability = AgentCapability(
            agent_id="test-agent",
            specializations=["python", "testing"],
        )

        task = Task(
            task_id="test-task",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
            metadata={"tags": ["python", "development"]},
        )

        score = capability.get_efficiency_score(task)

        # Test without specialization
        task_no_spec = Task(
            task_id="test-task-2",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
            metadata={"tags": ["javascript"]},
        )

        score_no_spec = capability.get_efficiency_score(task_no_spec)

        assert score > score_no_spec  # Should get specialization bonus

    def test_get_efficiency_score_with_load_penalty(self):
        """Test efficiency score with load penalty"""
        capability = AgentCapability(
            agent_id="test-agent",
            current_load=0.8,  # High load
        )

        task = Task(
            task_id="test-task",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
        )

        score_high_load = capability.get_efficiency_score(task)

        # Test with low load
        capability.current_load = 0.1
        score_low_load = capability.get_efficiency_score(task)

        assert score_low_load > score_high_load  # Lower load should have higher score


class TestPriorityTask:
    """Test cases for PriorityTask"""

    def test_priority_comparison(self):
        """Test priority task comparison for heap"""
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
        )

        pt1 = PriorityTask(priority_score=0.8, task=task1)
        pt2 = PriorityTask(priority_score=0.6, task=task2)

        # Higher priority should come first (pt1 < pt2 should be True)
        assert pt1 < pt2
        assert not (pt2 < pt1)


class TestTaskScheduler:
    """Test cases for TaskScheduler"""

    @pytest.fixture
    def scheduler(self):
        """Create TaskScheduler instance"""
        return TaskScheduler()

    @pytest.fixture
    def sample_agent(self):
        """Create sample agent"""
        return Agent(agent_id="test-agent")

    @pytest.fixture
    def sample_task(self):
        """Create sample task"""
        return Task(
            task_id="test-task",
            title="Test Task",
            description="A test task",
            command=["echo", "test"],
            working_directory="/tmp",
            priority=7,
            complexity=5,
        )

    def test_init(self, scheduler):
        """Test TaskScheduler initialization"""
        assert scheduler.agent_capabilities == {}
        assert scheduler.priority_queue == []
        assert scheduler.task_history == {}
        assert "total_scheduled" in scheduler.scheduling_metrics
        assert scheduler.priority_weight == 0.4
        assert scheduler.learning_rate == 0.1

    def test_register_agent(self, scheduler, sample_agent):
        """Test agent registration"""
        scheduler.register_agent(sample_agent)

        assert sample_agent.agent_id in scheduler.agent_capabilities
        assert sample_agent.agent_id in scheduler.task_history
        assert scheduler.task_history[sample_agent.agent_id] == []

        capability = scheduler.agent_capabilities[sample_agent.agent_id]
        assert capability.agent_id == sample_agent.agent_id

    def test_register_agent_with_capability(self, scheduler, sample_agent):
        """Test agent registration with custom capability"""
        custom_capability = AgentCapability(
            agent_id=sample_agent.agent_id,
            processing_power=2.0,
            specializations=["python"],
        )

        scheduler.register_agent(sample_agent, custom_capability)

        capability = scheduler.agent_capabilities[sample_agent.agent_id]
        assert capability.processing_power == 2.0
        assert capability.specializations == ["python"]

    def test_add_task(self, scheduler, sample_task):
        """Test adding task to priority queue"""
        scheduler.add_task(sample_task)

        assert len(scheduler.priority_queue) == 1
        priority_task = scheduler.priority_queue[0]
        assert priority_task.task == sample_task
        assert priority_task.priority_score > 0

    def test_calculate_priority_score(self, scheduler):
        """Test priority score calculation"""
        task = Task(
            task_id="test",
            title="Test",
            command=["echo"],
            working_directory="/tmp",
            priority=8,  # High priority
            complexity=6,  # Medium-high complexity
            metadata={"blocks_tasks": 3},  # Blocks other tasks
        )

        score = scheduler._calculate_priority_score(task)
        assert score > 0.0
        assert score <= 1.0  # Should be normalized

    def test_get_next_task_for_agent(self, scheduler, sample_agent, sample_task):
        """Test getting next task for agent"""
        scheduler.register_agent(sample_agent)
        scheduler.add_task(sample_task)

        task = scheduler.get_next_task_for_agent(sample_agent)

        assert task == sample_task
        assert len(scheduler.priority_queue) == 0  # Task should be removed
        assert scheduler.scheduling_metrics["total_scheduled"] == 1

    def test_get_next_task_for_unregistered_agent(
        self,
        scheduler,
        sample_agent,
        sample_task,
    ):
        """Test getting task for unregistered agent"""
        scheduler.add_task(sample_task)

        task = scheduler.get_next_task_for_agent(sample_agent)

        assert task == sample_task
        assert sample_agent.agent_id in scheduler.agent_capabilities  # Should auto-register

    def test_get_next_task_empty_queue(self, scheduler, sample_agent):
        """Test getting task from empty queue"""
        scheduler.register_agent(sample_agent)

        task = scheduler.get_next_task_for_agent(sample_agent)
        assert task is None

    def test_get_optimal_task_assignment(self, scheduler):
        """Test optimal task assignment for multiple agents"""
        # Create agents
        agent1 = Agent(agent_id="agent-1")
        agent2 = Agent(agent_id="agent-2")
        agents = [agent1, agent2]

        # Register agents with different capabilities
        scheduler.register_agent(
            agent1,
            AgentCapability(
                agent_id="agent-1",
                processing_power=1.5,
                specializations=["python"],
            ),
        )
        scheduler.register_agent(
            agent2,
            AgentCapability(
                agent_id="agent-2",
                processing_power=1.0,
                specializations=["javascript"],
            ),
        )

        # Add tasks
        task1 = Task(
            task_id="task-1",
            title="Python Task",
            command=["python", "script.py"],
            working_directory="/tmp",
            priority=8,
            metadata={"tags": ["python"]},
        )
        task2 = Task(
            task_id="task-2",
            title="JS Task",
            command=["node", "script.js"],
            working_directory="/tmp",
            priority=6,
            metadata={"tags": ["javascript"]},
        )

        scheduler.add_task(task1)
        scheduler.add_task(task2)

        assignments = scheduler.get_optimal_task_assignment(agents)

        assert len(assignments) == 2

        # Check that assignments make sense (agent1 gets python task, agent2 gets js task)
        agent_task_map = {agent.agent_id: task for agent, task in assignments}
        assert "task-1" in [task.task_id for agent, task in assignments]
        assert "task-2" in [task.task_id for agent, task in assignments]

    def test_update_agent_performance(self, scheduler, sample_agent, sample_task):
        """Test updating agent performance metrics"""
        scheduler.register_agent(sample_agent)

        # Simulate successful task completion
        scheduler.update_agent_performance(
            sample_agent.agent_id,
            sample_task,
            success=True,
            execution_time=120.0,
        )

        capability = scheduler.agent_capabilities[sample_agent.agent_id]
        assert capability.success_rate > 0.9  # Should improve
        assert capability.average_execution_time == 120.0
        assert len(scheduler.task_history[sample_agent.agent_id]) == 1

    def test_update_agent_performance_failure(
        self,
        scheduler,
        sample_agent,
        sample_task,
    ):
        """Test updating agent performance on failure"""
        scheduler.register_agent(sample_agent)

        # Simulate failed task
        scheduler.update_agent_performance(
            sample_agent.agent_id,
            sample_task,
            success=False,
            execution_time=60.0,
        )

        capability = scheduler.agent_capabilities[sample_agent.agent_id]
        assert capability.success_rate < 1.0  # Should decrease

    def test_estimate_task_time(self, scheduler):
        """Test task time estimation"""
        capability = AgentCapability(
            agent_id="test-agent",
            processing_power=2.0,
            specializations=["python"],
        )

        task = Task(
            task_id="test",
            title="Test",
            command=["python", "test.py"],
            working_directory="/tmp",
            complexity=5,
            metadata={"tags": ["python"]},
        )

        estimated_time = scheduler._estimate_task_time(task, capability)
        assert estimated_time > 0

        # Should be faster due to high processing power and specialization
        base_time = scheduler._estimate_base_task_time(task)
        assert estimated_time < base_time

    def test_estimate_base_task_time(self, scheduler):
        """Test base task time estimation"""
        # Test task
        test_task = Task(
            task_id="test",
            title="Test",
            command=["pytest", "tests/"],
            working_directory="/tmp",
            complexity=5,
        )

        test_time = scheduler._estimate_base_task_time(test_task)

        # Build task
        build_task = Task(
            task_id="build",
            title="Build",
            command=["make", "build"],
            working_directory="/tmp",
            complexity=5,
        )

        build_time = scheduler._estimate_base_task_time(build_task)

        # Lint task
        lint_task = Task(
            task_id="lint",
            title="Lint",
            command=["ruff", "check"],
            working_directory="/tmp",
            complexity=5,
        )

        lint_time = scheduler._estimate_base_task_time(lint_task)

        # Test tasks should take longer than lint tasks
        assert test_time > lint_time
        assert build_time > lint_time

    def test_update_agent_load(self, scheduler, sample_agent):
        """Test updating agent load"""
        scheduler.register_agent(sample_agent)

        scheduler.update_agent_load(sample_agent.agent_id, 0.7)

        capability = scheduler.agent_capabilities[sample_agent.agent_id]
        assert capability.current_load == 0.7

        # Test bounds
        scheduler.update_agent_load(sample_agent.agent_id, 1.5)  # Over limit
        assert capability.current_load == 1.0  # Should be capped

        scheduler.update_agent_load(sample_agent.agent_id, -0.5)  # Under limit
        assert capability.current_load == 0.0  # Should be floored

    def test_get_scheduling_metrics(self, scheduler):
        """Test getting scheduling metrics"""
        metrics = scheduler.get_scheduling_metrics()

        assert "total_scheduled" in metrics
        assert "load_balancing_score" in metrics
        assert "efficiency_score" in metrics
        assert "queue_size" in metrics

        # Add some agents and test again
        agent1 = Agent(agent_id="agent-1")
        agent2 = Agent(agent_id="agent-2")

        scheduler.register_agent(agent1)
        scheduler.register_agent(agent2)

        scheduler.update_agent_load("agent-1", 0.3)
        scheduler.update_agent_load("agent-2", 0.7)

        metrics = scheduler.get_scheduling_metrics()
        assert metrics["active_agents"] == 1  # Only agent-2 has load > 0
        assert 0.0 <= metrics["load_balancing_score"] <= 1.0
        assert 0.0 <= metrics["efficiency_score"] <= 2.0

    def test_rebalance_tasks(self, scheduler):
        """Test task rebalancing"""
        # Create agents with different loads
        agent1 = Agent(agent_id="agent-1")
        agent2 = Agent(agent_id="agent-2")
        agent3 = Agent(agent_id="agent-3")

        scheduler.register_agent(agent1)
        scheduler.register_agent(agent2)
        scheduler.register_agent(agent3)

        # Set loads: agent1 overloaded, agent2 underloaded, agent3 normal
        scheduler.update_agent_load("agent-1", 0.9)  # Overloaded
        scheduler.update_agent_load("agent-2", 0.2)  # Underloaded
        scheduler.update_agent_load("agent-3", 0.5)  # Normal

        rebalancing_actions = scheduler.rebalance_tasks()

        assert len(rebalancing_actions) > 0
        assert any("agent-1" in action for action in rebalancing_actions)
        assert any("agent-2" in action for action in rebalancing_actions)

    def test_task_dependency_check(self, scheduler):
        """Test task dependency checking"""
        # Task with no dependencies
        task_no_deps = Task(
            task_id="no-deps",
            title="No Dependencies",
            command=["echo"],
            working_directory="/tmp",
        )

        assert scheduler._are_dependencies_met(task_no_deps) is True

        # Task with dependencies (should fail for now)
        task_with_deps = Task(
            task_id="with-deps",
            title="With Dependencies",
            command=["echo"],
            working_directory="/tmp",
            dependencies=["other-task"],
        )

        assert scheduler._are_dependencies_met(task_with_deps) is False

    def test_task_history_limit(self, scheduler, sample_agent):
        """Test task history size limiting"""
        scheduler.register_agent(sample_agent)

        # Add more than 100 tasks to history
        for i in range(105):
            task = Task(
                task_id=f"task-{i}",
                title=f"Task {i}",
                command=["echo"],
                working_directory="/tmp",
            )
            scheduler.update_agent_performance(
                sample_agent.agent_id,
                task,
                success=True,
                execution_time=60.0,
            )

        # History should be limited to 100
        history = scheduler.task_history[sample_agent.agent_id]
        assert len(history) == 100
        assert history[0].task_id == "task-5"  # Should have removed first 5
        assert history[-1].task_id == "task-104"

# Copyright notice.

import heapq
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

from .types import Agent, Task

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Intelligent task scheduling and distribution algorithms for multi-agent system."""


logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents an agent's capabilities and performance metrics."""

    agent_id: str
    processing_power: float = 1.0  # Relative processing speed multiplier
    success_rate: float = 1.0  # Historical success rate (0.0-1.0)
    average_execution_time: float = 0.0  # Average time per task in seconds
    complexity_preference: float = 0.5  # Preference for complex tasks (0.0-1.0)
    specializations: list[str] = field(
        default_factory=list,
    )  # Task type specializations
    current_load: float = 0.0  # Current workload (0.0-1.0)

    def get_efficiency_score(self, task: Task) -> float:
        """Calculate efficiency score for this agent handling a specific task.

        Returns:
        float: Description of return value.
        """
        # Base efficiency from processing power and success rate
        base_efficiency = self.processing_power * self.success_rate

        # Complexity matching bonus
        complexity_match = 1.0 - abs(
            self.complexity_preference - (task.complexity / 10.0),
        )
        complexity_bonus = 0.2 * complexity_match

        # Specialization bonus
        specialization_bonus = 0.0
        task_tags = cast(list[str], task.metadata.get("tags", []))
        if any(spec in task_tags for spec in self.specializations):
            specialization_bonus = 0.3

        # Load penalty
        load_penalty = self.current_load * 0.5

        return max(
            0.1,
            base_efficiency + complexity_bonus + specialization_bonus - load_penalty,
        )


@dataclass
class PriorityTask:
    """Task wrapper for priority queue."""

    priority_score: float
    task: Task

    def __lt__(self, other: "PriorityTask") -> bool:
        # Higher priority score = higher priority (so negate for min-heap)
        return self.priority_score > other.priority_score


class TaskScheduler:
    """Intelligent task scheduler with priority and complexity-based
    distribution."""

    def __init__(self) -> None:
        """Initialize the task scheduler."""
        self.agent_capabilities: dict[str, AgentCapability] = {}
        self.priority_queue: list[PriorityTask] = []
        self.task_history: dict[str, list[Task]] = {}  # agent_id -> task history
        self.scheduling_metrics: dict[str, Any] = {
            "total_scheduled": 0,
            "average_wait_time": 0.0,
            "load_balancing_score": 0.0,
            "efficiency_score": 0.0,
        }

        # Scheduling parameters
        self.priority_weight = 0.4
        self.complexity_weight = 0.3
        self.urgency_weight = 0.2
        self.dependency_weight = 0.1

        # Learning parameters
        self.learning_rate = 0.1
        self.performance_decay = 0.95  # Gradual decay of old performance data

    def register_agent(
        self,
        agent: Agent,
        capabilities: AgentCapability | None = None,
    ) -> None:
        """Register an agent with the scheduler.

        Returns:
        None: Description of return value.
        """
        if capabilities is None:
            capabilities = AgentCapability(agent_id=agent.agent_id)

        self.agent_capabilities[agent.agent_id] = capabilities
        self.task_history[agent.agent_id] = []

        logger.info("Registered agent %s with scheduler", agent.agent_id)

    def add_task(self, task: Task) -> None:
        """Add a task to the priority queue."""
        priority_score = self._calculate_priority_score(task)
        priority_task = PriorityTask(priority_score=priority_score, task=task)

        heapq.heappush(self.priority_queue, priority_task)
        logger.debug(
            "Added task %s with priority score %.3f",
            task.task_id,
            priority_score,
        )

    def get_next_task_for_agent(self, agent: Agent) -> Task | None:
        """Get the best next task for a specific agent.

        Returns:
            Task | None object the requested data.
        """
        if not self.priority_queue:
            return None

        agent_capability = self.agent_capabilities.get(agent.agent_id)
        if not agent_capability:
            # If agent not registered, create default capability
            self.register_agent(agent)
            agent_capability = self.agent_capabilities[agent.agent_id]

        # Find the best task for this agent
        best_task_index = self._find_best_task_for_agent(agent_capability)

        if best_task_index is not None:
            # Remove and return the selected task
            priority_task = self.priority_queue.pop(best_task_index)
            heapq.heapify(self.priority_queue)  # Re-heapify after pop

            self.scheduling_metrics["total_scheduled"] += 1
            return priority_task.task

        return None

    def get_optimal_task_assignment(
        self,
        available_agents: list[Agent],
    ) -> list[tuple[Agent, Task]]:
        """Get optimal task assignments for multiple agents.

        Returns:
        object: Description of return value.
        """
        assignments = []

        # Create a copy of the priority queue for manipulation
        temp_queue = self.priority_queue.copy()
        agent_loads = {agent.agent_id: 0.0 for agent in available_agents}

        # Sort agents by current capability and load
        sorted_agents = sorted(
            available_agents,
            key=self._get_agent_total_score,
            reverse=True,
        )

        for agent in sorted_agents:
            if not temp_queue:
                break

            agent_capability = self.agent_capabilities.get(agent.agent_id)
            if not agent_capability:
                self.register_agent(agent)
                agent_capability = self.agent_capabilities[agent.agent_id]

            # Find best task for this agent from remaining tasks
            best_task = None
            best_score = 0.0
            best_index = -1

            for i, priority_task in enumerate(temp_queue):
                task = priority_task.task

                # Skip if task has unmet dependencies
                if not self._are_dependencies_met(task):
                    continue

                # Calculate assignment score
                efficiency = agent_capability.get_efficiency_score(task)
                load_factor = 1.0 - agent_loads[agent.agent_id]
                assignment_score = efficiency * load_factor

                if assignment_score > best_score:
                    best_score = assignment_score
                    best_task = task
                    best_index = i

            if best_task:
                # Assign task to agent
                assignments.append((agent, best_task))

                # Update agent load
                estimated_time = self._estimate_task_time(best_task, agent_capability)
                agent_loads[agent.agent_id] += estimated_time / 3600.0  # Convert to hours

                # Remove task from temp queue
                temp_queue.pop(best_index)

        return assignments

    def update_agent_performance(
        self,
        agent_id: str,
        task: Task,
        success: bool,  # noqa: FBT001
        execution_time: float,
    ) -> None:
        """Update agent performance metrics based on task completion.

        Returns:
        None: Description of return value.
        """
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return

        # Update success rate with exponential moving average
        if success:
            capability.success_rate = capability.success_rate * (1 - self.learning_rate) + 1.0 * self.learning_rate
        else:
            capability.success_rate = capability.success_rate * (1 - self.learning_rate) + 0.0 * self.learning_rate

        # Update average execution time
        if capability.average_execution_time == 0.0:
            capability.average_execution_time = execution_time
        else:
            capability.average_execution_time = capability.average_execution_time * (1 - self.learning_rate) + execution_time * self.learning_rate

        # Update processing power based on performance vs expected time
        expected_time = self._estimate_base_task_time(task)
        if expected_time > 0:
            performance_ratio = expected_time / execution_time
            capability.processing_power = capability.processing_power * (1 - self.learning_rate) + performance_ratio * self.learning_rate

        # Add to task history
        self.task_history[agent_id].append(task)

        # Limit history size
        if len(self.task_history[agent_id]) > 100:
            self.task_history[agent_id] = self.task_history[agent_id][-100:]

        logger.debug(
            "Updated performance for agent %s: success_rate=%.3f, processing_power=%.3f",
            agent_id,
            capability.success_rate,
            capability.processing_power,
        )

    def _calculate_priority_score(self, task: Task) -> float:
        """Calculate priority score for a task.

        Returns:
        float: Description of return value.
        """
        # Base priority from task priority field (1-10)
        priority_score = task.priority / 10.0 * self.priority_weight

        # Complexity contribution (more complex = higher priority in some cases)
        complexity_score = task.complexity / 10.0 * self.complexity_weight

        # Urgency based on how long task has been waiting
        age_hours = 0.0
        if hasattr(task, "created_at") and task.created_at:
            age_hours = (datetime.now(UTC) - task.created_at).total_seconds() / 3600.0

        urgency_score = min(1.0, age_hours / 24.0) * self.urgency_weight  # Max urgency after 24h

        # Dependency impact (tasks that unblock others get higher priority)
        dependency_score = 0.0
        blocks_tasks = cast(int, task.metadata.get("blocks_tasks", 0))
        if blocks_tasks > 0:
            dependency_score = min(1.0, blocks_tasks / 5.0) * self.dependency_weight

        return priority_score + complexity_score + urgency_score + dependency_score

    def _find_best_task_for_agent(
        self,
        agent_capability: AgentCapability,
    ) -> int | None:
        """Find the best task index for a specific agent.

        Returns:
        object: Description of return value.
        """
        if not self.priority_queue:
            return None

        best_index = None
        best_score = 0.0

        for i, priority_task in enumerate(self.priority_queue):
            task = priority_task.task

            # Skip if dependencies not met
            if not self._are_dependencies_met(task):
                continue

            # Calculate how well this agent can handle this task
            efficiency_score = agent_capability.get_efficiency_score(task)

            # Combine with task priority
            combined_score = priority_task.priority_score * 0.7 + efficiency_score * 0.3

            if combined_score > best_score:
                best_score = combined_score
                best_index = i

        return best_index

    def _get_agent_total_score(self, agent: Agent) -> float:
        """Get total capability score for an agent.

        Returns:
        float: Description of return value.
        """
        capability = self.agent_capabilities.get(agent.agent_id)
        if not capability:
            return 0.5

        return capability.processing_power * 0.4 + capability.success_rate * 0.4 + (1.0 - capability.current_load) * 0.2

    @staticmethod
    def _are_dependencies_met(task: Task) -> bool:
        """Check if task dependencies are satisfied.

        Returns:
        bool: Description of return value.
        """
        if not task.dependencies:
            return True

        # For now, assume dependencies are task IDs that should be completed
        # In a real implementation, this would check against completed tasks
        return len(task.dependencies) == 0

    def _estimate_task_time(
        self,
        task: Task,
        agent_capability: AgentCapability,
    ) -> float:
        """Estimate how long a task will take for a specific agent.

        Returns:
        float: Description of return value.
        """
        base_time = self._estimate_base_task_time(task)

        # Adjust for agent's processing power and specializations
        agent_multiplier = 1.0 / max(0.1, agent_capability.processing_power)

        # Specialization bonus
        task_tags = cast(list[str], task.metadata.get("tags", []))
        if any(spec in task_tags for spec in agent_capability.specializations):
            agent_multiplier *= 0.8  # 20% faster for specialized tasks

        return base_time * agent_multiplier

    @staticmethod
    def _estimate_base_task_time(task: Task) -> float:
        """Estimate base time for a task.

        Returns:
        float: Description of return value.
        """
        # Simple heuristic based on complexity and command type
        base_time = task.complexity * 60.0  # Base: complexity * 60 seconds

        # Adjust based on command type
        if task.command:
            command = task.command[0].lower()
            if command in {"test", "pytest", "npm test"}:
                base_time *= 2.0  # Tests take longer
            elif command in {"build", "compile", "make"}:
                base_time *= 1.5  # Builds take longer
            elif command in {"lint", "format", "check"}:
                base_time *= 0.5  # Quick tasks

        return base_time

    def update_agent_load(self, agent_id: str, load: float) -> None:
        """Update current load for an agent."""
        capability = self.agent_capabilities.get(agent_id)
        if capability:
            capability.current_load = max(0.0, min(1.0, load))

    def get_scheduling_metrics(self) -> dict[str, Any]:
        """Get current scheduling performance metrics.

        Returns:
        object: Description of return value.
        """
        if not self.agent_capabilities:
            return self.scheduling_metrics

        # Calculate load balancing score
        loads = [cap.current_load for cap in self.agent_capabilities.values()]
        if loads:
            avg_load = sum(loads) / len(loads)
            load_variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
            load_balancing_score = max(0.0, 1.0 - load_variance)
        else:
            load_balancing_score = 1.0

        # Calculate efficiency score
        efficiency_scores = [cap.processing_power * cap.success_rate for cap in self.agent_capabilities.values()]
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.5

        self.scheduling_metrics.update(
            {
                "load_balancing_score": load_balancing_score,
                "efficiency_score": avg_efficiency,
                "queue_size": len(self.priority_queue),
                "active_agents": len(
                    [cap for cap in self.agent_capabilities.values() if cap.current_load > 0],
                ),
            },
        )

        return self.scheduling_metrics.copy()

    def rebalance_tasks(self) -> list[tuple[str, str]]:
        """Rebalance workload between agents by adjusting task assignment
        preferences.

        Returns:
        object: Description of return value.
        """
        rebalancing_actions = []

        # Find overloaded and underloaded agents
        overloaded = []
        underloaded = []

        for agent_id, capability in self.agent_capabilities.items():
            if capability.current_load > 0.8:
                overloaded.append((agent_id, capability))
            elif capability.current_load < 0.3:
                underloaded.append((agent_id, capability))

        # Perform load balancing adjustments
        if overloaded and underloaded:
            logger.info(
                "Rebalancing workload: %d overloaded, %d underloaded agents",
                len(overloaded),
                len(underloaded),
            )

            # Sort by load difference to prioritize most urgent rebalancing
            overloaded.sort(key=lambda x: x[1].current_load, reverse=True)
            underloaded.sort(key=lambda x: x[1].current_load)

            for overloaded_agent_id, overloaded_cap in overloaded:
                for underloaded_agent_id, underloaded_cap in underloaded:
                    # Calculate load difference
                    load_diff = overloaded_cap.current_load - underloaded_cap.current_load

                    # Only rebalance if significant difference (>0.4)
                    if load_diff > 0.4:
                        # Apply workload redistribution
                        load_transfer = min(0.15, load_diff * 0.3)  # Transfer up to 15% or 30% of difference

                        # Adjust agent loads
                        overloaded_cap.current_load = max(0.0, overloaded_cap.current_load - load_transfer)
                        underloaded_cap.current_load = min(1.0, underloaded_cap.current_load + load_transfer)

                        # Boost underloaded agent's assignment preference temporarily
                        underloaded_cap.processing_power *= 1.2  # 20% boost for next assignments

                        rebalancing_actions.append((overloaded_agent_id, underloaded_agent_id))
                        logger.info(
                            "Redistributed %.2f load from %s (%.2f) to %s (%.2f)",
                            load_transfer,
                            overloaded_agent_id,
                            overloaded_cap.current_load,
                            underloaded_agent_id,
                            underloaded_cap.current_load,
                        )

                        # Apply scheduling preference adjustment
                        self._adjust_assignment_preferences(overloaded_agent_id, underloaded_agent_id)

        return rebalancing_actions

    def _adjust_assignment_preferences(self, overloaded_agent_id: str, underloaded_agent_id: str) -> None:
        """Adjust task assignment preferences to favor underloaded agents."""
        overloaded_cap = self.agent_capabilities.get(overloaded_agent_id)
        underloaded_cap = self.agent_capabilities.get(underloaded_agent_id)

        if not overloaded_cap or not underloaded_cap:
            return

        # Temporarily reduce overloaded agent's processing power score
        overloaded_cap.processing_power *= 0.8  # 20% penalty

        # The boost to underloaded agent was already applied in rebalance_tasks
        logger.debug(
            "Adjusted assignment preferences: %s penalty, %s boost",
            overloaded_agent_id,
            underloaded_agent_id,
        )

    def reset_assignment_preferences(self, agent_id: str) -> None:
        """Reset assignment preferences for an agent to baseline values."""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return

        # Reset processing power to a baseline (assume 1.0 is baseline)
        if hasattr(capability, "_baseline_processing_power"):
            capability.processing_power = capability._baseline_processing_power
        else:
            # Store baseline and reset to 1.0
            capability.processing_power = 1.0
            capability.processing_power = 1.0

        logger.debug("Reset assignment preferences for agent %s", agent_id)

    def _estimate_task_load(self, task: Task, agent_capability: AgentCapability) -> float:
        """Estimate the load a task represents for an agent.

        Returns:
        float: Description of return value.
        """
        estimated_time = self._estimate_task_time(task, agent_capability)
        # Convert to load factor (assuming 8-hour workday)
        return estimated_time / (8 * 3600.0)

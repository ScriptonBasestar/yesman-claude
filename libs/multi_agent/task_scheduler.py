"""Intelligent task scheduling and distribution algorithms for multi-agent system"""

import heapq
import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from .types import Agent, Task, AgentState, TaskStatus


logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents an agent's capabilities and performance metrics"""

    agent_id: str
    processing_power: float = 1.0  # Relative processing speed multiplier
    success_rate: float = 1.0  # Historical success rate (0.0-1.0)
    average_execution_time: float = 0.0  # Average time per task in seconds
    complexity_preference: float = 0.5  # Preference for complex tasks (0.0-1.0)
    specializations: List[str] = field(
        default_factory=list
    )  # Task type specializations
    current_load: float = 0.0  # Current workload (0.0-1.0)

    def get_efficiency_score(self, task: Task) -> float:
        """Calculate efficiency score for this agent handling a specific task"""
        # Base efficiency from processing power and success rate
        base_efficiency = self.processing_power * self.success_rate

        # Complexity matching bonus
        complexity_match = 1.0 - abs(
            self.complexity_preference - (task.complexity / 10.0)
        )
        complexity_bonus = 0.2 * complexity_match

        # Specialization bonus
        specialization_bonus = 0.0
        task_tags = task.metadata.get("tags", [])
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
    """Task wrapper for priority queue"""

    priority_score: float
    task: Task

    def __lt__(self, other):
        # Higher priority score = higher priority (so negate for min-heap)
        return self.priority_score > other.priority_score


class TaskScheduler:
    """Intelligent task scheduler with priority and complexity-based distribution"""

    def __init__(self):
        """Initialize the task scheduler"""
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.priority_queue: List[PriorityTask] = []
        self.task_history: Dict[str, List[Task]] = {}  # agent_id -> task history
        self.scheduling_metrics = {
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
        self, agent: Agent, capabilities: Optional[AgentCapability] = None
    ) -> None:
        """Register an agent with the scheduler"""
        if capabilities is None:
            capabilities = AgentCapability(agent_id=agent.agent_id)

        self.agent_capabilities[agent.agent_id] = capabilities
        self.task_history[agent.agent_id] = []

        logger.info(f"Registered agent {agent.agent_id} with scheduler")

    def add_task(self, task: Task) -> None:
        """Add a task to the priority queue"""
        priority_score = self._calculate_priority_score(task)
        priority_task = PriorityTask(priority_score=priority_score, task=task)

        heapq.heappush(self.priority_queue, priority_task)
        logger.debug(
            f"Added task {task.task_id} with priority score {priority_score:.3f}"
        )

    def get_next_task_for_agent(self, agent: Agent) -> Optional[Task]:
        """Get the best next task for a specific agent"""
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
        self, available_agents: List[Agent]
    ) -> List[Tuple[Agent, Task]]:
        """Get optimal task assignments for multiple agents"""
        assignments = []

        # Create a copy of the priority queue for manipulation
        temp_queue = self.priority_queue.copy()
        agent_loads = {agent.agent_id: 0.0 for agent in available_agents}

        # Sort agents by current capability and load
        sorted_agents = sorted(
            available_agents, key=lambda a: self._get_agent_total_score(a), reverse=True
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
                agent_loads[agent.agent_id] += (
                    estimated_time / 3600.0
                )  # Convert to hours

                # Remove task from temp queue
                temp_queue.pop(best_index)

        return assignments

    def update_agent_performance(
        self, agent_id: str, task: Task, success: bool, execution_time: float
    ) -> None:
        """Update agent performance metrics based on task completion"""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return

        # Update success rate with exponential moving average
        if success:
            capability.success_rate = (
                capability.success_rate * (1 - self.learning_rate)
                + 1.0 * self.learning_rate
            )
        else:
            capability.success_rate = (
                capability.success_rate * (1 - self.learning_rate)
                + 0.0 * self.learning_rate
            )

        # Update average execution time
        if capability.average_execution_time == 0.0:
            capability.average_execution_time = execution_time
        else:
            capability.average_execution_time = (
                capability.average_execution_time * (1 - self.learning_rate)
                + execution_time * self.learning_rate
            )

        # Update processing power based on performance vs expected time
        expected_time = self._estimate_base_task_time(task)
        if expected_time > 0:
            performance_ratio = expected_time / execution_time
            capability.processing_power = (
                capability.processing_power * (1 - self.learning_rate)
                + performance_ratio * self.learning_rate
            )

        # Add to task history
        self.task_history[agent_id].append(task)

        # Limit history size
        if len(self.task_history[agent_id]) > 100:
            self.task_history[agent_id] = self.task_history[agent_id][-100:]

        logger.debug(
            f"Updated performance for agent {agent_id}: "
            f"success_rate={capability.success_rate:.3f}, "
            f"processing_power={capability.processing_power:.3f}"
        )

    def _calculate_priority_score(self, task: Task) -> float:
        """Calculate priority score for a task"""
        # Base priority from task priority field (1-10)
        priority_score = task.priority / 10.0 * self.priority_weight

        # Complexity contribution (more complex = higher priority in some cases)
        complexity_score = task.complexity / 10.0 * self.complexity_weight

        # Urgency based on how long task has been waiting
        age_hours = 0.0
        if hasattr(task, "created_at") and task.created_at:
            age_hours = (datetime.now() - task.created_at).total_seconds() / 3600.0

        urgency_score = (
            min(1.0, age_hours / 24.0) * self.urgency_weight
        )  # Max urgency after 24h

        # Dependency impact (tasks that unblock others get higher priority)
        dependency_score = 0.0
        if task.metadata.get("blocks_tasks", 0) > 0:
            dependency_score = (
                min(1.0, task.metadata["blocks_tasks"] / 5.0) * self.dependency_weight
            )

        total_score = (
            priority_score + complexity_score + urgency_score + dependency_score
        )
        return total_score

    def _find_best_task_for_agent(
        self, agent_capability: AgentCapability
    ) -> Optional[int]:
        """Find the best task index for a specific agent"""
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
        """Get total capability score for an agent"""
        capability = self.agent_capabilities.get(agent.agent_id)
        if not capability:
            return 0.5

        return (
            capability.processing_power * 0.4
            + capability.success_rate * 0.4
            + (1.0 - capability.current_load) * 0.2
        )

    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True

        # For now, assume dependencies are task IDs that should be completed
        # In a real implementation, this would check against completed tasks
        return len(task.dependencies) == 0

    def _estimate_task_time(
        self, task: Task, agent_capability: AgentCapability
    ) -> float:
        """Estimate how long a task will take for a specific agent"""
        base_time = self._estimate_base_task_time(task)

        # Adjust for agent's processing power and specializations
        agent_multiplier = 1.0 / max(0.1, agent_capability.processing_power)

        # Specialization bonus
        task_tags = task.metadata.get("tags", [])
        if any(spec in task_tags for spec in agent_capability.specializations):
            agent_multiplier *= 0.8  # 20% faster for specialized tasks

        return base_time * agent_multiplier

    def _estimate_base_task_time(self, task: Task) -> float:
        """Estimate base time for a task"""
        # Simple heuristic based on complexity and command type
        base_time = task.complexity * 60.0  # Base: complexity * 60 seconds

        # Adjust based on command type
        if task.command:
            command = task.command[0].lower()
            if command in ["test", "pytest", "npm test"]:
                base_time *= 2.0  # Tests take longer
            elif command in ["build", "compile", "make"]:
                base_time *= 1.5  # Builds take longer
            elif command in ["lint", "format", "check"]:
                base_time *= 0.5  # Quick tasks

        return base_time

    def update_agent_load(self, agent_id: str, load: float) -> None:
        """Update current load for an agent"""
        capability = self.agent_capabilities.get(agent_id)
        if capability:
            capability.current_load = max(0.0, min(1.0, load))

    def get_scheduling_metrics(self) -> Dict[str, Any]:
        """Get current scheduling performance metrics"""
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
        efficiency_scores = [
            cap.processing_power * cap.success_rate
            for cap in self.agent_capabilities.values()
        ]
        avg_efficiency = (
            sum(efficiency_scores) / len(efficiency_scores)
            if efficiency_scores
            else 0.5
        )

        self.scheduling_metrics.update(
            {
                "load_balancing_score": load_balancing_score,
                "efficiency_score": avg_efficiency,
                "queue_size": len(self.priority_queue),
                "active_agents": len(
                    [
                        cap
                        for cap in self.agent_capabilities.values()
                        if cap.current_load > 0
                    ]
                ),
            }
        )

        return self.scheduling_metrics.copy()

    def rebalance_tasks(self) -> List[Tuple[str, str]]:
        """Rebalance tasks between agents if needed"""
        rebalancing_actions = []

        # Find overloaded and underloaded agents
        overloaded = []
        underloaded = []

        for agent_id, capability in self.agent_capabilities.items():
            if capability.current_load > 0.8:
                overloaded.append((agent_id, capability))
            elif capability.current_load < 0.3:
                underloaded.append((agent_id, capability))

        # For now, just log the need for rebalancing
        # In a full implementation, this would trigger task migration
        if overloaded and underloaded:
            logger.info(
                f"Rebalancing needed: {len(overloaded)} overloaded, {len(underloaded)} underloaded agents"
            )

            for overloaded_agent, _ in overloaded:
                for underloaded_agent, _ in underloaded:
                    rebalancing_actions.append((overloaded_agent, underloaded_agent))

        return rebalancing_actions

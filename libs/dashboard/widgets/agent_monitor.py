"""Agent monitoring widgets and metrics collection."""

from datetime import UTC, datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class MonitorDisplayMode(Enum):
    """Display modes for agent monitor."""
    OVERVIEW = "overview"
    DETAILED = "detailed"
    COMPACT = "compact"


@dataclass
class TaskMetrics:
    """Metrics for individual tasks."""
    task_id: str
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration: float = 0.0
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class AgentMetrics:
    """Comprehensive metrics for an agent."""
    agent_id: str
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    success_rate: float = 1.0
    current_load: float = 0.0
    task_history: List[TaskMetrics] = field(default_factory=list)
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score based on performance metrics."""
        if self.tasks_completed == 0:
            return 0.5  # Default score for new agents
        
        # Base score from success rate
        base_score = self.success_rate
        
        # Load adjustment (lower load is better for efficiency)
        load_adjustment = max(0, 1.0 - self.current_load)
        
        # Average task completion time adjustment
        time_factor = 1.0
        if self.task_history:
            avg_duration = sum(t.duration for t in self.task_history) / len(self.task_history)
            # Normalize around 30 seconds as baseline
            time_factor = min(1.0, 30.0 / max(1.0, avg_duration))
        
        return min(1.0, (base_score * 0.6 + load_adjustment * 0.2 + time_factor * 0.2))


class AgentMonitor:
    """Monitors and tracks agent performance metrics."""
    
    def __init__(self):
        self.agents: Dict[str, AgentMetrics] = {}
        self.display_mode = MonitorDisplayMode.OVERVIEW
        self.monitoring_active = False
    
    def register_agent(self, agent_id: str) -> None:
        """Register a new agent for monitoring."""
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMetrics(agent_id=agent_id)
    
    def update_agent_metrics(self, agent_id: str, **kwargs) -> None:
        """Update metrics for a specific agent."""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        metrics = self.agents[agent_id]
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
    
    def start_task(self, agent_id: str, task_id: str) -> None:
        """Start tracking a new task for an agent."""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        
        self.agents[agent_id].current_task = task_id
        task_metrics = TaskMetrics(task_id=task_id)
        self.agents[agent_id].task_history.append(task_metrics)
    
    def complete_task(self, agent_id: str, task_id: str, success: bool = True, error_message: Optional[str] = None) -> None:
        """Complete a task for an agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.current_task = None
            
            # Update task history
            for task in agent.task_history:
                if task.task_id == task_id and task.end_time is None:
                    task.end_time = datetime.now(UTC)
                    task.duration = (task.end_time - task.start_time).total_seconds()
                    task.success = success
                    task.error_message = error_message
                    break
            
            # Update agent metrics
            if success:
                agent.tasks_completed += 1
            else:
                agent.tasks_failed += 1
            
            # Recalculate success rate
            total_tasks = agent.tasks_completed + agent.tasks_failed
            if total_tasks > 0:
                agent.success_rate = agent.tasks_completed / total_tasks
    
    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent."""
        return self.agents.get(agent_id)
    
    def get_all_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents."""
        return self.agents.copy()
    
    def set_display_mode(self, mode: MonitorDisplayMode) -> None:
        """Set the display mode for the monitor."""
        self.display_mode = mode
    
    def start_monitoring(self) -> None:
        """Start active monitoring."""
        self.monitoring_active = True
    
    def stop_monitoring(self) -> None:
        """Stop active monitoring."""
        self.monitoring_active = False
    
    def clear_metrics(self) -> None:
        """Clear all agent metrics."""
        self.agents.clear()
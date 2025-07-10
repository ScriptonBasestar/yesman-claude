"""Multi-agent system for parallel branch-based development automation"""

from .branch_manager import BranchManager
from .task_analyzer import TaskAnalyzer, TaskDefinition, CodeDependency
from .graph import DirectedGraph
from .work_environment import WorkEnvironmentManager, WorkEnvironment
from .agent_pool import AgentPool, Agent, Task, AgentState, TaskStatus

__all__ = [
    "BranchManager",
    "TaskAnalyzer",
    "TaskDefinition",
    "CodeDependency",
    "DirectedGraph",
    "WorkEnvironmentManager",
    "WorkEnvironment",
    "AgentPool",
    "Agent",
    "Task",
    "AgentState",
    "TaskStatus",
]

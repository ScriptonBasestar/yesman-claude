"""Multi-agent system for parallel branch-based development automation"""

from .branch_manager import BranchManager
from .task_analyzer import TaskAnalyzer, TaskDefinition, CodeDependency
from .graph import DirectedGraph
from .work_environment import WorkEnvironmentManager, WorkEnvironment
from .types import Agent, Task, AgentState, TaskStatus
from .agent_pool import AgentPool
from .task_scheduler import TaskScheduler, AgentCapability
from .conflict_resolution import (
    ConflictResolutionEngine, 
    ConflictInfo, 
    ConflictType, 
    ConflictSeverity, 
    ResolutionStrategy,
    ResolutionResult
)
from .conflict_prediction import (
    ConflictPredictor,
    PredictionResult,
    PredictionConfidence,
    ConflictPattern,
    ConflictVector
)

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
    "TaskScheduler",
    "AgentCapability",
    "ConflictResolutionEngine",
    "ConflictInfo",
    "ConflictType",
    "ConflictSeverity",
    "ResolutionStrategy",
    "ResolutionResult",
    "ConflictPredictor",
    "PredictionResult",
    "PredictionConfidence",
    "ConflictPattern",
    "ConflictVector",
]

"""Multi-agent system for parallel branch-based development automation"""

from .branch_manager import BranchManager
from .task_analyzer import TaskAnalyzer, TaskDefinition, CodeDependency
from .graph import DirectedGraph

__all__ = [
    "BranchManager",
    "TaskAnalyzer",
    "TaskDefinition",
    "CodeDependency",
    "DirectedGraph",
]

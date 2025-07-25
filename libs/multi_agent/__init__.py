# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Multi-agent system for parallel branch-based development automation."""

from .agent_pool import AgentPool
from .auto_resolver import (
    AutoResolutionMode,
    AutoResolutionResult,
    AutoResolver,
    ResolutionOutcome,
)
from .branch_info_protocol import (
    BranchInfo,
    BranchInfoProtocol,
    BranchInfoType,
    BranchSyncEvent,
    SyncStrategy,
)
from .branch_manager import BranchManager
from .code_review_engine import (
    CodeReview,
    CodeReviewEngine,
    QualityMetric,
    QualityMetrics,
    ReviewFinding,
    ReviewSeverity,
    ReviewStatus,
    ReviewSummary,
    ReviewType,
)
from .collaboration_engine import (
    CollaborationEngine,
    CollaborationMessage,
    CollaborationMode,
    CollaborationSession,
    MessagePriority,
    MessageType,
    SharedKnowledge,
)
from .conflict_prediction import (
    ConflictPattern,
    ConflictPredictor,
    ConflictVector,
    PredictionConfidence,
    PredictionResult,
)
from .conflict_prevention import (
    ConflictPreventionSystem,
    PreventionAction,
    PreventionMeasure,
    PreventionResult,
    PreventionStrategy,
)
from .conflict_resolution import (
    ConflictInfo,
    ConflictResolutionEngine,
    ConflictSeverity,
    ConflictType,
    ResolutionResult,
    ResolutionStrategy,
)
from .dependency_propagation import (
    ChangeImpact,
    DependencyChange,
    DependencyNode,
    DependencyPropagationSystem,
    DependencyType,
    PropagationResult,
    PropagationStrategy,
)
from .graph import DirectedGraph
from .semantic_analyzer import (
    ClassDefinition,
    FunctionSignature,
    SemanticAnalyzer,
    SemanticConflict,
    SemanticConflictType,
    SemanticContext,
    SymbolVisibility,
)
from .semantic_merger import (
    ConflictResolutionRule,
    MergeResolution,
    MergeResult,
    MergeStrategy,
    SemanticMerger,
)
from .task_analyzer import CodeDependency, TaskAnalyzer, TaskDefinition
from .task_scheduler import AgentCapability, TaskScheduler
from .types import Agent, AgentState, Task, TaskStatus
from .work_environment import WorkEnvironment, WorkEnvironmentManager

__all__ = [
    "Agent",
    "AgentCapability",
    "AgentPool",
    "AgentState",
    "AutoResolutionMode",
    "AutoResolutionResult",
    "AutoResolver",
    "BranchInfo",
    "BranchInfoProtocol",
    "BranchInfoType",
    "BranchManager",
    "BranchSyncEvent",
    "ChangeImpact",
    "ClassDefinition",
    "CodeDependency",
    "CodeReview",
    "CodeReviewEngine",
    "CollaborationEngine",
    "CollaborationMessage",
    "CollaborationMode",
    "CollaborationSession",
    "ConflictInfo",
    "ConflictPattern",
    "ConflictPredictor",
    "ConflictPreventionSystem",
    "ConflictResolutionEngine",
    "ConflictResolutionRule",
    "ConflictSeverity",
    "ConflictType",
    "ConflictVector",
    "DependencyChange",
    "DependencyNode",
    "DependencyPropagationSystem",
    "DependencyType",
    "DirectedGraph",
    "FunctionSignature",
    "MergeResolution",
    "MergeResult",
    "MergeStrategy",
    "MessagePriority",
    "MessageType",
    "PredictionConfidence",
    "PredictionResult",
    "PreventionAction",
    "PreventionMeasure",
    "PreventionResult",
    "PreventionStrategy",
    "PropagationResult",
    "PropagationStrategy",
    "QualityMetric",
    "QualityMetrics",
    "ResolutionOutcome",
    "ResolutionResult",
    "ResolutionStrategy",
    "ReviewFinding",
    "ReviewSeverity",
    "ReviewStatus",
    "ReviewSummary",
    "ReviewType",
    "SemanticAnalyzer",
    "SemanticConflict",
    "SemanticConflictType",
    "SemanticContext",
    "SemanticMerger",
    "SharedKnowledge",
    "SymbolVisibility",
    "SyncStrategy",
    "Task",
    "TaskAnalyzer",
    "TaskDefinition",
    "TaskScheduler",
    "TaskStatus",
    "WorkEnvironment",
    "WorkEnvironmentManager",
]

# Copyright notice.

from .agent_pool import AgentPool
from .auto_resolver import (
from .branch_info_protocol import (
from .branch_manager import BranchManager
from .code_review_engine import (
from .collaboration_engine import (
from .conflict_prediction import (
from .conflict_prevention import (
from .conflict_resolution import (
from .dependency_propagation import (
from .graph import DirectedGraph
from .semantic_analyzer import (
from .semantic_merger import (
from .task_analyzer import CodeDependency, TaskAnalyzer, TaskDefinition
from .task_scheduler import AgentCapability, TaskScheduler
from .types import Agent, AgentState, Task, TaskStatus
from .work_environment import WorkEnvironment, WorkEnvironmentManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Multi-agent system for parallel branch-based development automation."""

    AutoResolutionMode,
    AutoResolutionResult,
    AutoResolver,
    ResolutionOutcome,
)
    BranchInfo,
    BranchInfoProtocol,
    BranchInfoType,
    BranchSyncEvent,
    SyncStrategy,
)
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
    CollaborationEngine,
    CollaborationMessage,
    CollaborationMode,
    CollaborationSession,
    MessagePriority,
    MessageType,
    SharedKnowledge,
)
    ConflictPattern,
    ConflictPredictor,
    ConflictVector,
    PredictionConfidence,
    PredictionResult,
)
    ConflictPreventionSystem,
    PreventionAction,
    PreventionMeasure,
    PreventionResult,
    PreventionStrategy,
)
    ConflictInfo,
    ConflictResolutionEngine,
    ConflictSeverity,
    ConflictType,
    ResolutionResult,
    ResolutionStrategy,
)
    ChangeImpact,
    DependencyChange,
    DependencyNode,
    DependencyPropagationSystem,
    DependencyType,
    PropagationResult,
    PropagationStrategy,
)
    ClassDefinition,
    FunctionSignature,
    SemanticAnalyzer,
    SemanticConflict,
    SemanticConflictType,
    SemanticContext,
    SymbolVisibility,
)
    ConflictResolutionRule,
    MergeResolution,
    MergeResult,
    MergeStrategy,
    SemanticMerger,
)

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

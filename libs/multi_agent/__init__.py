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
    ResolutionResult,
)
from .conflict_prediction import (
    ConflictPredictor,
    PredictionResult,
    PredictionConfidence,
    ConflictPattern,
    ConflictVector,
)
from .semantic_analyzer import (
    SemanticAnalyzer,
    SemanticConflict,
    SemanticConflictType,
    FunctionSignature,
    ClassDefinition,
    SemanticContext,
    SymbolVisibility,
)
from .semantic_merger import (
    SemanticMerger,
    MergeStrategy,
    MergeResolution,
    MergeResult,
    ConflictResolutionRule,
)
from .auto_resolver import (
    AutoResolver,
    AutoResolutionMode,
    ResolutionOutcome,
    AutoResolutionResult,
)
from .collaboration_engine import (
    CollaborationEngine,
    CollaborationMode,
    MessageType,
    MessagePriority,
    CollaborationMessage,
    SharedKnowledge,
    CollaborationSession,
)
from .branch_info_protocol import (
    BranchInfoProtocol,
    BranchInfo,
    BranchInfoType,
    SyncStrategy,
    BranchSyncEvent,
)
from .dependency_propagation import (
    DependencyPropagationSystem,
    DependencyType,
    ChangeImpact,
    PropagationStrategy,
    DependencyNode,
    DependencyChange,
    PropagationResult,
)
from .code_review_engine import (
    CodeReviewEngine,
    ReviewType,
    ReviewSeverity,
    ReviewStatus,
    QualityMetric,
    ReviewFinding,
    QualityMetrics,
    CodeReview,
    ReviewSummary,
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
    "SemanticAnalyzer",
    "SemanticConflict",
    "SemanticConflictType",
    "FunctionSignature",
    "ClassDefinition",
    "SemanticContext",
    "SymbolVisibility",
    "SemanticMerger",
    "MergeStrategy",
    "MergeResolution",
    "MergeResult",
    "ConflictResolutionRule",
    "AutoResolver",
    "AutoResolutionMode",
    "ResolutionOutcome",
    "AutoResolutionResult",
    "CollaborationEngine",
    "CollaborationMode",
    "MessageType",
    "MessagePriority",
    "CollaborationMessage",
    "SharedKnowledge",
    "CollaborationSession",
    "BranchInfoProtocol",
    "BranchInfo",
    "BranchInfoType",
    "SyncStrategy",
    "BranchSyncEvent",
    "DependencyPropagationSystem",
    "DependencyType",
    "ChangeImpact",
    "PropagationStrategy",
    "DependencyNode",
    "DependencyChange",
    "PropagationResult",
    "CodeReviewEngine",
    "ReviewType",
    "ReviewSeverity",
    "ReviewStatus",
    "QualityMetric",
    "ReviewFinding",
    "QualityMetrics",
    "CodeReview",
    "ReviewSummary",
]

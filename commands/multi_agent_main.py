# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

from commands.multi_agent.agent_pool import (
    AddTaskCommand,
    ListTasksCommand,
    MonitorAgentsCommand,
    StartAgentsCommand,
    StatusCommand,
    StopAgentsCommand,
)
from commands.multi_agent.batch_operations import (
    AutoResolveCommand,
    BatchMergeCommand,
    PreventConflictsCommand,
)
from commands.multi_agent.cli import multi_agent
from commands.multi_agent.code_review import (
    QualityCheckCommand,
    ReviewApproveCommand,
    ReviewInitiateCommand,
    ReviewRejectCommand,
    ReviewStatusCommand,
    ReviewSummaryCommand,
)
from commands.multi_agent.collaboration import (
    BranchInfoCommand,
    CollaborateCommand,
    SendMessageCommand,
    ShareKnowledgeCommand,
)
from commands.multi_agent.conflict_prediction import (
    AnalyzeConflictPatternsCommand,
    PredictConflictsCommand,
    PredictionSummaryCommand,
)
from commands.multi_agent.conflict_resolution import (
    ConflictSummaryCommand,
    DetectConflictsCommand,
    ResolveConflictCommand,
)
from commands.multi_agent.dependency_tracking import (
    DependencyImpactCommand,
    DependencyPropagateCommand,
    DependencyStatusCommand,
    DependencyTrackCommand,
)
from commands.multi_agent.semantic_analysis import (
    AnalyzeSemanticConflictsCommand,
    FunctionDiffCommand,
    SemanticMergeCommand,
    SemanticSummaryCommand,
)

# Export the CLI group and classes
__all__ = [
    "AddTaskCommand",
    "AnalyzeConflictPatternsCommand",
    # Semantic Analysis
    "AnalyzeSemanticConflictsCommand",
    "AutoResolveCommand",
    # Batch Operations
    "BatchMergeCommand",
    "BranchInfoCommand",
    # Collaboration
    "CollaborateCommand",
    "ConflictSummaryCommand",
    "DependencyImpactCommand",
    "DependencyPropagateCommand",
    "DependencyStatusCommand",
    # Dependency Tracking
    "DependencyTrackCommand",
    # Conflict Resolution
    "DetectConflictsCommand",
    "FunctionDiffCommand",
    "ListTasksCommand",
    "MonitorAgentsCommand",
    # Conflict Prediction
    "PredictConflictsCommand",
    "PredictionSummaryCommand",
    "PreventConflictsCommand",
    "QualityCheckCommand",
    "ResolveConflictCommand",
    "ReviewApproveCommand",
    # Code Review
    "ReviewInitiateCommand",
    "ReviewRejectCommand",
    "ReviewStatusCommand",
    "ReviewSummaryCommand",
    "SemanticMergeCommand",
    "SemanticSummaryCommand",
    "SendMessageCommand",
    "ShareKnowledgeCommand",
    # Agent Pool Management
    "StartAgentsCommand",
    "StatusCommand",
    "StopAgentsCommand",
    "multi_agent",
]

"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Multi-agent system commands - Modular Architecture.

This file has been refactored from a monolithic 3,434-line file into a modular
architecture for better maintainability, development velocity, and code organization.

Original file backed up as: commands/multi_agent_backup.py

New modular structure:
- commands/multi_agent/agent_pool.py - Agent pool management
- commands/multi_agent/conflict_resolution.py - Conflict detection and resolution
- commands/multi_agent/conflict_prediction.py - Conflict prediction and analysis
- commands/multi_agent/semantic_analysis.py - AST-based semantic analysis
- commands/multi_agent/batch_operations.py - Batch operations and auto-resolution
- commands/multi_agent/collaboration.py - Agent collaboration features
- commands/multi_agent/dependency_tracking.py - Dependency management
- commands/multi_agent/code_review.py - Code review system
- commands/multi_agent/cli.py - CLI registration and coordination

Benefits of this refactoring:
- 9 focused modules averaging 300-400 lines each vs 1 monolithic 3,434-line file
- Clear separation of concerns and responsibilities
- Easier parallel development and testing
- Reduced import complexity and circular dependencies
- Better code discoverability and navigation
- Simplified debugging and maintenance
"""

# Import the main CLI group from the modular structure
# Import all command classes for backward compatibility
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

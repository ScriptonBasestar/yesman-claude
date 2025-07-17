#!/usr/bin/env python3
"""
Tests for the modular multi-agent system
"""


# Test that all command classes can be imported from the modular structure
def test_agent_pool_imports():
    """Test agent pool command imports"""
    from commands.multi_agent.agent_pool import AddTaskCommand, ListTasksCommand, MonitorAgentsCommand, StartAgentsCommand, StatusCommand, StopAgentsCommand

    # Verify classes are BaseCommand subclasses
    from libs.core.base_command import BaseCommand

    assert issubclass(StartAgentsCommand, BaseCommand)
    assert issubclass(MonitorAgentsCommand, BaseCommand)
    assert issubclass(StatusCommand, BaseCommand)
    assert issubclass(StopAgentsCommand, BaseCommand)
    assert issubclass(AddTaskCommand, BaseCommand)
    assert issubclass(ListTasksCommand, BaseCommand)


def test_conflict_resolution_imports():
    """Test conflict resolution command imports"""
    from commands.multi_agent.conflict_resolution import ConflictSummaryCommand, DetectConflictsCommand, ResolveConflictCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(DetectConflictsCommand, BaseCommand)
    assert issubclass(ResolveConflictCommand, BaseCommand)
    assert issubclass(ConflictSummaryCommand, BaseCommand)


def test_conflict_prediction_imports():
    """Test conflict prediction command imports"""
    from commands.multi_agent.conflict_prediction import AnalyzeConflictPatternsCommand, PredictConflictsCommand, PredictionSummaryCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(PredictConflictsCommand, BaseCommand)
    assert issubclass(PredictionSummaryCommand, BaseCommand)
    assert issubclass(AnalyzeConflictPatternsCommand, BaseCommand)


def test_semantic_analysis_imports():
    """Test semantic analysis command imports"""
    from commands.multi_agent.semantic_analysis import AnalyzeSemanticConflictsCommand, FunctionDiffCommand, SemanticMergeCommand, SemanticSummaryCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(AnalyzeSemanticConflictsCommand, BaseCommand)
    assert issubclass(SemanticSummaryCommand, BaseCommand)
    assert issubclass(FunctionDiffCommand, BaseCommand)
    assert issubclass(SemanticMergeCommand, BaseCommand)


def test_batch_operations_imports():
    """Test batch operations command imports"""
    from commands.multi_agent.batch_operations import AutoResolveCommand, BatchMergeCommand, PreventConflictsCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(BatchMergeCommand, BaseCommand)
    assert issubclass(AutoResolveCommand, BaseCommand)
    assert issubclass(PreventConflictsCommand, BaseCommand)


def test_collaboration_imports():
    """Test collaboration command imports"""
    from commands.multi_agent.collaboration import BranchInfoCommand, CollaborateCommand, SendMessageCommand, ShareKnowledgeCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(CollaborateCommand, BaseCommand)
    assert issubclass(SendMessageCommand, BaseCommand)
    assert issubclass(ShareKnowledgeCommand, BaseCommand)
    assert issubclass(BranchInfoCommand, BaseCommand)


def test_dependency_tracking_imports():
    """Test dependency tracking command imports"""
    from commands.multi_agent.dependency_tracking import DependencyImpactCommand, DependencyPropagateCommand, DependencyStatusCommand, DependencyTrackCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(DependencyTrackCommand, BaseCommand)
    assert issubclass(DependencyStatusCommand, BaseCommand)
    assert issubclass(DependencyImpactCommand, BaseCommand)
    assert issubclass(DependencyPropagateCommand, BaseCommand)


def test_code_review_imports():
    """Test code review command imports"""
    from commands.multi_agent.code_review import QualityCheckCommand, ReviewApproveCommand, ReviewInitiateCommand, ReviewRejectCommand, ReviewStatusCommand, ReviewSummaryCommand
    from libs.core.base_command import BaseCommand

    assert issubclass(ReviewInitiateCommand, BaseCommand)
    assert issubclass(ReviewApproveCommand, BaseCommand)
    assert issubclass(ReviewRejectCommand, BaseCommand)
    assert issubclass(ReviewStatusCommand, BaseCommand)
    assert issubclass(QualityCheckCommand, BaseCommand)
    assert issubclass(ReviewSummaryCommand, BaseCommand)


def test_backward_compatibility():
    """Test that the main multi_agent.py still exports all command classes"""
    from commands.multi_agent import DetectConflictsCommand, StartAgentsCommand

    # Sample test to ensure backward compatibility works
    from libs.core.base_command import BaseCommand

    assert issubclass(StartAgentsCommand, BaseCommand)
    assert issubclass(DetectConflictsCommand, BaseCommand)


def test_cli_registration():
    """Test that CLI commands are properly registered"""
    import click

    from commands.multi_agent.cli import multi_agent

    # Verify it's a click group
    assert isinstance(multi_agent, click.Group)

    # Verify some key commands are registered
    command_names = list(multi_agent.commands.keys())

    # Agent pool commands
    assert "start" in command_names
    assert "monitor" in command_names
    assert "status" in command_names
    assert "stop" in command_names
    assert "add-task" in command_names
    assert "list-tasks" in command_names

    # Conflict resolution commands
    assert "detect-conflicts" in command_names
    assert "resolve-conflict" in command_names
    assert "conflict-summary" in command_names

    # Should have significant number of commands
    assert len(command_names) >= 20


def test_module_structure():
    """Test the overall module structure"""
    import commands.multi_agent

    # Verify package structure
    assert hasattr(commands.multi_agent, "agent_pool")
    assert hasattr(commands.multi_agent, "conflict_resolution")
    assert hasattr(commands.multi_agent, "semantic_analysis")

    # Verify main CLI export
    assert hasattr(commands.multi_agent, "multi_agent")


def test_file_organization():
    """Test that files are properly organized"""
    from pathlib import Path

    multi_agent_dir = Path("commands/multi_agent")
    assert multi_agent_dir.exists()
    assert multi_agent_dir.is_dir()

    # Check required files exist
    required_files = [
        "__init__.py",
        "agent_pool.py",
        "conflict_resolution.py",
        "conflict_prediction.py",
        "semantic_analysis.py",
        "batch_operations.py",
        "collaboration.py",
        "dependency_tracking.py",
        "code_review.py",
        "cli.py",
    ]

    for file_name in required_files:
        file_path = multi_agent_dir / file_name
        assert file_path.exists(), f"Missing required file: {file_name}"
        assert file_path.is_file(), f"Not a file: {file_name}"


class TestCommandExecution:
    """Test that commands can be instantiated and have execute methods"""

    def test_agent_pool_commands_executable(self):
        """Test that agent pool commands can be instantiated"""
        from commands.multi_agent.agent_pool import StartAgentsCommand

        command = StartAgentsCommand()
        assert hasattr(command, "execute")
        assert callable(command.execute)

    def test_conflict_resolution_commands_executable(self):
        """Test that conflict resolution commands can be instantiated"""
        from commands.multi_agent.conflict_resolution import DetectConflictsCommand

        command = DetectConflictsCommand()
        assert hasattr(command, "execute")
        assert callable(command.execute)

    def test_semantic_analysis_commands_executable(self):
        """Test that semantic analysis commands can be instantiated"""
        from commands.multi_agent.semantic_analysis import FunctionDiffCommand

        command = FunctionDiffCommand()
        assert hasattr(command, "execute")
        assert callable(command.execute)


class TestRefactoringBenefits:
    """Test the benefits of the refactoring"""

    def test_reduced_file_sizes(self):
        """Test that individual files are much smaller than original"""
        import os

        # Original backup file
        backup_size = os.path.getsize("commands/multi_agent_backup.py")

        # New main file
        main_size = os.path.getsize("commands/multi_agent.py")

        # Individual module files
        from pathlib import Path

        multi_agent_dir = Path("commands/multi_agent")

        module_files = ["agent_pool.py", "conflict_resolution.py", "semantic_analysis.py", "cli.py"]

        for file_name in module_files:
            file_path = multi_agent_dir / file_name
            if file_path.exists():
                module_size = os.path.getsize(file_path)
                # Each module should be significantly smaller than original
                assert module_size < backup_size / 4, f"{file_name} is too large relative to original"

        # New main file should be much smaller
        assert main_size < backup_size / 10, "Main file should be much smaller after refactoring"

    def test_focused_responsibilities(self):
        """Test that each module has focused responsibilities"""
        # Agent pool module should only have agent-related commands
        from commands.multi_agent import agent_pool

        agent_classes = [name for name in dir(agent_pool) if name.endswith("Command") and not name.startswith("_") and name != "BaseCommand"]

        # All agent pool commands should be related to agent management
        for class_name in agent_classes:
            assert any(keyword in class_name.lower() for keyword in ["agent", "start", "stop", "monitor", "status", "task"]), f"Agent pool command {class_name} seems misplaced"

        # Conflict resolution module should only have conflict-related commands
        from commands.multi_agent import conflict_resolution

        conflict_classes = [name for name in dir(conflict_resolution) if name.endswith("Command") and not name.startswith("_") and name != "BaseCommand"]

        for class_name in conflict_classes:
            assert any(keyword in class_name.lower() for keyword in ["conflict", "detect", "resolve", "summary"]), f"Conflict resolution command {class_name} seems misplaced"

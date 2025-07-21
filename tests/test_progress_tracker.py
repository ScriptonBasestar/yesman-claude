"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test progress tracking functionality."""

from libs.core.models import SessionProgress, TaskPhase, TaskProgress
from libs.core.progress_tracker import ProgressAnalyzer


class TestTaskProgress:
    """Test TaskProgress model."""

    @staticmethod
    def test_phase_update() -> None:
        """Test phase updates and progress calculation."""
        task = TaskProgress()
        assert task.phase == TaskPhase.IDLE
        assert task.overall_progress == 0.0

        # Update to analyzing phase
        task.update_phase(TaskPhase.ANALYZING)
        assert task.phase == TaskPhase.ANALYZING
        assert task.phase_progress == 0.0

        # Set phase progress
        task.phase_progress = 50.0
        task._recalculate_overall_progress()
        # Analyzing phase has 0.2 weight, so 50% of 0.2 = 0.1 = 10%
        assert task.overall_progress == 10.0

    @staticmethod
    def test_phase_progression() -> None:
        """Test progression through all phases."""
        task = TaskProgress()

        # Starting phase (10% weight)
        task.update_phase(TaskPhase.STARTING)
        task.phase_progress = 100.0
        task._recalculate_overall_progress()
        assert task.overall_progress == 10.0

        # Analyzing phase (20% weight)
        task.update_phase(TaskPhase.ANALYZING)
        task.phase_progress = 100.0
        task._recalculate_overall_progress()
        assert task.overall_progress == 30.0  # 10% + 20%

        # Implementing phase (50% weight)
        task.update_phase(TaskPhase.IMPLEMENTING)
        task.phase_progress = 100.0
        task._recalculate_overall_progress()
        assert task.overall_progress == 80.0  # 10% + 20% + 50%

        # Testing phase (15% weight)
        task.update_phase(TaskPhase.TESTING)
        task.phase_progress = 100.0
        task._recalculate_overall_progress()
        assert task.overall_progress == 95.0  # 10% + 20% + 50% + 15%

        # Completing phase (5% weight)
        task.update_phase(TaskPhase.COMPLETING)
        task.phase_progress = 100.0
        task._recalculate_overall_progress()
        assert task.overall_progress == 100.0

    @staticmethod
    def test_to_dict() -> None:
        """Test serialization to dictionary."""
        task = TaskProgress()
        task.files_created = 3
        task.files_modified = 5
        task.commands_executed = 10
        task.commands_succeeded = 8
        task.commands_failed = 2

        data = task.to_dict()
        assert data["files_created"] == 3
        assert data["files_modified"] == 5
        assert data["commands_executed"] == 10
        assert data["commands_succeeded"] == 8
        assert data["commands_failed"] == 2


class TestSessionProgress:
    """Test SessionProgress model."""

    @staticmethod
    def test_add_task() -> None:
        """Test adding tasks to session."""
        session = SessionProgress(session_name="test-session")
        assert len(session.tasks) == 0

        task1 = session.add_task()
        assert len(session.tasks) == 1
        assert session.current_task_index == 0
        assert session.get_current_task() == task1

        task2 = session.add_task()
        assert len(session.tasks) == 2
        assert session.current_task_index == 1
        assert session.get_current_task() == task2

    @staticmethod
    def test_overall_progress() -> None:
        """Test overall progress calculation."""
        session = SessionProgress(session_name="test-session")

        # No tasks
        assert session.calculate_overall_progress() == 0.0

        # Add tasks with different progress
        task1 = session.add_task()
        task1.overall_progress = 100.0

        task2 = session.add_task()
        task2.overall_progress = 50.0

        # Average of 100% and 50% = 75%
        assert session.calculate_overall_progress() == 75.0

    @staticmethod
    def test_aggregate_updates() -> None:
        """Test aggregate metric updates."""
        session = SessionProgress(session_name="test-session")

        task1 = session.add_task()
        task1.files_created = 2
        task1.files_modified = 3
        task1.commands_executed = 5
        task1.todos_completed = 1

        task2 = session.add_task()
        task2.files_created = 1
        task2.files_modified = 2
        task2.commands_executed = 3
        task2.todos_completed = 2

        session.update_aggregates()

        assert session.total_files_changed == 8  # (2+3) + (1+2)
        assert session.total_commands == 8  # 5 + 3
        assert session.total_todos_completed == 3  # 1 + 2


class TestProgressAnalyzer:
    """Test ProgressAnalyzer functionality."""

    @staticmethod
    def test_phase_detection() -> None:
        """Test phase detection from output."""
        analyzer = ProgressAnalyzer()

        # Test starting phase
        output = [
            "I'll help you implement this feature",
            "Let me begin by analyzing the code",
        ]
        progress = analyzer.analyze_pane_output("test-session", output)
        assert progress.get_current_task().phase == TaskPhase.STARTING

        # Test analyzing phase
        output = [
            "Analyzing the existing codebase",
            "Let me check the current implementation",
        ]
        progress = analyzer.analyze_pane_output("test-session", output)
        assert progress.get_current_task().phase == TaskPhase.ANALYZING

        # Test implementing phase
        output = ["Now I'll implement the new feature", "Creating the new component"]
        progress = analyzer.analyze_pane_output("test-session", output)
        assert progress.get_current_task().phase == TaskPhase.IMPLEMENTING

    @staticmethod
    def test_file_activity_analysis() -> None:
        """Test file activity detection."""
        analyzer = ProgressAnalyzer()

        output = [
            "Created new file: src/components/Widget.tsx",
            "Modified existing file: src/app.tsx",
            "Updated configuration in config.json",
        ]

        progress = analyzer.analyze_pane_output("test-session", output)
        task = progress.get_current_task()

        assert task.files_created >= 1
        assert task.files_modified >= 1

    @staticmethod
    def test_command_activity_analysis() -> None:
        """Test command execution detection."""
        analyzer = ProgressAnalyzer()

        output = [
            "$ npm install",
            "✓ All dependencies installed successfully",
            "$ pytest tests/",
            "✗ 2 tests failed",
            "$ npm run build",
            "Build completed successfully",
        ]

        progress = analyzer.analyze_pane_output("test-session", output)
        task = progress.get_current_task()

        assert task.commands_executed >= 3
        assert task.commands_succeeded >= 2
        assert task.commands_failed >= 1

    @staticmethod
    def test_todo_activity_analysis() -> None:
        """Test TODO tracking."""
        analyzer = ProgressAnalyzer()

        output = [
            "TODO: Implement error handling",
            "TODO: Add unit tests",
            "✓ Completed TODO: Setup project structure",
        ]

        progress = analyzer.analyze_pane_output("test-session", output)
        task = progress.get_current_task()

        assert task.todos_identified >= 2
        assert task.todos_completed >= 1

    @staticmethod
    def test_session_persistence() -> None:
        """Test that analyzer maintains session state."""
        analyzer = ProgressAnalyzer()

        # First analysis
        output1 = ["Starting the implementation"]
        progress1 = analyzer.analyze_pane_output("test-session", output1)
        assert len(progress1.tasks) == 1

        # Second analysis on same session
        output2 = ["Continuing with the implementation"]
        progress2 = analyzer.analyze_pane_output("test-session", output2)
        assert progress2 == progress1  # Same object
        assert len(progress2.tasks) == 1  # Still one task

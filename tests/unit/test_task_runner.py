"""Tests for task runner functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.task_runner import TaskRunner, TodoFile, TodoTask


class TestTodoTask:
    """Test TodoTask class."""

    def test_task_creation(self) -> None:
        """Test creating todo tasks."""
        task = TodoTask("Complete feature X", completed=False)
        assert task.content == "Complete feature X"
        assert not task.completed
        assert not task.skipped

    def test_task_str_representation(self) -> None:
        """Test string representation of tasks."""
        incomplete = TodoTask("Todo item")
        completed = TodoTask("Done item", completed=True)
        skipped = TodoTask("Skipped item", skipped=True)

        assert str(incomplete) == "[ ] Todo item"
        assert str(completed) == "[x] Done item"
        assert str(skipped) == "[>] Skipped item"


class TestTodoFile:
    """Test TodoFile class."""

    def test_parse_todo_file(self) -> None:
        """Test parsing todo markdown file."""
        content = """# Test File

## Tasks
- [ ] Task 1
- [x] Task 2 completed
- [>] Task 3 skipped
- [ ] ] Task 4 with double bracket

Regular text here.

- [ ] Task 5
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                todo_file = TodoFile(f.name)

                assert len(todo_file.tasks) == 5
                assert todo_file.tasks[0].content == "Task 1"
                assert not todo_file.tasks[0].completed

                assert todo_file.tasks[1].content == "Task 2 completed"
                assert todo_file.tasks[1].completed

                assert todo_file.tasks[2].content == "Task 3 skipped"
                assert todo_file.tasks[2].skipped

                assert todo_file.tasks[3].content == "Task 4 with double bracket"
                assert not todo_file.tasks[3].completed

                assert todo_file.tasks[4].content == "Task 5"
                assert not todo_file.tasks[4].completed

            finally:
                os.unlink(f.name)

    def test_get_next_incomplete_task(self) -> None:
        """Test finding next incomplete task."""
        content = """# Test
- [x] Completed task
- [ ] Next task
- [ ] Another task
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                todo_file = TodoFile(f.name)
                next_task = todo_file.get_next_incomplete_task()

                assert next_task is not None
                assert next_task.content == "Next task"

            finally:
                os.unlink(f.name)

    def test_all_completed_check(self) -> None:
        """Test checking if all tasks are completed."""
        all_done_content = """# Test
- [x] Task 1
- [x] Task 2
- [>] Skipped task
"""

        incomplete_content = """# Test
- [x] Task 1
- [ ] Incomplete task
- [>] Skipped task
"""

        # Test all completed
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(all_done_content)
            f.flush()

            try:
                todo_file = TodoFile(f.name)
                assert todo_file.is_all_completed()
            finally:
                os.unlink(f.name)

        # Test incomplete
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(incomplete_content)
            f.flush()

            try:
                todo_file = TodoFile(f.name)
                assert not todo_file.is_all_completed()
            finally:
                os.unlink(f.name)


class TestTaskRunner:
    """Test TaskRunner class."""

    def test_analyze_task_dependencies(self) -> None:
        """Test task dependency analysis."""
        runner = TaskRunner("test/todo")

        # Simple task should not be broken down
        simple_task = TodoTask("Fix typo in readme")
        subtasks = runner.analyze_task_dependencies(simple_task)
        assert len(subtasks) == 0

        # Complex task should be broken down
        complex_task = TodoTask("Implement comprehensive user authentication system with OAuth2, JWT tokens, password reset, email verification, and role-based access control")
        subtasks = runner.analyze_task_dependencies(complex_task)
        assert len(subtasks) == 5
        assert "Analyze requirements" in subtasks[0]

    def test_find_todo_files(self) -> None:
        """Test finding todo files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test directory structure
            todo_dir = Path(tmpdir) / "todo"
            todo_dir.mkdir()

            # Create test files
            (todo_dir / "01-task.md").write_text("# Task 1\n- [ ] Do something")
            (todo_dir / "README.md").write_text("# Readme")  # Should be ignored
            (todo_dir / "02-task.md").write_text("# Task 2\n- [ ] Do something else")

            runner = TaskRunner(str(todo_dir))
            todo_files = runner.find_todo_files()

            # Should find 2 files (ignoring README.md)
            assert len(todo_files) == 2
            assert any("01-task.md" in str(f) for f in todo_files)
            assert any("02-task.md" in str(f) for f in todo_files)
            assert not any("README.md" in str(f) for f in todo_files)

    @patch("subprocess.run")
    def test_commit_changes(self, mock_run: MagicMock) -> None:
        """Test committing changes."""
        mock_run.return_value.returncode = 0

        runner = TaskRunner("test/todo")
        task = TodoTask("Complete feature X")

        result = runner.commit_changes(task, [])

        assert result
        assert mock_run.call_count == 2  # git add and git commit

        # Check git add was called
        add_call = mock_run.call_args_list[0]
        assert add_call[0][0] == ["git", "add", "."]

        # Check git commit was called with proper message
        commit_call = mock_run.call_args_list[1]
        assert commit_call[0][0][0] == "git"
        assert commit_call[0][0][1] == "commit"
        assert commit_call[0][0][2] == "-m"
        assert "feat(task-runner):" in commit_call[0][0][3]

    @patch("subprocess.run")
    def test_run_tests(self, mock_run: MagicMock) -> None:
        """Test running tests."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "All tests passed"
        mock_run.return_value.stderr = ""

        runner = TaskRunner("test/todo")
        result = runner.run_tests()

        assert result
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["python", "-m", "pytest", "--tb=short"]


if __name__ == "__main__":
    pytest.main([__file__])

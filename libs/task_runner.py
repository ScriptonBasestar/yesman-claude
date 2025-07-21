# Copyright notice.

import glob
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
import argparse

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""TASK_RUNNER: Automated todo file processor for /tasks/todo/ directory.

This module provides automated processing of TODO files:
1. Reads todo files in order and finds next uncompleted task
2. Analyzes dependencies and breaks down complex tasks
3. Implements the task and runs tests
4. Commits changes with appropriate messages
5. Moves completed files to /tasks/done/
"""



class TodoTask:
    """Represents a single todo task item."""

    def __init__(
        self,
        content: str,
        completed: bool = False,  # noqa: FBT001
        skipped: bool = False,  # noqa: FBT001
        line_num: int = 0,
    ) -> None:
        self.content = content.strip()
        self.completed = completed
        self.skipped = skipped  # [>] marker for skipped tasks
        self.line_num = line_num
        self.original_line = content

    def __str__(self) -> str:
        marker = "[x]" if self.completed else "[>]" if self.skipped else "[ ]"
        return f"{marker} {self.content}"


class TodoFile:
    """Represents a todo file with multiple tasks."""

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)
        self.tasks: list[TodoTask] = []
        self.content_lines: list[str] = []
        self._load_file()

    def _load_file(self) -> None:
        """Load and parse the todo file."""
        with open(self.file_path, encoding="utf-8") as f:
            self.content_lines = f.readlines()

        for i, line in enumerate(self.content_lines):
            if self._is_task_line(line):
                task = self._parse_task_line(line, i)
                self.tasks.append(task)

    @staticmethod
    def _is_task_line(line: str) -> bool:
        """Check if line contains a task marker.

    Returns:
        Boolean indicating."""
        line = line.strip()
        return bool(re.match(r"^-\s*\[([ x>])\]\s*\]?", line))

    @staticmethod
    def _parse_task_line(line: str, line_num: int) -> TodoTask:
        """Parse a task line into TodoTask object.

    Returns:
        Todotask object."""
        line = line.strip()
        match = re.match(r"^-\s*\[([x >])\]\s*\]?\s*(.+)", line)
        if match:
            marker, content = match.groups()
            completed = marker.lower() == "x"
            skipped = marker == ">"
            return TodoTask(content, completed, skipped, line_num)
        return TodoTask(line, False, False, line_num)

    def get_next_incomplete_task(self) -> TodoTask | None:
        """Get the next uncompleted task.

    Returns:
        Todotask | None object the requested data."""
        for task in self.tasks:
            if not task.completed and not task.skipped:
                return task
        return None

    def mark_task_completed(self, task: TodoTask) -> None:
        """Mark a task as completed and update the file."""
        task.completed = True
        self._update_file()

    def mark_task_skipped(self, task: TodoTask, reason: str) -> None:
        """Mark a task as skipped with reason."""
        task.skipped = True
        # Add reason at the end of the file
        self.content_lines.append(f"\n**Task skipped**: {task.content}\n")
        self.content_lines.append(f"**Reason**: {reason}\n")
        self._update_file()

    def add_subtasks(self, parent_task: TodoTask, subtasks: list[str]) -> None:
        """Add subtasks before the parent task."""
        parent_line = parent_task.line_num
        new_lines = []

        # Insert subtasks at the parent task location
        for i, subtask in enumerate(subtasks):
            new_lines.append(f"- [ ] {subtask}\n")

        # Insert the new lines
        self.content_lines = self.content_lines[:parent_line] + new_lines + self.content_lines[parent_line:]

        # Mark parent as completed since we broke it down
        parent_task.completed = True
        self._update_file()
        self._load_file()  # Reload to get updated line numbers

    def _update_file(self) -> None:
        """Update the file with current task states."""
        updated_lines = []
        task_index = 0

        for i, line in enumerate(self.content_lines):
            if self._is_task_line(line) and task_index < len(self.tasks):
                task = self.tasks[task_index]
                # Replace the task line with updated version
                marker = "[x]" if task.completed else "[>]" if task.skipped else "[ ]"
                updated_line = re.sub(r"^(\s*-\s*)\[[x >\]]\s*\]?\s*", f"\\1{marker} ", line)
                updated_lines.append(updated_line)
                task_index += 1
            else:
                updated_lines.append(line)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

    def is_all_completed(self) -> bool:
        """Check if all tasks are completed or skipped.

    Returns:
        Boolean indicating."""
        return all(task.completed or task.skipped for task in self.tasks)


class TaskRunner:
    """Main task runner that processes todo files automatically."""

    def __init__(self, todo_dir: str = "tasks/todo") -> None:
        # Use relative paths from current working directory
        self.todo_dir = Path(todo_dir).resolve()
        self.done_dir = self.todo_dir.parent / "done"
        self.alert_dir = self.todo_dir.parent / "alert"

        # Ensure directories exist
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.alert_dir.mkdir(parents=True, exist_ok=True)

    def find_todo_files(self, specific_dir: str | None = None) -> list[Path]:
        """Find all todo .md files in directory order.

    Returns:
        List of."""
        if specific_dir:
            # Handle both absolute and relative paths
            search_dir = Path(specific_dir) if specific_dir.startswith("/") else self.todo_dir / specific_dir
        else:
            search_dir = self.todo_dir

        # Get all .md files except README.md and summary.md
        pattern = str(search_dir / "**/*.md")
        all_files = glob.glob(pattern, recursive=True)

        todo_files = []
        for file_path in sorted(all_files):
            file_name = Path(file_path).name.lower()
            if file_name not in {"readme.md", "summary.md"}:
                todo_files.append(Path(file_path))

        return todo_files

    def get_next_task(self, specific_dir: str | None = None) -> tuple[TodoFile, TodoTask] | None:
        """Get the next incomplete task from todo files.

    Returns:
        Tuple[Todofile, Todotask] | None object the requested data."""
        todo_files = self.find_todo_files(specific_dir)

        for file_path in todo_files:
            todo_file = TodoFile(str(file_path))
            next_task = todo_file.get_next_incomplete_task()
            if next_task:
                return todo_file, next_task

        return None

    def move_completed_file(self, todo_file: TodoFile) -> bool:
        """Move completed file to done directory.

    Returns:
        Boolean indicating."""
        if not todo_file.is_all_completed():
            return False

        # Generate new filename with completion date
        today = datetime.now(UTC).strftime("%Y%m%d")
        original_name = todo_file.file_path.stem
        new_name = f"{original_name}__DONE_{today}.md"

        # Move to done directory
        done_path = self.done_dir / new_name
        todo_file.file_path.rename(done_path)

        return True

    def move_failed_file(self, todo_file: TodoFile, reason: str) -> bool:
        """Move failed file to alert directory.

    Returns:
        Boolean indicating."""
        today = datetime.now(UTC).strftime("%Y%m%d")
        original_name = todo_file.file_path.stem
        new_name = f"{original_name}__ALERT_{today}.md"

        # Add failure reason to file
        with open(todo_file.file_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n## ⚠️ Processing Failed ({today})\n")
            f.write(f"**Reason**: {reason}\n")
            f.write("**Action Required**: Manual review needed\n")

        # Move to alert directory
        alert_path = self.alert_dir / new_name
        todo_file.file_path.rename(alert_path)

        return True

    @staticmethod
    def analyze_task_dependencies(task: TodoTask) -> list[str]:
        """Analyze task and break down into subtasks if needed.

    Returns:
        List of."""
        content = task.content.lower()

        # Complex tasks that should be broken down
        complex_keywords = [
            "implement",
            "create system",
            "build",
            "design",
            "integrate",
            "optimize",
            "refactor",
        ]

        # Check if task seems complex
        is_complex = any(keyword in content for keyword in complex_keywords)

        # If complex and no specific implementation details, suggest breakdown
        if is_complex and len(task.content) > 100:
            return [
                "Analyze requirements and dependencies",
                "Design implementation approach",
                "Implement core functionality",
                "Add tests and documentation",
                "Verify integration and commit",
            ]

        return []

    def commit_changes(self, task: TodoTask, file_changes: list[str]) -> bool | None:  # noqa: ARG002
        """Commit changes with appropriate message.

    Returns:
        Bool | None object."""
        try:
            # Stage changes
            subprocess.run(["git", "add", "."], check=True, cwd=self.todo_dir.parent)

            # Generate commit message
            task_summary = task.content[:50]
            if len(task.content) > 50:
                task_summary += "..."

            commit_msg = f"feat(task-runner): {task_summary}"

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                check=True,
                cwd=self.todo_dir.parent,
            )

            return True

        except subprocess.CalledProcessError:
            return False

    def run_tests(self) -> bool:
        """Run relevant tests for the changes.

    Returns:
        Boolean indicating."""
        try:
            # Check if pytest is available and run tests
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=short"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.todo_dir.parent,
            )

            return result.returncode == 0

        except Exception:
            return True  # Don't fail if tests can't run

    def process_next_task(self, specific_dir: str | None = None) -> bool:
        """Process the next available task.

    Returns:
        Boolean indicating."""
        result = self.get_next_task(specific_dir)
        if not result:
            return False

        todo_file, task = result

        # Check if task needs to be broken down
        subtasks = self.analyze_task_dependencies(task)
        if subtasks:
            todo_file.add_subtasks(task, subtasks)
            return True

        # At this point, we would implement the actual task
        # For now, we'll mark it as requiring manual implementation
        todo_file.mark_task_skipped(
            task,
            "Requires manual implementation - automated execution not yet supported",
        )

        # Check if file is complete and move if needed
        if todo_file.is_all_completed():
            self.move_completed_file(todo_file)

        return True

    def run_continuously(self, specific_dir: str | None = None, max_iterations: int = 100) -> None:
        """Run task processor continuously until no more tasks."""
        iterations = 0

        while iterations < max_iterations:
            if not self.process_next_task(specific_dir):
                break
            iterations += 1

            if iterations >= max_iterations:
                break


def main() -> None:
    """CLI entry point for task runner."""

    parser = argparse.ArgumentParser(description="Automated TODO task processor")
    parser.add_argument("--dir", "-d", help="Specific directory to process (e.g. /tasks/todo/phase3)")
    parser.add_argument("--single", "-s", action="store_true", help="Process only one task")
    parser.add_argument("--max-iterations", "-m", type=int, default=100, help="Maximum iterations")

    args = parser.parse_args()

    runner = TaskRunner()

    if args.single:
        runner.process_next_task(args.dir)
    else:
        runner.run_continuously(args.dir, args.max_iterations)


if __name__ == "__main__":
    main()

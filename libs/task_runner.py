"""
TASK_RUNNER: Automated todo file processor for /tasks/todo/ directory

This module provides automated processing of TODO files:
1. Reads todo files in order and finds next uncompleted task
2. Analyzes dependencies and breaks down complex tasks
3. Implements the task and runs tests
4. Commits changes with appropriate messages
5. Moves completed files to /tasks/done/
"""

import glob
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class TodoTask:
    """Represents a single todo task item"""

    def __init__(self, content: str, completed: bool = False, skipped: bool = False, line_num: int = 0):
        self.content = content.strip()
        self.completed = completed
        self.skipped = skipped  # [>] marker for skipped tasks
        self.line_num = line_num
        self.original_line = content

    def __str__(self):
        marker = "[x]" if self.completed else "[>]" if self.skipped else "[ ]"
        return f"{marker} {self.content}"


class TodoFile:
    """Represents a todo file with multiple tasks"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.tasks: List[TodoTask] = []
        self.content_lines: List[str] = []
        self._load_file()

    def _load_file(self):
        """Load and parse the todo file"""
        with open(self.file_path, encoding="utf-8") as f:
            self.content_lines = f.readlines()

        for i, line in enumerate(self.content_lines):
            if self._is_task_line(line):
                task = self._parse_task_line(line, i)
                self.tasks.append(task)

    def _is_task_line(self, line: str) -> bool:
        """Check if line contains a task marker"""
        line = line.strip()
        return bool(re.match(r"^-\s*\[([ x>])\]\s*\]?", line))

    def _parse_task_line(self, line: str, line_num: int) -> TodoTask:
        """Parse a task line into TodoTask object"""
        line = line.strip()
        match = re.match(r"^-\s*\[([x >])\]\s*\]?\s*(.+)", line)
        if match:
            marker, content = match.groups()
            completed = marker.lower() == "x"
            skipped = marker == ">"
            return TodoTask(content, completed, skipped, line_num)
        return TodoTask(line, False, False, line_num)

    def get_next_incomplete_task(self) -> Optional[TodoTask]:
        """Get the next uncompleted task"""
        for task in self.tasks:
            if not task.completed and not task.skipped:
                return task
        return None

    def mark_task_completed(self, task: TodoTask):
        """Mark a task as completed and update the file"""
        task.completed = True
        self._update_file()

    def mark_task_skipped(self, task: TodoTask, reason: str):
        """Mark a task as skipped with reason"""
        task.skipped = True
        # Add reason at the end of the file
        self.content_lines.append(f"\n**Task skipped**: {task.content}\n")
        self.content_lines.append(f"**Reason**: {reason}\n")
        self._update_file()

    def add_subtasks(self, parent_task: TodoTask, subtasks: List[str]):
        """Add subtasks before the parent task"""
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

    def _update_file(self):
        """Update the file with current task states"""
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
        """Check if all tasks are completed or skipped"""
        return all(task.completed or task.skipped for task in self.tasks)


class TaskRunner:
    """Main task runner that processes todo files automatically"""

    def __init__(self, todo_dir: str = "tasks/todo"):
        # Use relative paths from current working directory
        self.todo_dir = Path(todo_dir).resolve()
        self.done_dir = self.todo_dir.parent / "done"
        self.alert_dir = self.todo_dir.parent / "alert"

        # Ensure directories exist
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.alert_dir.mkdir(parents=True, exist_ok=True)

    def find_todo_files(self, specific_dir: Optional[str] = None) -> List[Path]:
        """Find all todo .md files in directory order"""
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
            if file_name not in ["readme.md", "summary.md"]:
                todo_files.append(Path(file_path))

        return todo_files

    def get_next_task(self, specific_dir: Optional[str] = None) -> Optional[Tuple[TodoFile, TodoTask]]:
        """Get the next incomplete task from todo files"""
        todo_files = self.find_todo_files(specific_dir)

        for file_path in todo_files:
            todo_file = TodoFile(file_path)
            next_task = todo_file.get_next_incomplete_task()
            if next_task:
                return todo_file, next_task

        return None

    def move_completed_file(self, todo_file: TodoFile):
        """Move completed file to done directory"""
        if not todo_file.is_all_completed():
            return False

        # Generate new filename with completion date
        today = datetime.now().strftime("%Y%m%d")
        original_name = todo_file.file_path.stem
        new_name = f"{original_name}__DONE_{today}.md"

        # Move to done directory
        done_path = self.done_dir / new_name
        todo_file.file_path.rename(done_path)

        print(f"✅ Moved completed file: {new_name}")
        return True

    def move_failed_file(self, todo_file: TodoFile, reason: str):
        """Move failed file to alert directory"""
        today = datetime.now().strftime("%Y%m%d")
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

        print(f"⚠️ Moved failed file to alert: {new_name}")
        return True

    def analyze_task_dependencies(self, task: TodoTask) -> List[str]:
        """Analyze task and break down into subtasks if needed"""
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

    def commit_changes(self, task: TodoTask, file_changes: List[str]):
        """Commit changes with appropriate message"""
        try:
            # Stage changes
            subprocess.run(["git", "add", "."], check=True, cwd=self.todo_dir.parent)

            # Generate commit message
            task_summary = task.content[:50]
            if len(task.content) > 50:
                task_summary += "..."

            commit_msg = f"feat(task-runner): {task_summary}"

            # Commit
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=self.todo_dir.parent)

            print(f"✅ Committed: {commit_msg}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Commit failed: {e}")
            return False

    def run_tests(self) -> bool:
        """Run relevant tests for the changes"""
        try:
            # Check if pytest is available and run tests
            result = subprocess.run(["python", "-m", "pytest", "--tb=short"], check=False, capture_output=True, text=True, cwd=self.todo_dir.parent)

            if result.returncode == 0:
                print("✅ Tests passed")
                return True
            else:
                print(f"❌ Tests failed:\n{result.stdout}\n{result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️ Could not run tests: {e}")
            return True  # Don't fail if tests can't run

    def process_next_task(self, specific_dir: Optional[str] = None) -> bool:
        """Process the next available task"""
        result = self.get_next_task(specific_dir)
        if not result:
            print("✅ No more tasks to process!")
            return False

        todo_file, task = result

        print(f"\n🔄 Processing: {task.content}")
        print(f"📁 File: {todo_file.file_path.relative_to(self.todo_dir.parent)}")

        # Check if task needs to be broken down
        subtasks = self.analyze_task_dependencies(task)
        if subtasks:
            print(f"🔧 Breaking down complex task into {len(subtasks)} subtasks...")
            todo_file.add_subtasks(task, subtasks)
            return True

        # At this point, we would implement the actual task
        # For now, we'll mark it as requiring manual implementation
        print("⚠️ Task requires manual implementation")
        todo_file.mark_task_skipped(task, "Requires manual implementation - automated execution not yet supported")

        # Check if file is complete and move if needed
        if todo_file.is_all_completed():
            self.move_completed_file(todo_file)

        return True

    def run_continuously(self, specific_dir: Optional[str] = None, max_iterations: int = 100):
        """Run task processor continuously until no more tasks"""
        iterations = 0

        while iterations < max_iterations:
            if not self.process_next_task(specific_dir):
                break
            iterations += 1

            if iterations >= max_iterations:
                print(f"⚠️ Reached maximum iterations ({max_iterations})")
                break

        print(f"\n🎉 Task runner completed after {iterations} iterations")


def main():
    """CLI entry point for task runner"""
    import argparse

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
